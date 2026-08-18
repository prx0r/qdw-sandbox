import pytest
from sandbox.estate.store import EstateStore
from sandbox.estate.verification import EstateVerificationService
from sandbox.estate.contracts import *
def setup(estate_db):
    s=EstateStore(estate_db); s.put_capability_request(CapabilityRequest('req','code','x','v1')); s.put_resource(ResourceDescriptor('res',ResourceKind.EXECUTOR_CONFIGURATION,'R',capabilities=('code',))); s.put_route_decision(RouteDecision('rd','req','p','1',(RouteCandidate('res',True),),'res')); s.create_episode(ExecutionEpisodeRecord('ep','g','n',1,'req','rd','res')); s.transition_episode('ep',{'CREATED'},EpisodeStatus.RUNNING); s.transition_episode('ep',{'RUNNING'},EpisodeStatus.SUBMITTED); return s
def test_zero_gate_certificate_rejected(estate_db):
    s=setup(estate_db); v=EstateVerificationService(s,estate_db)
    with pytest.raises(ValueError): v.issue_certificate('ep','p',[])
def test_failing_gate_rejected(estate_db):
    s=setup(estate_db); v=EstateVerificationService(s,estate_db)
    with pytest.raises(ValueError): v.issue_certificate('ep','p',[{'gate':'unit','passed':False}])
def test_verified_episode_can_update_profile(estate_db):
    s=setup(estate_db); v=EstateVerificationService(s,estate_db); cid=v.issue_certificate('ep','p',[{'gate':'unit','passed':True,'receipt':'sha256:x'}]); assert cid.startswith('evc_'); s.record_verified_profile_outcome('ep','code',True); p=s.get_profile('res','code'); assert p and p.sample_count==1 and p.verified_success_count==1
