from .time_utils import parse_time
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse,FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field,ConfigDict
from typing import Literal,Optional
from pathlib import Path
from datetime import datetime,timezone,timedelta
from uuid import uuid4
import secrets,os,hashlib,time,hmac
from copy import deepcopy
from .store import Store,StoreError
from .domain import create_quote,bind_session,actor,act,DomainError,require,new_job,current_fingerprint
from .fixtures import SCENARIOS,STAGES,FIXTURE_VERSION,now
from .calculations import fingerprint,dec,number,price
from .pdf_export import customer_pdf
from . import mcp

app=FastAPI(title='Agentic Arc · Manufacturing Quoting',docs_url=None,redoc_url=None)
store=Store()

class Intake(BaseModel):
    model_config=ConfigDict(extra='forbid')
    scenario:Literal['seed','grain','feed','custom']
    description:str=Field(min_length=5,max_length=3000)
    quantity:str=Field(max_length=8)
    company:str=Field(default='',max_length=150)
    contact:str=Field(min_length=2,max_length=150)
    mode:Literal['guided_demo','live_mcp']='guided_demo'
    event_key:str=Field(min_length=10,max_length=100)
    requested_date:Optional[str]=Field(default=None,max_length=30)
    notes:str=Field(default='',max_length=3000)

class Action(BaseModel):
    model_config=ConfigDict(extra='forbid')
    action:str=Field(max_length=40)
    version:int=Field(ge=1)
    event_key:str=Field(min_length=10,max_length=100)
    data:dict=Field(default_factory=dict)

@app.exception_handler(StoreError)
async def db_error(request,exc):return JSONResponse({'error':exc.message},status_code=exc.status)
@app.exception_handler(DomainError)
async def domain_error(request,exc):return JSONResponse({'error':str(exc)},status_code=409)
@app.exception_handler(ValueError)
async def value_error(request,exc):return JSONResponse({'error':str(exc)},status_code=422)

@app.middleware('http')
async def security(request:Request,call_next):
    if request.method=='POST' and request.url.path.startswith('/api/'):
        if request.headers.get('x-arc-client')!='web': return JSONResponse({'error':'Missing same-origin client header'},status_code=403)
        origin=request.headers.get('origin')
        if origin and origin!=str(request.base_url).rstrip('/'):
            # Forwarded scheme used by Vercel; never allow arbitrary cross-origin requests.
            allowed='https://'+request.headers.get('host','')
            if origin!=allowed:return JSONResponse({'error':'Cross-origin mutation denied'},status_code=403)
    if int(request.headers.get('content-length','0') or '0')>100000:return JSONResponse({'error':'Request too large'},status_code=413)
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff';response.headers['Referrer-Policy']='same-origin';response.headers['X-Frame-Options']='DENY'
    if request.url.path.startswith(('/api/','/mcp')):response.headers['Cache-Control']='no-store'
    response.headers['Content-Security-Policy']="default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; font-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    return response

def session(request):
    token=request.cookies.get('arc_session','')
    if len(token)<40:raise HTTPException(401,'Start or resume a demo session')
    return token

def safe_record(record):
    record=deepcopy(record);record['body'].pop('mcp_token_hash',None)
    for job in record['body']['jobs']:job.pop('lease',None)
    q=record['body'];clock=datetime.now(timezone.utc)
    def elapsed(start,end=None):
        if not start:return None
        seconds=max(0,int(((parse_time(end) if end else clock)-parse_time(start)).total_seconds()))
        return f'{seconds//3600}h {(seconds%3600)//60}m {seconds%60}s'
    from .workflow import workflow_state
    if q['scenario_id']!='custom':q['workflow']=workflow_state(q)
    q['elapsed_quote_time']=elapsed(q['created_at']);q['clock_as_of']=clock.isoformat()
    for stage in q['stages']:stage['elapsed']=elapsed(stage.get('entered_at'),stage.get('approved_at'))
    return record

@app.get('/api/health')
def health():return {'status':'ok','runtime':'python','spike_price':price('1000','100')['selling_price'],'persistence':'hosted_supabase','formula_version':'arc-decimal-1.0','runtime_assets':{'logo_light':(Path(__file__).resolve().parent/'assets'/'logo-light.png').is_file(),'logo_dark':(Path(__file__).resolve().parent/'assets'/'logo-dark.png').is_file(),'playbooks':len(list(Path('backend/playbooks').glob('*.md')))>=12}}

@app.get('/api/playbooks')
def playbooks():
    from .demo_sources import read_databases
    return read_databases(store,'D13')['rows']

@app.get('/api/playbooks/{playbook_id}')
def playbook(playbook_id:str):
    record=next((x for x in playbooks() if x['id']==playbook_id),None)
    if record is None:raise HTTPException(404,'Playbook not found')
    return record

@app.get('/api/databases')
def databases():
    from .demo_sources import read_databases
    return read_databases(store)

@app.get('/api/databases/{database_id}')
def database_detail(database_id:str):
    from .demo_sources import read_databases
    return read_databases(store,database_id)

@app.get('/api/catalog')
def catalog():return {'scenarios':SCENARIOS,'stages':STAGES,'fixture_version':FIXTURE_VERSION,'policy':{'target_margin':'30%','hold':'24 hours','validity':'14 days','escalation':'>5% cost increase OR <25% projected gross margin','tax_freight':'Explicitly excluded'}}

@app.post('/api/session')
def start(request:Request,response:Response):
    token=request.cookies.get('arc_session') or secrets.token_urlsafe(48)
    try:store.call(token,'session',{'ip_hash':hmac.new(store.secret.encode(),(request.client.host if request.client else 'unknown').encode(),hashlib.sha256).hexdigest()})
    except StoreError as e:
        if e.status!=401:raise
        token=secrets.token_urlsafe(48);store.call(token,'session',{'ip_hash':hmac.new(store.secret.encode(),(request.client.host if request.client else 'unknown').encode(),hashlib.sha256).hexdigest()})
    response.set_cookie('arc_session',token,httponly=True,secure=request.url.scheme=='https' or bool(os.environ.get('VERCEL')),samesite='strict',max_age=604800,path='/')
    return {'status':'ready','scope':'isolated fictional shop','expires_in_days':7}

@app.post('/api/reset')
def reset(request:Request,response:Response):
    # Creates a new isolated shop; cannot delete other visitors' records.
    token=secrets.token_urlsafe(48);store.call(token,'session',{'ip_hash':hmac.new(store.secret.encode(),(request.client.host if request.client else 'unknown').encode(),hashlib.sha256).hexdigest()})
    response.set_cookie('arc_session',token,httponly=True,secure=request.url.scheme=='https' or bool(os.environ.get('VERCEL')),samesite='strict',max_age=604800,path='/')
    return {'status':'new isolated demo session'}

@app.get('/api/quotes')
def quotes(request:Request):
    # Pipeline needs metadata only; never send full source packs/job contexts on a list.
    fields=['id','intake','scenario','revision','stage','lifecycle','mode','quantity','created_at','blocker']
    return [{'id':x['id'],'version':x['version'],'body':{k:x['body'].get(k) for k in fields}} for x in store.call(session(request),'list')]

@app.post('/api/quotes')
def create(data:Intake,request:Request):
    token=session(request);info=store.call(token,'session_info');q=bind_session(create_quote(data.model_dump()),info);q['workflow_version']='2.0';q['shop_rules']=store.call(token,'rules');record=store.call(token,'create',{'id':q['id'],'event_key':data.event_key,'body':q});return safe_record(record)

@app.get('/api/quotes/{qid}')
def get_quote(qid:str,request:Request):
    token=session(request);r=store.call(token,'get',{'id':qid});result=safe_record(r)
    result['shop_rules']=store.call(token,'rules');result['inventory']=store.call(token,'inventory');result['allocations']=store.call(token,'allocations',{'id':qid});return result

@app.post('/api/quotes/{qid}/actions')
def action(qid:str,data:Action,request:Request):
    token=session(request);r=store.call(token,'get',{'id':qid})
    action_hash=fingerprint({'action':data.action,'data':data.data})
    if data.event_key in r['body'].get('action_keys',{}):
        require(r['body']['action_keys'][data.event_key]==action_hash,'Idempotency key reused for different content')
        return safe_record(r)
    require(data.version==r['version'],'This workspace changed. Reload and review the latest revision.')
    allocations=store.call(token,'allocations',{'id':qid})
    d=deepcopy(data.data)
    if data.action=='reserve':
        inventory=store.call(token,'inventory');trusted=[]
        for l in d.get('lines',[]):
            lot=next((x for x in inventory if x['item']==l['item']),None);require(lot is not None,'Inventory lot not found')
            trusted.append({'item':l['item'],'quantity':l['quantity'],'unit_cost':lot['unit_cost'],'active':True,'status':'held','expires_at':(datetime.now(timezone.utc)+timedelta(hours=24)).isoformat()})
        d['trusted_allocations']=trusted
    r['body']['shop_rules']=store.call(token,'rules')
    if r['body']['scenario_id']!='custom' and 'base_route' not in r['body']:
        require(data.action in ('inspect','revise','export','respond','expire'),'This quote uses an earlier prepared fixture. Create a new revision before recalculating.')
    q,inv,lines=act(r['body'],data.action,d,allocations)
    shop_rule=None
    if d.get('save_rule'):
        require(data.action in ('route_override','reject_substitution','pricing'),'Save rules only alongside a reviewed override or rejection')
        reason=d.get('reason','').strip();statement=d.get('rule_statement','').strip()
        require(5<=len(reason)<=1500 and 5<=len(statement)<=1500,'Shop rule needs a clear statement and reason (5–1500 characters)')
        shop_rule={'key':d.get('rule_key') or ('route-'+d.get('operation','general') if data.action=='route_override' else 'substitution-compatibility' if data.action=='reject_substitution' else 'pricing-override'),'statement':statement,'reason':reason,'origin_scenario':q['scenario_id'],'origin_quote':qid,'reviewer':actor(q,'shop reviewer'),'guidance_only':True}

    # Expired holds are released in the same transaction as a new acceptance forecast.
    if data.action=='acceptance_check' and any(a['status']=='held' and not a['active'] for a in allocations):inv='release'
    q.setdefault('action_keys',{})[data.event_key]=action_hash;r['body']=q
    result=store.save(token,r,data.action,data.event_key,inv,lines,{'revision':q['revision']},shop_rule=shop_rule)
    return safe_record(result)

@app.get('/api/quotes/{qid}/documents/{document_id}/pdf')
def artifact_pdf(qid:str,document_id:str,request:Request):
    from .documents import document
    from .document_pdf import artifact_pdf
    q=store.call(session(request),'get',{'id':qid})['body']
    return Response(artifact_pdf(document(q,document_id),qid,str(request.base_url).rstrip('/')),media_type='application/pdf',headers={'Content-Disposition':f'attachment; filename="{document_id}-R{q["revision"]}.pdf"'})

@app.get('/api/quotes/{qid}/sources/{source_id}')
def source_lines(qid:str,source_id:str,request:Request,line:int=1):
    from html import escape
    from fastapi.responses import HTMLResponse
    q=store.call(session(request),'get',{'id':qid})['body']
    source=next((s for s in q['sources'] if s['id']==source_id),None)
    if source is None:raise HTTPException(404,'Source not found')
    rows=''.join('<p'+(' style="background:#fff0bd"' if i==line else '')+'>'+str(i)+': '+escape(t)+'</p>' for i,t in enumerate(source['content'].split('\n'),1))
    return HTMLResponse('<!doctype html><meta name="viewport" content="width=device-width"><title>Demo source</title><h1>'+escape(source['title'])+'</h1><p>Fictional demo copy · '+escape(source['revision'])+'</p>'+rows)

@app.get('/api/quotes/{qid}/documents/{document_id}')
def quote_document(qid:str,document_id:str,request:Request):
    from .documents import document
    q=store.call(session(request),'get',{'id':qid})['body']
    return document(q,document_id)

@app.get('/api/quotes/{qid}/pdf')
def pdf(qid:str,request:Request):
    r=store.call(session(request),'get',{'id':qid});q=r['body']
    require(q['lifecycle'] in ('exported','accepted','rejected','expired','changes_requested') and q.get('packages'),'Export must be recorded before downloading')
    p=q['packages'][-1];return Response(customer_pdf(p),media_type='application/pdf',headers={'Content-Disposition':f'attachment; filename="Ivy-quote-{qid[:8]}-R{p["revision"]}.pdf"'})

@app.get('/api/quotes/{qid}/handoff')
def handoff(qid:str,request:Request):
    q=store.call(session(request),'get',{'id':qid})['body'];require(q.get('procurement') is not None,'Acceptance checkpoint required')
    allowed={k:q[k] for k in ['id','revision','bom','route','requirements','risks','schedule','procurement']}
    return JSONResponse({'classification':'INTERNAL — fictional demonstration','production_status':'Awaiting production review','no_purchase_order_issued':True,**allowed},headers={'Content-Disposition':f'attachment; filename="internal-handoff-{qid[:8]}.json"'})

@app.get('/api/settings')
def settings():return {'providers':[{'id':'granola','name':'Granola','status':'setup_required','host_check':'Account metadata read succeeded on 2026-09-30; personal/public note scopes available.','app_status':'Owner-selected note and ingestion authorization required. No meeting content imported.'},{'id':'drive','name':'Google Drive','status':'setup_required','host_check':'One root-folder metadata read succeeded on 2026-09-30.','app_status':'Owner-selected document/folder scope required. No private documents imported.'},{'id':'gmail','name':'Gmail','status':'not_configured','host_check':'Not tested','app_status':'Optional; manual text import is available.'}],'ai':{'mode':'Client-driven MCP','api_inference':'Future only — unavailable; no paid model calls','offline':'Live jobs wait until an authorized client claims them.'},'security':'Public settings are read-only. No account credentials or private records are exposed.'}

@app.post('/api/quotes/{qid}/mcp-capability')
def capability(qid:str,request:Request):
    token=session(request);r=store.call(token,'get',{'id':qid});q=r['body'];require(q['mode']=='live_mcp','Switch to a new Live MCP request for client access')
    cap=secrets.token_urlsafe(48);q['mcp_token_hash']=hashlib.sha256(cap.encode()).hexdigest();store.save(token,r,'mcp_capability_created',str(uuid4()))
    return {'token':cap,'url':str(request.base_url).rstrip('/')+'/mcp','scope':'Only this quote; proposal tools only, no human approval or inventory mutation','expires':'With this demo session (7 days)'}

@app.post('/mcp')
async def mcp_rpc(request:Request):
    auth=request.headers.get('authorization','');require(auth.startswith('Bearer '),'MCP bearer capability required')
    cap=auth[7:];require(len(cap)>=40,'Invalid MCP capability')
    binding=store.call('', 'mcp_resolve',{'token_hash':hashlib.sha256(cap.encode()).hexdigest()})
    raw=await request.json();id=raw.get('id');method=raw.get('method')
    if method=='initialize':return {'jsonrpc':'2.0','id':id,'result':{'protocolVersion':'2025-03-26','capabilities':{'tools':{}},'serverInfo':{'name':'agentic-arc-manufacturing','version':'1.0.0'}}}
    if method=='notifications/initialized':return Response(status_code=202)
    if method=='tools/list':return {'jsonrpc':'2.0','id':id,'result':{'tools':mcp.tool_list()}}
    if method=='ping':return {'jsonrpc':'2.0','id':id,'result':{}}
    if method!='tools/call':return {'jsonrpc':'2.0','id':id,'error':{'code':-32601,'message':'Method not found'}}
    try:
        r=store.call_hash(binding['session_hash'],'get',{'id':binding['quote_id']});r['body']['shop_rules']=store.call_hash(binding['session_hash'],'rules')
        params=raw.get('params',{});inventory=store.call_hash(binding['session_hash'],'inventory');allocations=store.call_hash(binding['session_hash'],'allocations',{'id':r['id']})
        q,result,changed=mcp.execute(params.get('name'),params.get('arguments',{}),r['body'],inventory,allocations)
        if changed:
            r['body']=q
            store.call_hash(binding['session_hash'],'save',{'id':r['id'],'version':r['version'],'body':q,'kind':'mcp_'+params['name'],'event_key':str(uuid4()),'detail':{'tool':params['name']}})
        import json
        return {'jsonrpc':'2.0','id':id,'result':{'content':[{'type':'text','text':json.dumps(result)}],'isError':False}}
    except (DomainError,StoreError,ValueError,KeyError) as e:
        return {'jsonrpc':'2.0','id':id,'result':{'content':[{'type':'text','text':str(e)}],'isError':True}}

# API routes precede static mount, both locally and on Vercel.
if Path('dist').exists():app.mount('/',StaticFiles(directory='dist',html=True),name='frontend')
else:
    @app.get('/')
    def pending_frontend():return {'status':'Build frontend with npm run build'}
