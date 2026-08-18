"""SandboxSystem — single composition root. All DI happens here."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sandbox.bounty import BountyRegistry, BountyResolver, BountyVerifier
from sandbox.core import Database
from sandbox.data_rights import DataRightsBackend, RightsBackend, get_backend
from sandbox.human import HumanOracle
from sandbox.oracle import StackOracle


class SandboxSystem:
    def __init__(self, db_path: str | Path):
        self.db = Database(db_path)
        self.db.migrate()

        # Bounty Engine
        self.bounties = BountyRegistry(self.db)
        self.bounty_resolver = BountyResolver(self.db)
        self.bounty_verifier = BountyVerifier(self.db)

        # Human Oracle
        self.human_oracle = HumanOracle(self.db)

        # Data Rights
        self._rights_backends: dict[RightsBackend, DataRightsBackend] = {}
        self._default_rights_backend = RightsBackend.NATIVE_LOCAL

        # Stack Oracle
        self.oracle = StackOracle(self.db)

    def get_rights_backend(self, backend: RightsBackend | None = None) -> DataRightsBackend:
        key = backend or self._default_rights_backend
        if key not in self._rights_backends:
            self._rights_backends[key] = get_backend(key, self.db)
        return self._rights_backends[key]

    def doctor(self) -> dict[str, Any]:
        with self.db.connect() as con:
            tables = [
                r["name"]
                for r in con.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                ).fetchall()
            ]
        return {
            "ok": True,
            "tables": tables,
            "bounty_count": len(self.bounties.list_bounties()),
        }
