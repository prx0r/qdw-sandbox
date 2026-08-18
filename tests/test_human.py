"""Tests for human oracle."""

from sandbox.core import Database
from sandbox.human import HumanOracle, WorkerRegistry, HumanRouter
from sandbox.types import WorkerCapability


def make_db(tmp_path):
    return Database(str(tmp_path / "test.db"))


def test_register_worker(tmp_path):
    db = make_db(tmp_path)
    oracle = HumanOracle(db)
    oracle.workers.register_worker("w1", [WorkerCapability.QA_TESTING, WorkerCapability.USABILITY], True)
    workers = oracle.workers.list_workers()
    assert len(workers) == 1
    assert workers[0]["worker_id"] == "w1"
    assert workers[0]["identity_verified"] == 1


def test_register_route_and_find(tmp_path):
    db = make_db(tmp_path)
    oracle = HumanOracle(db)
    oracle.workers.register_worker("w1", [WorkerCapability.RESEARCH])
    oracle.router.register_route("w1", 25.0, 0.9, 3600)
    results = oracle.router.find_workers(WorkerCapability.RESEARCH)
    assert len(results) == 1
    assert results[0]["cost_per_hour_usd"] == 25.0


def test_resolve_workers(tmp_path):
    db = make_db(tmp_path)
    oracle = HumanOracle(db)
    oracle.workers.register_worker("w1", [WorkerCapability.QA_TESTING])
    oracle.router.register_route("w1", 50.0, 0.85, 1800)
    oracle.workers.register_worker("w2", [WorkerCapability.QA_TESTING])
    oracle.router.register_route("w2", 30.0, 0.7, 3600)
    results = oracle.resolve("test app", WorkerCapability.QA_TESTING, 100.0, 7200)
    assert len(results) > 0
    assert results[0]["score"] >= results[-1]["score"]


def test_log_task(tmp_path):
    db = make_db(tmp_path)
    oracle = HumanOracle(db)
    oracle.router.log_task("bounty_1", "w1", "started", {"step": "research"})
    with db.connect() as con:
        rows = con.execute("SELECT * FROM human_task_log").fetchall()
        assert len(rows) == 1
