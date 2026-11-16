import sys,json,gzip,collections,datetime,shutil
from pathlib import Path
sys.path.insert(0,'/home/zyrv/vulsim')
from experiments.arithmetic_dse.workload_abcd import read,write,sha,static_node
from experiments.arithmetic_dse.workload_two_depths_run import collect
from experiments.arithmetic_dse.workload_two_depths_monitor import review
from experiments.arithmetic_dse.workload_demand import Graph
from experiments.arithmetic_dse.workload_equivalent import score_key
from experiments.arithmetic_dse.workload_final_selection import BASE

ROOT=Path('/home/zyrv/vulsim')
LIVE=ROOT.parent/'vulsim-artifacts/workload-equivalent-two-depths-v1'
ART=ROOT.parent/'vulsim-artifacts/d-selection-review-20261116-v1'
EVIDENCE=ROOT/'experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/two-depths/operational-review'
EVIDENCE.mkdir(exist_ok=True)
SOURCES=[ROOT/'experiments/arithmetic_dse'/n for n in ('workload_latency_matrix.py','workload_final_selection.py',
 'workload_final_software.py','workload_equivalent.py','workload_tight_equivalent.py','workload_diagnostic.py',
 'workload_final_adapter.py','workload_final_prices.py','backend.py','workload_nine_runtime.py')]+[BASE/'diagnostic-model.json']
hashes={str(p):sha(p) for p in SOURCES}
selected=[];pool_checks=[]
for plan in sorted((LIVE/'plans').glob('*.json')):
 doc=read(plan);selpath=Path(doc['selection']);selection=read(selpath);soft=selpath.parents[1];cid=doc['case']
 for group in selection['records']:
  T=group['target']['T_ps'];m=group['methods']['D'];L=m['L'];folder=Path(m['rtl']).parent
  trace=json.loads(gzip.decompress((folder/'complete-budget-trace.json.gz').read_bytes()))
  p=trace['prediction'];raw=read(folder/'graph.json');graph=Graph(raw);owners=read(folder/'owners.json')
  counts=collections.Counter(m['placement'][n['id']] for n in graph.nodes if static_node(graph,n)>0)
  ownercounts=collections.Counter(m['placement'][o['node']] for o in p['owners'] if o['delay_ps']>0)
  idx,rank=map(int,trace['best_variant_id'].split(':'));entry=trace['trace'][idx]
  best=next(v for v in entry['variants'] if v['id']==trace['best_variant_id'])
  budgets=entry['budgets_ps'];queries=best['actual_queries']
  taus=[q.get('target_ps',q.get('flow_context',{}).get('target_period_ps')) for q in queries.values()]
  state=read(folder/'state.json');sim=read(folder/'functional-receipt.json')
  stages=[]
  for s in p['stages']:
   controls=[c for c in p['S']['controls'] if c['stage']==s['stage']]
   control=max(controls,key=lambda c:c['required_ps']) if controls else None
   stages.append(dict(s,positive_arithmetic_nodes=counts[s['stage']],positive_owners=ownercounts[s['stage']],
     control_max_ps=control['required_ps'] if control else 0,
     control_path=control['path_class'] if control else None,
     critical_kind='control' if control and control['required_ps']>s['comb_delay_ps']+s['boundary_ps'] else 'data'))
  top=[]
  for o in sorted(p['owners'],key=lambda r:r['delay_ps'],reverse=True)[:8]:
   n=raw['nodes'][o['node']];top.append(dict(node=o['node'],operation=n['operation'],width=n['width'],
    kind=o['kind'],stage=m['placement'][o['node']],delay_ps=o['delay_ps'],area_um2=o['area_um2']))
  source=m.get('source_selection',{})
  row=dict(case=cid,L=L,T_ps=T,grammar=m['grammar'],rtl=m['rtl'],rtl_sha256=m['rtl_sha256'],
    selection_file=str(selpath),selection_sha256=sha(selpath),stages=stages,top_owners=top,
    critical_required_ps=p['critical_required_ps'],total_area_um2=p['total_area_um2'],
    port_required_ps=p['port_required_ps'],model_target_met=p['target_met'],
    empty_arithmetic_stages=[s for s in range(L) if counts[s]==0],
    empty_priced_stages=[s for s in range(L) if ownercounts[s]==0],
    stage_max_over_mean=max(z['required_ps'] for z in stages)/(sum(z['required_ps'] for z in stages)/L),
    stage_FF_bits=[sum(w) for w in p['S']['projection']['stage_words']],
    stop_reason=trace['stop_reason'],complete_variants=trace['complete_variants'],
    local_requests_unmet=best['local_requests_unmet'],dynamic_queries=len(queries),
    budget_range_ps=[min(budgets.values()),max(budgets.values())] if budgets else [],
    equivalent_T_range_ps=[min(taus),max(taus)] if taus else [],
    equivalent_T_equal_global_count=sum(t==T for t in taus),
    owner_price_total_matches_receipt=abs(p['critical_required_ps']-m['prediction']['critical_required_ps'])<1e-8,
    functional_receipt_valid=sim['status']=='passed' and sim['rtl_sha256']==sha(folder/'workload.sv'),
    functional_receipt_sha256=sha(folder/'functional-receipt.json'),trace_sha256=sha(folder/'complete-budget-trace.json.gz'),
    source_candidate=source,search=group['search'])
  selected.append(row)
  summary=soft/cid/f'scores-T{T}/pool-summary.json.gz'
  if summary.exists():
   candidates=json.loads(gzip.decompress(summary.read_bytes()));valid=[c for c in candidates if c['model']]
   winner=min(valid,key=lambda c:score_key(c['model'])+(c['id'],));fastest=min(valid,key=lambda c:c['model']['critical_required_ps'])
   pool_checks.append(dict(case=cid,L=L,T_ps=T,pool_file=str(summary),pool_sha256=sha(summary),
    summary_matches_selection=sha(summary)==group['search']['pool_summary_sha256'],
    candidates=len(candidates),complete=len(valid),feasible=sum(c['model']['target_met'] for c in valid),
    selected_id=group['search']['selected_id'],score_order_correct=winner['id']==group['search']['selected_id'],
    selected_rtl_matches=winner['rtl_sha256']==m['rtl_sha256'],fastest=fastest,
    best_same_pool_score=score_key(winner['model']),all_candidates=candidates))
  else:
   pool_checks.append(dict(case=cid,L=L,T_ps=T,status='MAC32 L3 inherited step45 common pool; no local pool summary'))
  Graph.origins.cache_clear();Graph.roots.cache_clear()
 print('AUDITED',plan.stem,flush=True)

status=review(LIVE);rows=collect(LIVE);main=[r for r in rows if r['method'] in ('A','B','C','D')]
successes=[r for r in main if r['status']=='measured_grt' and r['setup_met']]
unique={};unique_status=collections.Counter();failure_types=collections.Counter()
for r in main:
 unique.setdefault(r['measurement']['run'],r)
for r in unique.values():unique_status[r['status']]+=1
backend_failures=[]
for ap in sorted((LIVE/'backend').glob('*/admission.json')):
 for t in read(ap)['tasks']:
  run=ap.parent/'runs'/t['id'];op=run/'measurement-outcome.json';mf=run/'manifest.json'
  if not mf.exists():continue
  m=read(mf);o=read(op) if op.exists() else {}
  if m['status']=='failed' or o.get('status')=='failed':
   why=o.get('reason',m.get('failure_reason'));failure_types[why]+=1
   tail=(run/'grt.log').read_text(errors='replace').splitlines() if (run/'grt.log').exists() else []
   errors=[x for x in tail if '[ERROR' in x or 'Signal ' in x or 'invalid chunk' in x]
   backend_failures.append(dict(task=t['id'],case=t['case'],reason=why,run=str(run),error_lines=errors[-4:],
    memory_limit_MiB=t['memory_limit_MiB'],timeout_s=t['grt_timeout_s']))
status.update(setup_met_rows=successes,main_unique_measurement_statuses=dict(unique_status),
    backend_failure_types=dict(failure_types),backend_failure_tasks=backend_failures)
changed=[name for name,digest in hashes.items() if sha(name)!=digest]
if changed:raise ValueError('live sources changed during review: '+str(changed))
result=dict(version='D-split-placement-review-20261116-v1',checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
 model_status='diagnostic_only',new_EDA_calls=0,new_model_fits=0,live_queue_modified=False,
 frozen_sources_sha256=hashes,source_unchanged=True,status=status,measurements=rows,
 selected_D=selected,pool_checks=pool_checks,counterfactuals=read(ART/'counterfactuals.json'),
 counterfactual_scope='development diagnostics only; not new final selection or independent generalization evidence')
dest=EVIDENCE/'d-split-placement-review-20261116-v1.json';write(dest,result)
shutil.copyfile('/tmp/vulsim_d_counterfactual_review.py',EVIDENCE/'d-counterfactual-review-20261116-v1.py')
shutil.copyfile(__file__,EVIDENCE/'d-selection-audit-20261116-v1.py')
print(json.dumps(dict(output=str(dest),main_statuses=status['main_statuses'],main_measured=status['main_measured'],
 setup_met=len(successes),failures=failure_types,pool_candidates=sum(p.get('candidates',0) for p in pool_checks),
 correct_pool_orders=sum(p.get('score_order_correct',False) for p in pool_checks),selected_D=len(selected),
 empty_D=[(r['case'],r['L'],r['T_ps'],r['empty_priced_stages']) for r in selected if r['empty_priced_stages']]),ensure_ascii=False),flush=True)
