from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import StrEnum
from typing import Any
from ..hashing import sha256_obj

class EpisodeStatus(StrEnum):
    CREATED="CREATED"; RUNNING="RUNNING"; SUBMITTED="SUBMITTED"; VERIFYING="VERIFYING"; VERIFIED="VERIFIED"; FAILED="FAILED"; CANCELLED="CANCELLED"

@dataclass(frozen=True)
class ExecutionEpisodeRecord:
    episode_id: str
    graph_id: str
    node_id: str
    attempt_number: int
    capability_request_id: str
    route_decision_id: str
    resource_id: str
    executor_config_hash: str | None = None
    context_pack_id: str | None = None
    sandbox_id: str | None = None
    status: EpisodeStatus = EpisodeStatus.CREATED
    started_at: str | None = None
    finished_at: str | None = None
    wall_ms: int | None = None
    model_cost_usd: float = 0.0
    tool_cost_usd: float = 0.0
    compute_cost_usd: float = 0.0
    human_cost_usd: float = 0.0
    output_hash: str | None = None
    failure_class: str | None = None
    trace_artifact_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    @property
    def total_cost_usd(self)->float: return self.model_cost_usd+self.tool_cost_usd+self.compute_cost_usd+self.human_cost_usd
    @property
    def content_hash(self)->str: return sha256_obj(asdict(self))
