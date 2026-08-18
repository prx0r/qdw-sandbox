"""HumanOracle — route tasks to humans as another capability provider."""

from __future__ import annotations

import json
from typing import Any

from sandbox.core import Database
from sandbox.types import (
    HumanRoute,
    ResourceType,
    WorkerCapability,
    WorkerProfile,
    new_id,
    utc_now,
)


class WorkerRegistry:
    def __init__(self, db: Database):
        self.db = db

    def register_worker(self, worker_id: str, capabilities: list[WorkerCapability], identity_verified: bool = False) -> WorkerProfile:
        profile = WorkerProfile(
            worker_id=worker_id,
            capabilities=tuple(capabilities),
            identity_verified=identity_verified,
        )
        with self.db.tx() as con:
            con.execute(
                """INSERT OR REPLACE INTO worker_profiles
                   (worker_id, capabilities_json, reputation, completion_rate,
                    total_tasks, avg_quality, identity_verified, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    profile.worker_id,
                    json.dumps([c.value for c in profile.capabilities]),
                    profile.reputation,
                    profile.completion_rate,
                    profile.total_tasks,
                    profile.avg_quality,
                    1 if profile.identity_verified else 0,
                    profile.created_at,
                ),
            )
        return profile

    def get_worker(self, worker_id: str) -> dict[str, Any] | None:
        with self.db.connect() as con:
            row = con.execute(
                "SELECT * FROM worker_profiles WHERE worker_id = ?", (worker_id,)
            ).fetchone()
            return dict(row) if row else None

    def list_workers(self) -> list[dict[str, Any]]:
        with self.db.connect() as con:
            rows = con.execute("SELECT * FROM worker_profiles ORDER BY reputation DESC").fetchall()
            return [dict(r) for r in rows]


class HumanRouter:
    def __init__(self, db: Database):
        self.db = db

    def register_route(self, worker_id: str, cost_per_hour_usd: float, reliability: float, latency_seconds: int) -> HumanRoute:
        route = HumanRoute(
            route_id=new_id("hroute"),
            worker_id=worker_id,
            capabilities=(),
            cost_per_hour_usd=cost_per_hour_usd,
            reliability=reliability,
            latency_seconds=latency_seconds,
        )
        with self.db.tx() as con:
            con.execute(
                """INSERT INTO human_routes
                   (route_id, worker_id, capabilities_json, cost_per_hour_usd,
                    reliability, latency_seconds, active)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    route.route_id,
                    route.worker_id,
                    json.dumps([]),
                    route.cost_per_hour_usd,
                    route.reliability,
                    route.latency_seconds,
                    1 if route.active else 0,
                ),
            )
        return route

    def find_workers(self, required_capability: WorkerCapability, max_cost_usd: float | None = None) -> list[dict[str, Any]]:
        with self.db.connect() as con:
            rows = con.execute(
                """SELECT hp.*, hr.route_id, hr.cost_per_hour_usd, hr.reliability, hr.latency_seconds
                   FROM worker_profiles hp
                   JOIN human_routes hr ON hp.worker_id = hr.worker_id
                   WHERE hr.active = 1
                   AND hp.capabilities_json LIKE ?
                   ORDER BY hp.reputation DESC, hr.cost_per_hour_usd ASC""",
                (f"%{required_capability.value}%",),
            ).fetchall()
            results = [dict(r) for r in rows]
            if max_cost_usd is not None:
                results = [r for r in results if r["cost_per_hour_usd"] <= max_cost_usd]
            return results

    def log_task(self, bounty_id: str, worker_id: str, action: str, detail: dict[str, Any]) -> None:
        with self.db.tx() as con:
            con.execute(
                """INSERT INTO human_task_log
                   (task_log_id, bounty_id, worker_id, action, detail_json, logged_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (new_id("htlog"), bounty_id, worker_id, action, json.dumps(detail), utc_now()),
            )


class HumanOracle:
    """High-level interface: resolve resource needs to human providers."""

    def __init__(self, db: Database):
        self.workers = WorkerRegistry(db)
        self.router = HumanRouter(db)

    def resolve(self, description: str, capability: WorkerCapability, budget_usd: float, deadline_seconds: int) -> list[dict[str, Any]]:
        candidates = self.router.find_workers(capability, max_cost_usd=budget_usd)
        scored = []
        for c in candidates:
            score = c["reputation"] * 0.4 + c["completion_rate"] * 0.3 + c["avg_quality"] * 0.3
            scored.append({**c, "score": score})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:5]
