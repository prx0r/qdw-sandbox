from __future__ import annotations

import json
from pathlib import Path

from sandbox.lifegit.db import LifeDB


def snapshot(db: LifeDB, at: str) -> dict:
    """Return only material observed at/before an ISO date/time."""
    cutoff = at if "T" in at else at + "T23:59:59+00:00"
    with db.connect() as con:
        conversations = [dict(r) for r in con.execute(
            "SELECT conversation_id,provider,title,created_at FROM conversations WHERE created_at IS NULL OR created_at<=? ORDER BY created_at", (cutoff,)
        )]
        objects = [dict(r) for r in con.execute(
            "SELECT object_id,object_type,canonical_text,first_observed_at,confidence,evidence_message_id FROM semantic_objects WHERE first_observed_at IS NULL OR first_observed_at<=? ORDER BY first_observed_at", (cutoff,)
        )]
        tensions = [dict(r) for r in con.execute(
            "SELECT * FROM tensions WHERE first_observed_at IS NULL OR first_observed_at<=? ORDER BY first_observed_at", (cutoff,)
        )]
    return {"as_of": at, "conversations": conversations, "semantic_objects": objects, "tensions": tensions}


def write_snapshot(db: LifeDB, at: str, path: str | Path) -> dict:
    data = snapshot(db, at)
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"path": str(p), "as_of": at, "objects": len(data["semantic_objects"])}
