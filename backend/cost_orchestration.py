"""Executable deterministic QA replay of a prepared pack-size error; no AI run claim."""
from copy import deepcopy
from .calculations import fingerprint
from .fixtures import now

def validate_candidate(candidate,bom):
    errors=[]
    if candidate['source_id']!=bom['source_id']:errors.append('Source reference does not support this item')
    if candidate['pack']!=bom['pack']:errors.append('Pack size does not match the prepared supplier evidence')
    if candidate['pack_price']!=bom['pack_price']:errors.append('Pack price does not match the prepared supplier evidence')
    if candidate['unit']!=bom['unit']:errors.append('Unit mismatch')
    return errors

def replay(q):
    b=next(b for b in q['bom'] if b['item']=='FASTENER')
    initial={k:b[k] for k in ['item','source_id','pack','pack_price','unit']};initial['pack']='1'
    failures=validate_candidate(initial,b)
    corrected={k:b[k] for k in initial}
    final_errors=validate_candidate(corrected,b)
    return dict(classification='Prepared example · deterministic QA replay, not a recorded AI run',at=now(),input_hash=fingerprint(q['bom']),initial=initial,failures=failures,corrected=corrected,final_errors=final_errors,status='passed' if not final_errors else 'failed',events=[dict(agent='individual-parts',action='Prepared candidate',detail='Fastener pack incorrectly recorded as 1.'),dict(agent='cost-qa',action='Rejected',detail='Validator compared pack size with the exact prepared supplier source.'),dict(agent='supervisor',action='Targeted rerun',detail='Returned only the fastener line to individual-parts agent.'),dict(agent='individual-parts',action='Prepared corrected output',detail='Reloaded pack, price and unit from the current BOM evidence.'),dict(agent='cost-qa',action='Passed',detail='Revalidated corrected output. Python totals remain authoritative.')])

def assignments(q):
    rows=[]
    for b in q['bom']:
        held=next((a for a in q.get('allocations',[]) if a['item']==b['item'] and a.get('active')),None)
        agent='custom-quote' if b['classification']=='custom_buy' else 'full-component' if b['item'].startswith('GATE') else 'individual-parts'
        rows.append(dict(item=b['item'],label=b['label'],agent=agent,inventory='Held '+held['quantity'] if held else 'No hold placed',source=b['source_id'],status='Awaiting supplier quote · prepared allowance' if agent=='custom-quote' else 'Prepared lookup; no live website price'))
    return rows
