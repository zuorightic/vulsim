from pathlib import Path
import json,subprocess,sys
R=Path.cwd();B=R/'build/step5-closure-20261031'
tasks=[
 ['build/step4-rtlzz/testv2/mul-template-test',str(R),str(B/'generated-final')],
 ['build/step4-rtlzz/testv2/arithmetic-interface-test',str(R),str(B/'interfaces-final')],
 ['build/step4-rtlzz/testv2/mul-replay-test',str(B/'historical_replay_inputs.json'),str(B/'historical_replay_final.json')],
 [sys.executable,'-m','unittest','regression.arithmetic_analysis','regression.arithmetic_block_evidence','regression.arithmetic_capacity_retest'],
 [sys.executable,str(B/'check_analysis.py'),str(B/'generated-final')],
 [sys.executable,str(B/'timing_report.py')],
]
for task in tasks:
 print('RUN',task,flush=True);subprocess.run(task,check=True,cwd=R)
result=json.loads((B/'historical_replay_final.json').read_text());assert result['status']=='passed' and result['unreconstructable_reports']==0
assert all('\0' not in x['reason'] for x in result['mutations'])
print('PASS final software, native diagnostics and full-chain timing')
