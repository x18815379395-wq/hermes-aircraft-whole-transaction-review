#!/usr/bin/env python3
"""Deterministic annual aircraft lease audit model (stdlib only)."""
from __future__ import annotations
import argparse, copy, json, math
from pathlib import Path

EPS=1e-9

def npv(rate, flows): return sum(v/((1+rate)**i) for i,v in enumerate(flows))

def irr(flows):
    if not flows or not (any(x<0 for x in flows) and any(x>0 for x in flows)): return None
    grid=[-0.99+i*0.01 for i in range(100)]+[i*0.05 for i in range(0,401)]
    last_r,last_v=grid[0],npv(grid[0],flows)
    for r in grid[1:]:
        v=npv(r,flows)
        if abs(v)<1e-10: return r
        if last_v*v<0:
            lo,hi=last_r,r
            for _ in range(100):
                mid=(lo+hi)/2; mv=npv(mid,flows)
                if npv(lo,flows)*mv<=0: hi=mid
                else: lo=mid
            return (lo+hi)/2
        last_r,last_v=r,v
    return None

def validate(d):
    n=int(d['term_years'])
    if n<=0: raise ValueError('term_years must be positive')
    for k in ('offhire_months','annual_asset_costs','annual_flight_hours'):
        if len(d[k])!=n: raise ValueError(f'{k} must have term_years values')
    if 'lessee_additional_costs' in d and len(d['lessee_additional_costs'])!=n: raise ValueError('lessee_additional_costs must have term_years values')
    corridor=d.get('pricing_corridor')
    if corridor:
        cash=corridor.get('lessee_cash_available_for_lease',[])
        if len(cash)!=n: raise ValueError('lessee_cash_available_for_lease must have term_years values')
        if any(float(x)<0 for x in cash): raise ValueError('lessee_cash_available_for_lease cannot be negative')
        if float(corridor.get('target_project_irr',d.get('discount_rate',0.1)))<=-1: raise ValueError('target_project_irr invalid')
    if any(x<0 or x>12 for x in d['offhire_months']): raise ValueError('offhire_months must be between 0 and 12')
    if d['purchase_price']<=0 or d['monthly_rent']<0: raise ValueError('purchase_price/rent invalid')
    for e in d.get('maintenance_events',[]):
        if not 1<=int(e['year'])<=n or e['cost']<0: raise ValueError('maintenance_events invalid')
    debt=d.get('debt',{})
    if debt.get('amount',0)<0 or debt.get('amount',0)>d['purchase_price']: raise ValueError('debt amount invalid')
    return n

def merged(base, changes):
    d=copy.deepcopy(base)
    for k,v in changes.items(): d[k]=v
    return d

def build_pricing_corridor(d, factors, result):
    """Solve an explicit-input lessor floor and lessee cash ceiling."""
    cfg=d.get('pricing_corridor')
    if not cfg: return None
    n=int(d['term_years']); target=float(cfg.get('target_project_irr',d.get('discount_rate',0.1)))
    trial=copy.deepcopy(d); trial.pop('pricing_corridor',None); trial['discount_rate']=target
    def target_npv(monthly_rent):
        trial['monthly_rent']=monthly_rent
        return calculate(trial,factors,include_pricing=False)['project_npv']
    lo=0.0; hi=max(float(d['monthly_rent']),float(d['purchase_price'])/12,EPS)
    while target_npv(hi)<0 and hi<float(d['purchase_price'])*100:
        hi*=2
    if target_npv(hi)<0:
        floor=None
    else:
        for _ in range(100):
            mid=(lo+hi)/2
            if target_npv(mid)>=0: hi=mid
            else: lo=mid
        floor=(lo+hi)/2
    cash=[float(x) for x in cfg['lessee_cash_available_for_lease']]
    costs=d.get('lessee_additional_costs',[0.0]*n)
    reserve_rate=float(d.get('maintenance_reserve_per_fh',0))
    growth=float(d.get('annual_rent_growth',0)); extra=float(factors.get('extra_offhire_months',0))
    annual=[]; ceilings=[]
    for y in range(1,n+1):
        off=min(12,float(d['offhire_months'][y-1])+extra)
        months=12-off; reserve=reserve_rate*float(d['annual_flight_hours'][y-1]); other=float(costs[y-1])
        available=max(0.0,cash[y-1]-reserve-other)
        ceiling=available/(months*((1+growth)**(y-1))*max(float(factors.get('rent_multiplier',1)),EPS)) if months>EPS else None
        if ceiling is not None: ceilings.append(ceiling)
        annual.append({'year':y,'cash_available_before_lease':cash[y-1],'maintenance_reserve_cash':reserve,'lessee_additional_costs':other,'rent_paid':result['years'][y-1]['rent'],'cash_margin_after_current_rent':cash[y-1]-reserve-other-result['years'][y-1]['rent'],'max_initial_monthly_rent':ceiling})
    ceiling=min(ceilings) if ceilings else None
    feasible=floor is not None and ceiling is not None and floor<=ceiling+EPS
    current=float(d['monthly_rent'])
    within=feasible and current+EPS>=floor and current<=ceiling+EPS
    return {'method':'explicit_cash_capacity_and_target_return','target_project_irr':target,'lessor_min_initial_monthly_rent':floor,'lessee_max_initial_monthly_rent':ceiling,'feasible':feasible,'current_initial_monthly_rent':current,'current_rent_within_corridor':within,'annual_affordability':annual,'market_defaults_used':False}

def calculate(d, factors=None, include_pricing=True):
    factors=factors or {}; n=validate(d)
    rent_mult=float(factors.get('rent_multiplier',1)); residual_mult=float(factors.get('residual_multiplier',1))
    opex_mult=float(factors.get('asset_cost_multiplier',1)); maint_mult=float(factors.get('maintenance_cost_multiplier',1))
    extra_offhire=float(factors.get('extra_offhire_months',0))
    rate=float(d.get('discount_rate',0.1)); debt=d.get('debt',{}); debt_amt=float(debt.get('amount',0)); debt_rate=float(debt.get('annual_rate',0))+float(factors.get('interest_rate_add',0)); tenor=min(int(debt.get('tenor_years',0)),n)
    principal=debt_amt/tenor if tenor else 0; debt_open=debt_amt; reserve=0.0
    events={}
    for e in d.get('maintenance_events',[]):
        y=int(e['year']); events[y]=events.get(y,0.0)+float(e['cost'])*maint_mult
    years=[]; project_flows=[-float(d['purchase_price'])]; equity_flows=[-(float(d['purchase_price'])-debt_amt)]
    lessee_npc_flows=[float(d.get('security_deposit',0))]
    lessee_costs=d.get('lessee_additional_costs',[0.0]*n)
    dscrs=[]; cfads_debt=[]
    for y in range(1,n+1):
        off=min(12,float(d['offhire_months'][y-1])+extra_offhire)
        monthly=float(d['monthly_rent'])*((1+float(d.get('annual_rent_growth',0)))**(y-1))*rent_mult
        rent=monthly*(12-off)
        collected=float(d.get('maintenance_reserve_per_fh',0))*float(d['annual_flight_hours'][y-1])
        reserve+=collected; event=events.get(y,0.0); paid=min(reserve,event); reserve-=paid; shortfall=event-paid
        asset_cost=float(d['annual_asset_costs'][y-1])*opex_mult
        cfads=rent-asset_cost-shortfall
        interest=debt_open*debt_rate if y<=tenor else 0; pmt=min(principal,debt_open) if y<=tenor else 0; service=interest+pmt
        close=max(0.0,debt_open-pmt); dscr=cfads/service if service>EPS else None
        if dscr is not None: dscrs.append(dscr); cfads_debt.append(cfads)
        retained=0.0; reserve_refund=0.0; deposit_refund=0.0
        net_residual=0.0
        if y==n:
            reserve_refund=reserve*float(d.get('reserve_refundable_fraction',0)); retained=reserve-reserve_refund
            deposit_refund=float(d.get('security_deposit',0)) if d.get('security_deposit_refundable',True) else 0.0
            net_residual=float(d.get('residual_value',0))*residual_mult*(1-float(d.get('sale_cost_rate',0)))
        project_cash=cfads+retained+net_residual
        equity_cash=cfads-service+retained+net_residual
        project_flows.append(project_cash); equity_flows.append(equity_cash)
        lessee_npc_flows.append(rent+collected+float(lessee_costs[y-1])-reserve_refund-deposit_refund)
        years.append({'year':y,'rent':rent,'offhire_months':off,'reserve_collected':collected,'maintenance_event_cost':event,'maintenance_paid_from_reserve':paid,'maintenance_shortfall':shortfall,'reserve_closing':reserve,'reserve_refund':reserve_refund,'reserve_retained':retained,'security_deposit_refund':deposit_refund,'lessee_additional_costs':float(lessee_costs[y-1]),'asset_costs':asset_cost,'cfads':cfads,'debt_opening':debt_open,'interest':interest,'principal':pmt,'debt_service':service,'dscr':dscr,'debt_closing':close,'project_cashflow':project_cash,'equity_cashflow':equity_cash})
        debt_open=close
    pv_cfads=sum(v/((1+debt_rate)**i) for i,v in enumerate(cfads_debt,1)); llcr=pv_cfads/debt_amt if debt_amt>EPS else None
    net_residual=float(d.get('residual_value',0))*residual_mult*(1-float(d.get('sale_cost_rate',0)))
    result={'years':years,'project_cashflows':project_flows,'equity_cashflows':equity_flows,'lessee_npc_cashflows':lessee_npc_flows,'project_npv':npv(rate,project_flows),'project_irr':irr(project_flows),'equity_irr':irr(equity_flows),'lessee_lease_npc':npv(float(d.get('lessee_discount_rate',rate)),lessee_npc_flows),'minimum_dscr':min(dscrs) if dscrs else None,'average_dscr':sum(dscrs)/len(dscrs) if dscrs else None,'llcr':llcr,'lrf_monthly':float(d['monthly_rent'])/float(d['purchase_price']),'net_residual':net_residual}
    if include_pricing and d.get('pricing_corridor'):
        result['pricing_corridor']=build_pricing_corridor(d,factors,result)
    return result

def run_model(d):
    validate(d); base=calculate(d); scenarios={k:calculate(d,v) for k,v in d.get('scenarios',{}).items()}
    flags=[]
    if base['minimum_dscr'] is not None and base['minimum_dscr']<1: flags.append('BASE_DSCR_BELOW_1_00')
    if base['project_npv']<0: flags.append('BASE_PROJECT_NPV_NEGATIVE')
    if base['years'][-1]['reserve_closing']<0: flags.append('RESERVE_BALANCE_NEGATIVE')
    if base.get('pricing_corridor') and not base['pricing_corridor']['feasible']: flags.append('NO_FEASIBLE_RENT_CORRIDOR')
    if base.get('pricing_corridor') and base['pricing_corridor']['feasible'] and not base['pricing_corridor']['current_rent_within_corridor']: flags.append('CURRENT_RENT_OUTSIDE_CORRIDOR')
    return {'validation':{'ok':True,'currency_unit':'same_as_input','market_defaults_used':False,'pricing_corridor_uses_explicit_inputs':bool(d.get('pricing_corridor'))},'base':base,'scenarios':scenarios,'hard_flags':flags}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('--output','-o'); a=ap.parse_args()
    out=run_model(json.loads(Path(a.input).read_text(encoding='utf-8'))); text=json.dumps(out,ensure_ascii=False,indent=2)
    if a.output: Path(a.output).write_text(text,encoding='utf-8')
    else: print(text)
if __name__=='__main__': main()
