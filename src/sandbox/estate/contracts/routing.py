from __future__ import annotations
from dataclasses import dataclass, field, asdict
from ..hashing import sha256_obj

@dataclass(frozen=True)
class RouteCandidate:
    resource_id: str
    eligible: bool
    reason_codes: tuple[str,...] = ()
    predicted_success: float | None = None
    expected_cost_usd: float | None = None
    expected_wall_ms: float | None = None
    score: float | None = None

@dataclass(frozen=True)
class RouteDecision:
    route_decision_id: str
    request_id: str
    policy_id: str
    policy_version: str
    candidates: tuple[RouteCandidate,...]
    chosen_resource_id: str | None
    reason_codes: tuple[str,...] = ()
    created_at: str | None = None
    @property
    def candidate_snapshot_hash(self)->str: return sha256_obj([asdict(x) for x in self.candidates])

@dataclass(frozen=True)
class RoutePlan:
    decision: RouteDecision
    fallbacks: tuple[str,...] = ()
