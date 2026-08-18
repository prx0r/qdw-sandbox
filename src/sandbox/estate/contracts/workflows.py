from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any
from ..hashing import sha256_obj

@dataclass(frozen=True)
class GraphNodeSpec:
    node_id: str
    capability_request_id: str
    title: str
    payload: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class GraphEdgeSpec:
    src: str
    dst: str
    relation: str = "blocks"

@dataclass(frozen=True)
class WorkflowTemplate:
    template_id: str
    version: str
    nodes: tuple[dict[str, Any], ...]
    edges: tuple[dict[str, Any], ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    @property
    def content_hash(self)->str: return sha256_obj(asdict(self))

@dataclass(frozen=True)
class RealizedGraphSpec:
    graph_id: str
    template_id: str | None
    template_version: str | None
    nodes: tuple[GraphNodeSpec, ...]
    edges: tuple[GraphEdgeSpec, ...] = ()
    planner_resource_id: str | None = None
    supersedes_graph_id: str | None = None
    sealed: bool = False
    @property
    def content_hash(self)->str: return sha256_obj(asdict(self))
