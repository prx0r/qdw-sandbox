"""Clean-room Avengers-style cold-start cluster routing.

Uses deterministic hashed token vectors to avoid embedding-provider dependency. Fit profiles from
verified labeled examples; assign a new objective to nearest centroid; choose best historical resource
for that cluster subject to Estate hard constraints. This is deliberately small and replaceable.
"""
from __future__ import annotations
import math,re,hashlib,uuid
from dataclasses import dataclass
from datetime import UTC,datetime
from .constraints import exclusions
from ..contracts import CapabilityRequest,ResourceDescriptor,ResourceProfile,RouteCandidate,RouteDecision,RoutePlan

def vec(text:str,dims:int=128)->list[float]:
    v=[0.0]*dims
    for t in re.findall(r'[a-z0-9_]+',text.lower()):
        h=int.from_bytes(hashlib.sha256(t.encode()).digest()[:8],'big'); i=h%dims; sign=1 if (h>>8)&1 else -1; v[i]+=sign
    n=math.sqrt(sum(x*x for x in v)) or 1.0
    return [x/n for x in v]
def dot(a,b): return sum(x*y for x,y in zip(a,b))
@dataclass
class Example:
    text:str; resource_id:str; success:bool; cost_usd:float=0.0
class ClusterProfilePolicy:
    policy_id='cluster-profile'; version='1'
    def __init__(self,k:int=16,dims:int=128): self.k=k; self.dims=dims; self.centroids=[]; self.stats=[]
    def fit(self,examples:list[Example],iterations:int=12):
        if not examples: self.centroids=[]; self.stats=[]; return self
        xs=[vec(e.text,self.dims) for e in examples]; k=min(self.k,len(xs)); cent=[xs[i*len(xs)//k][:] for i in range(k)]
        assign=[0]*len(xs)
        for _ in range(iterations):
            assign=[max(range(k),key=lambda j:dot(x,cent[j])) for x in xs]
            new=[]
            for j in range(k):
                members=[xs[i] for i,a in enumerate(assign) if a==j]
                if not members: new.append(cent[j]); continue
                c=[sum(m[d] for m in members)/len(members) for d in range(self.dims)]; n=math.sqrt(sum(z*z for z in c)) or 1; new.append([z/n for z in c])
            if all(dot(a,b)>0.999999 for a,b in zip(cent,new)): cent=new; break
            cent=new
        stats=[{} for _ in range(k)]
        for e,a in zip(examples,assign):
            s=stats[a].setdefault(e.resource_id,{'ok':0,'n':0,'cost':0.0}); s['n']+=1; s['ok']+=int(e.success); s['cost']+=e.cost_usd
        self.centroids,self.stats=cent,stats; return self
    def plan(self,request,resources,profiles):
        if not self.centroids:
            from .historical import HistoricalProfilePolicy
            return HistoricalProfilePolicy().plan(request,resources,profiles)
        x=vec(request.objective,self.dims); ci=max(range(len(self.centroids)),key=lambda j:dot(x,self.centroids[j])); st=self.stats[ci]
        cs=[]
        for r in resources:
            ex=exclusions(request,r); ss=st.get(r.resource_id); p=(ss['ok']/ss['n']) if ss else (profiles.get(r.resource_id).success_mean if profiles.get(r.resource_id) else None)
            cost=(ss['cost']/ss['n']) if ss else (profiles.get(r.resource_id).mean_cost_usd if profiles.get(r.resource_id) else r.attributes.get('estimated_cost_usd'))
            eligible=not ex and (request.quality_floor is None or p is None or p>=request.quality_floor)
            reasons=list(ex); reasons += ([] if eligible or ex else ['QUALITY_FLOOR'])
            score=None if p is None else p-(float(cost or 0)*0.05)
            cs.append(RouteCandidate(r.resource_id,eligible,tuple(reasons),p,cost,r.attributes.get('estimated_wall_ms'),score))
        good=[c for c in cs if c.eligible]; good.sort(key=lambda c:(c.score is None,-(c.score or -1e30),c.resource_id)); chosen=good[0].resource_id if good else None
        d=RouteDecision('route_'+uuid.uuid4().hex[:16],request.request_id,self.policy_id,self.version,tuple(cs),chosen,(f'CLUSTER_{ci}',) if chosen else ('NO_CANDIDATES',),datetime.now(UTC).isoformat())
        return RoutePlan(d,tuple(c.resource_id for c in good[1:5]))
