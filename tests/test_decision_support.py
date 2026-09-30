from decimal import Decimal
from datetime import datetime,timezone,timedelta
from backend.decision_support import HISTORY,route_estimates,pricing_options,feature_hours,central_today
from backend.fixtures import build
from backend.domain import bind_session
from backend.calculations import estimate,variance
from test_domain import make,step,walkthrough

def test_history_is_nine_complete_synthetic_records():
    assert len(HISTORY)==9
    assert sum(j['inspection_result']=='failed_then_reworked' for j in HISTORY)>=1
    for j in HISTORY:
        assert j['quoted_hours'] and j['actual_hours'] and j['scrap_fraction']
        assert j['win_loss'] in ('won','lost') and j['synthetic']
        assert Decimal(j['actual_hours'])==sum(Decimal(x) for x in j['actual_operation_hours'].values())

def test_feature_formulas_and_fixture_allocation():
    f=build('seed');d=route_estimates('seed',f['scenario']['material'],'4',f['base_route'],'batch')
    # Independent checks: 18 m / 0.8 m/min = 22.5 min = 0.375h; 12 bends *3.2=38.4min.
    feature=feature_hours(d['features'],f['scenario']['material'])
    assert feature['cut']==Decimal('.375') and feature['form']==Decimal('.64')
    assert d['fixture_cost']=='360.00' and d['fixture_per_assembly']=='90.00'
    assert len(d['choices'])==3 and len(d['similar_jobs'])==3
    for op in d['selected_route']:
        assert Decimal(op['low_hours'])<=Decimal(op['likely_hours'])<=Decimal(op['high_hours'])
        assert len(op['historical_job_ids'])==3

def test_engineering_cost_is_separate_and_not_duplicated():
    for sid,expected in [('seed','440.00'),('feed','720.00')]:
        q=make(sid);lines=q['calculation']['lines'];eng=[x for x in lines if x['id']=='engineering-drafting']
        assert len(eng)==1 and eng[0]['total']==expected
        assert sum(Decimal(x['total']) for x in lines)==Decimal(q['calculation']['base_cost'])
        assert len([x for x in lines if x['id']=='weld-fixture'])==1

def test_options_and_load_are_python_outputs():
    q=make('grain');options=q['pricing_options'];assert len(options)==4
    assert [x['target_margin_percent'] for x in options]==['20.00','25.00','30.00','35.00']
    prices=[Decimal(x['selling_price']) for x in options];assert prices==sorted(prices)
    for x in options:
        assert Decimal(0)<Decimal(x['win_likelihood_percent'])<100
        assert x['win_model']=='Illustrative, synthetic history'
        assert len(x['history_ids'])==9
        assert x['shop_load']['timezone']=='America/Chicago'
        assert x['customer_tier']=='Standard customer'

def test_session_offsets_and_stale_selected_feed_price():
    info={'id':'session-test','created_at':'2026-09-30T05:00:00+00:00'}
    q=bind_session(make('feed'),info);start=datetime.fromisoformat(info['created_at'])
    stale=[s for s in q['sources'] if s.get('intentionally_stale')];assert len(stale)==1
    assert datetime.fromisoformat(stale[0]['price_as_of'])==start-timedelta(days=7)
    lot=next(s for s in q['sources'] if s['id']=='inventory-ledger')
    assert datetime.fromisoformat(lot['lot_acquired_at'])==start-timedelta(days=120)

def test_approvals_are_explicit_simulations_and_stage_clocked():
    q=make();q['session_id']='synthetic-session-id';q=step(q,'inspect',{'source_id':'request-seed'});q=step(q,'approve',{'stage':0})
    a=q['approvals'][-1];assert a['simulated'] and 'Demo visitor (synthetic-session-id), simulated' in a['reviewer']
    assert q['stages'][0]['approved_at'] and q['stages'][1]['entered_at']

def test_route_override_reopens_estimate_without_changing_engineering():
    q=make();q['stage']=3;q['stages'][0]['status']=q['stages'][1]['status']=q['stages'][2]['status']='approved'
    q=step(q,'route_override',{'operation':'weld','hours':'2.50','reason':'Illustrative fixture alignment allowance'})
    assert q['stage']==3 and q['stages'][2]['status']=='approved'
    assert next(x for x in q['route'] if x['id']=='weld')['run_hours']=='2.50'
    assert q['stages'][4]['status']=='invalidated'

def test_postgres_timestamp_fraction_compatibility():
    from backend.time_utils import parse_time
    assert parse_time('2026-09-30T06:14:32.8112+00:00').microsecond==811200
    assert parse_time('2026-09-30T06:14:32.8Z').microsecond==800000
    q=bind_session(make(),{'id':'test','created_at':'2026-09-30T06:14:32.8112+00:00'})
    assert q['session_started_at'].endswith('.8112+00:00')

def test_same_shop_same_requested_week_has_same_current_load():
    info={'id':'test-shop','created_at':'2026-09-30T05:00:00+00:00'}
    seed=make('seed');grain=make('grain')
    for q in [seed,grain]:q['intake']['requested_date']='2026-10-07'
    seed=bind_session(seed,info);grain=bind_session(grain,info)
    a=seed['pricing_options'][0]['shop_load'];b=grain['pricing_options'][0]['shop_load']
    assert a['booked_hours']==b['booked_hours']=='102.00'
    assert a['window_start']==b['window_start']=='2026-10-05'
