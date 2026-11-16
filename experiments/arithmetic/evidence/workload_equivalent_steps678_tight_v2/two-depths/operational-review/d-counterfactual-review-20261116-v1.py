import json,gzip,shutil,os,sys
from pathlib import Path
sys.path.insert(0,'/home/zyrv/vulsim')
from experiments.arithmetic_dse.workload_abcd import read,write,sha,static_node
from experiments.arithmetic_dse.workload_contracts import load
from experiments.arithmetic_dse.workload_demand import Graph
from experiments.arithmetic_dse.workload_final_software import export,record,simulate,balanced,ENV
from experiments.arithmetic_dse.workload_final_selection import metadata,BASE
from experiments.arithmetic_dse.workload_final_prices import CachedPrices
from experiments.arithmetic_dse.workload_tight_equivalent import optimize
from experiments.arithmetic_dse.workload_equivalent_run import compressed,compact_prediction

LIVE=Path('/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1')
OUT=Path('/home/zyrv/vulsim-artifacts/d-selection-review-20261116-v1')
OUT.mkdir(exist_ok=True)
sentinel=OUT/'no-eda-bin';sentinel.mkdir(exist_ok=True)
for name in ('yosys','yosys-abc','abc','openroad','opensta','sta'):
 p=sentinel/name;p.write_text('#!/bin/sh\nexit 97\n');p.chmod(0o755)
ENV['PATH']=str(sentinel)+os.pathsep+os.environ['PATH']
prices=CachedPrices(read(BASE/'diagnostic-model.json'))
rows=[]

def evaluate_case(cid,L,T,*,limb=None,shift=False):
 plan=read(LIVE/'plans'/f'{cid}-L{L}.json');selection=Path(plan['selection']);soft=selection.parents[1]
 original=next(g['methods']['D'] for g in read(selection)['records'] if g['target']['T_ps']==T)
 block,w=original['grammar'];w=w if limb is None else limb
 name=f'{cid}-L{L}-T{T}-'+('shift-all-one-later' if shift else f'limb{w}')
 root=OUT/name;root.mkdir(exist_ok=True);(root/cid).mkdir(exist_ok=True)
 source=root/cid/'source'
 if not source.exists():shutil.copytree(soft/cid/'source',source)
 for n in ('bindings.json','characterization-contract.json'):
  shutil.copyfile(soft/n,root/n)
 case=next(c for c in load()['cases'] if c['id']==cid)
 native=export(root,case,block,w,T,L)
 raw=read(native/'graph.json');units=read(native/'scheduling-units.json')['units']
 if shift:
  if sha(native/'graph.json')!=sha(Path(original['rtl']).parent/'graph.json'):raise ValueError('graph changed')
  placement=original['placement'].copy()
  for u in units:
   if u['fixed'] or u['constant']:continue
   for n in u['members']:placement[n]=min(L-1,placement[n]+1)
  placements=[placement]
 else:
  graph=Graph(raw);weights={n['id']:static_node(graph,n) for n in graph.nodes}
  placements=[v["placement"] for v in read(native/"inventory.json")["views"]]
  for v in balanced(raw,units,L,weights):
   if v not in placements:placements.append(v)
 dest=export(root,case,block,w,T,L,placements,tag='audit-native-and-balanced')
 for k,view in enumerate(read(dest/'inventory.json')['views']):
  row=record(dest,view,0,L,'audit_only_counterfactual');receipt=simulate(root,case,row)
  g,v,s,o=metadata(row,T);result=optimize(g,v,s,o,prices,read(root/'characterization-contract.json'))
  compressed(root/f'result-{k}.json.gz',result)
  outcome=dict(case=cid,L=L,T_ps=T,label=name,grammar=[block,w],row=row,
    original_rtl=original['rtl'],original_prediction=original['prediction'],
    prediction=compact_prediction(result['prediction']),functional_receipt=receipt,
    stop=result['stop_reason'],complete_variants=result['complete_variants'],
    native_legality_checked=True,EDA_calls=0,model_refitted=False,
    selected_application_RTL_modified=False,
    inside_frozen_grammar=limb is None or [block,w] in read(soft/cid/'static-pool.json')['grammar'])
  rows.append(outcome);write(OUT/'counterfactuals.json',dict(rows=rows,EDA_calls=0,diagnostic_only=True))
  print(name,k,'original',round(original['prediction']['critical_required_ps'],3),'alternative',round(result['prediction']['critical_required_ps'],3),'stages',[round(z['required_ps'],2) for z in result['prediction']['stages']],flush=True)
  Graph.origins.cache_clear();Graph.roots.cache_clear()

for cid,L,T,kwargs in [('add512',2,700,dict(shift=True)),('add512',2,800,dict(shift=True)),
                      ('add512',2,700,dict(limb=256)),('add512',2,800,dict(limb=256)),
                      ('barrett64',8,900,dict(shift=True)),('barrett64',8,1100,dict(shift=True))]:
 evaluate_case(cid,L,T,**kwargs)
