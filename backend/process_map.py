from .workflow import STEPS,DOCS
from .demo.agents import AGENTS
import json
from pathlib import Path

# Model assumptions, not measured stage benchmarks. Sum is 90 estimator minutes.
MODELED_MINUTES=[8,15,20,15,15,7,5,5]

def process_map():
    steps=[]
    for i,s in enumerate(STEPS):
        steps.append(dict(index=i,**s,agents=[a[1] for a in AGENTS if a[2]==i],outputs=[d[1] for d in DOCS if d[0] in s['documents']],modeled_minutes=MODELED_MINUTES[i]))
    steps.append(dict(index=8,title='After acceptance',owner='Salesperson → PM + Procurement',handoff='Sales → Project manager: add job to project system',databases=['D1','D2','D4'],agents=['Post-acceptance recheck','Full-component','Individual-parts','Custom-quote','Completion extraction (future only)'],outputs=['Post-acceptance recheck','Purchase list','PM handoff'],modeled_minutes=None))
    return dict(steps=steps,baseline='RFQ to sent quote: 2–4 business days; approximately 1–2 estimator-hours per routine quote · per research summary.',model_note='Per-stage allocation is modeled: 90 estimator minutes total. It is not a measured benchmark. Demo elapsed time includes user reading and pauses, and is not production labor time.',research=json.loads(Path('backend/demo/research_context.json').read_text()))
