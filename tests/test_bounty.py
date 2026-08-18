"""Tests for bounty engine."""

from sandbox.bounty import BountyRegistry, BountyResolver, BountyVerifier
from sandbox.core import Database
from sandbox.types import (
    BountySpec,
    BountyType,
    ResourceType,
    SubmissionFormat,
    new_id,
)


def make_db(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    db.migrate()
    return db


def test_create_and_list_bounty(tmp_path):
    db = make_db(tmp_path)
    reg = BountyRegistry(db)
    spec = BountySpec(
        bounty_id=new_id("bounty"),
        bounty_type=BountyType.EVIDENCE,
        title="Find examples",
        description="Find 20 examples of X",
        requirement="URL + quotation + classification",
        budget_usd=50.0,
        deadline_seconds=3600,
        submission_format=SubmissionFormat(required_fields=("url", "quotation")),
    )
    reg.create_bounty(spec)
    bounties = reg.list_bounties()
    assert len(bounties) == 1
    assert bounties[0]["bounty_type"] == "evidence"
    assert bounties[0]["title"] == "Find examples"


def test_open_bounty(tmp_path):
    db = make_db(tmp_path)
    reg = BountyRegistry(db)
    spec = BountySpec(
        bounty_id=new_id("bounty"),
        bounty_type=BountyType.TASK,
        title="Test task",
        description="desc",
        requirement="req",
        budget_usd=10.0,
        deadline_seconds=600,
        submission_format=SubmissionFormat(),
    )
    reg.create_bounty(spec)
    reg.open_bounty(spec.bounty_id)
    bounty = reg.get_bounty(spec.bounty_id)
    assert bounty["status"] == "open"


def test_submit_bounty(tmp_path):
    db = make_db(tmp_path)
    reg = BountyRegistry(db)
    resolver = BountyResolver(db)
    spec = BountySpec(
        bounty_id=new_id("bounty"),
        bounty_type=BountyType.DATA,
        title="Data bounty",
        description="desc",
        requirement="req",
        budget_usd=100.0,
        deadline_seconds=7200,
        submission_format=SubmissionFormat(),
    )
    reg.create_bounty(spec)
    sub = resolver.submit(spec.bounty_id, "worker_1", "human", {"data": "test"})
    assert sub.submission_id.startswith("sub_")
    subs = resolver.get_submissions(spec.bounty_id)
    assert len(subs) == 1


def test_evaluate_bounty(tmp_path):
    db = make_db(tmp_path)
    reg = BountyRegistry(db)
    resolver = BountyResolver(db)
    spec = BountySpec(
        bounty_id=new_id("bounty"),
        bounty_type=BountyType.EVIDENCE,
        title="Eval test",
        description="desc",
        requirement="req",
        budget_usd=200.0,
        deadline_seconds=3600,
        submission_format=SubmissionFormat(),
    )
    reg.create_bounty(spec)
    evals = resolver.evaluate_options(spec.bounty_id)
    assert len(evals) > 0
    assert all(e.expected_cost_usd > 0 for e in evals)


def test_add_gate_and_certificate(tmp_path):
    db = make_db(tmp_path)
    reg = BountyRegistry(db)
    verifier = BountyVerifier(db)
    spec = BountySpec(
        bounty_id=new_id("bounty"),
        bounty_type=BountyType.EVIDENCE,
        title="Gate test",
        description="desc",
        requirement="req",
        budget_usd=10.0,
        deadline_seconds=600,
        submission_format=SubmissionFormat(),
    )
    reg.create_bounty(spec)
    gate = verifier.add_gate(spec.bounty_id, "format", "python -m pytest tests/", 0, 300)
    gates = verifier.get_gates(spec.bounty_id)
    assert len(gates) == 1

    cert = verifier.issue_certificate(spec.bounty_id, "sub_1", ["hash1"], ["ghash1"], "root1", "commit1")
    assert cert.certificate_id.startswith("cert_")
