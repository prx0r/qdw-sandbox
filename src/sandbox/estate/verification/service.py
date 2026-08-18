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
        # All operations in a single transaction for atomicity
        with self.db.tx(immediate=True) as c:
            # Insert certificate
            c.execute('INSERT INTO estate_verification_certificates(verification_certificate_id,subject_type,subject_id,policy_id,certificate_json,certificate_hash,issued_at) VALUES(?,?,?,?,?,?,?)',(cid,'execution_episode',episode_id,policy_id,canonical_bytes(payload).decode(),h,payload['issued_at']))
            # Transition episode: SUBMITTED -> VERIFYING -> VERIFIED (if needed)
            if e['status']=='SUBMITTED':
                c.execute("UPDATE estate_execution_episodes SET status=?,verification_certificate_id=? WHERE episode_id=? AND status=?",(str(EpisodeStatus.VERIFYING),cid,episode_id,str(EpisodeStatus.SUBMITTED)))
            c.execute("UPDATE estate_execution_episodes SET status=?,verification_certificate_id=? WHERE episode_id=? AND status=?",(str(EpisodeStatus.VERIFIED),cid,episode_id,str(EpisodeStatus.VERIFYING)))
        if self.graph_store is not None:
            self.graph_store.complete(e['node_id'],{'estate_episode_id':episode_id,'verification_certificate_id':cid,'certificate_hash':h})
        return cid
