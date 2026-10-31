from pathlib import Path
import json,sys
R=Path.cwd();sys.path.insert(0,str(R))
from experiments.arithmetic_dse.closure_evidence import software,capacity,document
B=R/'build/step5-closure-20261031';old=R/'experiments/arithmetic/evidence/step5_mul_templates_v1'
# Only audit preparations are copied before the successor freeze is assembled.
# No generator or EDA command runs here.
e=B/'validation-inputs';e.mkdir(exist_ok=True)
import shutil
for source,target in [('historical_replay_inputs.json','historical_replay_inputs.json'),('historical_replay_final.json','historical_replay.json'),('positions_v2.json','positions_v2.json'),('sensitivity_v2.json','sensitivity_v2.json')]:shutil.copy2(B/source,e/target)
parent=document(R/'experiments/arithmetic/mul_templates_freeze_v1.json');data,s=software(R,e,parent);c=capacity(R,R/'experiments/arithmetic/evidence/step5_mul_capacity_v2',data)
d={'status':'passed','software':s,'capacity':c};(B/'retest_validation.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2))
