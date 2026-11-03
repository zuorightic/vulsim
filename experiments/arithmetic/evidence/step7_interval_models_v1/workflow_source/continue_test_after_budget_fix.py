import json
import subprocess
import sys
from pathlib import Path
R=Path.cwd();O=R/'build/step7-intervals-20261103';B=R/'build/step7-models-20261102/native-interval-asap7-v4';F=O/'asap7-fit-v1/selection-freeze.json'

def command(args):
    print('RUN',json.dumps(list(map(str,args))),flush=True);subprocess.run(list(map(str,args)),cwd=R,check=True)
def support(stem,*args):command([sys.executable,R/'build/step7-models-20261102/support.py',stem,900,*args])
def status(phase,**extra):
    data={'phase':phase,**extra,'full_step7_complete':False,'main_matrix_authorized':False}
    (O/'asap7-test-continuation-status.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(data),flush=True)
def main():
    assert (O/'test-preflight-correction-v1.json').is_file()
    status('collecting_frozen_independent_test_after_accounting_fix')
    command([sys.executable,'-B','-m','experiments.arithmetic_dse.model_collection','run','--out',B,'--splits','test','--selection-freeze',F])
    if (B/'PAUSE').exists():status('stopped_at_explicit_task_boundary');return
    test=O/'asap7-test-data-v1.json';result=O/'asap7-independent-test-v1/independent-test.json';release=O/'asap7-qualified-interval-v1'
    support('interval-asap7-independent-data-v1',sys.executable,'-B','-m','experiments.arithmetic_dse.model_mul_interval_fit','extract','--data',B,'--splits','test','--selection-freeze',F,'--out',test)
    status('evaluating_frozen_independent_test')
    support('interval-asap7-independent-test-v1',sys.executable,'-B','-m','experiments.arithmetic_dse.model_mul_interval_evaluation','test','--data',test,'--selection-freeze',F,'--out',result.parent)
    support('interval-asap7-independent-replay-v1',sys.executable,'-B','-m','experiments.arithmetic_dse.model_mul_interval_evaluation','verify','--selection-freeze',F,'--result',result)
    support('interval-asap7-release-v1',sys.executable,'-B','-m','experiments.arithmetic_dse.model_mul_interval_evaluation','publish','--selection-freeze',F,'--result',result,'--out',release)
    published=json.loads((release/'release.json').read_text())
    status('qualified_local_interval_model_native_closure_pending' if published['published'] else 'failed_independent_test_no_model_released',release=str(release))
if __name__=='__main__':
    try:main()
    except Exception as exc:status('stopped_on_error',reason=str(exc));raise
