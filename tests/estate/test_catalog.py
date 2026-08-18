import pytest, tempfile, os
from pathlib import Path
from sandbox.estate.store import EstateStore
from sandbox.estate.catalog import EstateCatalog
from sandbox.estate.contracts import *

def test_load_manifest_does_not_delete_other_components(estate_db):
    s=EstateStore(estate_db); cat=EstateCatalog(estate_db)
    # Load first manifest with component A
    manifest_a={'components':{'comp_a':{'kind':'service','repo':'r1','depends_on':[]}}}
    p_a=Path(tempfile.mktemp(suffix='.yaml')); p_a.write_text(__import__('yaml').safe_dump(manifest_a))
    cat.load_manifest(p_a)
    # Load second manifest with component B — should NOT delete comp_a's dependencies
    manifest_b={'components':{'comp_b':{'kind':'service','repo':'r2','depends_on':[{'provider':'comp_a','capability':'x'}]}}}
    p_b=Path(tempfile.mktemp(suffix='.yaml')); p_b.write_text(__import__('yaml').safe_dump(manifest_b))
    cat.load_manifest(p_b)
    # comp_a should still exist
    deps_a=cat.dependencies('comp_a')
    assert len(deps_a)==0  # comp_a has no deps
    deps_b=cat.dependencies('comp_b')
    assert len(deps_b)==1
    assert deps_b[0]['provider_component_id']=='comp_a'

def test_load_manifest_updates_existing_component(estate_db):
    cat=EstateCatalog(estate_db)
    m1={'components':{'cx':{'kind':'v1','repo':'r1'}}}
    p1=Path(tempfile.mktemp(suffix='.yaml')); p1.write_text(__import__('yaml').safe_dump(m1))
    cat.load_manifest(p1)
    m2={'components':{'cx':{'kind':'v2','repo':'r2'}}}
    p2=Path(tempfile.mktemp(suffix='.yaml')); p2.write_text(__import__('yaml').safe_dump(m2))
    cat.load_manifest(p2)
    deps=cat.dependencies('cx')
    # Component should be updated, not duplicated
    assert len(deps)==0
