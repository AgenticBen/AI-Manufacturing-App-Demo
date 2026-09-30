import sys,json
from pathlib import Path
from uuid import uuid4
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from backend.api import app
from backend.fixtures import SCENARIOS
c=TestClient(app);h={'X-Arc-Client':'web'}
def post(path,payload):
    r=c.post('/api'+path,json=payload,headers=h);assert r.status_code==200,(r.status_code,r.text);return r.json()
def action(r,name,d):return post('/quotes/'+r['id']+'/actions',{'action':name,'data':d,'version':r['version'],'event_key':str(uuid4())})
def create(sid):return post('/quotes',{'scenario':sid,'description':SCENARIOS[sid]['description'],'quantity':'1','contact':'Shop-rule test visitor','event_key':str(uuid4())})
post('/session',{});seed=create('seed');seed=action(seed,'inspect',{'source_id':'request-seed'});seed=action(seed,'approve',{'stage':0});seed=action(seed,'inspect',{'source_id':'clarification-seed'});seed=action(seed,'resolve',{'confirmed':True})
for stage in [1,2]:seed=action(seed,'approve',{'stage':stage})
rule={'operation':'weld','hours':'2.10','reason':'Synthetic adapter trial required additional fixture alignment time.','save_rule':True,'rule_statement':'For drawing-controlled mating adapters, review fixture alignment time explicitly before accepting the weld estimate.'}
seed=action(seed,'route_override',rule)
grain=create('grain');rules=c.get('/api/quotes/'+grain['id']).json()['shop_rules'];assert len(rules)==1 and rules[0]['version']==1 and rules[0]['body']['origin_scenario']=='seed'
rule['hours']='2.20';rule['reason']='Second synthetic trial warrants a revised alignment allowance.';seed=action(seed,'route_override',rule)
grain=c.get('/api/quotes/'+grain['id']).json();assert grain['shop_rules'][0]['version']==2
assert grain['body']['route_overrides']=={},'Guidance must not silently alter other quotes'
grain=action(grain,'inspect',{'source_id':'request-grain'});grain=action(grain,'approve',{'stage':0});assert grain['body']['approvals'][-1]['shop_rule_refs'][0]['version']==2
foreign=TestClient(app);foreign.post('/api/session',json={},headers=h)
other=foreign.post('/api/quotes',json={'scenario':'grain','description':SCENARIOS['grain']['description'],'quantity':'1','contact':'Foreign shop visitor','event_key':str(uuid4())},headers=h).json();assert not other['body']['shop_rules']
Path('artifacts/shop-rule-proof.json').write_text(json.dumps({'result':'passed','source_scenario':'seed','target_scenario':'grain','rule_id':rules[0]['id'],'versions':[1,2],'rule':rule['rule_statement'],'automatic_value_mutation':False,'foreign_session_rules_visible':False,'target_approval_cites_version':2},indent=2))
print('PASS seed → grain versioned guidance, version-two approval citation, no silent value changes, foreign-session isolation')
