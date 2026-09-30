from pathlib import Path
import sys,os,httpx,secrets
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.store import Store
s=Store();h={'apikey':s.key}
for table in ['arc_sessions','arc_quotes','arc_events','arc_lots','arc_reservations']:
    r=httpx.get(s.url+'/rest/v1/'+table,headers=h,timeout=20)
    assert r.status_code in (401,403), (table,r.status_code,r.text)
    print('PASS direct table denied:',table,flush=True)
r=httpx.post(s.url+'/rest/v1/rpc/arc_rpc',headers=h,json={'p_key':'wrong','p_session':'0'*64,'p_op':'list','p_data':{}},timeout=20)
assert r.status_code in (401,403),r.text
print('PASS public RPC denied without server capability')
token=secrets.token_urlsafe(48);s.call(token,'session');assert s.call(token,'list')==[]
print('PASS authorized server capability works, empty isolated session')
