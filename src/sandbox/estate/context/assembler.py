from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json,uuid
from ..contracts import ContextItem,ContextPackManifest
from ..hashing import sha256_bytes
@dataclass(frozen=True)
class ContextPolicy:
    policy_id:str='default/v1'
    allowed_sensitivities:tuple[str,...]=('public','internal')
    max_bytes:int=2_000_000
class ContextAssembler:
    def __init__(self,store,artifact_store=None): self.store=store; self.artifact_store=artifact_store
    def build(self,node_id:str,candidates:list[dict],policy:ContextPolicy=ContextPolicy()):
        items=[]; denied=[]; used=0; payload=[]
        for c in candidates:
            ref=str(c['ref']); sens=c.get('sensitivity','internal'); data=c.get('content','')
            b=data.encode() if isinstance(data,str) else bytes(data)
            if sens not in policy.allowed_sensitivities or used+len(b)>policy.max_bytes:
                denied.append(ref); continue
            h=sha256_bytes(b); items.append(ContextItem(ref,c.get('kind','text'),sens,h,len(b)>0)); payload.append({'ref':ref,'content':data}); used+=len(b)
        m=ContextPackManifest('ctx_'+uuid.uuid4().hex[:16],node_id,tuple(items),policy.policy_id,tuple(denied))
        artifact_id=None
        if self.artifact_store:
            ar=self.artifact_store.put_bytes(json.dumps(payload,sort_keys=True).encode(),'application/json'); artifact_id=ar.uri
        self.store.put_context_pack(m,artifact_id); return m,payload
