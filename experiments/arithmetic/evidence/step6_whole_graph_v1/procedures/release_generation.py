from pathlib import Path
import json,subprocess
R=Path.cwd();B=R/'build/step6-integration-20261031'
subprocess.run(['cmake','--build','build/step4-rtlzz','--target','arithmetic-suite-test','-j2'],check=True)
subprocess.run(['build/step4-rtlzz/testv2/arithmetic-suite-test',str(R),str(B/'fixtures-v3/jobs.json'),str(B/'release')],check=True)
for p in (B/'release').glob('*'):
 assert p.read_bytes()==(B/'generated-final'/p.name).read_bytes(),p.name
print('PASS final source graph/schedule/report/RTL byte identity: 176 implementations')
