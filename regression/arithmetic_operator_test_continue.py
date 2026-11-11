"""Exercise independent-only continuation transitions without EDA/test labels."""
import argparse
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha
from experiments.arithmetic_dse import operator_condition_v2_continue as controller


def check(out):
    if out.exists():raise ValueError('preserve prior proof')
    checks=[]
    with TemporaryDirectory(prefix='independent-resume-test-') as temporary:
        for case in ('complete','reviewed_stop','unknown_stop','exhausted','changed_freeze','bounded'):
            root=Path(temporary)/case;root.mkdir();work=root/'work';selection=root/'fit-v2/selection-freeze.json'
            write(selection,dict(immutable=True));original=sha(selection)
            write(root/'v2-work-status.json',dict(phase='stopped_preserve_failure',producer_sha256='original-frozen-controller'))
            write(root/'progress.json',dict(phase='stopped_on_error',current_batch='batch-017',errors=['original_acquisition_failure']))
            audit=root/'audit.json';write(audit,dict(status='passed_refusal_audit',selection_sha256=original if case!='changed_freeze' else 'forged',
                remaining_original_batch_allowance=0 if case=='exhausted' else 16))
            calls=[];checkpoints=[];sealed=[];closed=[]
            def collect(r,mode,selection,max_batches):
                assert r==root and mode=='independent' and sha(selection)==original
                calls.append(('collection',max_batches))
                if case=='unknown_stop':raise ValueError('unknown ownership/CEC failure')
                if case=='reviewed_stop' and len(calls)==1:
                    write(root/'progress.json',dict(phase='stopped_on_error',current_batch='batch-018',errors=['original_acquisition_failure','new_acquisition_failure']))
                    raise ValueError('batch failure preserved; explicit diagnosis before continuation')
                write(root/'progress.json',dict(phase='independent_bounded_batch_complete' if case=='bounded' else 'independent_collection_complete',
                    errors=['original_acquisition_failure']))
            support_calls=[]
            def support(w,name,command,timeout):
                support_calls.append(name)
                if name.startswith('independent-stop-audit-'):
                    dest=Path(command[command.index('--out')+1]);write(dest,dict(status='passed_refusal_audit',selection_sha256=original,remaining_original_batch_allowance=15))
                if name=='v2-test-evaluate':write(root/'test-v2/independent-test.json',dict(status='failed_independent'))
            def checkpoint(*args):checkpoints.append(True)
            def finish(*args):sealed.append(True)
            def close(*args):closed.append(True)
            error=None
            with patch.object(controller.wide,'validate_admission'),patch.object(controller.wide,'verify_selection'),patch.object(controller.wide,'run',collect),\
                 patch.object(controller,'checkpoint',checkpoint),patch.object(controller.stages,'support',support),\
                 patch.object(controller,'finish',finish),patch.object(controller,'close_resources',close):
                try:controller.run(root,work,root/'evidence',audit)
                except ValueError as e:error=str(e)
            assert sha(selection)==original,'frozen model changed'
            assert not any('fit' in n or 'freeze' in n for n in support_calls),'fitting relaunched'
            if case in ('complete','reviewed_stop'):
                assert error is None and read(root/'v2-work-status.json')['phase']=='failed_independent' and len(sealed)==1
                assert support_calls.count('v2-test-extract')==support_calls.count('v2-test-evaluate')==1
                assert calls==([('collection',16),('collection',15)] if case=='reviewed_stop' else [('collection',16)])
                assert len(checkpoints)==(2 if case=='reviewed_stop' else 1)
            elif case=='bounded':
                assert error is None and not sealed and not support_calls
                assert read(root/'v2-work-status.json')['phase']=='bounded_independent_still_pending'
            else:
                assert error is not None and not sealed and 'v2-test-evaluate' not in support_calls
                assert len(calls)==(1 if case=='unknown_stop' else 0)
            checks.append(dict(case=case,passed=True,collection_calls=len(calls),evaluation_calls=support_calls.count('v2-test-evaluate'),error=error))
    write(out,dict(status='passed_independent_continuation_state_checks',cases=checks,new_EDA_calls=0,physical_test_labels_read=False,
        guarantees=['no fitting/refreeze','original batch allowance decreases','known stop reviewed before continuation','unknown stop halts',
            'changed freeze blocks launch','once-only terminal evaluation','acquisition failure verdict preserved','bounded completion never promoted'],full_D_ready=False))
    print(dict(status='passed_independent_continuation_state_checks',cases=len(checks),new_EDA_calls=0),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();check(a.out.resolve())
