"""Intelligence module — TensionSynthesizer."""

from __future__ import annotations

import json
from typing import Any

from sandbox.core import Database
from sandbox.types import Tension, new_id, utc_now


class TensionSynthesizer:
    def __init__(self, db: Database):
        self.db = db

    def create_tension(self, space_id: str, subject_segment: str, dimension: str,
                       observed_state_concept: str, desired_state_concept: str,
                       prevalence: float = 0.0, recurrence: float = 0.0,
                       severity: float = 0.0, persistence: float = 0.0,
                       confidence: float = 0.0, evidence: dict[str, Any] | None = None) -> Tension:
        tension = Tension(
            tension_id=new_id("tension"),
            space_id=space_id,
            subject_segment=subject_segment,
            dimension=dimension,
            observed_state_concept=observed_state_concept,
            desired_state_concept=desired_state_concept,
            prevalence=prevalence,
            recurrence=recurrence,
            severity=severity,
            persistence=persistence,
            confidence=confidence,
            evidence=evidence or {},
        )
        with self.db.tx() as con:
            con.execute(
                """INSERT INTO tensions
                   (tension_id, space_id, subject_segment, dimension,
                    observed_state_concept, desired_state_concept,
                    evidence_json, prevalence, recurrence, severity,
                    persistence, confidence, status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (tension.tension_id, tension.space_id, tension.subject_segment,
                 tension.dimension, tension.observed_state_concept,
                 tension.desired_state_concept, json.dumps(tension.evidence),
                 tension.prevalence, tension.recurrence, tension.severity,
                 tension.persistence, tension.confidence, tension.status,
                 tension.created_at, tension.updated_at),
            )
        return tension

    def add_evidence(self, tension_id: str, evidence_key: str, evidence_data: Any) -> None:
        with self.db.connect() as con:
            row = con.execute("SELECT evidence_json FROM tensions WHERE tension_id = ?", (tension_id,)).fetchone()
            if not row:
                return
            evidence = json.loads(row["evidence_json"])
            evidence[evidence_key] = evidence_data
        with self.db.tx() as con:
            con.execute(
                "UPDATE tensions SET evidence_json = ?, updated_at = ? WHERE tension_id = ?",
                (json.dumps(evidence), utc_now(), tension_id),
            )

    def get_tension(self, tension_id: str) -> dict[str, Any] | None:
        with self.db.connect() as con:
            row = con.execute("SELECT * FROM tensions WHERE tension_id = ?", (tension_id,)).fetchone()
            return dict(row) if row else None

    def list_tensions(self, space_id: str | None = None, dimension: str | None = None) -> list[dict[str, Any]]:
        with self.db.connect() as con:
            query = "SELECT * FROM tensions WHERE 1=1"
            params: list[Any] = []
            if space_id:
                query += " AND space_id = ?"
                params.append(space_id)
            if dimension:
                query += " AND dimension = ?"
                params.append(dimension)
            query += " ORDER BY confidence DESC, severity DESC"
            rows = con.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def score_opportunity(self, tension_id: str) -> dict[str, Any] | None:
        tension = self.get_tension(tension_id)
        if not tension:
            return None
        score = (
            tension["prevalence"] * 0.25
            + tension["severity"] * 0.25
            + tension["recurrence"] * 0.20
            + tension["persistence"] * 0.15
            + tension["confidence"] * 0.15
        )
        return {
            "tension_id": tension_id,
            "opportunity_score": round(score, 4),
            "prevalence": tension["prevalence"],
            "severity": tension["severity"],
            "recurrence": tension["recurrence"],
            "persistence": tension["persistence"],
            "confidence": tension["confidence"],
        }
