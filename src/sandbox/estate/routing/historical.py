from __future__ import annotations
import uuid
from datetime import UTC,datetime
from .constraints import exclusions
from ..contracts import CapabilityRequest, ResourceDescriptor, ResourceProfile, RouteCandidate, RouteDecision, RoutePlan
class HistoricalProfilePolicy:
    policy_id='historical-profile'; version='1'
    def plan(self,request,resources,profiles):
        cs=[]
        for r in resources:
            ex=exclusions(request,r); p=profiles.get(r.resource_id)
            succ=p.success_mean if p else r.attributes.get('prior_success')
            cost=p.mean_cost_usd if p and p.mean_cost_usd is not None else r.attributes.get('estimated_cost_usd')
            cpvs=None if succ in {None,0} or cost is None else float(cost)/float(succ)
            eligible=not ex and (request.quality_floor is None or succ is None or succ>=request.quality_floor)
            reasons=list(ex)
            if not ex and not eligible: reasons.append('QUALITY_FLOOR')
            score=None if cpvs is None else -cpvs
            cs.append(RouteCandidate(r.resource_id,eligible,tuple(reasons),succ,cost,r.attributes.get('estimated_wall_ms'),score))
        eligible=[c for c in cs if c.eligible]
        # Known CPVS first; unknown remains eligible for cold-start exploration but ranks later.
        eligible.sort(key=lambda c:(c.score is None, -(c.score or -1e30), -(c.predicted_success or 0), c.resource_id))
        chosen=eligible[0].resource_id if eligible else None
        rc=('HISTORICAL_CPVS',) if chosen else ('NO_CANDIDATES',)
        d=RouteDecision('route_'+uuid.uuid4().hex[:16],request.request_id,self.policy_id,self.version,tuple(cs),chosen,rc,datetime.now(UTC).isoformat())
        return RoutePlan(d,tuple(c.resource_id for c in eligible[1:5]))
