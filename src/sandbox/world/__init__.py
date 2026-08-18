"""World module — spaces, ontology, universal edges."""

from __future__ import annotations

import json
from typing import Any

from sandbox.core import Database
from sandbox.types import ObjectEdge, OntologyKind, OntologyTerm, Space, new_id, utc_now


class SpaceRegistry:
    def __init__(self, db: Database):
        self.db = db

    def create_space(self, space_id: str, kind: str, owner_entity_id: str = "", default_visibility: str = "private", policy_id: str = "") -> Space:
        space = Space(space_id=space_id, kind=kind, owner_entity_id=owner_entity_id,
                      default_visibility=default_visibility, policy_id=policy_id)
        with self.db.tx() as con:
            con.execute(
                """INSERT OR REPLACE INTO spaces
                   (space_id, kind, owner_entity_id, default_visibility, policy_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (space.space_id, space.kind, space.owner_entity_id,
                 space.default_visibility, space.policy_id, space.created_at),
            )
        return space

    def get_space(self, space_id: str) -> dict[str, Any] | None:
        with self.db.connect() as con:
            row = con.execute("SELECT * FROM spaces WHERE space_id = ?", (space_id,)).fetchone()
            return dict(row) if row else None

    def list_spaces(self, kind: str | None = None) -> list[dict[str, Any]]:
        with self.db.connect() as con:
            if kind:
                rows = con.execute("SELECT * FROM spaces WHERE kind = ? ORDER BY created_at", (kind,)).fetchall()
            else:
                rows = con.execute("SELECT * FROM spaces ORDER BY created_at").fetchall()
            return [dict(r) for r in rows]


class OntologyRegistry:
    def __init__(self, db: Database):
        self.db = db

    def register_term(self, kind: OntologyKind, canonical_key: str, label: str, parent_term_id: str = "") -> OntologyTerm:
        term = OntologyTerm(
            term_id=new_id("ont"),
            kind=kind,
            canonical_key=canonical_key,
            label=label,
            parent_term_id=parent_term_id,
        )
        with self.db.tx() as con:
            con.execute(
                """INSERT OR REPLACE INTO ontology_terms
                   (term_id, kind, canonical_key, label, parent_term_id,
                    schema_version, status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (term.term_id, term.kind.value, term.canonical_key, term.label,
                 term.parent_term_id, term.schema_version, term.status, term.created_at),
            )
        return term

    def get_term(self, term_id: str) -> dict[str, Any] | None:
        with self.db.connect() as con:
            row = con.execute("SELECT * FROM ontology_terms WHERE term_id = ?", (term_id,)).fetchone()
            return dict(row) if row else None

    def find_by_key(self, kind: str, canonical_key: str) -> dict[str, Any] | None:
        with self.db.connect() as con:
            row = con.execute(
                "SELECT * FROM ontology_terms WHERE kind = ? AND canonical_key = ?",
                (kind, canonical_key),
            ).fetchone()
            return dict(row) if row else None

    def list_terms(self, kind: str | None = None) -> list[dict[str, Any]]:
        with self.db.connect() as con:
            if kind:
                rows = con.execute("SELECT * FROM ontology_terms WHERE kind = ? ORDER BY canonical_key", (kind,)).fetchall()
            else:
                rows = con.execute("SELECT * FROM ontology_terms ORDER BY kind, canonical_key").fetchall()
            return [dict(r) for r in rows]


class ObjectEdgeStore:
    def __init__(self, db: Database):
        self.db = db

    def add_edge(self, subject_type: str, subject_id: str, predicate_term_id: str,
                 object_type: str, object_id: str, supporting_claim_id: str = "", confidence: float = 1.0) -> ObjectEdge:
        edge = ObjectEdge(
            edge_id=new_id("edge"),
            subject_type=subject_type,
            subject_id=subject_id,
            predicate_term_id=predicate_term_id,
            object_type=object_type,
            object_id=object_id,
            supporting_claim_id=supporting_claim_id,
            confidence=confidence,
        )
        with self.db.tx() as con:
            con.execute(
                """INSERT INTO object_edges
                   (edge_id, subject_type, subject_id, predicate_term_id,
                    object_type, object_id, supporting_claim_id, confidence, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (edge.edge_id, edge.subject_type, edge.subject_id, edge.predicate_term_id,
                 edge.object_type, edge.object_id, edge.supporting_claim_id,
                 edge.confidence, edge.created_at),
            )
        return edge

    def get_edges_from(self, subject_type: str, subject_id: str) -> list[dict[str, Any]]:
        with self.db.connect() as con:
            rows = con.execute(
                "SELECT * FROM object_edges WHERE subject_type = ? AND subject_id = ?",
                (subject_type, subject_id),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_edges_to(self, object_type: str, object_id: str) -> list[dict[str, Any]]:
        with self.db.connect() as con:
            rows = con.execute(
                "SELECT * FROM object_edges WHERE object_type = ? AND object_id = ?",
                (object_type, object_id),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_edges_by_predicate(self, predicate_term_id: str) -> list[dict[str, Any]]:
        with self.db.connect() as con:
            rows = con.execute(
                "SELECT * FROM object_edges WHERE predicate_term_id = ?",
                (predicate_term_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def count_edges(self, subject_type: str | None = None, object_type: str | None = None) -> int:
        with self.db.connect() as con:
            if subject_type and object_type:
                row = con.execute(
                    "SELECT COUNT(*) as c FROM object_edges WHERE subject_type = ? AND object_type = ?",
                    (subject_type, object_type),
                ).fetchone()
            elif subject_type:
                row = con.execute("SELECT COUNT(*) as c FROM object_edges WHERE subject_type = ?", (subject_type,)).fetchone()
            elif object_type:
                row = con.execute("SELECT COUNT(*) as c FROM object_edges WHERE object_type = ?", (object_type,)).fetchone()
            else:
                row = con.execute("SELECT COUNT(*) as c FROM object_edges").fetchone()
            return row["c"]


def seed_default_ontology(registry: OntologyRegistry) -> None:
    """Seed canonical ontology terms."""
    predicates = [
        ("addresses", "Addresses"),
        ("requires", "Requires"),
        ("enables", "Enables"),
        ("derived_from", "Derived From"),
        ("produces", "Produces"),
        ("consumes", "Consumes"),
        ("supports", "Supports"),
        ("contradicts", "Contradicts"),
        ("resolves", "Resolves"),
        ("implements", "Implements"),
    ]
    for key, label in predicates:
        if not registry.find_by_key("predicate", key):
            registry.register_term(OntologyKind.PREDICATE, key, label)

    dimensions = [
        ("information_retrieval", "Information Retrieval"),
        ("api_cost", "API Cost"),
        ("social_connection", "Social Connection"),
        ("developer_productivity", "Developer Productivity"),
        ("data_quality", "Data Quality"),
    ]
    for key, label in dimensions:
        if not registry.find_by_key("dimension", key):
            registry.register_term(OntologyKind.DIMENSION, key, label)

    event_types = [
        ("project_started", "Project Started"),
        ("project_finished", "Project Finished"),
        ("idea_expressed", "Idea Expressed"),
        ("question_asked", "Question Asked"),
        ("problem_resolved", "Problem Resolved"),
        ("role_started", "Role Started"),
        ("achievement", "Achievement"),
        ("discovery", "Discovery"),
    ]
    for key, label in event_types:
        if not registry.find_by_key("event_type", key):
            registry.register_term(OntologyKind.EVENT_TYPE, key, label)
