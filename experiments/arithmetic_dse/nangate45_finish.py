"""Sequential, stop-on-error completion after the running N3 train worker.

This driver never retries a physical leaf or starts another train worker. It
waits for its named finite predecessor, then collects validation, freezes N4,
collects the sealed test, evaluates and emits small evidence.
"""
import argparse
from contextlib import redirect_stdout,redirect_stderr
import fcntl
import json
from pathlib import Path
import time
import traceback

from .nangate45_samples import ROOT,read,write,sha,verify
from .nangate45_collect import run as collect
from .nangate45_response_features import run as fit
from .nangate45_artifacts import export
from .nangate45_verify import software,receipts
from .nangate45_report import report


def run(root,out):
    root=Path(root).resolve();out=Path(out).resolve();a=verify(root)
    train={t['id'] for t in a['tasks'] if t['role']=='train'}
    if (root/'finish-status.json').exists():raise ValueError('finish driver already attempted; preserve prior evidence')
    with (root/'finish.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        status=dict(phase='waiting_for_named_train_worker',implementation_sha256=sha(__file__),automatic_retries=0)
        write(root/'finish-status.json',status)
        with (root/'finish.log').open('x') as log,redirect_stdout(log),redirect_stderr(log):
            try:
                while True:
                    p=read(root/'progress.json')
                    if p['errors']:raise ValueError('named train worker stopped; no automatic continuation')
                    if train<=set(p['completed']):break
                    time.sleep(1)
                for name,action in (
                    ('collecting_validation',lambda:collect(root,'validation')),
                    ('fitting_and_freezing',lambda:fit(root,'freeze')),
                    ('collecting_sealed_test',lambda:collect(root,'test')),
                    ('evaluating_sealed_test',lambda:fit(root,'evaluate')),
                    ('exporting_small_model',lambda:export(root,out/'model.json')),
                    ('verifying',lambda:write(root/'verification.json',dict(software=software(root,out/'model.json'),receipts=receipts(root)))),
                    ('writing_small_evidence',lambda:report(root,out))):
                    status['phase']=name;write(root/'finish-status.json',status)
                    print(name,flush=True);action();log.flush()
                status.update(phase='completed',test_gates_passed=read(root/'evaluation.json')['arithmetic_test_gates_passed'],full_D_ready=False)
            except Exception as e:
                status.update(phase='stopped_on_error',error=str(e));traceback.print_exc(file=log);raise
            finally:write(root/'finish-status.json',status)
    return status


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();print(json.dumps(run(a.root,a.out),indent=2))
