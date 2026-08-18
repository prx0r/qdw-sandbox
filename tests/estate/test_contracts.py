from dataclasses import asdict
import pytest
from sandbox.estate.contracts import *
def test_capability_hash_deterministic():
    a=CapabilityRequest('r1','code.modify','fix x','code/v1'); b=CapabilityRequest('r1','code.modify','fix x','code/v1')
    assert a.content_hash==b.content_hash and a.content_hash.startswith('sha256:')
def test_invalid_constraints_rejected():
    with pytest.raises(ValueError): ExecutionConstraints(max_wall_seconds=0)
def test_executor_configuration_hash_changes():
    a=ExecutorConfiguration('x',model_resource_id='m1'); b=ExecutorConfiguration('x',model_resource_id='m2')
    assert a.content_hash!=b.content_hash
