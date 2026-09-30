from .time_utils import parse_time
from copy import deepcopy
from datetime import datetime,timezone,timedelta,date
from uuid import uuid4
import secrets
from .fixtures import build, SCENARIOS, STAGES, FIXTURE_VERSION, source, now
from .decision_support import route_estimates,pricing_options,central_today
from .calculations import estimate, fingerprint, dec, number, variance, schedule, money

class DomainError(ValueError): pass

def require(condition,message):
    if not condition: raise DomainError(message)

def current_fingerprint(q,stage):
    # Immutable stage snapshots each depend on the current revision and explicit reviewed data.
    scopes=[q.get('intake'),q.get('requirements'),q.get('bom'),q.get('route'),q.get('calculation'),q.get('risks'),{'margin':q.get('margin'),'discount':q.get('discount'),'terms':q.get('terms')},q.get('package')]
    return fingerprint({'revision':q['revision'],'stage':stage,'inputs':scopes[:stage+1]})

def actor(q,role='employee'):
    return f"Demo visitor ({q.get('session_id','local-script-session')}), simulated {role}"

def event(q,kind,detail): q['timeline'].append({'at':now(),'kind':kind,'detail':detail})

def new_job(q, stage):
    return {'id':str(uuid4()),'revision':q['revision'],'stage':stage,'state':'queued','attempts':0,'input_fingerprint':current_fingerprint(q,stage),'playbook':f'{stage+1:02d}','lease':None,'lease_expires':None,'proposal':None,'errors':[]}

def recalculate(q, allocations=None):
    if q['scenario_id']=='custom': return
    q['margin']=number(dec(q['margin']));q['discount']=number(dec(q['discount']))
    if allocations is not None: q['allocations']=allocations
    active={}
    for a in q.get('allocations',[]):
        if a.get('active'):
            item=a['item']; old=active.get(item,{'quantity':'0','unit_cost':a['unit_cost']})
            old['quantity']=number(dec(old['quantity'])+dec(a['quantity'])); active[item]=old
    q['route_support']=route_estimates(q['scenario_id'],q['scenario']['material'],q['quantity'],q['base_route'],q['route_choice'],q.get('route_overrides',{}))
    q['route']=q['route_support']['selected_route'];q['fixture_cost']=q['route_support']['fixture_cost']
    for evidence in q['sources']:
        if evidence['id']=='route-history-'+q['scenario_id']:
            evidence['content']=__import__('json').dumps(q['route_support'],indent=2);evidence['hash']=fingerprint(evidence['content'])
    q['calculation']=estimate(q['bom'],q['route'],q['quantity'],active,q['margin'],q['discount'],q['contingency'],engineering=q.get('engineering'),fixture_cost=q['fixture_cost'])
    q['pricing_options']=pricing_options(q)
    q['calculation']['id']=str(uuid4()); q['calculation']['created_at']=now()
    q['calculation_runs'].append(deepcopy(q['calculation']))
    import json
    for sid,title,content in [('calculation-current','Current Python calculation record',json.dumps(q['calculation'],indent=2)),('intake-fields','Current quote input fields',json.dumps({'quantity':q['quantity'],'scenario':q['scenario_id'],'requirements':q['requirements']},indent=2))]:
        record=source(sid,title,content,'python_record' if sid=='calculation-current' else 'synthetic_customer','Numbered quote record lines')
        q['sources']=[x for x in q['sources'] if x['id']!=sid]+[record]
    q['schedule_inputs']=[{'id':'drawing','dependencies':[],'days':'2'},{'id':'materials','dependencies':[],'days':q['scenario']['lead_days']},{'id':'fabrication','dependencies':['drawing','materials'],'days':number(sum(dec(x['hours']) for x in q['calculation']['lines'] if x['category']=='operation')/dec('8'))},{'id':'outside-coating','dependencies':['fabrication'],'days':'10' if q['scenario']['material']=='Galvanized carbon steel' else '0'},{'id':'ready-to-ship','dependencies':['outside-coating'],'days':'1'}]
    q['schedule_origin']=central_today().isoformat()
    q['schedule']=schedule(q['schedule_inputs'],q['schedule_origin'])

def invalidate(q,from_stage,reason):
    for i in range(from_stage,8): q['stages'][i]['status']='invalidated'; q['stages'][i]['reason']=reason; q['stages'][i]['invalidated_at']=now(); q['stages'][i]['approved_at']=None
    for job in q['jobs']:
        if job['stage']>=from_stage and job['state'] not in ('succeeded','cancelled'): job['state']='stale'
    q['stage']=min(q['stage'],from_stage);q['stages'][q['stage']]['entered_at']=now(); q['stages'][q['stage']]['status']='awaiting_review' if q['mode']=='guided_demo' else 'waiting_client'
    q['lifecycle']='draft'; q['package']=None
    if from_stage<=4: q['verifications']={}
    if q['mode']=='live_mcp': q['jobs'].append(new_job(q,q['stage']))
    event(q,'invalidated',reason)

def create_quote(data):
    from .survey import normalize,defaults,attach
    submitted_sid=data['scenario'];values=normalize(submitted_sid,data.get('survey'))
    survey_changed=submitted_sid in SCENARIOS and values!=defaults(submitted_sid)
    sid=submitted_sid; custom=sid=='custom'
    if sid in SCENARIOS and (data['description'].strip()!=SCENARIOS[sid]['description'] or data.get('notes','').strip() or survey_changed):
        sid='custom'; custom=True
    require(sid in SCENARIOS or custom,'Unknown scenario')
    qty=dec(data['quantity'],'order quantity',True); require(qty==qty.to_integral() and qty<=12,'Supported quantity is 1–12 assemblies')
    q={'id':str(uuid4()),'revision':1,'revision_history':[],'created_at':now(),'scenario_id':sid,'mode':data.get('mode','guided_demo'),'quantity':number(qty),'stage':0,'lifecycle':'draft','margin':'0.30','discount':'0','contingency':'0','fixture_version':FIXTURE_VERSION,'offers_valid_until':(datetime.now(timezone.utc)+timedelta(hours=24)).isoformat(),'policy_version':'demo-policy-v1','intake':data,'timeline':[],'approvals':[],'verifications':{},'inspected':[],'allocations':[],'calculation_runs':[],'packages':[],'package':None,'jobs':[],'risk_review':{'first_pass':None,'reconciliation':None},'acceptance':None,'procurement':None,'custom_sources':[],'terms':{'currency':'USD','payment':'50% deposit; balance before dispatch.','validity_days':'14','freight':'Excluded; arrange separately.','tax':'Excluded; not a tax determination.','delivery':'Conditional ready-to-ship forecast; no committed delivery date.','exclusions':'Foundations, anchors, powered downstream equipment, installation, certification and production release.'}}
    if custom:
        q.update(scenario={'name':data.get('company') or 'Custom request','short':'Custom request','description':data['description']},requirements=[],bom=[],route=[],sources=[source('custom-request','Submitted custom request',data['description'],'operator_input')],risks=[],calculation=None,schedule=None)
        q['sources'][0]['synthetic']=False
        q['blocker']='Needs live AI / engineering review. No prepared design or estimate matches this request.'
    else:
        q.update(build(sid)); q['blocker']=q['scenario']['clarification']; q['clarification_resolved']=False
    attach(q,values,'Prepared fictional example' if not custom else 'Customer / operator input · unverified')
    if not custom:recalculate(q)
    q['stages']=[{'name':name,'status':'awaiting_review' if i==0 and q['mode']=='guided_demo' else 'waiting_client' if i==0 else 'waiting_input','reason':'','entered_at':now() if i==0 else None,'approved_at':None} for i,name in enumerate(STAGES)]
    if custom: q['stages'][0]['status']='blocked'
    if q['mode']=='live_mcp': q['jobs'].append(new_job(q,0))
    event(q,'created','Saved request before analysis. '+('Custom request requires live review.' if custom else f'Saved example {FIXTURE_VERSION}; no model inference.'))
    return q

def can_approve(q,stage, allocations=None):
    require(q['scenario_id']!='custom','Custom request needs a validated engineering proposal; no fixture is applicable.')
    require(q['stage']==stage,'Review the current stage first')
    require(all(s['status']=='approved' for s in q['stages'][:stage]),'Upstream approvals are required')
    if q['mode']=='live_mcp': require(any(j['stage']==stage and j['revision']==q['revision'] and j['state']=='succeeded' for j in q['jobs']),'Waiting for the active MCP client to submit a valid proposal')
    from .workflow import approval_check
    approval_check(q,stage)
    if stage==0: require('request-'+q['scenario_id'] in q['inspected'],'Inspect the request source and customer identity first')
    if stage>=1: require(q.get('clarification_resolved'),'Resolve the customer/engineering clarification before approving the baseline')
    if stage>=4:
        if allocations is not None:
            actual=[(a['item'],a['quantity']) for a in allocations if a['active']]
            previous=[(a['item'],a['quantity']) for a in q['allocations'] if a['active']]
            require(sorted(actual)==sorted(previous),'Inventory allocation changed or expired. Refresh cost and reverify selected evidence.')
        require(parse_time(q['offers_valid_until'])>datetime.now(timezone.utc),'Selected offers are stale. Refresh evidence and reverify costs.')
        for line in q['calculation']['lines']:
            require(q['verifications'].get(line['id'],{}).get('hash')==fingerprint(line),'Verify every selected cost input against its current source')
    if stage>=5:
        require(q['risk_review']['first_pass'] and q['risk_review']['reconciliation'],'Save the distinct first-pass risk review, then reconcile')
        require(all(r['disposition']!='open' for r in q['risks']),'Disposition every risk before approval')
        require(not any(r['blocking'] and r['disposition']!='resolved' for r in q['risks']),'Critical feasibility blockers cannot be priced away')
    if stage>=7: require(q['package'] is not None,'Preview the exact customer package before release')

def package(q):
    return {'id':str(uuid4()),'quote_id':q['id'],'revision':q['revision'],'seller':'Ivy Hopper Works (fictional demo company)','customer':q['intake'].get('company') or q['scenario']['name'],'recipient':q['intake']['contact'],'description':f"Stationary gravity-discharge hopper for {q['scenario']['handled']}; {q['scenario']['capacity']}, {q['scenario']['material']}, {q['scenario']['outlet']}. Scope subject to reviewed drawing and exclusions.",'quantity':q['quantity'],'configuration':{k:q['scenario'][k] for k in ['capacity','material','outlet','frame','cover']},'drawing':'Illustrative E-'+q['scenario_id']+' R1; not released for manufacture','selling_price':q['calculation']['selling_price'],'currency':'USD','terms':deepcopy(q['terms']),'created_at':now(),'expires_at':(datetime.now(timezone.utc)+timedelta(days=14)).isoformat(),'ready_to_ship':q['schedule']['ready_to_ship'],'attachments':[],'branding':'Powered by Agentic Arc','synthetic':True}

def act(q, action, data, allocations=None):
    """Mutates a copy, then caller persists with version CAS and inventory atomically."""
    if action in ('open_document','confirm_documents','simulate_email','replay_cost_qa','request_correction','insurance_option','draft_material','approve_material'):
        from .workflow import workflow_action
        return workflow_action(q,action,data)
    q=deepcopy(q); inventory_action=None; reserve_lines=[]
    from .survey import ensure_survey
    ensure_survey(q)
    require(action in ['inspect','verify','resolve','approve','reject_stage','revise','reserve','release','refresh','risk_first','risk_reconcile','risk_dispose','pricing','preview','export','respond','acceptance_check','approve_procurement','expire','attach_source','route_choice','route_override','reject_substitution'],'Unknown action')
    if q['lifecycle'] in ('accepted','rejected','expired'):
        require(action in ['inspect','acceptance_check','approve_procurement','export'],'This response is final; preserve the issued revision. Start a new request for changed scope.')
    if q['lifecycle']=='exported':
        require(action in ['inspect','respond','expire','revise','export','acceptance_check'],'Issued quote is immutable. Create a revision to change it.')
    if action=='inspect':
        source_id=data['source_id']; require(any(s['id']==source_id for s in q['sources']),'Source not found')
        if source_id not in q['inspected']: q['inspected'].append(source_id)
    elif action=='verify':
        require(q['stage']>=4,'Selected cost verification opens at sourcing')
        line=next((l for l in q['calculation']['lines'] if l['id']==data['line_id']),None); require(line is not None,'Cost line not found')
        require(all(s in q['inspected'] for s in line['evidence']),'Open every linked evidence record before verifying this input')
        require(data.get('confirmed') is True,'Explicit personal verification required')
        q['verifications'][line['id']]={'hash':fingerprint(line),'reviewer':actor(q),'at':now(),'evidence':line['evidence']}
    elif action=='resolve':
        require(q['scenario_id']!='custom','No prepared clarification for custom requests')
        require('clarification-'+q['scenario_id'] in q['inspected'],'Inspect the prepared customer/engineering response first')
        require(data.get('confirmed') is True,'Human confirmation required')
        q['clarification_resolved']=True; q['blocker']=None
        for r in q['risks']:
            if r['id']=='engineering': r['disposition']='resolved'; r['resolved_at']=now()
        for r in q['requirements']:
            if not r.get('section'):r['status']='confirmed'
        if q['mode']=='live_mcp': invalidate(q,1,'Human clarified baseline; live proposal inputs refreshed')
        event(q,'clarification_resolved',q['scenario']['resolution'])
    elif action=='approve':
        stage=int(data['stage'])
        # Idempotent repeated approval cannot approve a subsequent stage.
        if stage<=q['stage'] and q['stages'][stage]['status']=='approved': return q,None,[]
        can_approve(q,stage,allocations)
        approval={'id':str(uuid4()),'stage':stage,'revision':q['revision'],'fingerprint':current_fingerprint(q,stage),'reviewer':actor(q,['intake reviewer','requirements reviewer','engineer','estimator','cost reviewer','risk reviewer','commercial manager','release reviewer'][stage]),'simulated':True,'shop_rule_refs':[{'id':r['id'],'version':r['version']} for r in q.get('shop_rules',[])],'at':now(),'decision':'approved','mode':q['mode']}
        q['approvals'].append(approval); q['stages'][stage]['status']='approved';q['stages'][stage]['approved_at']=now()
        if stage==7: q['lifecycle']='approved_for_release'; q['package']['release_approval']=approval['id']
        else:
            q['stage']=stage+1;q['stages'][stage+1]['entered_at']=now(); q['stages'][stage+1]['status']='awaiting_review' if q['mode']=='guided_demo' else 'waiting_client'
            if q['mode']=='live_mcp': q['jobs'].append(new_job(q,stage+1))
        event(q,'human_approval',STAGES[stage]+' approved at revision '+str(q['revision']))
    elif action=='reject_stage':
        reason=data.get('reason','').strip(); require(bool(reason),'Explain the requested change')
        invalidate(q,q['stage'],reason); q['stages'][q['stage']]['status']='needs_changes'
        q['approvals'].append({'stage':q['stage'],'revision':q['revision'],'at':now(),'decision':'changes_requested','reason':reason,'reviewer':actor(q)})
    elif action=='revise':
        require(q['scenario_id']!='custom','Custom scope changes need engineering review')
        qty=dec(data.get('quantity',q['quantity']),'quantity',True); require(qty==qty.to_integral() and qty<=12,'Quantity must be 1–12')
        material=data.get('material',q['scenario']['material']); require(material in q['scenario']['material_options'],'Unsupported material requires live engineering review')
        q['revision_history'].append({'revision':q['revision'],'at':now(),'reason':data.get('reason','Quantity/material change'),'snapshot':{k:deepcopy(q[k]) for k in ['quantity','scenario','bom','route','calculation','approvals','requirements','stages']}})
        q['revision']+=1; q['quantity']=number(qty); q.update(build(q['scenario_id'],material)); q['clarification_resolved']=False; q['blocker']=q['scenario']['clarification']; q['allocations']=[]; q['risk_review']={'first_pass':None,'reconciliation':None};q['inspected']=[]
        from .survey import attach,defaults
        revised_answers=deepcopy(q.get('survey_answers') or defaults(q['scenario_id']));revised_answers['construction_material']=material
        attach(q,revised_answers,'Prepared example · revised requirements; initial submission retained in intake')
        if q.get('session_started_at'):bind_session(q,{'id':q['session_id'],'created_at':q['session_started_at']})
        recalculate(q); invalidate(q,1,'Quantity/material revision changed requirements, BOM, route, cost, risk and package');inventory_action='release'
    elif action=='reserve':
        require(q['stage']==4,'Reserve stock explicitly during sourcing review')
        require(bool(data.get('lines')),'Select at least one available lot')
        for x in data['lines']:
            b=next((b for b in q['bom'] if b['item']==x['item']),None); require(b is not None,'Item is outside the current BOM')
            amount=dec(x['quantity'],'reservation',True); require(amount<=dec(b['per_unit'])*dec(q['quantity']),'Reservation exceeds BOM need')
            reserve_lines.append({'item':x['item'],'quantity':number(amount)})
        require(len({x['item'] for x in reserve_lines})==len(reserve_lines),'Duplicate lot in reservation')
        # Database owns lot rates and availability; caller fills trusted allocation preview.
        q['allocations']=data['trusted_allocations']; recalculate(q); invalidate(q,4,'Inventory allocation changed selected costs'); inventory_action='reserve'
    elif action in ('release','refresh'):
        require(q['scenario_id']!='custom','No estimate exists')
        recalculate(q,[] if action=='release' else allocations)
        if action=='refresh':
            q['offers_valid_until']=(datetime.now(timezone.utc)+timedelta(hours=24)).isoformat()
            for s in q['sources']:
                if s['kind']=='synthetic_supplier': s['retrieved_at']=now();s['price_as_of']=now();s['valid_until']=q['offers_valid_until'];s['intentionally_stale']=False; s['revision']='Demo refresh '+str(len(q['calculation_runs']))
        invalidate(q,4,'Stock/evidence refreshed; selected input verification reopened')
        if action=='release': inventory_action='release'
    elif action=='risk_first':
        require(q['stage']==5,'Risk review opens after approved sourcing')
        q['risk_review']['first_pass']={'id':str(uuid4()),'at':now(),'mode':'prepared_example','facts_hash':fingerprint({'requirements':q['requirements'],'bom':q['bom'],'route':q['route']}),'findings':['Validate engineering envelope and interface against confirmed source.','Check offered supply and quote hold duration against fulfillment dependencies.','Keep freight/tax exclusions visible.'],'prior_risk_conclusions_visible':False}
    elif action=='risk_reconcile':
        require(q['risk_review']['first_pass'] is not None,'Save first pass before seeing prior conclusions')
        q['risk_review']['reconciliation']={'at':now(),'first_pass_id':q['risk_review']['first_pass']['id'],'retained_original_ids':[r['id'] for r in q['risks']],'note':'Prepared example reconciliation; distinct pass is not proof of independence or testing.'}
    elif action=='risk_dispose':
        require(q['risk_review']['reconciliation'] is not None,'Reconcile findings first')
        r=next((r for r in q['risks'] if r['id']==data['risk_id']),None); require(r is not None,'Risk not found')
        disposition=data.get('disposition');require(disposition in ('qualified','resolved','blocked'),'Invalid disposition')
        require(not r['blocking'] or (disposition=='resolved' and q['clarification_resolved'] and r['id']=='engineering'),'Critical engineering risk needs specifically resolved evidence; this finding cannot be overridden as a commercial qualification')
        r['disposition']=disposition;r['reviewer']=actor(q);r['reviewed_at']=now()
    elif action in ('route_choice','route_override'):
        require(q['stage']==3,'Estimator route decisions belong to stage 4')
        if action=='route_choice':q['route_choice']=data['choice']
        else:
            require(data.get('operation') in {o['id'] for o in q['base_route']},'Unknown operation')
            hours=dec(data.get('hours'),'reviewed hours',True);require(hours<=100,'Reviewed run hours must be no more than 100 per assembly')
            require(len(data.get('reason','').strip())>=5,'Estimator reason required')
            q['route_overrides'][data['operation']]={'hours':number(hours),'reason':data['reason'],'reviewer':actor(q,'estimator'),'at':now()}
        recalculate(q,allocations);invalidate(q,3,'Estimator selected/edited route; cost, risk, price and release reopened')
    elif action=='reject_substitution':
        require(q['stage'] in (2,3,4),'Review substitutions during engineering or sourcing')
        require(len(data.get('reason','').strip())>=5,'Rejection reason required')
        q.setdefault('substitution_decisions',[]).append({'candidate':'alternate-'+q['scenario_id'],'decision':'rejected','reason':data['reason'],'reviewer':actor(q,'engineer'),'at':now()})
        event(q,'substitution_rejected',data['reason'])
    elif action=='pricing':
        require(q['stage']>=6,'Pricing requires approved cost and risk')
        # Preserve input verification since only commercial assumptions change.
        q['margin']=str(data.get('margin',q['margin']));q['discount']=str(data.get('discount',q['discount']))
        recalculate(q,allocations); invalidate(q,6,'Commercial margin/discount changed; actual projected margin recalculated')
    elif action=='preview':
        require(q['stage']==7 and all(s['status']=='approved' for s in q['stages'][:7]),'Approve upstream stages first')
        q['package']=package(q);event(q,'package_generated','Exact allowlisted customer package generated for human preview')
    elif action=='export':
        require(q['lifecycle'] in ('approved_for_release','exported','accepted'),'Approve release before downloading')
        if q['lifecycle']=='approved_for_release':
            can_approve(q,7,allocations)
            q['packages'].append(deepcopy(q['package']));q['lifecycle']='exported';event(q,'exported','PDF exported. No send event or customer acceptance implied.')
    elif action=='respond':
        require(q['lifecycle']=='exported','Export the approved quote before recording response')
        response=data.get('response');require(response in ('accepted','rejected','changes_requested'),'Unsupported response')
        require(parse_time(q['package']['expires_at'])>datetime.now(timezone.utc),'Quote expired; issue a reviewed revision')
        q['lifecycle']=response;q['acceptance']={'response':response,'at':now(),'simulated':True,'package_id':q['package']['id'],'accepted_price':q['package']['selling_price'],'original_cost':q['calculation']['pricing_cost']}
        event(q,'simulated_response',response)
        if response!='accepted': inventory_action='release'
    elif action=='expire':
        q['lifecycle']='expired';inventory_action='release';event(q,'expired','Simulated expiry releases held stock')
    elif action=='acceptance_check':
        require(q['lifecycle']=='accepted','Customer acceptance required')
        factor='1.20' if q['scenario_id']=='feed' else '1'
        active={a['item']:{'quantity':a['quantity'],'unit_cost':a['unit_cost']} for a in (allocations or []) if a['active']}
        refreshed=estimate(q['bom'],q['route'],q['quantity'],active,q['margin'],q['discount'],q['contingency'],factor,engineering=q.get('engineering'),fixture_cost=q.get('fixture_cost','0'))
        v=variance(q['acceptance']['original_cost'],refreshed['pricing_cost'],q['acceptance']['accepted_price'])
        purchase_lines=[l for l in refreshed['lines'] if l['category']=='material' and dec(l['purchase_quantity'])>0]
        q['procurement']={'id':str(uuid4()),'at':now(),'calculation':refreshed,'variance':v,'purchase_lines':purchase_lines,'covered_stock':[a for a in (allocations or []) if a['active']],'status':'awaiting_buyer_review','exception':None,'production_status':'Awaiting production review','required_date':q['schedule']['ready_to_ship'],'refresh_evidence':{'classification':'synthetic_supplier','factor':factor,'note':'Prepared acceptance offer refresh; no live market check.'},'allocation_hash':fingerprint([a for a in (allocations or []) if a['active']])}
        q['procurement']['agent_rechecks']=[{'agent':a,'classification':'Prepared example','items':[l['id'] for l in purchase_lines if (a=='custom-quote' and 'ADAPTER' in l['id']) or (a=='full-component' and 'GATE' in l['id']) or (a=='individual-parts' and 'ADAPTER' not in l['id'] and 'GATE' not in l['id'])]} for a in ['full-component','individual-parts','custom-quote']]
        q['calculation_runs'].append(deepcopy(refreshed));event(q,'acceptance_cost_check','Accepted price fixed; refreshed cost and buy-only requisition created')
    elif action=='approve_procurement':
        p=q['procurement'];require(p is not None,'Run the acceptance cost check first')
        require(p['allocation_hash']==fingerprint([a for a in (allocations or []) if a['active']]),'Allocation changed; repeat acceptance check')
        require(not any(r['blocking'] and r['disposition']!='resolved' for r in q['risks']),'Engineering blocker prevents procurement')
        if p['variance']['escalation_required']:
            require(len(data.get('exception_reason','').strip())>=10,'Manager exception reason required: cost increased >5% or projected margin <25%')
            p['exception']={'reviewer':actor(q,'manager'),'reason':data['exception_reason'],'at':now()}
        p['status']='approved_requisition';p['reviewer']=actor(q,'buyer');p['approved_at']=now(); inventory_action='commit'
        event(q,'procurement_approved','Purchase requisition approved; no PO, payment or production release. Valid holds committed without decrementing on-hand.')
    elif action=='attach_source':
        text=data.get('content',''); require(0<len(text)<=30000,'Plain text import must be 1–30,000 characters')
        s=source(str(uuid4()),data.get('title','Imported text')[:100],text,'operator_import');s['synthetic']=False
        q['sources'].append(s);q['custom_sources'].append(s['id']);event(q,'source_saved','Imported text retained as untrusted evidence; confirmed fields preserved. Needs live extraction review.')
        if q['mode']=='live_mcp': q['jobs'].append(new_job(q,0))
    return q,inventory_action,reserve_lines


def bind_session(q,info):
    q['session_id']=info['id'];q['session_started_at']=info['created_at'];q['shop_rules']=q.get('shop_rules',[])
    start=parse_time(info['created_at'].replace('Z','+00:00'))
    q['offers_valid_until']=(start+timedelta(hours=24)).isoformat()
    for src in q['sources']:
        src['retrieved_at']=start.isoformat()
        if src['kind']=='synthetic_supplier':src['price_as_of']=(start-timedelta(hours=4)).isoformat();src['valid_until']=q['offers_valid_until']
        if src['id']=='inventory-ledger':src['lot_acquired_at']=(start-timedelta(days=120)).isoformat()
    if q['scenario_id']=='feed':
        stale=next(s for s in q['sources'] if s['id']==q['bom'][0]['source_id'])
        stale['price_as_of']=(start-timedelta(days=7)).isoformat();stale['valid_until']=(start-timedelta(days=6)).isoformat();stale['intentionally_stale']=True
        q['offers_valid_until']=stale['valid_until']
    if q['scenario_id']!='custom':q['pricing_options']=pricing_options(q)
    return q
