import pytest
from backend.domain import act,can_approve,DomainError
from backend.workflow import checklist,workflow_state
from backend.documents import document
from test_domain import make,step

def test_document_gate_is_server_enforced_and_reopens():
 q=make();q['workflow_version']='2.0';q=step(q,'inspect',{'source_id':'request-seed'})
 with pytest.raises(DomainError,match='Open every'):can_approve(q,0)
 q=step(q,'open_document',{'id':'request-packet'})
 with pytest.raises(DomainError,match='Confirm that'):can_approve(q,0)
 q=step(q,'confirm_documents',{'confirmed':True});can_approve(q,0)
 q['intake']['company']='Corrected fictional name'
 with pytest.raises(DomainError,match='Open every'):can_approve(q,0)

def test_future_documents_and_email_gates():
 q=make()
 with pytest.raises(DomainError):document(q,'completed-cost')
 with pytest.raises(DomainError):step(q,'simulate_email',{'kind':'procurement'})
 with pytest.raises(DomainError):step(q,'simulate_email',{'kind':'customer-quote'})
 with pytest.raises(DomainError):step(q,'open_document',{'id':'not-a-document'})

def test_document_has_exact_citations_and_no_bom_sourcing():
 q=make();q['stage']=2
 d=document(q,'bom')
 assert len(d['sections'])==len(q['bom'])
 assert all(s['citations'] for s in d['sections'])
 assert not any('supplier' in s['text'] or 'stock' in s['text'] for s in d['sections'])

def test_simulated_email_is_audited_without_network():
 q=make();q['stage']=1
 q=step(q,'simulate_email',{'kind':'clarification'})
 assert q['simulated_messages'][0]['simulated'] is True
 assert q['timeline'][-1]['kind']=='simulated_email'

def test_pm_confirmation_required():
 q=make();q['workflow_version']='2.0';q['stage']=3;q['clarification_resolved']=True
 for s in q['stages'][:3]:s['status']='approved'
 q=step(q,'open_document',{'id':'manufacturing-plan'})
 q=step(q,'confirm_documents',{'confirmed':True})
 with pytest.raises(DomainError,match='Project manager'):can_approve(q,3)
 q=step(q,'confirm_documents',{'confirmed':True,'role_confirmed':True});can_approve(q,3)

def test_all_seed_documents_generate_pdf_and_citations():
 from test_domain import walkthrough
 from backend.workflow import DOCS
 from backend.document_pdf import artifact_pdf
 from pypdf import PdfReader
 from io import BytesIO
 q=walkthrough()
 for id,title,stage,creator in DOCS:
  d=document(q,id)
  assert d['sections'] and all(s['citations'] for s in d['sections'])
  pdf=artifact_pdf(d,q['id'],'https://demo.example')
  reader=PdfReader(BytesIO(pdf))
  assert reader.pages and any(p.get('/Annots') for p in reader.pages)

def test_document_api_requires_session_and_quote_ownership():
 from fastapi.testclient import TestClient
 from backend.api import app
 from unittest.mock import patch
 from backend.store import StoreError
 c=TestClient(app)
 assert c.get('/api/quotes/foreign/documents/request-packet').status_code==401
 c.cookies.set('arc_session','a'*48)
 with patch('backend.api.store.call',side_effect=StoreError('Not found',404)):
  assert c.get('/api/quotes/foreign/documents/request-packet').status_code==404
  assert c.get('/api/quotes/foreign/documents/request-packet/pdf').status_code==404
  assert c.get('/api/quotes/foreign/sources/request-seed').status_code==404

def test_qa_replay_rejects_pack_error_and_reruns_only_responsible_agent():
 from backend.cost_orchestration import replay,validate_candidate
 q=make();q['stage']=4
 q=step(q,'replay_cost_qa')
 qa=q['cost_qa']
 assert qa['initial']['pack']=='1' and qa['corrected']['pack']=='10'
 assert qa['failures'] and not qa['final_errors'] and qa['status']=='passed'
 assert qa['events'][2]['agent']=='supervisor'
 assert qa['events'][3]['agent']=='individual-parts'
 assert len([e for e in q['timeline'] if e['kind']=='cost_qa_replay'])==5

def test_full_document_gated_flow_remains_exportable_after_release_stamp():
 q=make();q['workflow_version']='2.0'
 q=step(q,'inspect',{'source_id':'request-seed'})
 for stage in range(8):
  if stage==1:q=step(step(q,'inspect',{'source_id':'clarification-seed'}),'resolve',{'confirmed':True})
  if stage==4:
   q=step(q,'replay_cost_qa')
   for line in q['calculation']['lines']:
    for source in line['evidence']:q=step(q,'inspect',{'source_id':source})
    q=step(q,'verify',{'line_id':line['id'],'confirmed':True})
  if stage==5:
   q=step(step(q,'risk_first'),'risk_reconcile')
   for risk in q['risks']:
    if risk['disposition']=='open':q=step(q,'risk_dispose',{'risk_id':risk['id'],'disposition':'qualified'})
  if stage==7:q=step(q,'preview')
  for d in checklist(q,stage):q=step(q,'open_document',{'id':d['id']})
  q=step(q,'confirm_documents',{'confirmed':True,'role_confirmed':True})
  q=step(q,'approve',{'stage':stage})
 q=step(q,'simulate_email',{'kind':'customer-quote'})
 q=step(q,'export')
 assert q['lifecycle']=='exported'
 q=step(q,'respond',{'response':'accepted'});q=step(q,'acceptance_check');q=step(q,'approve_procurement',{'exception_reason':'Fictional test approval'})
 q=step(q,'simulate_email',{'kind':'pm-handoff'})
 assert q['simulated_messages'][-1]['kind']=='pm-handoff'

def test_targeted_correction_preserves_previous_output_and_reopens_review():
 q=make();q['workflow_version']='2.0'
 q=step(q,'open_document',{'id':'request-packet'});q=step(q,'confirm_documents',{'confirmed':True})
 q=step(q,'request_correction',{'agent':'crm-check','reason':'Use the exact fictional client identity.','corrected_input':'Cedar Rapids Seed Co.; D10 row 1.'})
 assert len(q['corrections'])==1
 c=q['corrections'][0]
 assert c['agent']=='crm-check' and c['previous_output'] and c['new_output']
 assert c['previous_output'][-1]['sections']!=c['new_output'][-1]['sections']
 assert not q['workflow_reviews'] and not checklist(q,0)[0]['opened']
 assert q['timeline'][-1]['kind']=='targeted_prepared_rerun'
 assert q['corrections'][0]['new_output'][0]['reviewed_by']=='Pending human approval'
 with pytest.raises(DomainError):step(q,'request_correction',{'agent':'cost-qa','reason':'Unreached agent','corrected_input':'no'})

@pytest.mark.parametrize('sid',['seed','grain','feed'])
def test_every_scenario_artifact_and_bom_citation(sid):
 from test_domain import walkthrough
 from backend.demo.catalog import seed_databases
 from backend.workflow import DOCS
 from backend.document_pdf import artifact_pdf
 q=walkthrough(sid);db=next(d for d in seed_databases() if d['id']=='D5')
 for section,bom in zip(document(q,'bom')['sections'],q['bom']):
  c=next(c for c in section['citations'] if c.get('database')=='D5')
  row=db['rows'][c['line']-1]
  assert row['job']=='Template-'+sid and row['part']==bom['item']
 for id,*_ in DOCS:
  doc=document(q,id)
  assert all(x['citations'] for x in doc['sections'])
  assert artifact_pdf(doc,q['id'],'https://example.test').startswith(b'%PDF')
 assert {a['agent'] for a in q['procurement']['agent_rechecks']}=={'full-component','individual-parts','custom-quote'}
 assert sorted(i for a in q['procurement']['agent_rechecks'] for i in a['items'])==sorted(l['id'] for l in q['procurement']['purchase_lines'])

def test_material_supplement_requires_review_and_invalidates_document_read():
 q=make();q['stage']=1;q['workflow_version']='2.0'
 q=step(q,'draft_material',{'name':'Fictional new material','notes':'Reviewer supplied SDS needs engineering confirmation.'})
 from backend.workflow import approval_check
 for doc in checklist(q,1):q=step(q,'open_document',{'id':doc['id']})
 q=step(q,'confirm_documents',{'confirmed':True})
 with pytest.raises(DomainError,match='pending material'):approval_check(q,1)
 q=step(q,'approve_material')
 assert q['material_supplement']['status']=='approved_for_session_library'
 assert not all(d['opened'] for d in checklist(q,1))
 assert 'material-supplement' in [s['id'] for s in q['sources']]

def test_insurance_is_placeholder_only_and_cannot_change_issued_quote():
 q=make();q['stage']=5;price=q['calculation']['selling_price']
 q=step(q,'insurance_option',{'option':'project'})
 assert q['calculation']['selling_price']==price
 assert 'USD TBD' in document(q,'master-risk')['sections'][-1]['text']
 q['lifecycle']='exported'
 with pytest.raises(DomainError):step(q,'insurance_option',{'option':'minimal'})

def test_process_map_and_read_only_jump_preserve_real_quote():
 from fastapi.testclient import TestClient
 from backend.api import app
 from unittest.mock import patch
 from copy import deepcopy
 c=TestClient(app);m=c.get('/api/process-map').json()
 assert len(m['steps'])==9 and sum(s['modeled_minutes'] or 0 for s in m['steps'])==90
 assert c.get('/api/quotes/owned/steps/4').status_code==401
 c.cookies.set('arc_session','a'*48);q=make();before=deepcopy(q)
 with patch('backend.api.store.call',return_value={'body':q,'id':q['id'],'version':1}):
  r=c.get('/api/quotes/owned/steps/4')
  assert r.status_code==200 and r.json()['stage']==4
  assert not r.json()['workflow']['can_approve']
  assert q==before
