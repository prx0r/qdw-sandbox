from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import StrEnum
from typing import Any
from ..hashing import sha256_obj

class ResourceKind(StrEnum):
    MODEL="MODEL"; TOOL="TOOL"; AGENT_EXECUTOR="AGENT_EXECUTOR"; EXECUTOR_CONFIGURATION="EXECUTOR_CONFIGURATION"; SANDBOX="SANDBOX"; ENVIRONMENT="ENVIRONMENT"; HUMAN="HUMAN"; DATA_ASSET="DATA_ASSET"; VERIFIER="VERIFIER"; SERVICE="SERVICE"

@dataclass(frozen=True)
class ExecutorConfiguration:
    config_id: str
    agent_resource_id: str | None = None
    model_resource_id: str | None = None
    harness_recipe_id: str | None = None
    toolset_id: str | None = None
    environment_resource_id: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    @property
    def content_hash(self) -> str: return sha256_obj(asdict(self))

@dataclass(frozen=True)
class ResourceDescriptor:
    resource_id: str
    kind: ResourceKind
    name: str
    version: str | None = None
    capabilities: tuple[str, ...] = ()
    executor_configuration: ExecutorConfiguration | None = None
    interface_kind: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    active: bool = True
    @property
    def content_hash(self) -> str: return sha256_obj(asdict(self))

@dataclass(frozen=True)
class ResourceProfile:
    resource_id: str
    capability: str
    sample_count: int
    verified_success_count: int
    success_alpha: float = 1.0
    success_beta: float = 1.0
    mean_cost_usd: float | None = None
    mean_wall_ms: float | None = None
    failure_distribution: dict[str, int] = field(default_factory=dict)
    updated_at: str | None = None
    @property
    def success_mean(self) -> float: return self.success_alpha/(self.success_alpha+self.success_beta)
    @property
    def cost_per_verified_success(self) -> float | None:
        if self.mean_cost_usd is None or self.success_mean <= 0: return None
        return self.mean_cost_usd/self.success_mean
