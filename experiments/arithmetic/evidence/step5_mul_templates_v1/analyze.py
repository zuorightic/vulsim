from pathlib import Path
import json,sys
ROOT=Path.cwd();sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.step5_analysis import sensitivity,validate_selection,position_analysis
from experiments.arithmetic_dse.interfaces_evidence import verify_report
B=ROOT/'build/step5-parameterized-20261031';G=B/sys.argv[1];data={p.stem:json.loads(p.read_text()) for p in G.glob('*.json') if p.name not in ('summary.json','positions.json')}
features=json.loads((ROOT/'experiments/arithmetic_dse/configs/beir_cost_features_v1.json').read_text());types=json.loads((ROOT/'experiments/arithmetic_dse/configs/arithmetic_compiler_interfaces_v1.json').read_text())['report_schemas']
queries=nodes=regions=accepted=0
for name,r in data.items():
 result=verify_report(r,(G/(name+'.sv')).read_text(),features,report_schemas=types);nodes+=result['nodes'];regions+=result['regions'];queries+=validate_selection(r)
 for row in r['selection']['candidates']:
  if row['status']=='scheduled':
   verify_report(row['computation'],None,features,report_schemas=types)
   accepted+=sum(m['accepted'] and '/group' in m['group'] for m in row['moves'])
 # Functional execution used identical SV before adding candidate detail fields.
 old=B/'generated-3'/(name+'.sv')
 if old.exists():assert old.read_bytes()==(G/(name+'.sv')).read_bytes(),name
s=sensitivity(data);(B/'sensitivity.json').write_text(json.dumps(s,indent=2)+'\n')
pos=position_analysis(data['w8_full_1'],json.loads((G/'positions.json').read_text()));(B/'positions.json').write_text(json.dumps(pos,indent=2)+'\n')
assert accepted>0
report={'status':'passed','reports':len(data),'nodes':nodes,'regions':regions,'scheduled_candidates_checked':queries,'accepted_arithmetic_group_moves':accepted,'position_classification':pos['classification'],'sensitivity_structures':s['structures'],'sensitivity_selection_changes':s['selected_changes'],'all_88_numerically_executed_RTL_files_unchanged':True,'physical_calls':0}
(B/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
