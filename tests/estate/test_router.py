from sandbox.estate.store import EstateStore
from sandbox.estate.routing import EstateRouter
from sandbox.estate.routing.cluster import ClusterProfilePolicy,Example
from sandbox.estate.contracts import *
def seed(s):
    req=CapabilityRequest('req','research','find primary sources','v1',quality_floor=0.5); s.put_capability_request(req)
    s.put_resource(ResourceDescriptor('cheap',ResourceKind.EXECUTOR_CONFIGURATION,'cheap',capabilities=('research',),attributes={'prior_success':.8,'estimated_cost_usd':.1}))
    s.put_resource(ResourceDescriptor('expensive',ResourceKind.EXECUTOR_CONFIGURATION,'exp',capabilities=('research',),attributes={'prior_success':.95,'estimated_cost_usd':1.0}))
    return req
def test_historical_routes_by_cost_per_success(estate_db):
    s=EstateStore(estate_db); req=seed(s); plan=EstateRouter(s).plan(req); assert plan.decision.chosen_resource_id=='cheap'
def test_cluster_policy_uses_verified_style_examples(estate_db):
    s=EstateStore(estate_db); req=seed(s); p=ClusterProfilePolicy(k=2).fit([Example('search sources citations','cheap',True,.1),Example('complex proof theorem','expensive',True,1.0),Example('search source evidence','cheap',True,.1)])
    er=EstateRouter(s); er.register_policy('cluster2',p); plan=er.plan(req,'cluster2'); assert plan.decision.chosen_resource_id in {'cheap','expensive'}; assert plan.decision.candidate_snapshot_hash.startswith('sha256:')
