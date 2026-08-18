"""StackOracle — allocate resources across LLM/tool/human/data/asset providers."""

from __future__ import annotations

import json
from typing import Any

from sandbox.core import Database
from sandbox.types import (
    ResourceAllocation,
    ResourceNeed,
    ResourceType,
    new_id,
    utc_now,
)


class StackOracle:
    def __init__(self, db: Database):
        self.db = db

    def register_need(self, description: str, required_capabilities: list[str], budget_usd: float, deadline_seconds: int, quality_floor: float = 0.7) -> ResourceNeed:
        need = ResourceNeed(
            need_id=new_id("need"),
            description=description,
            required_capabilities=tuple(required_capabilities),
            budget_usd=budget_usd,
            deadline_seconds=deadline_seconds,
            quality_floor=quality_floor,
        )
        with self.db.tx() as con:
            con.execute(
                """INSERT INTO resource_needs
                   (need_id, description, required_capabilities_json, budget_usd,
                    deadline_seconds, quality_floor, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    need.need_id,
                    need.description,
                    json.dumps(list(need.required_capabilities)),
                    need.budget_usd,
                    need.deadline_seconds,
                    need.quality_floor,
                    need.created_at,
                ),
            )
        return need

    def allocate(self, need_id: str, resource_type: ResourceType, resource_id: str, expected_cost_usd: float, expected_confidence: float, expected_time_seconds: int, reason_codes: list[str] | None = None) -> ResourceAllocation:
        alloc = ResourceAllocation(
            allocation_id=new_id("alloc"),
            need_id=need_id,
            resource_type=resource_type,
            resource_id=resource_id,
            expected_cost_usd=expected_cost_usd,
            expected_confidence=expected_confidence,
            expected_time_seconds=expected_time_seconds,
            reason_codes=tuple(reason_codes or []),
        )
        with self.db.tx() as con:
            con.execute(
                """INSERT INTO resource_allocations
                   (allocation_id, need_id, resource_type, resource_id,
                    expected_cost_usd, expected_confidence, expected_time_seconds,
                    reason_codes_json, allocated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    alloc.allocation_id,
                    alloc.need_id,
                    alloc.resource_type.value,
                    alloc.resource_id,
                    alloc.expected_cost_usd,
                    alloc.expected_confidence,
                    alloc.expected_time_seconds,
                    json.dumps(list(alloc.reason_codes)),
                    alloc.allocated_at,
                ),
            )
        return alloc

    def record_outcome(self, allocation_id: str, actual_cost_usd: float | None, actual_confidence: float | None, success: bool | None, evidence: dict[str, Any] | None = None) -> None:
        with self.db.tx() as con:
            con.execute(
                """INSERT INTO allocation_outcomes
                   (outcome_id, allocation_id, actual_cost_usd, actual_confidence,
                    success, evidence_json, recorded_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    new_id("aoutcome"),
                    allocation_id,
                    actual_cost_usd,
                    actual_confidence,
                    1 if success else (0 if success is not None else None),
                    json.dumps(evidence or {}),
                    utc_now(),
                ),
            )

    def get_need(self, need_id: str) -> dict[str, Any] | None:
        with self.db.connect() as con:
            row = con.execute(
                "SELECT * FROM resource_needs WHERE need_id = ?", (need_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_allocations(self, need_id: str) -> list[dict[str, Any]]:
        with self.db.connect() as con:
            rows = con.execute(
                "SELECT * FROM resource_allocations WHERE need_id = ? ORDER BY allocated_at",
                (need_id,),
            ).fetchall()
            return [dict(r) for r in rows]
