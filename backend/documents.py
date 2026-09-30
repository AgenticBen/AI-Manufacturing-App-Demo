"""Prepared, cited quote artifacts generated using trusted Python state."""
from .workflow import DOCS,STEPS,available,review_fingerprint
from .calculations import dec,number,money

def document(q,id):
    from .domain import require
    require(available(q,id),'Document is not available yet')
    spec=next(d for d in DOCS if d[0]==id);sid=q['scenario_id'];si=['seed','grain','feed'].index(sid);sections=[]
    def add(text,db=None,line=1,source=None):
        src=next((s for s in q['sources'] if s['id']==source),None)
        source_line=3 if source and source.startswith('offer-') and src and len(src['content'].splitlines())>=3 else 2 if source and source.startswith('request-') else 1
        if source=='calculation-current' and src:
            field='base_cost' if 'base cost' in text.lower() else 'selling_price' if 'price USD' in text else 'pricing_cost'
            source_line=next((i for i,t in enumerate(src['content'].splitlines(),1) if '"'+field+'"' in t),1)
        sections.append(dict(text=text,citations=([dict(database=db,line=line)] if db else [])+([dict(source=source,line=source_line)] if source else [])))
    if id in ['working-cost','completed-cost'] and q.get('cost_qa'):
        for e in q['cost_qa']['events']:add('Prepared QA replay: '+e['agent']+' → '+e['action']+'. '+e['detail'],source='offer-fastener')
    if id=='request-packet':
        add(q['intake']['description'],'D11',si*4+1, 'request-'+sid)
        add('Survey: '+q['quantity']+' assemblies; '+q['scenario']['capacity']+'; '+q['scenario']['handled']+'.','D11',si*4+3,'intake-fields')
        add(('Returning client; past jobs H-101 and H-102.' if sid=='seed' else 'New fictional client; company background requires review.'),'D10',si+1)
    elif id=='client-document':
        add(q['scenario']['name']+' — fictional '+q['scenario']['short']+'. No verified public company page exists for this demo identity.','D12',si+1)
        for r in q['requirements']:add(r['field'].replace('_',' ')+': '+r['value'],source=r['source_id'])
        add(('v2 · Customer answer confirmed: '+q['scenario']['resolution']) if q.get('clarification_resolved') else 'v1 · Open gap: '+q['scenario']['clarification'],'D11',si*4+4)
    elif id=='material-review':
        add('Handled product: '+q['scenario']['handled']+'. Corn/grain and DDGS entries are reference analogs only; exact product properties require engineering confirmation.','D11',si*4+3)
        add('Organic dust and moisture can affect handling. Do not treat reference dust classes or angles as design values. Confirm sample properties, dust controls and site conditions.','D9',1 if sid!='feed' else 5)
        add('Customer decision needed: confirm the stated environment and any cleaning or moisture exposure before choosing materials or enclosures.','D11',si*4+1)
    elif id=='clarification-email':
        add('To: fictional customer purchasing contact. Subject: One clarification bundle for your hopper quote.','D10',si+1)
        add('Please confirm: '+q['scenario']['clarification'],'D12',si+1)
        add('Prepared response, used only after explicit confirmation: '+q['scenario']['resolution'],'D11',si*4+4)
    elif id=='anchor-comparison':
        for j in q['route_support']['similar_jobs']:
            idx=next(i+1 for i,x in enumerate(q['historical_jobs']) if x['id']==j['id'])
            add(f"{j['id']}: Python distance {j['similarity_distance']} (lower is closer); quantity {j['quantity']}; {j['material']}; quoted {j['quoted_hours']} h, actual {j['actual_hours']} h. {j['actual_basis']}",'D4',idx,'route-history-'+sid)
        add('Best match proposed: '+q['route_support']['similar_jobs'][0]['id']+'. Engineer must compare geometry, quantity and interface before accepting the anchor.',source='route-history-'+sid)
    elif id=='concept-design':
        add('Reference template image includes illustrative equipment outside the quoted scope; controls and powered auxiliaries are not included. AI concept · not an engineering drawing. '+q['scenario']['capacity']+'; '+q['scenario']['material']+'; '+q['scenario']['outlet']+'.','D7',si+1,'drawing-'+sid)
        add('Qualified engineer must verify structure, slope, loads, welds and interface before production.',source='drawing-'+sid)
    elif id=='bom':
        for i,b in enumerate(q['bom']):add(f"{b['item']} · {b['label']} · {b['spec']} · material {q['scenario']['material']} · {b['per_unit']} {b['unit']} per assembly · {number(dec(b['per_unit'])*dec(q['quantity']))} total · drawing {b['drawing_ref']}",'D5',si*8+i+1,'drawing-'+sid)
    elif id=='manufacturing-plan':
        add('Build sequence: legs → cone → body → gate → finish → inspect. Engineer confirms the selected estimating route; PM confirms timeline.','D8',1)
        for i,o in enumerate(q['route']):add(f"{o['operation']} · {o['work_center']} · setup {o['setup_hours']} h/batch · run {o['run_hours']} h/assembly · historical comparison {o.get('history_hours','unknown')} h/assembly · USD {o['loaded_rate']}/h loaded.",'D3',min(i+1,7),o['source_id'])
        add('Selected route: '+q['route_choice']+'. Conditional ready to ship: '+q['schedule']['ready_to_ship']+'.',source='route-history-'+sid)
    elif id in ['working-cost','completed-cost','procurement-message']:
        if id=='procurement-message':add('Draft to Procurement: approved expected costs, proposed purchases, custom quotes pending and held inventory. Explicit simulated Send email required.',source='policy-v1')
        for l in q['calculation']['lines']:
            if l['category']=='material':
                add(f"{l['label']} · need {l['required']} {l['unit']} · held stock {l['covered_stock']} · buy {l['purchase_quantity']} · pack {l['pack']} · USD {l['pack_price']}/pack · line USD {l['total']}. Demo price, fictional offer; not a price taken from a real supplier page.",source=l['evidence'][0])
            else:add(f"{l['label']} · USD {l['total']} · Python computed {l['category']} cost.",source=l['evidence'][0])
        add('Custom adapter: awaiting supplier quote in a live deployment. The demo uses a prepared estimating allowance; no supplier contact.', 'D2',6)
        add('Inventory holds: '+('; '.join(a['item']+' '+a['quantity']+' '+a['status'] for a in q.get('allocations',[]) if a.get('active')) or 'none placed')+'. Holds require the explicit Reserve control.',source='inventory-ledger')
        if id!='working-cost':add('Python base cost USD '+q['calculation']['base_cost']+'; contingency USD '+q['calculation']['contingency']+'; pricing cost USD '+q['calculation']['pricing_cost']+'. Calculation '+q['calculation']['id']+'.',source='calculation-current')
    elif id=='master-risk':
        for r in q['risks']:add(r['title']+' · '+r['owner']+' · '+r['disposition']+'. '+r['mitigation'],source=r['source_id'])
        add('Handling and site: confirm dust, access, moisture and customer operating conditions. Transport damage: packaging is included, freight excluded; customer confirms shipping arrangements.','D11',si*4+1)
    elif id=='pricing-decision':
        add('Salesperson-selected target margin '+q['margin']+'; discount '+q['discount']+'; Python price USD '+q['calculation']['selling_price']+'; projected gross margin '+q['calculation']['gross_margin_percent']+'%.',source='calculation-current')
        add('Win likelihood is illustrative from synthetic history; shop load is a modeled shared calendar, not live ERP data.','D6',1,'shop-load-v1')
    elif id=='customer-quote':
        p=q.get('package')
        if p:
            add(p['description'],source='drawing-'+sid)
            add('Quantity '+p['quantity']+' · USD '+p['selling_price']+' · Conditional ready to ship '+p['ready_to_ship']+'.',source='policy-v1')
            for k,v in p['terms'].items():add(k.replace('_',' ')+': '+str(v),source='policy-v1')
        else:add('Draft not generated yet. Use Generate customer preview after upstream approvals.',source='policy-v1')
    elif id=='release-qa':
        add('Verify current revision '+str(q['revision'])+', approved price and required drawing/exclusions. Customer export uses an explicit allowlist that excludes internal costs and margin.',source='policy-v1')
        add('Ops final check required. Sending and exporting are separate explicit salesperson actions.',source='policy-v1')
    elif id in ['post-acceptance','purchase-list','pm-handoff']:
        p=q['procurement']
        add('Accepted customer price remains USD '+q['acceptance']['accepted_price']+'. Prepared supplier refresh; no live market lookup.',source='policy-v1')
        if id=='post-acceptance':add('Python cost variance USD '+p['variance']['cost_variance']+' ('+p['variance']['variance_percent']+'%); projected margin '+p['variance']['gross_margin_percent']+'%.',source='policy-v1')
        for l in p['purchase_lines']:add(l['label']+' · buy '+l['purchase_quantity']+' · USD '+l['purchase_cost']+' acquisition cost.',source=l['evidence'][0])
        if id=='pm-handoff':add('Sales → Project manager: add job to project system. Attach approved BOM and manufacturing plan. Production status: '+p['production_status']+'. No project-system sync occurs.',source='route-'+sid)
    approval=next((a for a in reversed(q['approvals']) if a.get('stage')==spec[2] and a.get('revision')==q['revision'] and a.get('decision')=='approved'),None)
    return dict(id=id,title=spec[1],stage=spec[2],creator=spec[3],version=f"R{q['revision']}"+(' · v2' if id=='client-document' and q.get('clarification_resolved') else ''),classification='Prepared example',created_at=q['created_at'],reviewed_by=approval['reviewer'] if approval else 'Pending human approval',reviewed_at=approval['at'] if approval else None,stale=q['stages'][min(spec[2],7)].get('reason') if q['stages'][min(spec[2],7)]['status']=='invalidated' else None,used_by='Next step and downstream review' if spec[2]<7 else 'Sales / Procurement / Project manager',sections=sections)
