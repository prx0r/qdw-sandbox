from __future__ import annotations
import dataclasses,httpx
from ..contracts import ExecutionEnvelope,ExecutionReceipt,ArtifactRef
class RemoteSandboxClient:
    def __init__(self,base_url:str,timeout:float=1200): self.base_url=base_url.rstrip('/'); self.timeout=timeout
    def execute(self,envelope:ExecutionEnvelope)->ExecutionReceipt:
        d=dataclasses.asdict(envelope); r=httpx.post(self.base_url+'/v1/runs',json=d,timeout=self.timeout); r.raise_for_status(); x=r.json()
        def ar(v): return ArtifactRef(**v)
        return ExecutionReceipt(episode_id=x['episode_id'],sandbox_id=x['sandbox_id'],started_at=x['started_at'],finished_at=x['finished_at'],exit_code=x['exit_code'],stdout=ar(x['stdout']),stderr=ar(x['stderr']),patch=ar(x['patch']) if x.get('patch') else None,environment_hash=x['environment_hash'],wall_ms=x['wall_ms'],killed_reason=x.get('killed_reason'),metadata=x.get('metadata',{}))
