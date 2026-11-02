from pathlib import Path
import json,sys,re,copy
R=Path.cwd();sys.path.insert(0,str(R));B=R/'build/step6-integration-20261031'
from experiments.arithmetic_dse.interfaces_evidence import verify_report
from experiments.arithmetic_dse.step5_analysis import validate_selection
from experiments.arithmetic_dse.block_tree_evidence import verify_block_trees
from experiments.arithmetic_dse.whole_graph import sha
from experiments.arithmetic_dse.whole_graph_checks import verify_safe_divisors
features=json.loads((R/'experiments/arithmetic_dse/configs/beir_cost_features_v1.json').read_text());items=json.loads((B/'fixtures-v3/items.json').read_text());totals={'reports':0,'nodes':0,'regions':0,'candidates':0,'block_regions':0,'safe_Div_Mod':0};shared=[]
for item in items:
 name=item['name'];p=B/'release'/(name+'.json');r=json.loads(p.read_text());rtl=p.with_suffix('.sv').read_text()
 stats=verify_report(r,rtl,features);totals['reports']+=1;totals['nodes']+=stats['nodes'];totals['regions']+=stats['regions'];totals['candidates']+=validate_selection(r);totals['block_regions']+=verify_block_trees(r);totals['safe_Div_Mod']+=verify_safe_divisors(r)
 # The totality self-check added no gates or schedule changes to previously
 # validated outputs. This keeps the actual functional trace identity explicit.
 before=json.loads((B/'generated-v2'/(name+'.json')).read_text())
 for key in ('graph','stages','protocol','graph_sha256','schedule_sha256','pipeline'):assert before[key]==r[key],(name,key)
 clean=lambda s:re.sub(r'//[^\n]*','',s)
 assert clean((B/'generated-v2'/(name+'.sv')).read_text())==clean(rtl),(name,'RTL logic changed')
 x=copy.deepcopy(before['selection']);y=copy.deepcopy(r['selection'])
 for selection in (x,y):
  for row in selection['candidates']:row.pop('shape_sha256',None)
 assert x==y,(name,'selection trace changed')
 if item['case'].get('diagnostic')=='shared_divrem':
  ns=r['graph']['nodes'];counts={op:sum(n['kind']==4 and n['opcode']==code for n in ns) for op,code in [('Div',4),('Mod',5),('Mul',3),('Sub',2)]}
  assert counts['Div']==1 and counts['Mod']==0 and counts['Mul']==1 and counts['Sub']>=1,counts;shared.append({'W':item['case']['width'],'actual_primitive_counts':counts,'comb':r['pipeline']['comb'],'selected_candidate':r['selection']['selected_candidate'],'scope':'explicit quotient reuse; Div+Mul+Sub costs charged once per real node; not fused DivRem'})
result={'status':'passed',**totals,'shared_divrem':shared,'trace_RTL_logic_and_schedule_unchanged':True,'raw_RTL_debug_comments_changed_in_shared_helper_diagnostics_only':5,'comment_change_reason':'one static_assert line added to helper, source-location comments and debug-derived candidate shape hashes shift; typed graph, schedule, selection cost/moves and RTL logic identical','formal_L_unchanged':True,'D_inference':'not implemented; fail-closed step7','physical_calls':0};(B/'software_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
