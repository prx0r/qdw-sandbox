from __future__ import annotations
import json,uuid
from datetime import UTC,datetime
from ..hashing import canonical_bytes,sha256_obj
from ..contracts import EpisodeStatus
class EstateVerificationService:
    """Authority bridge: a verifier certificate, never executor output, transitions an episode to VERIFIED."""
    def __init__(self,store,db,graph_store=None,ledger=None): self.store=store; self.db=db; self.graph_store=graph_store; self.ledger=ledger
    def issue_certificate(self,episode_id:str,policy_id:str,gates:list[dict])->str:
        if not gates: raise ValueError('cannot certify zero gates')
        if any(not g.get('passed') for g in gates): raise ValueError('cannot certify failing gates')
        e=self.store.get_episode(episode_id)
        if e['status'] not in {'SUBMITTED','VERIFYING'}: raise ValueError('episode not submitted for verification')
        cid='evc_'+uuid.uuid4().hex[:16]; payload={'certificate_id':cid,'episode_id':episode_id,'node_id':e['node_id'],'policy_id':policy_id,'gates':gates,'issued_at':datetime.now(UTC).isoformat()}; h=sha256_obj(payload)
        with self.db.tx(immediate=True) as c:
            c.execute('INSERT INTO estate_verification_certificates(verification_certificate_id,subject_type,subject_id,policy_id,certificate_json,certificate_hash,issued_at) VALUES(?,?,?,?,?,?,?)',(cid,'execution_episode',episode_id,policy_id,canonical_bytes(payload).decode(),h,payload['issued_at']))
        # transition is separate through EstateStore, which checks legal state. If SUBMITTED first mark VERIFYING.
        if e['status']=='SUBMITTED': self.store.transition_episode(episode_id,{'SUBMITTED'},EpisodeStatus.VERIFYING)
        self.store.transition_episode(episode_id,{'VERIFYING'},EpisodeStatus.VERIFIED,verification_certificate_id=cid)
        if self.graph_store is not None:
            # Existing QDW complete() is only invoked by this authority bridge.
            self.graph_store.complete(e['node_id'],{'estate_episode_id':episode_id,'verification_certificate_id':cid,'certificate_hash':h})
        return cid
