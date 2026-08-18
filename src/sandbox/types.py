"""Core types for qdw-sandbox — bounty engine, human oracle, data rights."""

from __future__ import annotations

import enum
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def new_id(prefix: str = "sbx") -> str:
    return f"{prefix}_{secrets.token_hex(12)}"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_json(obj: Any) -> str:
    import json
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(data: bytes) -> str:
    import hashlib
    return hashlib.sha256(data).hexdigest()


def hash_object(obj: Any) -> str:
    return sha256_hex(canonical_json(obj).encode())


# ── Bounty Types ──────────────────────────────────────────────────────────


class BountyType(enum.Enum):
    TASK = "task"
    DATA = "data"
    EVIDENCE = "evidence"
    ASSET = "asset"


class BountyStatus(enum.Enum):
    DRAFT = "draft"
    OPEN = "open"
    SUBMITTED = "submitted"
    VERIFYING = "verifying"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PAID = "paid"
    CLOSED = "closed"
    EXPIRED = "expired"


class SubmissionStatus(enum.Enum):
    PENDING = "pending"
    VALIDATING = "validating"
    VALID = "valid"
    INVALID = "invalid"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class ResourceType(enum.Enum):
    LLM = "llm"
    TOOL = "tool"
    API = "api"
    BROWSER = "browser"
    COMPUTE = "compute"
    HUMAN = "human"
    DATASET = "dataset"
    REPOSITORY = "repository"
    PAID_SOURCE = "paid_source"
    EXPERT_REVIEW = "expert_review"


# ── Bounty Spec ───────────────────────────────────────────────────────────


@dataclass(frozen=True)
class SubmissionFormat:
    schema_version: str = "1.0"
    required_fields: tuple[str, ...] = ()
    optional_fields: tuple[str, ...] = ()
    content_hash_required: bool = True
    min_sources: int = 0
    source_families_required: int = 0


@dataclass(frozen=True)
class BountySpec:
    bounty_id: str
    bounty_type: BountyType
    title: str
    description: str
    requirement: str
    budget_usd: float
    deadline_seconds: int
    submission_format: SubmissionFormat
    verification_commands: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    created_at: str = field(default_factory=utc_now)
    status: BountyStatus = BountyStatus.DRAFT


@dataclass(frozen=True)
class BountyEvaluation:
    resource_type: ResourceType
    expected_cost_usd: float
    confidence: float
    time_seconds: int
    evidence_quality: float
    rights_clearance: str = "unknown"
    risk: float = 0.0


@dataclass(frozen=True)
class Submission:
    submission_id: str
    bounty_id: str
    solver_id: str
    resource_type: ResourceType
    content: dict[str, Any]
    content_hash: str
    submitted_at: str = field(default_factory=utc_now)
    status: SubmissionStatus = SubmissionStatus.PENDING


@dataclass(frozen=True)
class BountyReward:
    reward_id: str
    bounty_id: str
    submission_id: str
    solver_id: str
    amount_usd: float
    paid_at: str = field(default_factory=utc_now)


# ── Human Oracle Types ────────────────────────────────────────────────────


class WorkerCapability(enum.Enum):
    QA_TESTING = "qa_testing"
    USABILITY = "usability"
    RESEARCH = "research"
    DATA_ENTRY = "data_entry"
    CONTENT_REVIEW = "content_review"
    FIELD_WORK = "field_work"
    EXPERT_JUDGMENT = "expert_judgment"
    COMPREHENSION_TEST = "comprehension_test"


@dataclass(frozen=True)
class WorkerProfile:
    worker_id: str
    capabilities: tuple[WorkerCapability, ...]
    reputation: float = 0.5
    completion_rate: float = 0.0
    total_tasks: int = 0
    avg_quality: float = 0.0
    identity_verified: bool = False
    created_at: str = field(default_factory=utc_now)


@dataclass(frozen=True)
class HumanRoute:
    route_id: str
    worker_id: str
    capabilities: tuple[WorkerCapability, ...]
    cost_per_hour_usd: float
    reliability: float
    latency_seconds: int
    active: bool = True


# ── Data Rights Types ─────────────────────────────────────────────────────


class RightsBackend(enum.Enum):
    NATIVE_LOCAL = "native_local"
    VANA = "vana"
    ENTERPRISE_VAULT = "enterprise_vault"


class LicenseOperation(enum.Enum):
    AGGREGATE = "aggregate"
    CLASSIFY = "classify"
    CLUSTER = "cluster"
    READ = "read"
    EXPORT = "export"
    TRAIN = "train"
    REDISTRIBUTE = "redistribute"


@dataclass(frozen=True)
class DataLicence:
    licence_id: str
    asset_id: str
    contributor_id: str
    purpose: str
    scope: str
    window_start: str
    window_end: str
    operations: tuple[LicenseOperation, ...]
    raw_export: bool = False
    training: bool = False
    redistribution: bool = False
    expires_at: str = ""
    price_usd: float = 0.0
    rights_backend: RightsBackend = RightsBackend.NATIVE_LOCAL
    created_at: str = field(default_factory=utc_now)


@dataclass(frozen=True)
class RightsClearance:
    licence_id: str
    asset_id: str
    granted: bool
    reason: str = ""
    checked_at: str = field(default_factory=utc_now)


# ── Oracle Types ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ResourceNeed:
    need_id: str
    description: str
    required_capabilities: tuple[str, ...]
    budget_usd: float
    deadline_seconds: int
    quality_floor: float = 0.7


@dataclass(frozen=True)
class ResourceAllocation:
    allocation_id: str
    need_id: str
    resource_type: ResourceType
    resource_id: str
    expected_cost_usd: float
    expected_confidence: float
    expected_time_seconds: int
    reason_codes: tuple[str, ...] = ()


# ── Integration with QDW ─────────────────────────────────────────────────


@dataclass(frozen=True)
class BountyGate:
    gate_id: str
    bounty_id: str
    gate_type: str
    command: str
    expected_exit_code: int = 0
    timeout_seconds: int = 300


@dataclass(frozen=True)
class BountyCertificate:
    certificate_id: str
    bounty_id: str
    submission_id: str
    artifact_hashes: tuple[str, ...]
    gate_hashes: tuple[str, ...]
    ledger_root: str
    source_commit: str
    issued_at: str = field(default_factory=utc_now)
