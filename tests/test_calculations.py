import pytest
from backend.calculations import price,purchase,variance,schedule,estimate
from backend.fixtures import build

def test_hand_checks():
    p=price('1000','100','.30'); assert p['selling_price']=='1571.43'; assert p['gross_profit']=='471.43'; assert p['gross_margin_percent']=='30.00'
    v=variance('1400','1500','2000'); assert v['gross_margin_percent']=='25.00'; assert v['cost_variance']=='100.00'; assert v['variance_percent']=='7.14'
    p=purchase('18','5','0','10','10','2','.10'); assert p['purchase_quantity']=='20'; assert p['surplus']=='7'; assert p['total']=='4.50'

def test_strict_boundaries():
    assert not variance('100','105','140')['escalation_required']
    assert variance('100','105.01','140')['escalation_required']
    assert variance('100','105','139.99')['escalation_required']

@pytest.mark.parametrize('bad',['NaN','Infinity','-1',None,0.3])
def test_invalid(bad):
    with pytest.raises(ValueError): price('1000',margin=bad)

def test_other_invalids():
    for pack in ['0','-1']:
        with pytest.raises(ValueError): purchase('18','5','0',pack,'10','2')
    with pytest.raises(ValueError): price('100',margin='1')
    with pytest.raises(ValueError): purchase('18','5','0','10','10',None)
    with pytest.raises(ValueError): purchase('18','5','0','10','10','2',unit='unknown')

def test_discount_real_margin():
    p=price('700',margin='.30',discount='.1'); assert p['selling_price']=='900.00'; assert p['gross_margin_percent']=='22.22'

def test_parallel_schedule():
    r=schedule([{'id':'a','days':'3','dependencies':[]},{'id':'b','days':'5','dependencies':[]},{'id':'c','days':'2','dependencies':['a','b']}],'2026-09-28')
    assert r['ready_to_ship']=='2026-10-07'

def test_scenario_line_sums_and_variants():
    from decimal import Decimal
    for sid in ['seed','grain','feed']:
        for material in build(sid)['scenario']['material_options']:
            f=build(sid,material)
            for q in ['1','3','12']:
                r=estimate(f['bom'],f['route'],q)
                assert sum(Decimal(x['total']) for x in r['lines'])==Decimal(r['base_cost'])
                assert Decimal(r['selling_price'])>Decimal(r['pricing_cost'])
