"""Resume only the frozen v2 independent acquisition, then evaluate once.

The original fitting/inference/evaluation implementations remain immutable.
Source stops retain their failed gates; this controller never retries a point.
"""
import argparse
from pathlib import Path
import shutil
import sys

from .model_fast_preflight import read,write,sha
from . import operator_stage4 as stages,operator_condition_wide as wide
from .operator_condition_v2_finish import finish,close_resources

ROOT=Path(__file__).resolve().parents[2]


def checkpoint(root,work):
    attempts=root/'controller-attempts';attempts.mkdir(exist_ok=True)
    number=1
    while (attempts/f'attempt-{number:03d}').exists():number+=1
    dest=attempts/f'attempt-{number:03d}';dest.mkdir()
    for name in ('progress.json','v2-work-status.json','v2-evidence-status.json','v2-work-resource-closure.json','test-acquisition-v2.json'):
        if (root/name).exists():shutil.copy2(root/name,dest/name)
    for path in root.glob('independent-stop-audit-*.json'):shutil.copy2(path,dest/path.name)
    for path in (Path(__file__),ROOT/'regression/arithmetic_operator_test_stop.py'):shutil.copy2(path,dest/path.name)
    write(dest/'continuation.json',dict(version='operator-v2-frozen-independent-continuation-v1',
        producer_sha256=sha(Path(__file__)),selection_sha256=sha(root/'fit-v2/selection-freeze.json'),
        failed_points_and_source_roles_retained=True,no_fitting_or_domain_retuning=True,full_D_ready=False))
    stages.support(work,'independent-checkpoint-'+str(number),[sys.executable,'-B','-m','experiments.arithmetic_dse.operator_condition_v2_continue','archive','--root',str(root),'--checkpoint',str(dest)],180)
    return dest


def run(root,work,evidence,audit):
    wide.validate_admission(root);selection=root/'fit-v2/selection-freeze.json';wide.verify_selection(root/'corpus',selection)
    initial=read(audit)
    if initial['status']!='passed_refusal_audit' or initial['selection_sha256']!=sha(selection):raise ValueError('reviewed independent stop required')
    if (root/'test-v2').exists() or (root/'test-data.json').exists():raise ValueError('independent extraction/evaluation already started; preserve it')
    prior=read(root/'v2-work-status.json')
    if prior['phase']!='stopped_preserve_failure':raise ValueError('expected fully settled stopped worker')
    checkpoint(root,work)
    producer=sha(Path(__file__))
    def state(phase,**values):
        stages.atomic(root/'v2-work-status.json',dict(version='operator-v2-work-status-v1',phase=phase,root=str(root),work=str(work),
            producer_sha256=prior['producer_sha256'],continuation_producer_sha256=producer,full_D_ready=False,**values))
        print('V2_CONTINUATION '+phase,flush=True)
    def support(name,args,timeout=300):return stages.support(work,name,[sys.executable,'-B']+args,timeout)
    stages.atomic(root/'v2-evidence-status.json',dict(phase='waiting_for_frozen_independent_continuation',full_D_ready=False))
    try:
        while True:
            wide.verify_selection(root/'corpus',selection)
            review=read(audit);remaining=review['remaining_original_batch_allowance']
            state('frozen_independent_collection',selection=str(selection),remaining_original_batches=remaining,review_sha256=sha(audit))
            if remaining<=0:raise ValueError('original finite independent batch envelope exhausted')
            try:wide.run(root,'independent',selection=selection,max_batches=remaining)
            except ValueError as error:
                if str(error)!='batch failure preserved; explicit diagnosis before continuation':raise
                progress=read(root/'progress.json');batch=progress['current_batch']
                # Review actual evidence before each continuation. Unknown
                # errors, broken CEC or changed scopes terminate the worker.
                audit=root/('independent-stop-audit-'+batch+'.json')
                support('independent-stop-audit-'+batch,['regression/arithmetic_operator_test_stop.py','--root',str(root),'--selection',str(selection),'--out',str(audit)],180)
                state('stopped_preserve_failure',error=str(error),physical_progress=progress['phase'],review=str(audit))
                close_resources(root,work,Path('/nonexistent-v2-evidence'))
                checkpoint(root,work)
                continue
            break
        if read(root/'progress.json')['phase']!='independent_collection_complete':
            state('bounded_independent_still_pending',selection=str(selection));close_resources(root,work,Path('/nonexistent-v2-evidence'));return
        if sha(Path(__file__))!=producer:raise ValueError('running continuation implementation changed')
        state('independent_extract_and_evaluate_once')
        support('v2-test-extract',['-m','experiments.arithmetic_dse.operator_condition_fit_v2','extract','--root',str(root),'--mode','independent',
            '--selection',str(selection),'--out',str(root/'test-data.json')],900)
        support('v2-test-evaluate',['-m','experiments.arithmetic_dse.operator_condition_fit_v2','test','--data',str(root/'test-data.json'),
            '--selection',str(selection),'--out',str(root/'test-v2')],300)
        report=read(root/'test-v2/independent-test.json')
        state(report['status'],independent_report=str(root/'test-v2/independent-test.json'),model=str(root/'test-v2/tested-model.json'))
        finish(root,work,evidence,60)
    except Exception as error:
        state('stopped_preserve_failure',error=str(error),physical_progress=read(root/'progress.json')['phase'])
        close_resources(root,work,Path('/nonexistent-v2-evidence'))
        stages.atomic(root/'v2-evidence-status.json',dict(phase='continuation_stopped_preserve_failure',error=str(error),full_D_ready=False))
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('run','archive'))
    for n in ('root','work','evidence','audit','checkpoint'):p.add_argument('--'+n,type=Path)
    a=p.parse_args()
    if a.action=='archive':stages.archive(a.root.resolve(),[a.checkpoint.resolve()],a.checkpoint.name+'-independent-stop.tar.gz')
    else:run(a.root.resolve(),a.work.resolve(),a.evidence.resolve(),a.audit.resolve())
