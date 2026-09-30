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
