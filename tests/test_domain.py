from copy import deepcopy
from datetime import datetime,timezone,timedelta
import pytest
from backend.domain import create_quote,act,DomainError,current_fingerprint
from backend.fixtures import SCENARIOS
from backend.calculations import fingerprint

def make(s='seed',mode='guided_demo'):
    return create_quote({'scenario':s,'quantity':SCENARIOS[s]['quantity'],'description':SCENARIOS[s]['description'],'contact':'Demo reviewer','company':SCENARIOS[s]['name'],'mode':mode,'event_key':'test-event-key'})

def step(q,action,data=None,allocations=None):return act(q,action,data or {},allocations or [a for a in q.get('allocations',[])])[0]

def walkthrough(s='seed'):
    q=make(s)
    q=step(q,'inspect',{'source_id':'request-'+s});q=step(q,'approve',{'stage':0})
    with pytest.raises(DomainError):step(q,'approve',{'stage':1})
    q=step(q,'inspect',{'source_id':'clarification-'+s});q=step(q,'resolve',{'confirmed':True})
    for i in [1,2,3]:q=step(q,'approve',{'stage':i})
    with pytest.raises(DomainError):step(q,'approve',{'stage':4})
    for line in q['calculation']['lines']:
        for source in line['evidence']:q=step(q,'inspect',{'source_id':source})
        q=step(q,'verify',{'line_id':line['id'],'confirmed':True})
    q=step(q,'approve',{'stage':4});q=step(q,'risk_first');q=step(q,'risk_reconcile')
    for r in q['risks']:
        if r['disposition']=='open':q=step(q,'risk_dispose',{'risk_id':r['id'],'disposition':'qualified'})
    q=step(q,'approve',{'stage':5});q=step(q,'approve',{'stage':6});q=step(q,'preview');q=step(q,'approve',{'stage':7});q=step(q,'export');q=step(q,'respond',{'response':'accepted'});q=step(q,'acceptance_check')
    return q

@pytest.mark.parametrize('s',['seed','grain','feed'])
def test_complete_offline_paths(s):
    q=walkthrough(s)
    accepted=q['package']['selling_price'];q=step(q,'approve_procurement',{'exception_reason':'Demo manager accepts documented supplier variance.'})
    assert q['package']['selling_price']==accepted
    assert q['procurement']['status']=='approved_requisition'
    assert all(float(l['purchase_quantity'])>0 for l in q['procurement']['purchase_lines'])
    assert q['procurement']['production_status']=='Awaiting production review'
    if s=='feed':assert q['procurement']['variance']['escalation_required']

def test_revision_preserves_issued_package():
    q=walkthrough();q['lifecycle']='exported';old=deepcopy(q['packages']);q=step(q,'revise',{'quantity':'3','material':'Galvanized carbon steel'})
    assert q['revision']==2 and q['stage']==1
    assert q['packages']==old and not q['verifications']
    assert q['stages'][0]['status']=='approved'
    assert q['stages'][2]['status']=='invalidated'

def test_source_click_is_not_verification():
    q=make();q['stage']=4;q=step(q,'inspect',{'source_id':q['calculation']['lines'][0]['evidence'][0]})
    assert not q['verifications']

def test_future_stage_and_critical_risk_block():
    q=make()
    with pytest.raises(DomainError):step(q,'approve',{'stage':7})
    q['risk_review']['reconciliation']={}
    with pytest.raises(DomainError):step(q,'risk_dispose',{'risk_id':'engineering','disposition':'qualified'})

def test_stale_offer_invalidates_release():
    q=walkthrough();q['lifecycle']='approved_for_release';q['stage']=7;q['offers_valid_until']='2020-01-01T00:00:00+00:00'
    with pytest.raises(DomainError):step(q,'export')

def test_customer_allowlist():
    q=walkthrough();text=str(q['package']).lower()
    for forbidden in ['base_cost','gross_margin','gross_profit','loaded_rate','supplier','route-seed','inventory-ledger']:
        assert forbidden not in text

def test_custom_no_fake_estimate():
    q=create_quote({'scenario':'custom','description':'Completely different machine','quantity':'2','contact':'Test','mode':'guided_demo'})
    assert q['calculation'] is None
    with pytest.raises(DomainError):step(q,'approve',{'stage':0})

def test_live_offline_waits():
    q=make(mode='live_mcp')
    assert q['jobs'][0]['state']=='queued'
    with pytest.raises(DomainError):step(q,'approve',{'stage':0})

def test_arbitrary_new_survey_text_does_not_use_fixture():
    q=create_quote({'scenario':'seed','description':'Need a pressure vessel rated to 200 bar','quantity':'1','contact':'Test','mode':'guided_demo'})
    assert q['scenario_id']=='custom' and q['calculation'] is None
