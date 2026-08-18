from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any
from ..hashing import sha256_obj

@dataclass(frozen=True)
class ArtifactRef:
    uri: str
    sha256: str
    size_bytes: int | None = None
    media_type: str | None = None

@dataclass(frozen=True)
class WorkspaceSpec:
    repository_url: str
    revision: str
    sparse_paths: tuple[str,...] = ()

@dataclass(frozen=True)
class ResourceLimits:
    wall_seconds: int = 900
    memory_mb: int = 4096
    cpu_count: float = 2.0
    pids: int = 128

@dataclass(frozen=True)
class SandboxPolicy:
    backend: str = "docker"
    network: str = "none"
    allowed_domains: tuple[str,...] = ()
    read_only_root: bool = True
    workspace_write: bool = True

@dataclass(frozen=True)
class ExecutionEnvelope:
    episode_id: str
    command: tuple[str,...]
    workspace: WorkspaceSpec
    limits: ResourceLimits = field(default_factory=ResourceLimits)
    policy: SandboxPolicy = field(default_factory=SandboxPolicy)
    environment: dict[str,str] = field(default_factory=dict)
    metadata: dict[str,Any] = field(default_factory=dict)
    @property
    def content_hash(self)->str: return sha256_obj(asdict(self))

@dataclass(frozen=True)
class ExecutionReceipt:
    episode_id: str
    sandbox_id: str
    started_at: str
    finished_at: str
    exit_code: int
    stdout: ArtifactRef
    stderr: ArtifactRef
    patch: ArtifactRef | None
    environment_hash: str
    wall_ms: int
    killed_reason: str | None = None
    metadata: dict[str,Any] = field(default_factory=dict)
    @property
    def receipt_hash(self)->str: return sha256_obj(asdict(self))
