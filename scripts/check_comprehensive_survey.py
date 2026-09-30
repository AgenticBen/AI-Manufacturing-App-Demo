import os,uuid,json
from pathlib import Path
import httpx
base=os.environ.get('ARC_TEST_URL','http://127.0.0.1:8012')
with httpx.Client(base_url=base,headers={'X-Arc-Client':'web'},timeout=90) as c:
 cat=c.get('/api/catalog').json();assert sum(len(s['fields']) for s in cat['survey_sections'])==173
 logo=c.get('/assets/ivy-hopper-works.png');assert logo.status_code==200
 assert logo.content==Path('public/assets/ivy-hopper-works.png').read_bytes()
 c.post('/api/session',json={}).raise_for_status()
 s=cat['scenarios']['seed'];payload={'scenario':'seed','description':s['description'],'quantity':s['quantity'],'company':s['name'],'contact':'Fictional survey test','mode':'guided_demo','survey':s['survey'],'event_key':str(uuid.uuid4())}
 r=c.post('/api/quotes',json=payload);r.raise_for_status();q=r.json()['body'];assert q['scenario_id']=='seed' and len(q['survey_requirements'])==173
 pdf=c.get('/api/quotes/'+q['id']+'/survey/pdf');assert pdf.status_code==200 and pdf.content.startswith(b'%PDF')
 Path('artifacts/comprehensive-requirements.pdf').write_bytes(pdf.content)
 payload['survey']['nominal_capacity']='50 m³';payload['event_key']=str(uuid.uuid4())
 r=c.post('/api/quotes',json=payload);r.raise_for_status();custom=r.json()['body'];assert custom['scenario_id']=='custom' and custom['calculation'] is None and custom['survey_answers']['nominal_capacity']=='50 m³'
 proof={'fields':173,'sections':14,'logo_exact_match':True,'prepared_survey_persisted':True,'requirements_pdf':True,'changed_scope_retained_without_fixture_estimate':True,'quote':q['id'],'custom_quote':custom['id']}
 Path('artifacts/comprehensive-survey-proof.json').write_text(json.dumps(proof,indent=2));print(json.dumps(proof))
