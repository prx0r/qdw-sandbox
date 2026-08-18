"""SandboxSystem — single composition root. All DI happens here."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from sandbox.bounty import BountyRegistry, BountyResolver, BountyVerifier
from sandbox.core import Database
from sandbox.data_rights import DataRightsBackend, RightsBackend, get_backend
from sandbox.human import HumanOracle
from sandbox.intelligence import TensionSynthesizer
from sandbox.oracle import StackOracle
from sandbox.personal import PersonalExtractor, PersonalIngestor, PersonalPrivacy, PersonalReports, PersonalTimeline
from sandbox.r2 import R2Storage
from sandbox.estate import EstateServices
from sandbox.reports import ReportRegistry, ShareRegistry
from sandbox.rights import GrantRegistry
from sandbox.semantic import SemanticObjectStore
from sandbox.temporal import EventStore, StateStore, ThreadStore
from sandbox.world import ObjectEdgeStore, OntologyRegistry, SpaceRegistry, seed_default_ontology


def _load_env(path: str | Path | None = None) -> None:
    """Load .env file into os.environ if not already set."""
    if path is None:
        path = Path(__file__).parent.parent.parent / ".env"
    else:
        path = Path(path)
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key not in os.environ:
            os.environ[key] = value


class SandboxSystem:
    def __init__(self, db_path: str | Path):
        _load_env()

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

        # R2 Storage
        self.r2 = R2Storage()

        # World (spaces, ontology, edges)
        self.spaces = SpaceRegistry(self.db)
        self.ontology = OntologyRegistry(self.db)
        self.edges = ObjectEdgeStore(self.db)

        # Temporal (events, states, threads)
        self.events = EventStore(self.db)
        self.states = StateStore(self.db)
        self.threads = ThreadStore(self.db)

        # Intelligence (tensions)
        self.tensions = TensionSynthesizer(self.db)

        # Semantic (objects, ideas)
        self.semantic = SemanticObjectStore(self.db)

        # Personal (LifeGit)
        self.personal_ingest = PersonalIngestor(self.db)
        self.personal_extract = PersonalExtractor(self.db)
        self.personal_timeline = PersonalTimeline(self.db)
        self.personal_privacy = PersonalPrivacy(self.db)
        self.personal_reports = PersonalReports(self.db)

        # Rights / Grants
        self.grants = GrantRegistry(self.db)

        # Reports
        self.report_registry = ReportRegistry(self.db)
        self.share_registry = ShareRegistry(self.db)

        # Estate (resource orchestration, routing, verification)
        self.estate = EstateServices(self)

        # Seed default ontology
        seed_default_ontology(self.ontology)

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
            ontology_count = con.execute("SELECT COUNT(*) as c FROM ontology_terms").fetchone()["c"]
            space_count = con.execute("SELECT COUNT(*) as c FROM spaces").fetchone()["c"]
            edge_count = con.execute("SELECT COUNT(*) as c FROM object_edges").fetchone()["c"]
            tension_count = con.execute("SELECT COUNT(*) as c FROM tensions").fetchone()["c"]
            semobj_count = con.execute("SELECT COUNT(*) as c FROM semantic_objects").fetchone()["c"]
        return {
            "ok": True,
            "tables": tables,
            "bounty_count": len(self.bounties.list_bounties()),
            "ontology_terms": ontology_count,
            "spaces": space_count,
            "edges": edge_count,
            "tensions": tension_count,
            "semantic_objects": semobj_count,
            "r2_configured": self.r2.is_configured(),
            "r2_bucket": self.r2.bucket,
        }
