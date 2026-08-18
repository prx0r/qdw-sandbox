from __future__ import annotations
from dataclasses import dataclass, field, asdict
from ..hashing import sha256_obj

@dataclass(frozen=True)
class ContextItem:
    ref: str
    kind: str
    sensitivity: str = "internal"
    sha256: str | None = None
    required: bool = True

@dataclass(frozen=True)
class ContextPackManifest:
    context_pack_id: str
    node_id: str
    items: tuple[ContextItem,...]
    policy_id: str
    denied_refs: tuple[str,...] = ()
    @property
    def manifest_hash(self)->str: return sha256_obj(asdict(self))
