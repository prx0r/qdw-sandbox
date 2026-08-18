from __future__ import annotations
from pathlib import Path
from .store import EstateStore
from .routing import EstateRouter
from .episodes import EpisodeService
from .verification import EstateVerificationService
from .context import ContextAssembler
from .artifacts import LocalCAS
from .catalog import EstateCatalog
class EstateServices:
    """Composition bundle attached to SandboxSystem as `self.estate`."""
    def __init__(self,sandbox_system,artifact_root='data/artifacts'):
        self.store=EstateStore(sandbox_system.db)
        self.artifacts=LocalCAS(artifact_root)
        self.router=EstateRouter(self.store)
        self.episodes=EpisodeService(self.store)
        self.context=ContextAssembler(self.store,self.artifacts)
        graph_store=getattr(sandbox_system,'graphs',None)
        ledger=getattr(sandbox_system,'ledger',None)
        self.verification=EstateVerificationService(self.store,sandbox_system.db,graph_store,ledger)
        self.catalog=EstateCatalog(sandbox_system.db)
