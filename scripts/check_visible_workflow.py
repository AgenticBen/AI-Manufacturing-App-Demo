"""End-to-end HTTP acceptance of all human gates; creates only fictional test quotes."""
import sys,json,uuid,os
from pathlib import Path
import httpx
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.fixtures import SCENARIOS

def check(client,sid='seed'):
 def send(path,payload):
  r=client.post(path,json=payload);assert r.status_code==200,(path,r.status_code,r.text[:300]);return r.json()
 send('/api/session',{})
 s=SCENARIOS[sid];r=send('/api/quotes',{'scenario':sid,'description':s['description'],'quantity':s['quantity'],'company':s['name'],'contact':'Fictional demo reviewer','mode':'guided_demo','event_key':str(uuid.uuid4())})
 qid=r['id'];proof={'scenario':sid,'quote':qid,'stages':[]}
 def action(name,data=None):
  nonlocal r
  r=send('/api/quotes/'+qid+'/actions',{'action':name,'data':data or {},'version':r['version'],'event_key':str(uuid.uuid4())});return r['body']
 for stage in range(8):
  q=r['body'];assert q['stage']==stage
  locked=client.post('/api/quotes/'+qid+'/actions',json={'action':'approve','data':{'stage':stage},'version':r['version'],'event_key':str(uuid.uuid4())})
  assert locked.status_code==409
  if stage==0:action('inspect',{'source_id':'request-'+sid})
  if stage==1:
   action('simulate_email',{'kind':'clarification'});action('inspect',{'source_id':'clarification-'+sid});action('resolve',{'confirmed':True})
  if stage==4:
   if sid=='feed':action('refresh')
   action('replay_cost_qa')
   for line in r['body']['calculation']['lines']:
    for source in line['evidence']:action('inspect',{'source_id':source})
    action('verify',{'line_id':line['id'],'confirmed':True})
  if stage==5:
   action('risk_first');action('risk_reconcile')
   for risk in r['body']['risks']:
    if risk['disposition']=='open':action('risk_dispose',{'risk_id':risk['id'],'disposition':'qualified'})
  if stage==7:action('preview')
  for doc in r['body']['workflow']['checklist']:
   d=client.get(f'/api/quotes/{qid}/documents/{doc["id"]}');assert d.status_code==200
   assert all(x['citations'] for x in d.json()['sections'])
   action('open_document',{'id':doc['id']})
  action('confirm_documents',{'confirmed':True,'role_confirmed':stage in [3,7]})
  assert r['body']['workflow']['can_approve'],r['body']['workflow']['approval_blocker']
  action('approve',{'stage':stage});proof['stages'].append({'stage':stage+1,'locked_before_review':True,'approved_after_review':True})
  print(sid,'stage',stage+1,'passed',flush=True)
  if stage==4:action('simulate_email',{'kind':'procurement'})
 action('simulate_email',{'kind':'customer-quote'});action('export')
 assert client.get(f'/api/quotes/{qid}/pdf').content.startswith(b'%PDF')
 action('respond',{'response':'accepted'});action('acceptance_check');action('approve_procurement',{'exception_reason':'Fictional manager accepts the documented demo variance.'})
 action('simulate_email',{'kind':'purchase-list'});action('simulate_email',{'kind':'pm-handoff'})
 for doc in r['body']['workflow']['documents']:
  assert doc['available'],doc
  pdf=client.get(f'/api/quotes/{qid}/documents/{doc["id"]}/pdf');assert pdf.status_code==200 and pdf.content.startswith(b'%PDF'),doc
 proof['pdfs']=18;proof['buy_only']=all(float(x['purchase_quantity'])>0 for x in r['body']['procurement']['purchase_lines'])
 proof['no_real_messages']=True
 return proof
if __name__=='__main__':
 base=os.environ.get('ARC_TEST_URL','http://127.0.0.1:8011')
 with httpx.Client(base_url=base,headers={'X-Arc-Client':'web'},timeout=90) as c:proof=check(c,sys.argv[1] if len(sys.argv)>1 else 'seed')
 Path('artifacts/visible-workflow-proof.json').write_text(json.dumps(proof,indent=2))
 print(json.dumps(proof))
