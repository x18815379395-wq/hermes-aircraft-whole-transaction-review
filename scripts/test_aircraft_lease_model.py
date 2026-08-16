#!/usr/bin/env python3
import importlib.util
import math
from pathlib import Path

P=Path(__file__).with_name('aircraft_lease_model.py')
s=importlib.util.spec_from_file_location('m',P); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)

def sample():
 return {
  'purchase_price':100.0,'term_years':3,'monthly_rent':2.0,'annual_rent_growth':0.0,
  'offhire_months':[0,1,0],'annual_asset_costs':[2,2,2],'lessee_additional_costs':[0,0,0],
  'maintenance_reserve_per_fh':0.01,'annual_flight_hours':[1000,1000,1000],
  'maintenance_events':[{'year':2,'cost':15.0}], 'reserve_refundable_fraction':0.5,
  'security_deposit':4.0,'security_deposit_refundable':True,
  'residual_value':60.0,'sale_cost_rate':0.05,'discount_rate':0.10,
  'debt':{'amount':60.0,'annual_rate':0.06,'tenor_years':3,'repayment':'equal_principal'},
  'scenarios':{'residual_down_40':{'residual_multiplier':0.6},'rent_down_20':{'rent_multiplier':0.8},'interest_up_200bp':{'interest_rate_add':0.02}}
 }

def test_rent_and_reserve_are_not_double_counted():
 r=m.run_model(sample())['base']
 assert math.isclose(r['years'][0]['rent'],24.0)
 assert math.isclose(r['years'][1]['rent'],22.0)
 assert math.isclose(r['years'][0]['reserve_collected'],10.0)
 assert r['years'][0]['cfads']==22.0

def test_maintenance_reserve_rollforward_and_shortfall():
 r=m.run_model(sample())['base']
 assert r['years'][0]['reserve_closing']==10.0
 assert r['years'][1]['maintenance_paid_from_reserve']==15.0
 assert r['years'][1]['reserve_closing']==5.0
 assert r['years'][1]['maintenance_shortfall']==0.0

def test_metrics_and_debt_close():
 r=m.run_model(sample())['base']
 assert r['project_irr'] is not None and r['equity_irr'] is not None
 assert r['years'][-1]['debt_closing']==0.0
 assert r['minimum_dscr']>0
 assert r['llcr']>0
 assert math.isclose(r['net_residual'],57.0)

def test_stress_cannot_improve_base():
 out=m.run_model(sample())
 assert out['scenarios']['residual_down_40']['project_npv'] < out['base']['project_npv']
 assert out['scenarios']['rent_down_20']['minimum_dscr'] < out['base']['minimum_dscr']
 assert out['scenarios']['interest_up_200bp']['minimum_dscr'] < out['base']['minimum_dscr']

def test_same_year_maintenance_events_are_aggregated():
 d=sample(); d['maintenance_events'].append({'year':2,'cost':5.0})
 r=m.run_model(d)['base']
 assert math.isclose(r['years'][1]['maintenance_event_cost'],20.0)
 assert math.isclose(r['years'][1]['reserve_closing'],0.0)

def test_lessee_lease_npc_accounts_for_refunds():
 r=m.run_model(sample())['base']
 expected=4.0+34.0/1.1+32.0/(1.1**2)+(34.0-7.5-4.0)/(1.1**3)
 assert math.isclose(r['lessee_lease_npc'],expected)

def test_pricing_corridor_uses_explicit_cash_capacity():
 d=sample(); d['pricing_corridor']={'target_project_irr':0.10,'lessee_cash_available_for_lease':[40,40,40]}
 p=m.run_model(d)['base']['pricing_corridor']
 assert math.isclose(p['lessee_max_initial_monthly_rent'],2.5)
 assert p['lessor_min_initial_monthly_rent']>0
 assert p['feasible'] is True
 assert p['current_rent_within_corridor'] is True
 assert len(p['annual_affordability'])==3

def test_pricing_corridor_flags_no_overlap():
 d=sample(); d['pricing_corridor']={'target_project_irr':0.30,'lessee_cash_available_for_lease':[5,5,5]}
 out=m.run_model(d)
 assert out['base']['pricing_corridor']['feasible'] is False
 assert 'NO_FEASIBLE_RENT_CORRIDOR' in out['hard_flags']

def test_current_rent_outside_feasible_corridor_is_flagged():
 d=sample(); d['monthly_rent']=3.0; d['pricing_corridor']={'target_project_irr':0.10,'lessee_cash_available_for_lease':[40,40,40]}
 out=m.run_model(d)
 assert out['base']['pricing_corridor']['feasible'] is True
 assert out['base']['pricing_corridor']['current_rent_within_corridor'] is False
 assert 'CURRENT_RENT_OUTSIDE_CORRIDOR' in out['hard_flags']

def test_lessor_floor_has_zero_npv_at_target_return():
 d=sample(); d['pricing_corridor']={'target_project_irr':0.10,'lessee_cash_available_for_lease':[40,40,40]}
 floor=m.run_model(d)['base']['pricing_corridor']['lessor_min_initial_monthly_rent']
 d.pop('pricing_corridor'); d['monthly_rent']=floor; d['discount_rate']=0.10
 assert abs(m.run_model(d)['base']['project_npv'])<1e-8

def test_invalid_lengths_rejected():
 d=sample(); d['offhire_months']=[0]
 try: m.run_model(d)
 except ValueError as e: assert 'offhire_months' in str(e)
 else: raise AssertionError('expected ValueError')

if __name__=='__main__':
 tests=[v for k,v in sorted(globals().items()) if k.startswith('test_')]
 for t in tests: t()
 print(f'PASS {len(tests)}/{len(tests)}')
