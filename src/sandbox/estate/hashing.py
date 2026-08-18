from __future__ import annotations
import hashlib, json
from dataclasses import asdict, is_dataclass
from typing import Any

def _default(v: Any):
    if is_dataclass(v): return asdict(v)
    if hasattr(v, "model_dump"): return v.model_dump(mode="json")
    raise TypeError(type(v).__name__)

def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=_default).encode("utf-8")

def sha256_obj(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()

def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()
