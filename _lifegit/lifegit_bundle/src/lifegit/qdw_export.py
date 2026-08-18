from __future__ import annotations

import json
from pathlib import Path

from lifegit.db import LifeDB


def export_qdw_jsonl(db: LifeDB, path: str | Path, *, space_id: str = "life:default") -> dict:
    """Export private LifeGit facts into a QDW-friendly event stream.

    This does not publish them. ``space_id`` must remain private until an
    explicit grant exists.
    """
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with db.connect() as con, out.open("w", encoding="utf-8") as f:
        for r in con.execute("SELECT * FROM conversations ORDER BY created_at"):
            rec = {
                "record_type": "entity",
                "kind": "conversation",
                "external_key": r["conversation_id"],
                "space_id": space_id,
                "attributes": {
                    "provider": r["provider"],
                    "title": r["title"],
                    "created_at": r["created_at"],
                },
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
        for r in con.execute("SELECT * FROM semantic_objects ORDER BY first_observed_at"):
            rec = {
                "record_type": "semantic_object",
                "object_id": r["object_id"],
                "space_id": space_id,
                "object_type": r["object_type"],
                "canonical_text": r["canonical_text"],
                "observed_at": r["first_observed_at"],
                "confidence": r["confidence"],
                "privacy_class": r["privacy_class"],
                "evidence": {
                    "message_id": r["evidence_message_id"],
                    "conversation_id": r["evidence_conversation_id"],
                },
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
        for r in con.execute("SELECT * FROM tensions ORDER BY first_observed_at"):
            rec = {
                "record_type": "tension",
                "tension_id": r["tension_id"],
                "space_id": space_id,
                "tension_type": r["tension_type"],
                "current_state": r["current_state"],
                "desired_state": r["desired_state"],
                "recurrence": r["recurrence"],
                "confidence": r["confidence"],
                "evidence_count": r["evidence_count"],
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    return {"records": n, "path": str(out)}
