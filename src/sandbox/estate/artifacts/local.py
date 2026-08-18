from __future__ import annotations
from pathlib import Path
import hashlib,os
from ..contracts import ArtifactRef
class LocalCAS:
    def __init__(self,root): self.root=Path(root); self.root.mkdir(parents=True,exist_ok=True)
    def put_bytes(self,data:bytes,media_type='application/octet-stream'):
        h=hashlib.sha256(data).hexdigest(); path=self.root/h[:2]/h; path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()!=h: raise RuntimeError('CAS corruption')
        if not path.exists():
            tmp=path.with_suffix('.tmp'); tmp.write_bytes(data); os.replace(tmp,path)
        return ArtifactRef('cas://sha256/'+h,'sha256:'+h,len(data),media_type)
    def put_file(self,path,media_type='application/octet-stream'): return self.put_bytes(Path(path).read_bytes(),media_type)
    def resolve(self,ref:ArtifactRef):
        h=ref.sha256.removeprefix('sha256:'); p=self.root/h[:2]/h
        if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=h: raise FileNotFoundError(ref.uri)
        return p
