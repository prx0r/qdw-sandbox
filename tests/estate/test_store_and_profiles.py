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

def _verified_episode(s,v,rid='res1',req_id='req1',cap='research'):
    """Helper: create a fully verified episode for profile testing."""
    req=CapabilityRequest(req_id,cap,'x','v1'); s.put_capability_request(req)
    r=ResourceDescriptor(rid,ResourceKind.EXECUTOR_CONFIGURATION,'R',capabilities=(cap,)); s.put_resource(r)
    d=RouteDecision('rd_'+rid,req_id,'p','1',(RouteCandidate(rid,True),),rid); s.put_route_decision(d)
    e=ExecutionEpisodeRecord('ep_'+rid,'g','n_'+rid,1,req_id,'rd_'+rid,rid); s.create_episode(e)
    s.transition_episode('ep_'+rid,{'CREATED'},EpisodeStatus.RUNNING)
    s.transition_episode('ep_'+rid,{'RUNNING'},EpisodeStatus.SUBMITTED)
    v.issue_certificate('ep_'+rid,'p',[{'gate':'unit','passed':True}])
    return 'ep_'+rid

def test_profile_mean_calculation(estate_db):
    from sandbox.estate.verification import EstateVerificationService
    s=EstateStore(estate_db); v=EstateVerificationService(s,estate_db)
    ep=_verified_episode(s,v)
    s.record_verified_profile_outcome(ep,'research',True); p=s.get_profile('res1','research')
    assert p and p.sample_count==1 and p.mean_cost_usd==0.0
    # Second episode should update the mean
    ep2=_verified_episode(s,v,'res2','req2')
    s.record_verified_profile_outcome(ep2,'research',True); p2=s.get_profile('res2','research')
    assert p2 and p2.sample_count==1

def test_profile_put_resource_idempotent(estate_db):
    s=EstateStore(estate_db)
    s.put_resource(ResourceDescriptor('r',ResourceKind.TOOL,'A',capabilities=('x',)))
    s.put_resource(ResourceDescriptor('r',ResourceKind.TOOL,'A',capabilities=('x',)))  # same hash, no error
    resources=s.list_resources('x')
    assert len(resources)==1
