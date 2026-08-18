from __future__ import annotations
from typing import Protocol
from ..contracts import CapabilityRequest, ResourceDescriptor, ResourceProfile, RoutePlan
class RoutingPolicy(Protocol):
    policy_id:str; version:str
    def plan(self, request:CapabilityRequest, resources:list[ResourceDescriptor], profiles:dict[str,ResourceProfile|None])->RoutePlan: ...
