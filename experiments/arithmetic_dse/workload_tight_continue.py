"""Finite successor after the retained Montgomery reference-LEC timeout.

Prices, candidates, target factors and physical transformations are unchanged.
Only separately admitted Montgomery jobs use the sufficient buffer/size proof.
Independent completed cases can be measured before all software cases finish.
Outer subprocesses are dispatch only; physical leaves keep the common ledger.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from unittest.mock import patch

from .sampling_time_contract import ROOT
from .workload_abcd import read, write, sha
from .workload_contracts import load
from .workload_final_driver import final_tasks, report
from .workload_tight_run import DEFAULT, VERSION
from . import workload_final_backend as physical

SOURCE = Path(__file__).resolve()
PROXY = SOURCE.with_name('workload_kepler_proxy.py')
PROVER = SOURCE.with_name('workload_buffer_equivalence.py')
CASES = [c['id'] for c in load()['cases'] if c['id'] != 'mac32']
PROOF = ROOT.parent/'vulsim-artifacts/montgomery-cts-buffer-proof-v2'
SOFTWARE_CHILDREN = {}


def extend_admission(batch, *, repair=False):
    """Bind the dispatch and (when enabled) verifier before the first launch."""
    a = physical.verify(batch)
    if read(batch/'progress.json')['status'] != 'admitted':
        raise ValueError('extension must precede every physical attempt')
    paths = [SOURCE]
    extension = dict(version='tight-continuation-dispatch-v1', automatic_retries=0,
        physical_transformations_changed=False, wrapper=str(SOURCE),
        original_model_and_selector_unchanged=True, verification_override=None)
    if repair:
        result = read(PROOF/'result.json')
        if result['status'] != 'proven' or result['proof']['status'] != 'proven':
            raise ValueError('real predecessor repair proof required')
        before = DEFAULT/'A-reference/runs/montgomery256-A-reference/manifest.json'
        if read(before)['failure_reason'] != 'grt: timeout':
            raise ValueError('retained predecessor failure identity differs')
        paths += [PROXY, PROVER]
        extension['verification_override'] = dict(environment={'KEPLER_FORMAL_EXE':str(PROXY)},
            protocol='buffer-size-repair-proof-v1', timeout_s=300,
            sufficient_condition_only=True, fallback_on_failure=False,
            predecessor_manifest=str(before), predecessor_manifest_sha256=sha(before),
            predecessor_proof=str(PROOF/'result.json'), predecessor_proof_sha256=sha(PROOF/'result.json'),
            netlists_modified=False, unsupported_changes_fail_closed=True)
        paths += [before, PROOF/'result.json']
    extension['sources'] = {str(p):sha(p) for p in paths}
    write(batch/'dispatch-extension.json', extension)
    freeze = read(batch/'freeze.json')
    freeze['files'].update({str(p):sha(p) for p in paths+[batch/'dispatch-extension.json']})
    write(batch/'freeze.json',freeze)
    for p in [SOURCE]+([PROXY,PROVER] if repair else []):
        relative = str(p.relative_to(ROOT));a['sources'][relative] = sha(p)
        dest = batch/'measurement-source'/relative;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(p,dest)
    a.update(freeze_sha256=sha(batch/'freeze.json'),dispatch_extension_sha256=sha(batch/'dispatch-extension.json'))
    write(batch/'admission.json',a)
    physical.verify(batch)


def prepare_reference(root):
    batch = root/'A-reference-repair-v1'
    if batch.exists():
        physical.verify(batch)
        return batch
    original = physical.verify(root/'A-reference')
    task = dict(next(t for t in original['tasks'] if t['case']=='montgomery256'))
    task.update(id='montgomery256-A-reference-repair-v1',
        predecessor_batch=str(root/'A-reference'),predecessor_task='montgomery256-A-reference',
        verification_protocol='buffer-size-repair-proof-v1',physical_transformations_changed=False)
    physical.admit(batch,[task],'clock_calibration')
    extend_admission(batch,repair=True)
    return batch


def execute_task(batch, task_id):
    batch = Path(batch).resolve();a = physical.verify(batch)
    if a['dispatch_extension_sha256'] != sha(batch/'dispatch-extension.json'):
        raise ValueError('dispatch extension changed')
    extension = read(batch/'dispatch-extension.json')
    task = next(t for t in a['tasks'] if t['id']==task_id)
    override = extension['verification_override']
    if override:
        if task['case'] != 'montgomery256':raise ValueError('repair verifier outside declared case')
        os.environ.update(override['environment'])
    elif os.environ.get('KEPLER_FORMAL_EXE') == str(PROXY):
        raise ValueError('undeclared verifier inherited by ordinary task')
    with patch.object(physical.predecessor,'verify_admission',physical.verify_admission):
        physical.run_task(batch,task)
    if override:
        out = batch/'runs'/task_id
        proofs = list((out/'logs').rglob('4_rsz_lec_check.proof.json'))
        if len(proofs)!=1:raise ValueError('actual CTS verifier receipt missing or ambiguous')
        p=proofs[0];r=read(p)
        if (r['status']!='proven' or r['verifier_sha256']!=sha(PROXY) or
                r['prover_sha256']!=sha(PROVER) or r['physical_netlists_modified']):
            raise ValueError('actual repair proof identity differs')
        for source,h in r['inputs_sha256'].items():
            if sha(source)!=h:raise ValueError('actual repair proof input changed')
        write(out/'verification-receipt.json',dict(status='proven',
            protocol=override['protocol'],proof=str(p),proof_sha256=sha(p),
            dispatch_extension_sha256=sha(batch/'dispatch-extension.json'),
            actual_ORFS_consumption_checked=True,netlists_modified=False))
    return task_id


def launch(batch, task):
    command=[sys.executable,'-m','experiments.arithmetic_dse.workload_tight_continue',
             'task','--root',str(batch),'--task-id',task['id']]
    log=batch/'dispatch-logs'/(task['id']+'.log');log.parent.mkdir(exist_ok=True)
    with log.open('w') as stream:
        r=subprocess.run(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
    if r.returncode:raise RuntimeError('physical child failed; see '+str(log))


def drive(batches, on_settlement=None):
    tasks=[];progress={}
    for batch in batches:
        a=physical.verify(batch);p=read(batch/'progress.json')
        if p['status']=='batch_settled':continue
        if p['active']:raise ValueError('successor batch already active')
        attempted=set(p['completed'])|{e['task'] for e in p['errors']}
        pending=[t for t in a['tasks'] if t['id'] not in attempted]
        if any((batch/'runs'/t['id']).exists() for t in pending):
            raise ValueError('unsettled physical attempt cannot be restarted')
        p.update(status='running',active=[t['id'] for t in pending]);progress[batch]=p
        write(batch/'progress.json',p);tasks.extend((batch,t) for t in pending)
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures={pool.submit(launch,b,t):(b,t) for b,t in tasks}
        for f in as_completed(futures):
            batch,t=futures[f];p=progress[batch]
            try:
                f.result();p['completed'].append(t['id']);print('PHYSICAL_PASS '+t['id'],flush=True)
            except Exception as error:
                p['errors'].append(dict(task=t['id'],reason=str(error)))
                print('PHYSICAL_FAIL '+t['id']+' '+str(error),flush=True)
            p['active'].remove(t['id'])
            if not p['active']:p['status']='batch_settled'
            write(batch/'progress.json',p)
            if on_settlement is not None:on_settlement()


def freeze_reference_target(root):
    batch=root/'A-reference-repair-v1';task=physical.verify(batch)['tasks'][0]
    p=batch/'runs'/task['id']/'clock-readout/result.json'
    if not p.exists():return False
    receipt=p.parents[1]/'verification-receipt.json'
    if not receipt.exists() or read(receipt)['status']!='proven':
        raise ValueError('Montgomery reference has no consumed repair proof')
    r=read(p);case=next(c for c in load()['cases'] if c['id']=='montgomery256')
    L=case['formal_targets'][0]['L'];A=r['full_setup_minimum_period_ps']
    raw=[A/L*f for f in (1.25,1.5)];targets=[math.ceil(t/50)*50 for t in raw]
    targets[1]=max(targets[1],targets[0]+50)
    if not all(0<t<A for t in targets):raise ValueError('invalid measured A/L target')
    value=dict(case='montgomery256',L=L,targets_ps=targets,raw_target_ps=raw,
        A_reference_Tmin_ps=A,A_reference_request_ps=task['period_ps'],ideal_A_over_L_ps=A/L,
        factors=[1.25,1.5],quantum_ps=50,role='A_clock_calibration_only',
        reference_batch=str(batch),reference_task=task['id'],clock_readout_sha256=sha(p),
        verification_receipt_sha256=sha(receipt),predecessor_failure_retained=True,
        application_PPA_for_model=False,final_D_PPA_for_clock=False)
    dest=root/'targets/montgomery256.json'
    if dest.exists() and read(dest)!=value:raise ValueError('reference target changed')
    if not dest.exists():write(dest,value)
    print('TIGHT_TARGETS montgomery256 '+str(targets)+' A='+str(A),flush=True)
    return True


def publish_report(root):
    batches=['final-mac32']+[f'final-{cid}' for cid in CASES if (root/f'final-{cid}').exists()]
    return report(root,batches)


def start_reference_selection(root):
    if not freeze_reference_target(root):return
    if (root/'software/montgomery256/final-selections.json').exists():return
    isolated=root/'parallel-software/montgomery256'
    if (isolated/'selection-dispatch.json').exists():return
    isolated.mkdir(parents=True,exist_ok=True)
    command=[sys.executable,'-m','experiments.arithmetic_dse.workload_tight_parallel',
        'watch','--root',str(root),'--case','montgomery256']
    with (isolated/'selection-controller.log').open('w') as log:
        child=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
    SOFTWARE_CHILDREN['montgomery256']=child
    write(isolated/'selection-dispatch.json',dict(command=command,pid=child.pid,EDA_calls=0))


def run(root):
    root=Path(root).resolve()
    for name in ('final-mac32','A-reference'):
        if read(root/name/'progress.json')['status']!='batch_settled':
            raise ValueError('predecessor must settle before successor starts')
    record=root/'continuation-start.json'
    if record.exists():raise ValueError('finite continuation has already been launched')
    write(record,dict(version='tight-continuation-v1',source_sha256=sha(SOURCE),cases=CASES,
        previous_A_failure_retained=True,target_rule_unchanged=True,
        no_application_PPA_for_selection=True,automatic_retries=0,parallel_physical_jobs=3))
    remaining=list(CASES);reference=prepare_reference(root);first=True
    while remaining:
        batches=[reference] if first else [];first=False
        for cid in list(remaining):
            if not (root/'software'/cid/'final-selections.json').exists():continue
            batch=final_tasks(root,[cid],'final-'+cid)
            extend_admission(batch,repair=cid=='montgomery256')
            batches.append(batch);remaining.remove(cid)
        if batches:
            drive(batches,lambda:start_reference_selection(root));publish_report(root)
        start_reference_selection(root)
        for cid,child in SOFTWARE_CHILDREN.items():
            if child.poll() not in (None,0):raise RuntimeError('isolated software selection failed: '+cid)
        if 'montgomery256' in remaining and read(reference/'progress.json')['errors']:
            raise RuntimeError('retained successor reference failure; cannot invent Montgomery targets')
        if remaining and not batches:time.sleep(10)
    rows=[read(root/'targets'/(c['id']+'.json')) for c in load()['cases']]
    write(root/'target-matrix.json',dict(version=VERSION,rows=rows,
        groups=sum(len(r['targets_ps']) for r in rows),user_confirmed=True,clock_basis='unsplit_A',
        factors=[1.25,1.5],quantum_ps=50,no_C_based_clock_relaxation=True,
        application_PPA_for_model=False,final_D_PPA_for_clock=False))
    return publish_report(root)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['run','task','report'])
    p.add_argument('--root',type=Path,default=DEFAULT);p.add_argument('--task-id');a=p.parse_args()
    result=run(a.root) if a.action=='run' else execute_task(a.root,a.task_id) if a.action=='task' else publish_report(a.root)
    if isinstance(result,dict):print({k:result[k] for k in ('main_records','main_measured','physical_comparison_complete')})
    else:print(result)
