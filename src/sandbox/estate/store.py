from __future__ import annotations
import json, sqlite3, uuid
from datetime import UTC, datetime
from dataclasses import asdict
from typing import Any
from .hashing import canonical_bytes, sha256_obj
from .contracts import CapabilityRequest, ResourceDescriptor, RouteDecision, ExecutionEpisodeRecord, EpisodeStatus, ResourceProfile, ContextPackManifest

def now()->str: return datetime.now(UTC).isoformat()

class EstateStore:
    """Additive Estate persistence. Accepts QDW Database or a sqlite path for tests."""
    def __init__(self, db): self.db=db
    def _connect(self):
        if hasattr(self.db,'connect'): return self.db.connect()
        con=sqlite3.connect(str(self.db)); con.row_factory=sqlite3.Row; con.execute('PRAGMA foreign_keys=ON'); return con
    def _tx(self):
        if hasattr(self.db,'tx'): return self.db.tx(immediate=True)
        class C:
            def __init__(s, outer): s.outer=outer
            def __enter__(s): s.con=outer._connect(); s.con.execute('BEGIN IMMEDIATE'); return s.con
            def __exit__(s,t,v,tb): s.con.rollback() if t else s.con.commit(); s.con.close()
        outer=self; return C(self)

    def put_capability_request(self, r: CapabilityRequest)->None:
        with self._tx() as c:
            c.execute("""INSERT INTO capability_requests(request_id,capability,objective,request_json,request_hash,verification_policy,status,created_at)
                         VALUES(?,?,?,?,?,?,?,?)""",(r.request_id,r.capability,r.objective,canonical_bytes(asdict(r)).decode(),r.content_hash,r.verification_policy,'OPEN',now()))

    def put_resource(self, r: ResourceDescriptor)->None:
        payload=canonical_bytes(asdict(r)).decode()
        with self._tx() as c:
            row=c.execute('SELECT descriptor_hash FROM estate_resources WHERE resource_id=?',(r.resource_id,)).fetchone()
            if row and row['descriptor_hash']!=r.content_hash: raise ValueError('immutable resource descriptor conflict; register a new versioned resource_id')
            c.execute("""INSERT OR IGNORE INTO estate_resources(resource_id,kind,name,version,descriptor_json,descriptor_hash,status,created_at)
                         VALUES(?,?,?,?,?,?,?,?)""",(r.resource_id,str(r.kind),r.name,r.version,payload,r.content_hash,'ACTIVE' if r.active else 'DISABLED',now()))
            for cap in r.capabilities:
                c.execute('INSERT OR IGNORE INTO estate_resource_capabilities(resource_id,capability) VALUES(?,?)',(r.resource_id,cap))

    def list_resources(self, capability:str|None=None)->list[ResourceDescriptor]:
        with self._connect() as c:
            if capability:
                rows=c.execute("SELECT r.descriptor_json FROM estate_resources r JOIN estate_resource_capabilities rc ON rc.resource_id=r.resource_id WHERE rc.capability=? AND r.status='ACTIVE'",(capability,)).fetchall()
            else: rows=c.execute("SELECT descriptor_json FROM estate_resources WHERE status='ACTIVE'").fetchall()
        from .catalog.registry import descriptor_from_dict
        return [descriptor_from_dict(json.loads(x['descriptor_json'])) for x in rows]

    def put_route_decision(self,d:RouteDecision)->None:
        with self._tx() as c:
            c.execute("""INSERT INTO estate_route_decisions(route_decision_id,request_id,policy_id,policy_version,candidate_snapshot_json,candidate_snapshot_hash,chosen_resource_id,reason_codes_json,created_at)
                         VALUES(?,?,?,?,?,?,?,?,?)""",(d.route_decision_id,d.request_id,d.policy_id,d.policy_version,canonical_bytes([asdict(x) for x in d.candidates]).decode(),d.candidate_snapshot_hash,d.chosen_resource_id,json.dumps(list(d.reason_codes)),d.created_at or now()))

    def create_episode(self,e:ExecutionEpisodeRecord)->None:
        with self._tx() as c:
            c.execute("""INSERT INTO estate_execution_episodes(episode_id,graph_id,node_id,attempt_number,capability_request_id,route_decision_id,resource_id,executor_config_hash,context_pack_id,sandbox_id,status,created_at)
                         VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",(e.episode_id,e.graph_id,e.node_id,e.attempt_number,e.capability_request_id,e.route_decision_id,e.resource_id,e.executor_config_hash,e.context_pack_id,e.sandbox_id,str(e.status),now()))

    def transition_episode(self, episode_id:str, expected:set[str], new_status:EpisodeStatus, **fields)->None:
        allowed={'CREATED':{'RUNNING','CANCELLED'},'RUNNING':{'SUBMITTED','FAILED','CANCELLED'},'SUBMITTED':{'VERIFYING','FAILED'},'VERIFYING':{'VERIFIED','FAILED'},'VERIFIED':set(),'FAILED':set(),'CANCELLED':set()}
        with self._tx() as c:
            row=c.execute('SELECT status FROM estate_execution_episodes WHERE episode_id=?',(episode_id,)).fetchone()
            if not row: raise KeyError(episode_id)
            old=row['status']
            if old not in expected or str(new_status) not in allowed.get(old,set()): raise ValueError(f'invalid episode transition {old}->{new_status}')
            permit={'sandbox_id','started_at','finished_at','wall_ms','model_cost_usd','tool_cost_usd','compute_cost_usd','human_cost_usd','output_hash','failure_class','trace_artifact_id','verification_certificate_id'}
            bad=set(fields)-permit
            if bad: raise ValueError(f'unknown episode fields: {sorted(bad)}')
            sets=['status=?']; vals=[str(new_status)]
            for k,v in fields.items(): sets.append(f'{k}=?'); vals.append(v)
            vals.append(episode_id)
            c.execute(f"UPDATE estate_execution_episodes SET {','.join(sets)} WHERE episode_id=?",vals)

    def get_episode(self,episode_id:str)->dict[str,Any]:
        with self._connect() as c:
            r=c.execute('SELECT * FROM estate_execution_episodes WHERE episode_id=?',(episode_id,)).fetchone()
            if not r: raise KeyError(episode_id)
            return dict(r)

    def put_context_pack(self,m:ContextPackManifest,artifact_id:str|None=None)->None:
        with self._tx() as c:
            c.execute('INSERT INTO estate_context_packs(context_pack_id,node_id,manifest_json,manifest_hash,artifact_id,created_at) VALUES(?,?,?,?,?,?)',(m.context_pack_id,m.node_id,canonical_bytes(asdict(m)).decode(),m.manifest_hash,artifact_id,now()))

    def get_profile(self,resource_id:str,capability:str)->ResourceProfile|None:
        with self._connect() as c:
            r=c.execute('SELECT * FROM estate_resource_profiles WHERE resource_id=? AND capability=?',(resource_id,capability)).fetchone()
            if not r: return None
            return ResourceProfile(resource_id=r['resource_id'],capability=r['capability'],sample_count=r['sample_count'],verified_success_count=r['verified_success_count'],success_alpha=r['success_alpha'],success_beta=r['success_beta'],mean_cost_usd=r['mean_cost_usd'],mean_wall_ms=r['mean_wall_ms'],failure_distribution=json.loads(r['failure_distribution_json'] or '{}'),updated_at=r['updated_at'])

    def record_verified_profile_outcome(self,episode_id:str,capability:str,success:bool,failure_class:str|None=None)->None:
        """Only certificate-bound episodes are eligible. This is intentionally enforced in SQL state, not caller convention."""
        with self._tx() as c:
            e=c.execute('SELECT resource_id,status,verification_certificate_id,model_cost_usd+tool_cost_usd+compute_cost_usd+human_cost_usd AS cost,wall_ms FROM estate_execution_episodes WHERE episode_id=?',(episode_id,)).fetchone()
            if not e: raise KeyError(episode_id)
            if e['status']!='VERIFIED' or not e['verification_certificate_id']: raise PermissionError('profile update requires certificate-bound VERIFIED episode')
            old=c.execute('SELECT * FROM estate_resource_profiles WHERE resource_id=? AND capability=?',(e['resource_id'],capability)).fetchone()
            if old:
                n=old['sample_count']+1; vs=old['verified_success_count']+(1 if success else 0); a=old['success_alpha']+(1 if success else 0); b=old['success_beta']+(0 if success else 1)
                # Only update means when new observation has a value; skip None to avoid biasing mean toward 0
                new_cost=e['cost']; new_wall=e['wall_ms']
                if new_cost is not None and old['mean_cost_usd'] is not None:
                    mc=((old['mean_cost_usd'])*old['sample_count']+new_cost)/n
                elif new_cost is not None:
                    mc=new_cost
                else:
                    mc=old['mean_cost_usd']
                if new_wall is not None and old['mean_wall_ms'] is not None:
                    mw=((old['mean_wall_ms'])*old['sample_count']+new_wall)/n
                elif new_wall is not None:
                    mw=new_wall
                else:
                    mw=old['mean_wall_ms']
                fd=json.loads(old['failure_distribution_json'] or '{}')
                if failure_class: fd[failure_class]=fd.get(failure_class,0)+1
                c.execute("""UPDATE estate_resource_profiles SET sample_count=?,verified_success_count=?,success_alpha=?,success_beta=?,mean_cost_usd=?,mean_wall_ms=?,failure_distribution_json=?,updated_at=? WHERE resource_id=? AND capability=?""",(n,vs,a,b,mc,mw,json.dumps(fd,sort_keys=True),now(),e['resource_id'],capability))
            else:
                fd={failure_class:1} if failure_class else {}
                c.execute("""INSERT INTO estate_resource_profiles(resource_id,capability,sample_count,verified_success_count,success_alpha,success_beta,mean_cost_usd,mean_wall_ms,failure_distribution_json,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)""",(e['resource_id'],capability,1,1 if success else 0,2.0 if success else 1.0,1.0 if success else 2.0,e['cost'],e['wall_ms'],json.dumps(fd),now()))
