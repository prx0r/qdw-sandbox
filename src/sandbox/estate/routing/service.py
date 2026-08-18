from __future__ import annotations
from .historical import HistoricalProfilePolicy
from .cluster import ClusterProfilePolicy
from .cascade import CascadePolicy
class EstateRouter:
    def __init__(self,store): self.store=store; self.policies={'historical':HistoricalProfilePolicy(),'cluster':ClusterProfilePolicy(),'cascade':CascadePolicy()}
    def register_policy(self,name,policy): self.policies[name]=policy
    def plan(self,request,policy='historical'):
        rs=self.store.list_resources(request.capability); profiles={r.resource_id:self.store.get_profile(r.resource_id,request.capability) for r in rs}
        plan=self.policies[policy].plan(request,rs,profiles); self.store.put_route_decision(plan.decision); return plan
