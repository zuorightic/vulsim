from pathlib import Path
import json,os,subprocess,sys
R=Path.cwd();B=R/'build/step6-review-20261102';env=os.environ.copy();env['PATH']=str(R/'build/step4-review/circt-bin')+os.pathsep+env['PATH']
for cmd in [
 ['cmake','--build','build/step4-rtlzz','--target','divisor-contract-test','predicate-expand','-j2'],
 ['cmake','--build','build','--target','vulrtlgen','-j2'],
 ['build/step4-rtlzz/testv2/divisor-contract-test',str(B/'historical_manifest.json'),str(B/'new_cpp.json')],
 [sys.executable,'-m','unittest','regression.arithmetic_backend','regression.arithmetic_sdc','regression.arithmetic_divisor','regression.arithmetic_bounded_recheck','regression.arithmetic_documentation_snapshot','regression.arithmetic_report_types','regression.arithmetic_analysis','regression.arithmetic_block_evidence','regression.arithmetic_capacity_retest']
]:
 print('RUN',cmd,flush=True);subprocess.run(cmd,cwd=R,env=env,check=True)
print('PASS current standalone/public binaries rebuilt, native14 actual-width cases and original176/186 replay, final software regressions',flush=True)
