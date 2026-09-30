"""Reviewable workflow metadata and server-enforced document gates."""
from copy import deepcopy
from .demo.agents import AGENTS
from .calculations import fingerprint
from .fixtures import now

STEPS=[
 dict(title='Request',owner='Salesperson',handoff='Customer → Sales: request sources',databases=['D11','D10'],documents=['request-packet']),
 dict(title='Requirements',owner='Salesperson',handoff='Sales → Engineer: requirements, client document, material review',databases=['D10','D11','D12','D9'],documents=['client-document','material-review','clarification-email']),
 dict(title='Design & BOM',owner='Engineer',handoff='Engineer → Sales: approved design + BOM',databases=['D6','D4','D7','D5','D12','D9'],documents=['anchor-comparison','concept-design','bom']),
 dict(title='Manufacturing',owner='Engineer + Project manager',handoff='Engineer → Project manager: build plan confirmed',databases=['D8','D3','D4'],documents=['manufacturing-plan']),
 dict(title='Cost estimate',owner='Salesperson',handoff='Sales → Procurement: expected costs + held inventory',databases=['D1','D2','D3','D5'],documents=['working-cost','completed-cost']),
 dict(title='Risk',owner='Salesperson + Engineer / PM',handoff='Sales → Engineer / PM: reconciled risks',databases=['D9','D12','D2','D4'],documents=['master-risk']),
 dict(title='Price',owner='Salesperson',handoff='Sales → Ops: selected and verified price',databases=['D6','D4'],documents=['pricing-decision']),
 dict(title='Review & submit',owner='Salesperson + Ops',handoff='Ops → Sales: cleared to send',databases=['D6','D12'],documents=['customer-quote','release-qa'])]
DOCS=[('request-packet','Request packet',0,'intake'),('client-document','Client document',1,'conversation-synthesizer'),('material-review','Material & handling review',1,'material-check'),('clarification-email','Clarification email',1,'conversation-synthesizer'),('anchor-comparison','Anchor job comparison',2,'anchor-job'),('concept-design','Concept design',2,'design'),('bom','Bill of materials',2,'bom'),('manufacturing-plan','Manufacturing plan & labor estimate',3,'manufacturing'),('working-cost','Working cost sheet',4,'supervisor'),('completed-cost','Completed cost sheet',4,'cost-qa'),('procurement-message','Procurement message',4,'Salesperson'),('master-risk','Master risk document',5,'master-risk'),('pricing-decision','Pricing decision',6,'Salesperson'),('customer-quote','Customer quote',7,'quote-drafting'),('release-qa','Release QA checklist',7,'release-qa'),('post-acceptance','Post-acceptance recheck',8,'post-acceptance'),('purchase-list','Purchase list',8,'post-acceptance'),('pm-handoff','PM handoff',8,'Salesperson')]

def review_fingerprint(q,stage):
    from .domain import current_fingerprint
    reviewed=deepcopy(q)
    if reviewed.get('package'):reviewed['package'].pop('release_approval',None)
    return fingerprint({'inputs':current_fingerprint(reviewed,stage),'corrections':q.get('corrections',[]),'qa':q.get('cost_qa')})

def available(q,id):
    d=next((d for d in DOCS if d[0]==id),None)
    if not d:return False
    if d[2]==8:return bool(q.get('procurement'))
    if id=='procurement-message':return q['stages'][4]['status']=='approved'
    return d[2]<=q['stage']

def checklist(q,stage):
    fp=review_fingerprint(q,stage)
    return [dict(id=id,title=next(d[1] for d in DOCS if d[0]==id),opened=q.get('document_reviews',{}).get(id,{}).get('fingerprint')==fp) for id in STEPS[stage]['documents']]

def approval_check(q,stage):
    from .domain import require
    if not q.get('workflow_version'):return
    require(all(x['opened'] for x in checklist(q,stage)),'Open every required output document for this revision first')
    review=q.get('workflow_reviews',{}).get(str(stage),{})
    require(review.get('fingerprint')==review_fingerprint(q,stage) and review.get('confirmed'),'Confirm that you have read the documents and they are correct')
    if stage==4:
        require(q.get('cost_qa',{}).get('status')=='passed' and q['cost_qa'].get('input_hash')==fingerprint(q['bom']),'Replay and review the cost QA loop for current inputs')
    if stage==3:require(review.get('role_confirmed'),'Project manager must confirm the build plan and timeline')
    if stage==7:require(review.get('role_confirmed'),'Ops final check is required')

def workflow_state(q,allocations=None):
    from .domain import can_approve,DomainError
    stage=q['stage']; blocked=''
    try:can_approve(q,stage,allocations)
    except (DomainError,ValueError) as e:blocked=str(e)
    agents=[dict(id=id,name=name,stage=s,databases=db,outputs=outputs,task=task,status='Prepared example') for id,name,s,db,outputs,task in AGENTS if s==stage]
    if stage==1:
        for a in agents:
            if a['id']=='company-research' and q['scenario_id']=='seed':a['status']='Not run · returning client'
            if a['id']=='material-research':a['status']='Conditional · only if material missing'
    from .cost_orchestration import assignments
    return dict(assignments=assignments(q),steps=STEPS,step=STEPS[stage],agents=agents,checklist=checklist(q,stage),approval_blocker=blocked,can_approve=not blocked,documents=[dict(id=id,title=title,stage=s,creator=creator,available=available(q,id)) for id,title,s,creator in DOCS],review=q.get('workflow_reviews',{}).get(str(stage),{}))

def workflow_action(q,action,data):
    from .domain import require,actor,event
    q=deepcopy(q);stage=q['stage']
    require(q['scenario_id']!='custom','Custom requests require live engineering review')
    if action=='open_document':
        id=data.get('id');require(available(q,id),'Document is not available yet')
        doc=next(d for d in DOCS if d[0]==id)
        q.setdefault('document_reviews',{})[id]={'fingerprint':review_fingerprint(q,min(doc[2],7)),'reviewer':actor(q,STEPS[min(doc[2],7)]['owner']),'at':now()}
    elif action=='confirm_documents':
        require(q['lifecycle']=='draft','Issued/approved quote review is immutable')
        require(all(x['opened'] for x in checklist(q,stage)),'Read all required documents first')
        q.setdefault('workflow_reviews',{})[str(stage)]={'fingerprint':review_fingerprint(q,stage),'confirmed':data.get('confirmed') is True,'role_confirmed':data.get('role_confirmed') is True,'reviewer':actor(q,STEPS[stage]['owner']),'at':now()}
        event(q,'documents_confirmed','Explicit document review at step '+str(stage+1))
    elif action=='replay_cost_qa':
        from .cost_orchestration import replay
        require(stage==4 and q['lifecycle']=='draft','QA replay belongs to the cost review')
        q['cost_qa']=replay(q)
        for e in q['cost_qa']['events']:event(q,'cost_qa_replay',e['agent']+' · '+e['action']+' · '+e['detail'])
    elif action=='simulate_email':
        kind=data.get('kind');require(kind in ['clarification','requirements-summary','custom-rfq','procurement','customer-quote','purchase-list','pm-handoff'],'Unknown email')
        if kind in ['clarification','requirements-summary']:require(stage>=1,'Requirements step required')
        if kind=='custom-rfq':require(stage>=4,'Cost step required')
        if kind=='procurement':require(q['stages'][4]['status']=='approved','Approve cost estimate first')
        if kind=='customer-quote':require(q['lifecycle'] in ['approved_for_release','exported'],'Approve release first')
        if kind in ['purchase-list','pm-handoff']:require(q.get('procurement',{}).get('status')=='approved_requisition','Approve the buy-only requisition first')
        q.setdefault('simulated_messages',[]).append({'kind':kind,'at':now(),'revision':q['revision'],'sender':actor(q,'Salesperson'),'simulated':True})
        event(q,'simulated_email',kind+' · explicitly sent in demo only; no external message')
    else:raise ValueError('Unknown workflow action')
    return q,None,[]
