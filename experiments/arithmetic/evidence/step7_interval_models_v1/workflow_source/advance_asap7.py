"""Sequential original admission; stop on any failure or validation rejection."""
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path.cwd();OUT=ROOT/'build/step7-intervals-20261103';BATCH=ROOT/'build/step7-models-20261102/native-interval-asap7-v4'
BASE=ROOT/'experiments/arithmetic/evidence/step7_models_v1/models'
FIT=OUT/'asap7-fit-v1';FITTING=OUT/'asap7-fitting-data-v1.json';TEST=OUT/'asap7-test-data-v1.json'
SUPPORT=ROOT/'build/step7-models-20261102/support.py'


def status(phase,**values):
    note={'phase':phase,**values,'full_step7_complete':False,'main_matrix_authorized':False}
    (OUT/'asap7-advance-status.json').write_text(json.dumps(note,indent=2)+'\n')
    print(json.dumps(note),flush=True)


def command(args):
    print('RUN',json.dumps(list(map(str,args))),flush=True)
    subprocess.run(list(map(str,args)),cwd=ROOT,check=True)


def support(stem,*args):command([sys.executable,SUPPORT,stem,900,*args])


def main():
    status('collecting_train_validation')
    command([sys.executable,'-B','-m','experiments.arithmetic_dse.model_collection','run','--out',BATCH,'--splits','train','validation'])
    if (BATCH/'PAUSE').exists():
        status('stopped_at_explicit_task_boundary');return
    status('extracting_complete_fitting_data')
    support('interval-complete-fitting-data-v1',sys.executable,'-B','-m','experiments.arithmetic_dse.model_mul_interval_fit','extract','--data',BATCH,'--splits','train','validation','--out',FITTING)
    if json.loads(FITTING.read_text())['failures']:raise ValueError('fitting collection is incomplete')
    status('fitting_and_validating')
    support('interval-asap7-fit-v1',sys.executable,'-B','-m','experiments.arithmetic_dse.model_mul_interval_fit','fit','--data',FITTING,'--base',BASE,'--out',FIT)
    report=json.loads((FIT/'asap7.fit.json').read_text())
    rejected={stage:[name for name,e in info['model']['intervals'].items() if not e['validation_ready']] for stage,info in report.items()}
    if rejected['grt']:
        status('failed_validation_test_not_run',rejected_intervals=rejected);return
    freeze=FIT/'selection-freeze.json'
    status('reproducing_frozen_fit',synth_validation_rejections=rejected['synth'])
    support('interval-asap7-reproduce-v1',sys.executable,'-B','-m','experiments.arithmetic_dse.model_mul_interval_evaluation','reproduce','--selection-freeze',freeze,'--base',BASE,'--out',OUT/'asap7-reproduced-fit-v1')
    status('collecting_independent_test_after_frozen_validation')
    command([sys.executable,'-B','-m','experiments.arithmetic_dse.model_collection','run','--out',BATCH,'--splits','test','--selection-freeze',freeze])
    if (BATCH/'PAUSE').exists():
        status('stopped_during_test_collection_at_task_boundary');return
    support('interval-asap7-independent-data-v1',sys.executable,'-B','-m','experiments.arithmetic_dse.model_mul_interval_fit','extract','--data',BATCH,'--splits','test','--selection-freeze',freeze,'--out',TEST)
    result=OUT/'asap7-independent-test-v1/independent-test.json'
    status('evaluating_frozen_independent_test')
    support('interval-asap7-independent-test-v1',sys.executable,'-B','-m','experiments.arithmetic_dse.model_mul_interval_evaluation','test','--data',TEST,'--selection-freeze',freeze,'--out',result.parent)
    support('interval-asap7-independent-replay-v1',sys.executable,'-B','-m','experiments.arithmetic_dse.model_mul_interval_evaluation','verify','--selection-freeze',freeze,'--result',result)
    release=OUT/'asap7-qualified-interval-v1'
    support('interval-asap7-release-v1',sys.executable,'-B','-m','experiments.arithmetic_dse.model_mul_interval_evaluation','publish','--selection-freeze',freeze,'--result',result,'--out',release)
    published=json.loads((release/'release.json').read_text())
    if not published['published']:
        status('failed_independent_test_no_model_released');return
    status('qualified_local_interval_model_native_closure_pending',release=str(release))


if __name__=='__main__':
    try:main()
    except Exception as exc:
        status('stopped_on_error',reason=str(exc));raise
