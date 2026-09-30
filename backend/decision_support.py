"""Deterministic, synthetic decision support. No fitted model or market prediction."""
from decimal import Decimal
from datetime import datetime,timedelta,date
from zoneinfo import ZoneInfo
from copy import deepcopy
from .calculations import dec,number,money,price,fingerprint,add_workdays

CENTRAL=ZoneInfo('America/Chicago')
OPS=['cut','form','weld','finish','assemble','inspect','package']
FEATURES={
 'seed':{'cut_perimeter_m':'18','bend_count':'12','weld_seam_m':'9','capacity_m3':'3','tolerance_mm':'1.0','geometry':'Custom square-to-conveyor adapter','customer_tier':'Established customer'},
 'grain':{'cut_perimeter_m':'33','bend_count':'18','weld_seam_m':'16','capacity_m3':'8','tolerance_mm':'2.0','geometry':'Large body with weather cover','customer_tier':'Standard customer'},
 'feed':{'cut_perimeter_m':'25','bend_count':'16','weld_seam_m':'13','capacity_m3':'5','tolerance_mm':'0.5','geometry':'Cleanout panels and accessible contact seams','customer_tier':'Strategic customer'}
}

def central_today():return datetime.now(CENTRAL).date()

def feature_hours(features,material):
    stainless='stainless' in material.lower();factor=Decimal('1.25') if stainless else Decimal('1')
    return {'cut':dec(features['cut_perimeter_m'])/Decimal('0.8')/60,
            'form':dec(features['bend_count'])*Decimal('3.2')/60,
            'weld':dec(features['weld_seam_m'])*Decimal('7.0')*factor/60,
            'finish':dec(features['capacity_m3'])*Decimal('.10')*factor,
            'assemble':Decimal('.50')+dec(features['bend_count'])*Decimal('.02'),
            'inspect':Decimal('.30')+(Decimal('.25') if dec(features['tolerance_mm'])<=Decimal('1') else Decimal('.10')),
            'package':Decimal('.20')+dec(features['capacity_m3'])*Decimal('.03')}

# All input values are deliberate fictional shop records; no real performance claim.
def history():
    records=[]
    entries=[
     ('H-101','seed','1','Painted carbon steel','0.25',True,'Established customer','1.10','0.02',False),
     ('H-102','seed','3','Painted carbon steel','0.30',True,'Established customer','0.94','0.015',False),
     ('H-103','seed','2','Galvanized carbon steel','0.35',False,'Standard customer','1.24','0.05',True),
     ('H-201','grain','4','Galvanized carbon steel','0.20',True,'Standard customer','0.91','0.02',False),
     ('H-202','grain','2','Painted carbon steel','0.30',False,'Standard customer','1.08','0.03',False),
     ('H-203','grain','6','Galvanized carbon steel','0.25',True,'Established customer','0.88','0.01',False),
     ('H-301','feed','1','304 stainless contact surfaces','0.35',True,'Strategic customer','1.30','0.045',True),
     ('H-302','feed','2','304 stainless contact surfaces','0.30',True,'Strategic customer','1.06','0.02',False),
     ('H-303','feed','4','316 stainless contact surfaces','0.40',False,'Standard customer','0.98','0.025',False)]
    for id,sid,q,material,margin,won,tier,actual_factor,scrap,failed in entries:
        features=deepcopy(FEATURES[sid]);run=feature_hours(features,material)
        quoted={k:money(run[k]*dec(q)+Decimal('.4')) for k in OPS}
        actual={k:money((run[k]*dec(q)+Decimal('.4'))*dec(actual_factor)) for k in OPS}
        # Lost commercial bids still have prototype/analog shop actuals, explicitly separate.
        records.append({'id':id,'scenario':sid,'quantity':q,'material':material,'features':features,'quoted_hours':money(sum(dec(v) for v in quoted.values())),'actual_hours':money(sum(dec(v) for v in actual.values())),'quoted_operation_hours':quoted,'actual_operation_hours':actual,'actual_basis':'Completed fictional shop job' if won else 'Fictional prototype/analog trial; commercial bid lost','setup_hours_per_operation':'.4','scrap_fraction':scrap,'win_loss':'won' if won else 'lost','quoted_margin':margin,'customer_tier':tier,'inspection_result':'failed_then_reworked' if failed else 'passed','inspection_note':'Adapter flange position failed dimensional inspection; fixture alignment and reinspection required.' if id=='H-103' else 'Contact seam finish failed visual inspection; additional finishing and reinspection required.' if failed else 'Synthetic first-pass inspection passed.','synthetic':True,'source_id':'historical-jobs-v1'})
    return records

HISTORY=history()

def similar_jobs(sid,material,quantity):
    f=FEATURES[sid];q=dec(quantity)
    def score(j):
        return (abs(dec(j['quantity'])-q)/12+abs(dec(j['features']['capacity_m3'])-dec(f['capacity_m3']))/8+abs(dec(j['features']['weld_seam_m'])-dec(f['weld_seam_m']))/16+(Decimal(0) if j['material']==material else Decimal('2')))
    return [{**deepcopy(j),'similarity_distance':number(score(j))} for j in sorted(HISTORY,key=score)[:3]]

def route_estimates(sid,material,quantity,base_route,selected='flexible',overrides=None):
    q=dec(quantity,'quantity',True);f=deepcopy(FEATURES[sid]);feature=feature_hours(f,material);similar=similar_jobs(sid,material,quantity);choices=[]
    options=[('flexible','Flexible shop route','1.00','90','No dedicated fixture; economical setup for short runs.'),('batch','Dedicated batch fixture','0.78','360','Higher one-time fixture cost reduces repeat weld/assembly effort.'),('precision','Precision interface fixture','0.90','220','Dedicated interface checks add inspection effort for tighter tolerances.')]
    for code,label,speed,fixture,explanation in options:
        operations=[]
        for op in base_route:
            id=op['id'];historical=[]
            for j in similar:
                historical.append(max(Decimal('0.01'),(dec(j['actual_operation_hours'][id])-dec(j['setup_hours_per_operation']))/dec(j['quantity'])))
            hist=sum(historical)/len(historical);likely=(feature[id]+hist)/2
            multiplier=dec(speed) if id in ('weld','assemble') else Decimal(1)
            likely*=multiplier;low=min([feature[id]]+historical)*multiplier*Decimal('.90');high=max([feature[id]]+historical)*multiplier*Decimal('1.15')
            if code=='precision' and id=='inspect':likely+=Decimal('.20');low+=Decimal('.15');high+=Decimal('.30')
            override=(overrides or {}).get(id)
            reviewed=dec(override['hours'],'reviewed run hours',True) if override else Decimal(money(likely))
            operations.append({**op,'run_hours':money(reviewed),'feature_hours':money(feature[id]),'history_hours':money(hist),'low_hours':money(low),'likely_hours':money(likely),'high_hours':money(high),'historical_job_ids':[j['id'] for j in similar],'override':override,'source_id':'route-history-'+sid})
        labor=sum((dec(o['setup_hours'])*(q/dec(o['batch_limit'])).to_integral_value(rounding='ROUND_CEILING')+dec(o['run_hours'])*q)*dec(o['loaded_rate']) for o in operations)
        suitable=(code=='batch' and q>=4) or (code=='precision' and (sid in ('seed','feed'))) or (code=='flexible' and sid=='grain' and q<4)
        criteria={'volume':f'{quantity} assemblies; '+('batch economies favored' if q>=4 else 'short-run setup matters'),'lead_time':'Fixture preparation adds 1 working day' if code!='flexible' else 'Existing shop tooling; no dedicated fixture preparation','geometry':f['geometry'],'material':material,'tolerance':f['tolerance_mm']+' mm illustrative interface target; '+('dedicated interface inspection' if code=='precision' else 'standard dimensional checks'),'cost':f'USD {money(labor+dec(fixture))} route + fixture; fixture allocation USD {money(dec(fixture)/q)} per assembly'}
        choices.append({'id':code,'label':label,'explanation':explanation,'recommended':suitable,'criteria':criteria,'operations':operations,'fixture_cost':money(fixture),'fixture_per_assembly':money(dec(fixture)/q),'route_and_fixture_cost':money(labor+dec(fixture))})
    chosen=next((x for x in choices if x['id']==selected),None)
    if not chosen:raise ValueError('Unknown supported route choice')
    return {'features':f,'similar_jobs':similar,'choices':choices,'selected':selected,'selected_route':chosen['operations'],'fixture_cost':chosen['fixture_cost'],'fixture_per_assembly':chosen['fixture_per_assembly'],'method':'Feature estimate and mean normalized actual hours of 3 nearest synthetic jobs, blended equally. Low/high envelope includes ±10/15% illustrative range.','formula_notes':{'cut':'Cut perimeter ÷ 0.8 m/min ÷ 60','form':'Bend count × 3.2 min/bend ÷ 60','weld':'Weld seam length × 7 min/m × stainless factor (1.25) ÷ 60'},'version':'feature-history-v1'}

def pricing_options(q):
    tier=FEATURES[q['scenario_id']]['customer_tier'];day=date.fromisoformat(q['intake']['requested_date']) if q['intake'].get('requested_date') else central_today()
    monday=day-timedelta(days=day.weekday());end=monday+timedelta(days=4)
    from .time_utils import parse_time
    session_day=parse_time(q['session_started_at']).astimezone(CENTRAL).date() if q.get('session_started_at') else central_today()
    session_monday=session_day-timedelta(days=session_day.weekday());week_offset=(monday-session_monday).days//7
    capacity=Decimal('120');booked=Decimal({0:'84',1:'102',2:'72'}.get(week_offset,'60'))
    demand=sum(dec(l.get('hours','0')) for l in q['calculation']['lines'] if l['category']=='operation')
    load={'window_start':monday.isoformat(),'window_end':end.isoformat(),'timezone':'America/Chicago','capacity_hours':money(capacity),'booked_hours':money(booked),'current_load_percent':money(booked/capacity*100),'quote_hours':money(demand),'with_quote_percent':money((booked+demand)/capacity*100),'basis':'Synthetic shop capacity record; not live ERP scheduling','source_id':'shop-load-v1'}
    options=[]
    for margin in ['0.20','0.25','0.30','0.35']:
        wins=Decimal(1);total=Decimal(2)
        for j in HISTORY:
            distance=abs(dec(margin)-dec(j['quoted_margin']))*20+(Decimal(0) if j['customer_tier']==tier else Decimal(1))
            weight=Decimal(1)/(1+distance);total+=weight
            if j['win_loss']=='won':wins+=weight
        p=price(q['calculation']['base_cost'],q['contingency'],margin,q['discount'])
        options.append({**p,'target_margin_percent':money(dec(margin)*100),'win_likelihood_percent':money(wins/total*100),'win_model':'Illustrative, synthetic history','history_ids':[j['id'] for j in HISTORY],'customer_tier':tier,'shop_load':load,'method':'Smoothed similarity-weighted win fraction across nine fictional bids; not a predictive guarantee.'})
    return options
