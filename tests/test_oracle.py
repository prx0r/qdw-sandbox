"""Tests for stack oracle."""

from sandbox.core import Database
from sandbox.oracle import StackOracle
from sandbox.types import ResourceType


def make_db(tmp_path):
    return Database(str(tmp_path / "test.db"))


def test_register_and_get_need(tmp_path):
    db = make_db(tmp_path)
    oracle = StackOracle(db)
    need = oracle.register_need("Find 30 examples", ["research", "web"], 50.0, 7200)
    got = oracle.get_need(need.need_id)
    assert got is not None
    assert got["description"] == "Find 30 examples"


def test_allocate(tmp_path):
    db = make_db(tmp_path)
    oracle = StackOracle(db)
    need = oracle.register_need("Test task", [], 100.0, 3600)
    alloc = oracle.allocate(need.need_id, ResourceType.HUMAN, "w1", 25.0, 0.85, 1800, ["cost_optimal"])
    allocs = oracle.get_allocations(need.need_id)
    assert len(allocs) == 1
    assert allocs[0]["resource_type"] == "human"


def test_record_outcome(tmp_path):
    db = make_db(tmp_path)
    oracle = StackOracle(db)
    need = oracle.register_need("Test", [], 100.0, 3600)
    alloc = oracle.allocate(need.need_id, ResourceType.LLM, "gpt4", 5.0, 0.9, 300)
    oracle.record_outcome(alloc.allocation_id, 4.5, 0.92, True, {"evidence": "passed"})
    with db.connect() as con:
        rows = con.execute("SELECT * FROM allocation_outcomes").fetchall()
        assert len(rows) == 1
        assert rows[0]["success"] == 1
