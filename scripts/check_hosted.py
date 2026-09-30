"""Explicit opt-in integration test using isolated hosted demo sessions, no private data."""
import sys,json,secrets,hashlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from backend.api import app
from backend.store import Store,StoreError
from backend.domain import create_quote
from backend.fixtures import SCENARIOS
from backend.calculations import fingerprint
from uuid import uuid4

c=TestClient(app); headers={'X-Arc-Client':'web'}
def post(path,body):
    r=c.post(path,json=body,headers=headers)
    assert r.status_code==200,(path,r.status_code,r.text)
    return r.json()
def action(record,name,data=None):
    return post('/api/quotes/'+record['id']+'/actions',{'version':record['version'],'event_key':str(uuid4()),'action':name,'data':data or {}})
post('/api/session',{})
results=[]
for sid in ['seed','grain','feed']:
    s=SCENARIOS[sid];payload={'scenario':sid,'description':s['description'],'quantity':s['quantity'],'contact':'Hosted acceptance test','company':s['name'],'event_key':str(uuid4())}
    q=post('/api/quotes',payload);duplicate=post('/api/quotes',payload);assert duplicate['id']==q['id']
    q=action(q,'inspect',{'source_id':'request-'+sid});q=action(q,'approve',{'stage':0})
    q=action(q,'inspect',{'source_id':'clarification-'+sid});q=action(q,'resolve',{'confirmed':True})
    for stage in [1,2,3]:q=action(q,'approve',{'stage':stage})
    if sid=='feed':q=action(q,'refresh')
    if sid=='seed':q=action(q,'reserve',{'lines':[{'item':'FASTENER','quantity':'5'}]})
    sources=set(x for l in q['body']['calculation']['lines'] for x in l['evidence'])
    for src in sources:q=action(q,'inspect',{'source_id':src})
    for line in q['body']['calculation']['lines']:q=action(q,'verify',{'line_id':line['id'],'confirmed':True})
    q=action(q,'approve',{'stage':4});q=action(q,'risk_first');q=action(q,'risk_reconcile')
    for risk in q['body']['risks']:
        if risk['disposition']=='open':q=action(q,'risk_dispose',{'risk_id':risk['id'],'disposition':'qualified'})
    for stage in [5,6]:q=action(q,'approve',{'stage':stage})
    q=action(q,'preview');q=action(q,'approve',{'stage':7});q=action(q,'export')
    pdf=c.get('/api/quotes/'+q['id']+'/pdf');assert pdf.status_code==200 and pdf.content.startswith(b'%PDF')
    Path('artifacts').mkdir(exist_ok=True);Path('artifacts/'+sid+'-quote.pdf').write_bytes(pdf.content)
    q=action(q,'respond',{'response':'accepted'});original=q['body']['package']['selling_price'];q=action(q,'acceptance_check')
    q=action(q,'approve_procurement',{'exception_reason':'Synthetic manager review accepts documented test variance.'})
    assert q['body']['package']['selling_price']==original
    assert q['body']['procurement']['status']=='approved_requisition'
    results.append({'scenario':sid,'quote_id':q['id'],'selling_price':original,'status':'passed'})
    print('PASS full hosted flow:',sid,flush=True)
# Independent visitor cannot obtain quote or PDF, even if guessed.
b=TestClient(app);assert b.post('/api/session',headers=headers,json={}).status_code==200
assert b.get('/api/quotes/'+q['id']).status_code==404
assert b.get('/api/quotes/'+q['id']+'/pdf').status_code==404
assert c.post('/api/quotes',json=payload).status_code==403
print('PASS API session isolation and CSRF header',flush=True)
# Two quote locks compete for a single shared lot. PostgreSQL lot lock is the boundary.
s=Store();token=secrets.token_urlsafe(48);s.call(token,'session');records=[]
for _ in range(2):
    v=create_quote({'scenario':'seed','description':SCENARIOS['seed']['description'],'quantity':'1','contact':'Concurrency test','mode':'guided_demo'});records.append(s.call(token,'create',{'id':v['id'],'event_key':str(uuid4()),'body':v}))
def reserve(r):
    try:return s.save(token,r,'race',str(uuid4()),'reserve',[{'item':'FASTENER','quantity':'5'}])
    except StoreError as e:return {'error':e.message}
with ThreadPoolExecutor(2) as pool: race=list(pool.map(reserve,records))
assert sum('error' not in x for x in race)==1,race
lot=next(x for x in s.call(token,'inventory') if x['item']=='FASTENER');assert lot['available']=='0'
print('PASS simultaneous final-stock reservations',flush=True)
Path('artifacts/hosted-acceptance.json').write_text(json.dumps({'scenarios':results,'session_isolation':'passed','csrf':'passed','concurrent_reservations':'passed'},indent=2))
