"""DataRightsBackend — abstract data rights/licensing interface."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

from sandbox.core import Database
from sandbox.types import (
    DataLicence,
    LicenseOperation,
    RightsBackend,
    RightsClearance,
    new_id,
    utc_now,
)


class DataRightsBackend(ABC):
    @abstractmethod
    def check_clearance(self, asset_id: str, purpose: str, operations: list[LicenseOperation]) -> RightsClearance: ...

    @abstractmethod
    def register_licence(self, licence: DataLicence) -> DataLicence: ...

    @abstractmethod
    def list_licences(self, asset_id: str | None = None) -> list[dict[str, Any]]: ...


class NativeLocalBackend(DataRightsBackend):
    def __init__(self, db: Database):
        self.db = db

    def check_clearance(self, asset_id: str, purpose: str, operations: list[LicenseOperation]) -> RightsClearance:
        with self.db.connect() as con:
            rows = con.execute(
                """SELECT * FROM data_licences
                   WHERE asset_id = ? AND purpose = ?
                   AND (expires_at = '' OR expires_at > ?)""",
                (asset_id, purpose, utc_now()),
            ).fetchall()

        for row in rows:
            licence = dict(row)
            ops = json.loads(licence["operations_json"])
            granted = all(op.value in ops for op in operations)
            if granted:
                cr = RightsClearance(
                    licence_id=licence["licence_id"],
                    asset_id=asset_id,
                    granted=True,
                )
                self._log_clearance(cr)
                return cr

        cr = RightsClearance(
            licence_id="",
            asset_id=asset_id,
            granted=False,
            reason="no_matching_licence",
        )
        self._log_clearance(cr)
        return cr

    def register_licence(self, licence: DataLicence) -> DataLicence:
        with self.db.tx() as con:
            con.execute(
                """INSERT INTO data_licences
                   (licence_id, asset_id, contributor_id, purpose, scope,
                    window_start, window_end, operations_json, raw_export,
                    training, redistribution, expires_at, price_usd,
                    rights_backend, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    licence.licence_id,
                    licence.asset_id,
                    licence.contributor_id,
                    licence.purpose,
                    licence.scope,
                    licence.window_start,
                    licence.window_end,
                    json.dumps([op.value for op in licence.operations]),
                    1 if licence.raw_export else 0,
                    1 if licence.training else 0,
                    1 if licence.redistribution else 0,
                    licence.expires_at,
                    licence.price_usd,
                    licence.rights_backend.value,
                    licence.created_at,
                ),
            )
        return licence

    def list_licences(self, asset_id: str | None = None) -> list[dict[str, Any]]:
        with self.db.connect() as con:
            if asset_id:
                rows = con.execute(
                    "SELECT * FROM data_licences WHERE asset_id = ? ORDER BY created_at DESC",
                    (asset_id,),
                ).fetchall()
            else:
                rows = con.execute(
                    "SELECT * FROM data_licences ORDER BY created_at DESC"
                ).fetchall()
            return [dict(r) for r in rows]

    def _log_clearance(self, cr: RightsClearance) -> None:
        with self.db.tx() as con:
            con.execute(
                """INSERT INTO data_rights_log
                   (log_id, licence_id, asset_id, granted, reason, checked_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (new_id("drlog"), cr.licence_id, cr.asset_id, 1 if cr.granted else 0, cr.reason, cr.checked_at),
            )


class VanaBackend(DataRightsBackend):
    """Placeholder for Vana DLP integration."""

    def check_clearance(self, asset_id: str, purpose: str, operations: list[LicenseOperation]) -> RightsClearance:
        return RightsClearance(licence_id="vana_stub", asset_id=asset_id, granted=False, reason="vana_not_implemented")

    def register_licence(self, licence: DataLicence) -> DataLicence:
        return licence

    def list_licences(self, asset_id: str | None = None) -> list[dict[str, Any]]:
        return []


class EnterpriseVaultBackend(DataRightsBackend):
    """Placeholder for enterprise vault integration."""

    def check_clearance(self, asset_id: str, purpose: str, operations: list[LicenseOperation]) -> RightsClearance:
        return RightsClearance(licence_id="vault_stub", asset_id=asset_id, granted=False, reason="vault_not_implemented")

    def register_licence(self, licence: DataLicence) -> DataLicence:
        return licence

    def list_licences(self, asset_id: str | None = None) -> list[dict[str, Any]]:
        return []


def get_backend(backend: RightsBackend, db: Database) -> DataRightsBackend:
    if backend == RightsBackend.NATIVE_LOCAL:
        return NativeLocalBackend(db)
    elif backend == RightsBackend.VANA:
        return VanaBackend()
    elif backend == RightsBackend.ENTERPRISE_VAULT:
        return EnterpriseVaultBackend()
    else:
        raise ValueError(f"unknown backend: {backend}")
