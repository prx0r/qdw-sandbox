"""QDW Sandbox API — thin interface, zero business logic."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="QDW Sandbox API")

_system: Any = None


def _get_system():
    global _system
    if _system is None:
        from sandbox.system import SandboxSystem
        _system = SandboxSystem("data/sandbox.db")
    return _system


@app.get("/")
def root():
    return {
        "service": "qdw-sandbox",
        "version": "0.1.0",
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health")
def health():
    return _get_system().doctor()


# ── Bounty endpoints ──────────────────────────────────────────────────────


class CreateBountyRequest(BaseModel):
    bounty_type: str
    title: str
    description: str
    requirement: str
    budget_usd: float
    deadline_seconds: int
    tags: list[str] = []


@app.post("/bounties")
def create_bounty(req: CreateBountyRequest):
    from sandbox.types import BountySpec, BountyType, SubmissionFormat, new_id
    sys = _get_system()
    spec = BountySpec(
        bounty_id=new_id("bounty"),
        bounty_type=BountyType(req.bounty_type),
        title=req.title,
        description=req.description,
        requirement=req.requirement,
        budget_usd=req.budget_usd,
        deadline_seconds=req.deadline_seconds,
        submission_format=SubmissionFormat(),
        tags=tuple(req.tags),
    )
    sys.bounties.create_bounty(spec)
    return {"bounty_id": spec.bounty_id, "status": "created"}


@app.get("/bounties")
def list_bounties(status: str | None = None):
    return _get_system().bounties.list_bounties(status)


@app.get("/bounties/{bounty_id}")
def get_bounty(bounty_id: str):
    bounty = _get_system().bounties.get_bounty(bounty_id)
    if not bounty:
        return {"error": "not_found"}
    return bounty


@app.post("/bounties/{bounty_id}/open")
def open_bounty(bounty_id: str):
    _get_system().bounties.open_bounty(bounty_id)
    return {"status": "opened"}


@app.post("/bounties/{bounty_id}/evaluate")
def evaluate_bounty(bounty_id: str):
    return _get_system().bounty_resolver.evaluate_options(bounty_id)


class SubmitRequest(BaseModel):
    solver_id: str
    resource_type: str
    content: dict[str, Any]


@app.post("/bounties/{bounty_id}/submit")
def submit_bounty(bounty_id: str, req: SubmitRequest):
    sub = _get_system().bounty_resolver.submit(bounty_id, req.solver_id, req.resource_type, req.content)
    return {"submission_id": sub.submission_id, "status": sub.status.value}


@app.get("/bounties/{bounty_id}/submissions")
def list_submissions(bounty_id: str):
    return _get_system().bounty_resolver.get_submissions(bounty_id)


# ── Human Oracle endpoints ────────────────────────────────────────────────


@app.get("/workers")
def list_workers():
    return _get_system().human_oracle.workers.list_workers()


class RegisterWorkerRequest(BaseModel):
    worker_id: str
    capabilities: list[str]
    identity_verified: bool = False


@app.post("/workers")
def register_worker(req: RegisterWorkerRequest):
    from sandbox.types import WorkerCapability
    caps = [WorkerCapability(c) for c in req.capabilities]
    _get_system().human_oracle.workers.register_worker(req.worker_id, caps, req.identity_verified)
    return {"status": "registered"}


@app.get("/workers/resolve")
def resolve_workers(capability: str, budget_usd: float = 100.0, deadline_seconds: int = 3600):
    from sandbox.types import WorkerCapability
    return _get_system().human_oracle.resolve("", WorkerCapability(capability), budget_usd, deadline_seconds)


# ── Data Rights endpoints ─────────────────────────────────────────────────


@app.get("/licences")
def list_licences(asset_id: str | None = None):
    return _get_system().get_rights_backend().list_licences(asset_id)


class RegisterLicenceRequest(BaseModel):
    asset_id: str
    contributor_id: str
    purpose: str
    scope: str
    window_start: str
    window_end: str
    operations: list[str]
    raw_export: bool = False
    training: bool = False
    redistribution: bool = False
    expires_at: str = ""
    price_usd: float = 0.0


@app.post("/licences")
def register_licence(req: RegisterLicenceRequest):
    from sandbox.types import DataLicence, LicenseOperation, RightsBackend, new_id
    licence = DataLicence(
        licence_id=new_id("licence"),
        asset_id=req.asset_id,
        contributor_id=req.contributor_id,
        purpose=req.purpose,
        scope=req.scope,
        window_start=req.window_start,
        window_end=req.window_end,
        operations=tuple(LicenseOperation(o) for o in req.operations),
        raw_export=req.raw_export,
        training=req.training,
        redistribution=req.redistribution,
        expires_at=req.expires_at,
        price_usd=req.price_usd,
    )
    _get_system().get_rights_backend().register_licence(licence)
    return {"licence_id": licence.licence_id, "status": "registered"}


class CheckClearanceRequest(BaseModel):
    asset_id: str
    purpose: str
    operations: list[str]


@app.post("/licences/check")
def check_clearance(req: CheckClearanceRequest):
    from sandbox.types import LicenseOperation
    ops = [LicenseOperation(o) for o in req.operations]
    cr = _get_system().get_rights_backend().check_clearance(req.asset_id, req.purpose, ops)
    return {"granted": cr.granted, "reason": cr.reason, "licence_id": cr.licence_id}


# ── Stack Oracle endpoints ────────────────────────────────────────────────


class RegisterNeedRequest(BaseModel):
    description: str
    required_capabilities: list[str] = []
    budget_usd: float = 100.0
    deadline_seconds: int = 3600
    quality_floor: float = 0.7


@app.post("/oracle/needs")
def register_need(req: RegisterNeedRequest):
    need = _get_system().oracle.register_need(req.description, req.required_capabilities, req.budget_usd, req.deadline_seconds, req.quality_floor)
    return {"need_id": need.need_id, "status": "created"}


@app.get("/oracle/needs/{need_id}")
def get_need(need_id: str):
    need = _get_system().oracle.get_need(need_id)
    if not need:
        return {"error": "not_found"}
    return need


@app.get("/oracle/needs/{need_id}/allocations")
def get_allocations(need_id: str):
    return _get_system().oracle.get_allocations(need_id)


class AllocateRequest(BaseModel):
    resource_type: str
    resource_id: str
    expected_cost_usd: float
    expected_confidence: float
    expected_time_seconds: int
    reason_codes: list[str] = []


@app.post("/oracle/needs/{need_id}/allocate")
def allocate(need_id: str, req: AllocateRequest):
    from sandbox.types import ResourceType
    alloc = _get_system().oracle.allocate(
        need_id, ResourceType(req.resource_type), req.resource_id,
        req.expected_cost_usd, req.expected_confidence,
        req.expected_time_seconds, req.reason_codes,
    )
    return {"allocation_id": alloc.allocation_id, "status": "allocated"}
