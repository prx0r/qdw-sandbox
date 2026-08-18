from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any
from ..hashing import sha256_obj

@dataclass(frozen=True)
class ExecutionConstraints:
    max_cost_usd: float | None = None
    max_wall_seconds: int = 900
    network: str = "none"  # none | public_read | allowlist
    external_writes: bool = False
    human_escalation: bool = False
    required_resource_kinds: tuple[str, ...] = ()
    forbidden_resource_ids: tuple[str, ...] = ()

    def __post_init__(self):
        if self.max_cost_usd is not None and self.max_cost_usd < 0: raise ValueError("max_cost_usd must be >= 0")
        if self.max_wall_seconds <= 0: raise ValueError("max_wall_seconds must be > 0")
        if self.network not in {"none", "public_read", "allowlist"}: raise ValueError("invalid network policy")

@dataclass(frozen=True)
class CapabilityRequest:
    request_id: str
    capability: str
    objective: str
    verification_policy: str
    constraints: ExecutionConstraints = field(default_factory=ExecutionConstraints)
    input_refs: tuple[str, ...] = ()
    context_refs: tuple[str, ...] = ()
    output_schema: str | None = None
    quality_floor: float | None = None
    expected_value_usd: float | None = None
    created_by: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.request_id or not self.capability or not self.objective or not self.verification_policy: raise ValueError("required capability request field empty")
        if self.quality_floor is not None and not 0 <= self.quality_floor <= 1: raise ValueError("quality_floor outside [0,1]")

    @property
    def content_hash(self) -> str: return sha256_obj(asdict(self))
