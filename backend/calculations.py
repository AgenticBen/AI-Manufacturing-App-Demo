"""Decimal-only, evidence-bound business calculations. USD cents ROUND_HALF_UP.
Synthetic full-pack policy charges acquisition of surplus; no residual credit.
"""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, ROUND_CEILING
from datetime import date, timedelta
import hashlib, json

VERSION = 'arc-decimal-1.0'
CENT = Decimal('0.01')

def dec(value, name='value', positive=False):
    if not isinstance(value, (str, int, Decimal)) or isinstance(value, bool):
        raise ValueError(f'{name} must be a decimal string')
    try: v = Decimal(value)
    except (InvalidOperation, TypeError): raise ValueError(f'{name} is not numeric')
    if not v.is_finite() or v < 0 or (positive and v <= 0):
        raise ValueError(f'{name} must be finite and {"positive" if positive else "nonnegative"}')
    return v

def money(v): return str(Decimal(v).quantize(CENT, rounding=ROUND_HALF_UP))
def number(v): return format(Decimal(v).normalize(), 'f')
def fingerprint(v): return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(',',':')).encode()).hexdigest()

def purchase(required, assigned, inbound, pack, moq, pack_price, lot_cost='0', unit='ea', currency='USD'):
    if unit not in ('ea','kg','m','sheet') or currency != 'USD': raise ValueError('Unsupported unit or currency')
    required,assigned,inbound = [dec(x) for x in (required,assigned,inbound)]
    if assigned+inbound > required: raise ValueError('Allocated supply exceeds requirement')
    pack,moq,price,lot = dec(pack,'pack',True),dec(moq,'MOQ'),dec(pack_price,'selected price'),dec(lot_cost,'lot cost')
    need=max(Decimal(0),required-assigned-inbound)
    buy=pack*(max(need,moq)/pack).to_integral_value(rounding=ROUND_CEILING) if need else Decimal(0)
    owned=Decimal(money(assigned*lot)); acquisition=Decimal(money(buy/pack*price))
    return {'required':number(required),'covered_stock':number(assigned),'assigned_inbound':number(inbound),'shortage':number(need),'purchase_quantity':number(buy),'surplus':number(buy-need),'owned_cost':money(owned),'purchase_cost':money(acquisition),'total':money(owned+acquisition)}

def price(base, contingency='0', margin='0.30', discount='0', override=None):
    base,contingency,m,d=[dec(x) for x in (base,contingency,margin,discount)]
    if m>=1 or d>=1: raise ValueError('Margin and discount must be below 1')
    cost=base+contingency
    initial=Decimal(money(cost/(1-m)))
    sale=Decimal(money(dec(override,'override',True) if override is not None else initial*(1-d)))
    if sale<=0: raise ValueError('Selling price must be positive')
    profit=sale-cost; actual=profit/sale
    return {'base_cost':money(base),'contingency':money(contingency),'pricing_cost':money(cost),'pre_discount_price':money(initial),'selling_price':money(sale),'gross_profit':money(profit),'gross_margin':number(actual),'gross_margin_percent':money(actual*100),'target_margin':number(m),'discount':number(d)}

def variance(original, refreshed, sale):
    original,refreshed,sale=[dec(x,'cost/price',True) for x in (original,refreshed,sale)]
    delta=refreshed-original; ratio=delta/original; margin=(sale-refreshed)/sale
    return {'original_cost':money(original),'forecast_cost':money(refreshed),'accepted_price':money(sale),'cost_variance':money(delta),'variance_percent':money(ratio*100),'gross_profit':money(sale-refreshed),'gross_margin_percent':money(margin*100),'escalation_required':ratio>Decimal('.05') or margin<Decimal('.25')}

def estimate(bom, route, quantity, allocations=None, margin='0.30', discount='0', contingency='0', factor='1', engineering=None, fixture_cost='0'):
    q=dec(quantity,'quantity',True)
    if q!=q.to_integral() or q>12: raise ValueError('Supported order quantity is 1–12 assemblies')
    allocations=allocations or {}; lines=[]
    for b in bom:
        required=dec(b['per_unit'])*q
        a=allocations.get(b['item'],{})
        assigned=min(required,dec(a.get('quantity','0')))
        p=purchase(number(required),number(assigned),'0',b['pack'],b['moq'],number(dec(b['pack_price'])*dec(factor)),a.get('unit_cost','0'),b['unit'],b['currency'])
        evidence=[b['source_id']]+(['inventory-ledger'] if assigned else [])
        lines.append(dict(p,id=b['item'],label=b['label'],category='material',spec=b['spec'],unit=b['unit'],supplier=b['supplier'],pack=b['pack'],moq=b['moq'],pack_price=money(dec(b['pack_price'])*dec(factor)),evidence=evidence))
    for op in route:
        batch=(q/dec(op['batch_limit'],'batch limit',True)).to_integral_value(rounding=ROUND_CEILING)
        hours=dec(op['setup_hours'])*batch+dec(op['run_hours'])*q
        total=money(hours*dec(op['loaded_rate']))
        lines.append({'id':op['id'],'label':op['operation'],'category':'operation','hours':number(hours),'batch_count':number(batch),'rate':op['loaded_rate'],'total':total,'evidence':[op['source_id']],'rate_basis':'Loaded labor + work-center overhead; no duplicate overhead'})
    if engineering:
        hours=dec(engineering['hours'],'engineering hours',True); rate=dec(engineering['rate'],'engineering rate',True)
        lines.append({'id':'engineering-drafting','label':'Engineering and drafting','category':'engineering','hours':number(hours),'rate':number(rate),'batch_count':'1','total':money(hours*rate),'evidence':['engineering-hours'],'rate_basis':'Reviewed project hours × engineering/drafting rate; one project charge'})
    if dec(fixture_cost)>0:
        lines.append({'id':'weld-fixture','label':'Weld fixture / tooling','category':'fixture','total':money(fixture_cost),'per_assembly_cost':money(dec(fixture_cost)/q),'quantity':number(q),'evidence':['fixture-policy'],'rate_basis':'One-time fixture cost spread over order quantity'})
    base=sum((Decimal(l['total']) for l in lines),Decimal(0))
    result=price(money(base),contingency,margin,discount)
    result.update(lines=lines,currency='USD',formula_version=VERSION,warnings=['Freight and tax explicitly excluded; no landed-price claim.','Engineering artifacts illustrate a fictional estimate, not manufacturing certification.'])
    result['input_hash']=fingerprint({'bom':bom,'route':route,'quantity':quantity,'allocations':allocations,'margin':margin,'discount':discount,'contingency':contingency,'factor':factor,'engineering':engineering,'fixture_cost':fixture_cost})
    return result

def add_workdays(start, days):
    n=int(dec(days).to_integral_value(rounding=ROUND_CEILING)); d=start
    while n:
        d+=timedelta(days=1)
        if d.weekday()<5: n-=1
    return d

def schedule(operations, start_date):
    """Dependency-aware working-day schedule. No holidays claimed in synthetic calendar."""
    start=date.fromisoformat(start_date); done={}; remaining=list(operations)
    while remaining:
        progressed=False
        for op in remaining[:]:
            if all(x in done for x in op['dependencies']):
                earliest=max([start,date.fromisoformat(op.get('available',start_date))]+[date.fromisoformat(done[x]['finish']) for x in op['dependencies']])
                if op.get('days') is None: return {'conditional':True,'reason':f'Unknown duration: {op["id"]}','milestones':list(done.values())}
                finish=add_workdays(earliest,op['days'])
                done[op['id']]={'id':op['id'],'start':earliest.isoformat(),'finish':finish.isoformat(),'basis':'working days, Mon–Fri synthetic calendar'}
                remaining.remove(op); progressed=True
        if not progressed: raise ValueError('Schedule dependency cycle or unknown predecessor')
    return {'conditional':True,'reason':'Forecast starts only after order, drawing and material readiness; human capacity confirmation required.','milestones':list(done.values()),'ready_to_ship':max(v['finish'] for v in done.values()),'transit':'Excluded; not a committed delivery date'}
