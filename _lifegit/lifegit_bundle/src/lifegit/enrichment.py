from __future__ import annotations

import json
from pathlib import Path

from lifegit.db import LifeDB
from lifegit.util import normalize_text, stable_id

ALLOWED_TYPES = {
    "QUESTION", "IDEA", "PROBLEM", "PROJECT", "DISCOVERY", "DECISION",
    "GOAL", "ACHIEVEMENT", "WORK_CLAIM"
}

ENRICHMENT_SPEC = {
    "version": "lifegit-semantic-v0.1",
    "instructions": [
        "Extract only information explicitly supported by the user's message.",
        "Do not diagnose personality, mental health, relationships, or motives.",
        "Do not invent outcomes that are not stated.",
        "Every object must quote/closely paraphrase the supported user statement and retain message_id.",
        "Use only allowed object_type values.",
        "confidence is confidence in extraction, not importance.",
        "work_relevance measures whether the statement can plausibly belong in a work history; it is not permission to publish.",
    ],
    "object_schema": {
        "message_id": "string",
        "objects": [{
            "object_type": "enum",
            "canonical_text": "string <= 700 chars",
            "confidence": "0..1",
            "work_relevance": "0..1",
            "attributes": "object"
        }]
    }
}


def export_batches(db: LifeDB, path: str | Path) -> dict:
    """Create provider-neutral JSONL suitable for any batch-capable LLM runner."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with db.connect() as con, out.open("w", encoding="utf-8") as f:
        for r in con.execute("""SELECT m.message_id,m.conversation_id,m.created_at,m.text,c.title
                                FROM messages m JOIN conversations c USING(conversation_id)
                                WHERE m.role='user' AND m.is_current_path=1 AND length(trim(m.text))>0
                                ORDER BY m.created_at"""):
            rec = {
                "schema": ENRICHMENT_SPEC["version"],
                "message_id": r["message_id"],
                "conversation_id": r["conversation_id"],
                "created_at": r["created_at"],
                "conversation_title": r["title"],
                "text": r["text"],
                "instructions": ENRICHMENT_SPEC["instructions"],
                "allowed_types": sorted(ALLOWED_TYPES),
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    spec_path = out.with_suffix(out.suffix + ".schema.json")
    spec_path.write_text(json.dumps(ENRICHMENT_SPEC, indent=2), encoding="utf-8")
    return {"messages": n, "path": str(out), "schema": str(spec_path)}


def apply_results(db: LifeDB, path: str | Path, *, extractor_version: str = "llm-v0.1") -> dict:
    """Apply JSONL enrichment output with strict message provenance checks."""
    applied = skipped = 0
    with db.connect() as con, Path(path).open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            message_id = str(rec.get("message_id") or "")
            msg = con.execute("SELECT * FROM messages WHERE message_id=?", (message_id,)).fetchone()
            if not msg:
                skipped += 1
                continue
            for obj in rec.get("objects") or []:
                typ = str(obj.get("object_type") or "")
                text = " ".join(str(obj.get("canonical_text") or "").split())[:700]
                if typ not in ALLOWED_TYPES or not text:
                    skipped += 1
                    continue
                confidence = float(obj.get("confidence", 0.5))
                work = float(obj.get("work_relevance", 0.0))
                if not (0 <= confidence <= 1 and 0 <= work <= 1):
                    skipped += 1
                    continue
                oid = stable_id("sem", extractor_version, typ, message_id, normalize_text(text))
                privacy = "WORK_CANDIDATE" if work >= 0.45 else "PRIVATE"
                con.execute("""INSERT OR IGNORE INTO semantic_objects(object_id,space_id,object_type,canonical_text,normalized_key,
                    first_observed_at,last_observed_at,status,confidence,extractor_version,privacy_class,work_relevance,
                    evidence_message_id,evidence_conversation_id,attributes_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (oid, "life:default", typ, text, normalize_text(text)[:400], msg["created_at"], msg["created_at"],
                     "ACTIVE", confidence, extractor_version, privacy, work, message_id, msg["conversation_id"],
                     json.dumps(obj.get("attributes") or {}, ensure_ascii=False)))
                applied += 1
    return {"objects_applied": applied, "skipped": skipped}
