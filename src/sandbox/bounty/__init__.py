"""Bounty Engine — create, resolve, verify bounties across 4 types."""

from __future__ import annotations

import json
from typing import Any

from sandbox.core import Database
from sandbox.types import (
    BountyCertificate,
    BountyEvaluation,
    BountyGate,
    BountySpec,
    BountyStatus,
    BountyType,
    Submission,
    SubmissionFormat,
    SubmissionStatus,
    hash_object,
    new_id,
    utc_now,
)


class BountyRegistry:
    def __init__(self, db: Database):
        self.db = db

    def create_bounty(self, spec: BountySpec) -> BountySpec:
        with self.db.tx() as con:
            con.execute(
                """INSERT INTO bounty_definitions
                   (bounty_id, bounty_type, title, description, requirement,
                    budget_usd, deadline_seconds, submission_format_json,
                    verification_commands_json, tags_json, status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    spec.bounty_id,
                    spec.bounty_type.value,
                    spec.title,
                    spec.description,
                    spec.requirement,
                    spec.budget_usd,
                    spec.deadline_seconds,
                    json.dumps({"schema_version": spec.submission_format.schema_version,
                                "required_fields": list(spec.submission_format.required_fields),
                                "optional_fields": list(spec.submission_format.optional_fields),
                                "content_hash_required": spec.submission_format.content_hash_required,
                                "min_sources": spec.submission_format.min_sources,
                                "source_families_required": spec.submission_format.source_families_required}),
                    json.dumps(list(spec.verification_commands)),
                    json.dumps(list(spec.tags)),
                    spec.status.value,
                    spec.created_at,
                ),
            )
        return spec

    def open_bounty(self, bounty_id: str) -> None:
        with self.db.tx() as con:
            con.execute(
                "UPDATE bounty_definitions SET status = ? WHERE bounty_id = ?",
                (BountyStatus.OPEN.value, bounty_id),
            )

    def get_bounty(self, bounty_id: str) -> dict[str, Any] | None:
        with self.db.connect() as con:
            row = con.execute(
                "SELECT * FROM bounty_definitions WHERE bounty_id = ?", (bounty_id,)
            ).fetchone()
            return dict(row) if row else None

    def list_bounties(self, status: str | None = None) -> list[dict[str, Any]]:
        with self.db.connect() as con:
            if status:
                rows = con.execute(
                    "SELECT * FROM bounty_definitions WHERE status = ? ORDER BY created_at DESC",
                    (status,),
                ).fetchall()
            else:
                rows = con.execute(
                    "SELECT * FROM bounty_definitions ORDER BY created_at DESC"
                ).fetchall()
            return [dict(r) for r in rows]


class BountyResolver:
    def __init__(self, db: Database):
        self.db = db

    def evaluate_options(self, bounty_id: str) -> list[BountyEvaluation]:
        """Evaluate which resource types could solve this bounty."""
        with self.db.connect() as con:
            row = con.execute(
                "SELECT * FROM bounty_definitions WHERE bounty_id = ?", (bounty_id,)
            ).fetchone()
            if not row:
                return []

        bounty = dict(row)
        evaluations = []

        from sandbox.types import ResourceType

        for rt in ResourceType:
            ev = BountyEvaluation(
                resource_type=rt,
                expected_cost_usd=bounty["budget_usd"] * 0.5,
                confidence=0.5,
                time_seconds=bounty["deadline_seconds"],
                evidence_quality=0.5,
            )
            evaluations.append(ev)

        evaluations.sort(key=lambda e: e.expected_cost_usd)
        return evaluations

    def submit(self, bounty_id: str, solver_id: str, resource_type: str, content: dict[str, Any]) -> Submission:
        content_hash = hash_object(content)
        sub = Submission(
            submission_id=new_id("sub"),
            bounty_id=bounty_id,
            solver_id=solver_id,
            resource_type=resource_type,
            content=content,
            content_hash=content_hash,
        )
        with self.db.tx() as con:
            con.execute(
                """INSERT INTO bounty_submissions
                   (submission_id, bounty_id, solver_id, resource_type,
                    content_json, content_hash, status, submitted_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    sub.submission_id,
                    sub.bounty_id,
                    sub.solver_id,
                    sub.resource_type,
                    json.dumps(sub.content),
                    sub.content_hash,
                    sub.status.value,
                    sub.submitted_at,
                ),
            )
            con.execute(
                "UPDATE bounty_definitions SET status = ? WHERE bounty_id = ?",
                (BountyStatus.SUBMITTED.value, bounty_id),
            )
        return sub

    def get_submissions(self, bounty_id: str) -> list[dict[str, Any]]:
        with self.db.connect() as con:
            rows = con.execute(
                "SELECT * FROM bounty_submissions WHERE bounty_id = ? ORDER BY submitted_at",
                (bounty_id,),
            ).fetchall()
            return [dict(r) for r in rows]


class BountyVerifier:
    def __init__(self, db: Database):
        self.db = db

    def add_gate(self, bounty_id: str, gate_type: str, command: str, expected_exit_code: int = 0, timeout_seconds: int = 300) -> BountyGate:
        gate = BountyGate(
            gate_id=new_id("gate"),
            bounty_id=bounty_id,
            gate_type=gate_type,
            command=command,
            expected_exit_code=expected_exit_code,
            timeout_seconds=timeout_seconds,
        )
        with self.db.tx() as con:
            con.execute(
                """INSERT INTO bounty_gates
                   (gate_id, bounty_id, gate_type, command, expected_exit_code, timeout_seconds)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (gate.gate_id, gate.bounty_id, gate.gate_type, gate.command,
                 gate.expected_exit_code, gate.timeout_seconds),
            )
        return gate

    def get_gates(self, bounty_id: str) -> list[dict[str, Any]]:
        with self.db.connect() as con:
            rows = con.execute(
                "SELECT * FROM bounty_gates WHERE bounty_id = ?", (bounty_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    def issue_certificate(self, bounty_id: str, submission_id: str, artifact_hashes: list[str], gate_hashes: list[str], ledger_root: str, source_commit: str) -> BountyCertificate:
        cert = BountyCertificate(
            certificate_id=new_id("cert"),
            bounty_id=bounty_id,
            submission_id=submission_id,
            artifact_hashes=tuple(artifact_hashes),
            gate_hashes=tuple(gate_hashes),
            ledger_root=ledger_root,
            source_commit=source_commit,
        )
        with self.db.tx() as con:
            con.execute(
                """INSERT INTO bounty_certificates
                   (certificate_id, bounty_id, submission_id, artifact_hashes_json,
                    gate_hashes_json, ledger_root, source_commit, issued_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    cert.certificate_id,
                    cert.bounty_id,
                    cert.submission_id,
                    json.dumps(list(cert.artifact_hashes)),
                    json.dumps(list(cert.gate_hashes)),
                    cert.ledger_root,
                    cert.source_commit,
                    cert.issued_at,
                ),
            )
        return cert
