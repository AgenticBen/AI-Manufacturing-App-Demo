from copy import deepcopy
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from backend.api import app
from backend.survey import schema,defaults,normalize
from backend.domain import create_quote,act
from backend.documents import document
from test_domain import make,step

@pytest.mark.parametrize('sid',['seed','grain','feed'])
def test_full_survey_saved_and_cited_in_requirements(sid):
 q=make(sid);assert len(q['survey_requirements'])==173
 assert len({f['id'] for s in schema() for f in s['fields']})==173
 assert all(q['survey_answers'].values())
 q['stage']=1;d=document(q,'client-document');survey=[s for s in d['sections'] if any(c.get('source')=='survey-submission' for c in s['citations'])]
 assert len(survey)==173
 src=next(s for s in q['sources'] if s['id']=='survey-submission')
 for section,row in zip(survey,q['survey_requirements']):
  assert row['question'] in section['text'] and row['value'] in section['text']
  assert row['question'] in src['content'].splitlines()[section['citations'][0]['line']-1]


def test_changed_scope_keeps_answers_without_fixture_price():
 q=make();data=deepcopy(q['intake']);data['survey']=defaults('seed');data['survey']['nominal_capacity']='50 m³'
 changed=create_quote(data)
 assert changed['scenario_id']=='custom' and changed['calculation'] is None
 assert changed['survey_answers']['nominal_capacity']=='50 m³'
 assert len(changed['survey_requirements'])==173
 assert changed['survey_summary']['classification'].startswith('Customer')


def test_unknown_fields_and_oversized_answers_rejected():
 with pytest.raises(ValueError):normalize('seed',{'invented':'value'})
 with pytest.raises(ValueError):normalize('seed',{'bulk_density':'x'*1001})


def test_clarification_does_not_confirm_unanswered_engineering_fields():
 q=make();q=step(q,'inspect',{'source_id':'clarification-seed'});q=step(q,'resolve',{'confirmed':True})
 assert next(r for r in q['requirements'] if r['field']=='kst_st')['status']=='Needs confirmation'
 assert next(r for r in q['requirements'] if r['field']=='capacity')['status']=='confirmed'


def test_survey_survives_material_revision_without_duplicate_rows():
 q=step(make(),'revise',{'quantity':'2','material':'Galvanized carbon steel'})
 assert len(q['survey_requirements'])==173
 assert q['survey_answers']['construction_material']=='Galvanized carbon steel'
 assert len([r for r in q['requirements'] if r.get('section')])==173
 assert len([s for s in q['sources'] if s['id']=='survey-submission'])==1


def test_survey_pdf_requires_session_and_includes_complete_answers():
 from pypdf import PdfReader
 from io import BytesIO
 c=TestClient(app);q=make()
 assert c.get('/api/quotes/q/survey/pdf').status_code==401
 c.cookies.set('arc_session','a'*48)
 with patch('backend.api.store.call',return_value={'body':q}):
  result=c.get('/api/quotes/q/survey/pdf');assert result.status_code==200
  text='\n'.join(p.extract_text() for p in PdfReader(BytesIO(result.content)).pages)
  assert 'kg/m' in text and 'customer confirmed' in text.lower()
  assert 'Kst' in text and 'PO requirements' in text


def test_customer_survey_catalog_and_company_logo():
 c=TestClient(app);data=c.get('/api/catalog').json()
 assert len(data['survey_sections'])==14
 assert data['scenarios']['feed']['survey']['cleaning_method'].startswith('Intermittent wet')
 from pathlib import Path
 assert Path('public/assets/ivy-hopper-works.png').read_bytes().startswith(b'\x89PNG')


def test_legacy_quote_can_review_supplement_without_fingerprint_mismatch():
 from backend.api import safe_record
 from backend.workflow import checklist
 q=make()
 for key in ['survey_answers','survey_requirements','survey_summary']:q.pop(key)
 q['requirements']=[r for r in q['requirements'] if not r.get('section')]
 q['sources']=[s for s in q['sources'] if s['id']!='survey-submission']
 q['workflow_version']='2.0'
 q=step(q,'open_document',{'id':'request-packet'})
 visible=safe_record({'body':q})['body']
 assert checklist(visible,0)[0]['opened']
 assert 'not original customer submission' in visible['survey_summary']['classification']
