from __future__ import annotations
import json, yaml
from pathlib import Path
from dataclasses import asdict
from datetime import UTC,datetime
from ..contracts import ResourceDescriptor,ResourceKind,ExecutorConfiguration
from ..hashing import canonical_bytes,sha256_obj

def descriptor_from_dict(d):
    ec=d.get('executor_configuration'); ec=ExecutorConfiguration(**ec) if ec else None
    return ResourceDescriptor(resource_id=d['resource_id'],kind=ResourceKind(d['kind']),name=d['name'],version=d.get('version'),capabilities=tuple(d.get('capabilities',())),executor_configuration=ec,interface_kind=d.get('interface_kind'),attributes=d.get('attributes',{}),active=d.get('active',True))
class EstateCatalog:
    def __init__(self,db): self.db=db
    def load_manifest(self,path:str|Path):
        d=yaml.safe_load(Path(path).read_text()); comps=d.get('components',{})
        now=datetime.now(UTC).isoformat()
        with self.db.tx(immediate=True) as c:
            for cid,v in comps.items():
                payload={'component_id':cid,**v}; h=sha256_obj(payload)
                c.execute("""INSERT INTO estate_components(component_id,kind,canonical_repo,status,manifest_json,manifest_hash,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(component_id) DO UPDATE SET kind=excluded.kind,canonical_repo=excluded.canonical_repo,status=excluded.status,manifest_json=excluded.manifest_json,manifest_hash=excluded.manifest_hash,updated_at=excluded.updated_at""",(cid,v.get('kind','service'),v.get('repo'),'ACTIVE',canonical_bytes(payload).decode(),h,now,now))
            # Only delete dependencies for components being upserted, not all dependencies
            for cid in comps:
                c.execute('DELETE FROM estate_dependencies WHERE consumer_component_id=?',(cid,))
            for cid,v in comps.items():
                for dep in v.get('depends_on',[]):
                    c.execute('INSERT INTO estate_dependencies(consumer_component_id,provider_component_id,capability,required) VALUES(?,?,?,?)',(cid,dep['provider'],dep['capability'],1 if dep.get('required',True) else 0))
    def dependencies(self,component_id):
        with self.db.connect() as c: return [dict(r) for r in c.execute('SELECT * FROM estate_dependencies WHERE consumer_component_id=?',(component_id,)).fetchall()]
    def impact(self,component_id):
        with self.db.connect() as c: return [dict(r) for r in c.execute('SELECT * FROM estate_dependencies WHERE provider_component_id=?',(component_id,)).fetchall()]
