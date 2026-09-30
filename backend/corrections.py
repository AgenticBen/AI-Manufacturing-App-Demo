"""Targeted prepared-example reruns. Reviewer input remains identified as human input."""
from copy import deepcopy
from uuid import uuid4
from .demo.agents import AGENTS
from .fixtures import source,now

PRESETS={
 'seed':{'agent':'crm-check','reason':'The similar-name candidate is not this customer. Use the saved CRM identity.','input':'Cedar Rapids Seed Co. · returning client · D10 row 1 · past jobs H-101 and H-102.'},
 'grain':{'agent':'company-research','reason':'The company background must remain fictional; remove any assumed real-company website.','input':'Mason City Grain Works is a fictional new client. No verified public company website is supplied; background remains unverified.'},
 'feed':{'agent':'company-research','reason':'The similar-name company is not the demo client; preserve the stated cleaning requirements.','input':'Council Bluffs Feed Systems is fictional. Use D10 row 3 and D11 rows 9–12; do not infer a real website.'}}

def rerun(q,data):
    from .domain import require,actor,event,invalidate
    from .documents import document
    agent=next((a for a in AGENTS if a[0]==data.get('agent')),None)
    require(agent is not None,'Unknown agent')
    require(agent[2]<=q['stage'] and agent[2]<8,'Only reached agents can be corrected')
    require(q['mode']=='guided_demo','Live MCP corrections must be submitted through the connected host; this control replays prepared examples only')
    require(q['lifecycle']=='draft','Create a new revision before correcting an issued or approved quote')
    reason=data.get('reason','').strip();corrected=data.get('corrected_input','').strip()
    require(5<=len(reason)<=1500 and 3<=len(corrected)<=4000,'Provide a correction reason and corrected input')
    old=[document(q,id) for id in agent[4]]
    cid='correction-'+str(uuid4());at=now()
    evidence=source(cid,'Reviewer correction for '+agent[1],reason+'\nCorrected input: '+corrected,'operator_correction','Reviewer correction lines 1–2')
    evidence['synthetic']=True;q['sources'].append(evidence)
    result={'id':cid,'agent':agent[0],'stage':agent[2],'at':at,'reviewer':actor(q,'reviewer'),'reason':reason,'corrected_input':corrected,'previous_output':old,'classification':'Prepared correction rerun · no model inference','status':'awaiting_human_review','output_ids':agent[4]}
    q.setdefault('corrections',[]).append(result)
    # Rerun only this prepared agent. Dependent approvals reopen without running other agents.
    invalidate(q,agent[2],'Correction to '+agent[1]+' requires downstream review')
    q.setdefault('workflow_reviews',{}).clear()
    result['new_output']=[document(q,id) for id in agent[4]]
    event(q,'agent_correction',agent[1]+' · reviewer '+result['reviewer']+' · '+reason)
    event(q,'targeted_prepared_rerun',agent[0]+' only; corrected input retained as reviewer evidence. No live AI run.')
    return q,None,[]
