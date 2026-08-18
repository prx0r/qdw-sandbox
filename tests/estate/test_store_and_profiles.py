import pytest
from sandbox.estate.store import EstateStore
from sandbox.estate.contracts import *
def test_profile_cannot_learn_from_unverified_episode(estate_db):
    s=EstateStore(estate_db); req=CapabilityRequest('req1','research','x','v1'); s.put_capability_request(req)
    r=ResourceDescriptor('res1',ResourceKind.EXECUTOR_CONFIGURATION,'R',capabilities=('research',)); s.put_resource(r)
    d=RouteDecision('rd1','req1','test','1',(RouteCandidate('res1',True),),'res1'); s.put_route_decision(d)
    e=ExecutionEpisodeRecord('ep1','g','n',1,'req1','rd1','res1'); s.create_episode(e)
    with pytest.raises(PermissionError): s.record_verified_profile_outcome('ep1','research',True)
def test_immutable_resource_descriptor(estate_db):
    s=EstateStore(estate_db); s.put_resource(ResourceDescriptor('r',ResourceKind.TOOL,'A',capabilities=('x',)))
    with pytest.raises(ValueError): s.put_resource(ResourceDescriptor('r',ResourceKind.TOOL,'B',capabilities=('x',)))
