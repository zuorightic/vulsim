from pathlib import Path
import json,subprocess,sys
R=Path.cwd();B=R/'build/step5-closure-20261031';sys.path.insert(0,str(R))
from experiments.arithmetic_dse.closure_evidence import verify
from experiments.arithmetic_dse.platform_evidence import verify as platform
from experiments.arithmetic_dse.wide_evidence import verify as wide
result={'closure_complete_artifacts_and_parents':verify(R,True,True),'platform_external':platform(R,True),'wide':wide(R)}
assert all(v['status']=='passed' for v in result.values())
for directory in (R,R/'rtlzz'):subprocess.run(['git','diff','--check'],cwd=directory,check=True)
(B/'final_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v['status'] for k,v in result.items()},indent=2))
