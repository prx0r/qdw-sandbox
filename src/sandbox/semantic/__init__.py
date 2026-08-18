"""Semantic module — semantic objects, idea→tension promotion."""

from __future__ import annotations

import json
from typing import Any

from sandbox.core import Database
from sandbox.types import SemanticObject, SemanticObjectType, new_id, utc_now


class SemanticObjectStore:
    def __init__(self, db: Database):
        self.db = db

    def create_object(self, space_id: str, object_type: SemanticObjectType,
                      canonical_key: str, content: dict[str, Any] | None = None,
                      subject_entity_id: str = "", confidence: float = 1.0) -> SemanticObject:
        now = utc_now()
        obj = SemanticObject(
            object_id=new_id("semobj"),
            space_id=space_id,
            object_type_term_id=object_type,
            canonical_key=canonical_key,
            subject_entity_id=subject_entity_id,
            content=content or {},
            first_observed_at=now,
            last_observed_at=now,
            confidence=confidence,
            updated_at=now,
        )
        with self.db.tx() as con:
            con.execute(
                """INSERT INTO semantic_objects
                   (object_id, space_id, object_type_term_id, subject_entity_id,
                    canonical_key, content_json, first_observed_at, last_observed_at,
                    status, confidence, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (obj.object_id, obj.space_id, obj.object_type_term_id.value,
                 obj.subject_entity_id, obj.canonical_key, json.dumps(obj.content),
                 obj.first_observed_at, obj.last_observed_at, obj.status,
                 obj.confidence, obj.created_at, obj.updated_at),
            )
        return obj

    def touch(self, object_id: str) -> None:
        with self.db.tx() as con:
            con.execute(
                "UPDATE semantic_objects SET last_observed_at = ?, updated_at = ? WHERE object_id = ?",
                (utc_now(), utc_now(), object_id),
            )

    def get_object(self, object_id: str) -> dict[str, Any] | None:
        with self.db.connect() as con:
            row = con.execute("SELECT * FROM semantic_objects WHERE object_id = ?", (object_id,)).fetchone()
            return dict(row) if row else None

    def find_by_key(self, space_id: str, canonical_key: str) -> dict[str, Any] | None:
        with self.db.connect() as con:
            row = con.execute(
                "SELECT * FROM semantic_objects WHERE space_id = ? AND canonical_key = ?",
                (space_id, canonical_key),
            ).fetchone()
            return dict(row) if row else None

    def list_objects(self, space_id: str | None = None, object_type: str | None = None,
                     status: str | None = None) -> list[dict[str, Any]]:
        with self.db.connect() as con:
            query = "SELECT * FROM semantic_objects WHERE 1=1"
            params: list[Any] = []
            if space_id:
                query += " AND space_id = ?"
                params.append(space_id)
            if object_type:
                query += " AND object_type_term_id = ?"
                params.append(object_type)
            if status:
                query += " AND status = ?"
                params.append(status)
            query += " ORDER BY last_observed_at DESC"
            rows = con.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def promote_to_hypothesis(self, object_id: str) -> dict[str, Any] | None:
        """Promote a semantic IDEA object to a ProductHypothesis-like object."""
        obj = self.get_object(object_id)
        if not obj or obj["object_type_term_id"] != "idea":
            return None
        with self.db.tx() as con:
            con.execute(
                "UPDATE semantic_objects SET object_type_term_id = ?, status = ?, updated_at = ? WHERE object_id = ?",
                ("hypothesis", "promoted", utc_now(), object_id),
            )
        return self.get_object(object_id)

    def find_dormant(self, space_id: str, days_threshold: int = 90) -> list[dict[str, Any]]:
        """Find semantic objects with no recent activity (Idea Cemetery candidates)."""
        from datetime import datetime, timedelta, timezone
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days_threshold)).isoformat()
        with self.db.connect() as con:
            rows = con.execute(
                """SELECT * FROM semantic_objects
                   WHERE space_id = ? AND object_type_term_id = 'idea'
                   AND status = 'active' AND last_observed_at < ?
                   ORDER BY last_observed_at""",
                (space_id, cutoff),
            ).fetchall()
            return [dict(r) for r in rows]
