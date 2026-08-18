from sandbox.estate.store import EstateStore
from sandbox.estate.context import ContextAssembler,ContextPolicy
def test_context_denies_sensitive_and_caps_size(estate_db):
    s=EstateStore(estate_db); a=ContextAssembler(s)
    m,p=a.build('n',[{'ref':'ok','content':'abc','sensitivity':'internal'},{'ref':'secret','content':'pw','sensitivity':'secret'}],ContextPolicy())
    assert [x.ref for x in m.items]==['ok']; assert m.denied_refs==('secret',); assert p[0]['content']=='abc'
