from __future__ import annotations
from ..contracts import CapabilityRequest, ResourceDescriptor

def exclusions(req:CapabilityRequest,r:ResourceDescriptor)->list[str]:
    out=[]
    if not r.active: out.append('INACTIVE')
    if req.capability not in r.capabilities: out.append('CAPABILITY_MISMATCH')
    if r.resource_id in req.constraints.forbidden_resource_ids: out.append('FORBIDDEN_RESOURCE')
    if req.constraints.required_resource_kinds and str(r.kind) not in req.constraints.required_resource_kinds: out.append('RESOURCE_KIND_MISMATCH')
    cost=r.attributes.get('estimated_cost_usd')
    if req.constraints.max_cost_usd is not None and cost is not None and float(cost)>req.constraints.max_cost_usd: out.append('COST_CAP')
    wall=r.attributes.get('estimated_wall_ms')
    if wall is not None and float(wall)>req.constraints.max_wall_seconds*1000: out.append('WALL_CAP')
    if req.constraints.network=='none' and r.attributes.get('network_required'): out.append('NETWORK_FORBIDDEN')
    return out
