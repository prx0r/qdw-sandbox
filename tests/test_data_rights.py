"""Tests for data rights."""

from sandbox.core import Database
from sandbox.data_rights import NativeLocalBackend
from sandbox.types import DataLicence, LicenseOperation, RightsBackend, new_id


def make_db(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    db.migrate()
    return db


def test_register_and_list_licence(tmp_path):
    db = make_db(tmp_path)
    backend = NativeLocalBackend(db)
    licence = DataLicence(
        licence_id=new_id("licence"),
        asset_id="asset_1",
        contributor_id="contrib_1",
        purpose="market_research",
        scope="problem_events.agent_tools",
        window_start="2026-07-01",
        window_end="2026-07-31",
        operations=(LicenseOperation.AGGREGATE, LicenseOperation.CLASSIFY),
    )
    backend.register_licence(licence)
    licences = backend.list_licences("asset_1")
    assert len(licences) == 1
    assert licences[0]["purpose"] == "market_research"


def test_check_clearance_granted(tmp_path):
    db = make_db(tmp_path)
    backend = NativeLocalBackend(db)
    licence = DataLicence(
        licence_id=new_id("licence"),
        asset_id="asset_1",
        contributor_id="contrib_1",
        purpose="research",
        scope="all",
        window_start="2026-01-01",
        window_end="2026-12-31",
        operations=(LicenseOperation.READ, LicenseOperation.AGGREGATE),
    )
    backend.register_licence(licence)
    cr = backend.check_clearance("asset_1", "research", [LicenseOperation.READ])
    assert cr.granted is True


def test_check_clearance_denied(tmp_path):
    db = make_db(tmp_path)
    backend = NativeLocalBackend(db)
    cr = backend.check_clearance("asset_unknown", "research", [LicenseOperation.READ])
    assert cr.granted is False
    assert cr.reason == "no_matching_licence"


def test_check_clearance_insufficient_ops(tmp_path):
    db = make_db(tmp_path)
    backend = NativeLocalBackend(db)
    licence = DataLicence(
        licence_id=new_id("licence"),
        asset_id="asset_1",
        contributor_id="contrib_1",
        purpose="research",
        scope="all",
        window_start="2026-01-01",
        window_end="2026-12-31",
        operations=(LicenseOperation.READ,),
    )
    backend.register_licence(licence)
    cr = backend.check_clearance("asset_1", "research", [LicenseOperation.TRAIN])
    assert cr.granted is False
