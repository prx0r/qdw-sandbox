"""Tests for system composition root."""

from sandbox.system import SandboxSystem


def test_doctor(tmp_path):
    system = SandboxSystem(str(tmp_path / "test.db"))
    result = system.doctor()
    assert result["ok"] is True
    assert "bounty_definitions" in result["tables"]
    assert "worker_profiles" in result["tables"]
    assert "data_licences" in result["tables"]


def test_get_rights_backend(tmp_path):
    system = SandboxSystem(str(tmp_path / "test.db"))
    backend = system.get_rights_backend()
    assert backend is not None
    # Same instance on second call
    assert system.get_rights_backend() is backend
