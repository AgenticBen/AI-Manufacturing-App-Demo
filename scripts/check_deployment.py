"""Public URL check: no owner login; independent visitor cookies; real Python/Supabase."""
import httpx,json,sys
from pathlib import Path
from uuid import uuid4
base=sys.argv[1] if len(sys.argv)>1 else 'https://agentic-arc-manufacturing.vercel.app'
a=httpx.Client(base_url=base,timeout=45,follow_redirects=True);b=httpx.Client(base_url=base,timeout=45,follow_redirects=True);h={'X-Arc-Client':'web'}
health=a.get('/api/health');health.raise_for_status();d=health.json();assert d['spike_price']=='1571.43' and all(d['runtime_assets'].values()),d
for asset in ['/assets/logo-dark.png','/assets/logo-light.png']:
    r=a.get(asset);assert r.status_code==200 and r.content.startswith(b'\x89PNG'),(asset,r.status_code)
assert a.get('/').status_code==200
for client in [a,b]:
    r=client.post('/api/session',json={},headers=h);r.raise_for_status();assert 'httponly' in r.headers['set-cookie'].lower() and 'secure' in r.headers['set-cookie'].lower()
cat=a.get('/api/catalog').json();q=a.post('/api/quotes',headers=h,json={'scenario':'seed','description':cat['scenarios']['seed']['description'],'quantity':'1','contact':'Public deployment test','event_key':str(uuid4())});q.raise_for_status();q=q.json()
assert q['body']['calculation']['formula_version']=='arc-decimal-1.0'
assert b.get('/api/quotes/'+q['id']).status_code==404
assert b.get('/api/quotes/'+q['id']+'/pdf').status_code==404
assert 'mcp_token_hash' not in q['body']
assert q['body']['session_id']
# Exercise the must-have path through the deployed Python runtime, including its PDF bundle.
def action(name,data=None):
    global q
    r=a.post('/api/quotes/'+q['id']+'/actions',headers=h,json={'version':q['version'],'event_key':str(uuid4()),'action':name,'data':data or {}})
    r.raise_for_status();q=r.json()
action('inspect',{'source_id':'request-seed'});action('approve',{'stage':0})
action('inspect',{'source_id':'clarification-seed'});action('resolve',{'confirmed':True})
for stage in [1,2,3]:action('approve',{'stage':stage})
for src in {src for line in q['body']['calculation']['lines'] for src in line['evidence']}:action('inspect',{'source_id':src})
for line in q['body']['calculation']['lines']:action('verify',{'line_id':line['id'],'confirmed':True})
action('approve',{'stage':4});action('risk_first');action('risk_reconcile')
for risk in q['body']['risks']:
    if risk['disposition']=='open':action('risk_dispose',{'risk_id':risk['id'],'disposition':'qualified'})
for stage in [5,6]:action('approve',{'stage':stage})
action('preview');action('approve',{'stage':7});action('export')
pdf=a.get('/api/quotes/'+q['id']+'/pdf');pdf.raise_for_status()
from io import BytesIO
from pypdf import PdfReader
reader=PdfReader(BytesIO(pdf.content));assert sum(len(page.images) for page in reader.pages)>=1
assert 'Fictional demo company' in ''.join(page.extract_text() for page in reader.pages)
action('respond',{'response':'accepted'});action('acceptance_check');action('approve_procurement',{'exception_reason':'Simulated manager review of public deployment test.'})
assert q['body']['procurement']['status']=='approved_requisition'
Path('artifacts').mkdir(exist_ok=True);Path('artifacts/deployment-proof.json').write_text(json.dumps({'url':base,'health':d,'public_access':True,'server_python':True,'logos':True,'playbooks':True,'secure_httponly_cookie':True,'two_session_isolation':True,'quote_id':q['id'],'full_seed_flow':'passed','deployed_pdf_logo':'passed','buy_only_requisition':'passed'},indent=2))
print('PASS public deployment, Python math, hosted persistence, runtime logos/playbooks, secure cookies, two-session quote/PDF isolation, full seed flow and buy-only requisition')
