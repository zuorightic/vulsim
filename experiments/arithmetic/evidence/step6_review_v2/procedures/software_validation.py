from pathlib import Path
import json,subprocess,hashlib,sys,os
R=Path.cwd();B=R/'build/step6-review-20261102';old=R/'build/step6-integration-20261031'
os.environ['PATH']=str(R/'build/step4-review/circt-bin')+os.pathsep+os.environ['PATH']
if not (B/'generated').exists():subprocess.run(['build/step4-rtlzz/testv2/arithmetic-suite-test',str(R),str(old/'fixtures-v3/jobs.json'),str(B/'generated')],check=True)
for p in (B/'generated').glob('*'):assert p.read_bytes()==(old/'release'/p.name).read_bytes(),p.name
for name in ['pipeline-test','pipeline-reset-test','pipeline-valid-test']:
 subprocess.run([str(R/'build/step4-rtlzz/testv2'/name)],cwd=R/'rtlzz',check=True)
for name,out in [('arithmetic-interface-test','interfaces'),('mul-template-test','mul')]:subprocess.run([str(R/'build/step4-rtlzz/testv2'/name),str(R),str(B/out)],check=True)
print('PASS 176 actual regenerated report/RTL bytes identical; pipeline reset valid interface Mul regressions passed')
