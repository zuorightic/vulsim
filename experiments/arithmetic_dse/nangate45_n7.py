"""N7/N8: A-calibrated Nangate45 application evaluation; models stay frozen."""
import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from .nangate45_samples import ROOT, read, write, sha
from .nangate45_migration import SCOPE, software_root
from .nangate45_pipeline_runtime import load_package
from .nangate45_pipeline import rebind
from .workload_v10_replay import retarget
from .workload_demand import Graph
from .platforms import profile

VERSION='nangate45-three-application-N7-v2'
DEFAULT=ROOT.parent/'vulsim-artifacts/nangate45-applications-20261118-v2'
PACKAGE=ROOT/'experiments/arithmetic_dse/configs/nangate45_frozen_d_n56_v1.json'
POLICY=ROOT/'experiments/arithmetic_dse/configs/backend_policy_nangate45_app_v19.json'
AS_PRIORITY=ROOT.parent/'vulsim-artifacts/old-D-completion-priority-20261117-v1'


def now():return datetime.now(timezone.utc).isoformat()
def frozen(path,value):
    if Path(path).exists():
        if read(path)!=value:raise ValueError('frozen application identity differs: '+str(path))
    else:write(path,value)
    return value


def metadata(row,target):
    f=Path(row['folder']);state=read(f/'state.json');state['features']['sdc_period_ps']=target
    owners=retarget(rebind(read(f/'owners.json')),target)
    return Graph(read(row['graph'])),dict(placement=row['placement']),state,owners


def prepare(root):
    root=Path(root).resolve()
    if (root/'protocol.json').exists():return verify(root)
    root.mkdir(parents=True,exist_ok=True)
    from . import nangate45_n7_backend as physical
    from . import nangate45_n7_software as software
    prior=ROOT/'experiments/arithmetic_dse/configs/backend_policy_old_d_threads3_v16.json'
    resource=deepcopy(read(prior));resource.update(version=VERSION,revision_reason='User authorizes Nangate45 N7/N8 for MAC32/Add512/Mul128; A measured before target selection.')
    resource['resources']['memory_limit_MiB']=16384
    resource['application_authorization']=dict(at=now(),scope=SCOPE,threads=3,parallel_cap=3,global_cap=9,
        A_first=True,local_budget_before_tau=True,ABCD_records=39,model_refit=False,ASAP7_inputs_modified=False)
    frozen(POLICY,resource)
    rt=load_package(PACKAGE)
    inputs=[Path(__file__),Path(physical.__file__),Path(software.__file__),PACKAGE,POLICY,
        ROOT/'experiments/arithmetic_dse/workload_final_selection.py',ROOT/'experiments/arithmetic_dse/workload_latency_matrix.py',
        ROOT/'experiments/arithmetic_dse/workload_tight_equivalent.py',ROOT/'experiments/arithmetic_dse/workload_platform_entry.py',
        ROOT/'experiments/arithmetic_dse/nangate45_pipeline.py',ROOT/'experiments/arithmetic_dse/nangate45_pipeline_runtime.py',
        ROOT/'experiments/arithmetic_dse/nangate45_n7_cec.py',ROOT/'experiments/arithmetic_dse/model_m2_live_cec_v3.py',
        ROOT/'experiments/arithmetic_dse/configs/platforms/nangate45.json',
        ROOT/'experiments/arithmetic_dse/reference_assets/workload_minimum_period_v1.tcl']
    package=read(PACKAGE)
    inputs.extend((PACKAGE.parent/package[k]['path']).resolve() for k in ('arithmetic','state_shared','characterization','cell_cover'))
    pools={};initial=[]
    for case,depths in SCOPE.items():
        for depth in depths:
            path=software_root(case,depth)/case/'static-pool.json';pool=read(path);inputs.append(path)
            source=software_root(case,depth)/case/'source'
            inputs.extend(p for p in source.iterdir() if p.is_file())
            pools[f'{case}-L{depth}']=dict(path=str(path),sha256=sha(path),source=str(source))
            for row in pool['candidates']+[pool[k] for k in 'ABC']:
                inputs.extend([Path(row['graph']),*[Path(row['folder'])/name for name in ('workload.sv','state.json','owners.json')]])
        pool=read(pools[f'{case}-L{depths[0]}']['path']);a=pool['A']
        g,v,s,o=metadata(a,10000.);estimate=rt.evaluate(g,v,s,o)
        target=max(3000,int(math.ceil(1.25*estimate['critical_required_ps']/100)*100))
        initial.append(dict(case=case,row=a,period_ps=target,software_estimate_ps=estimate['critical_required_ps']))
        Graph.origins.cache_clear();Graph.roots.cache_clear()
    # MAC L3's additional frozen grammar/candidate views are prospective only.
    extra=ROOT.parent/'vulsim-artifacts/workload-equivalent-steps45-v1/search/native'
    if extra.exists():
        inputs.extend(extra.glob('*/inventory.json'))
        inputs.extend(extra.glob('*/graph.json'))
        for p in extra.glob('*/inventory.json'):
            for v in read(p)['views']:
                inputs.extend(p.parent/v['directory']/name for name in ('workload.sv','owners.json','state.json'))
    protocol=dict(version=VERSION,at=now(),scope=SCOPE,pools=pools,initial_A=initial,
        package=str(PACKAGE),package_sha256=sha(PACKAGE),profile_sha256=profile('nangate45')['profile_sha256'],
        target_rule='ceil50(1.25*A_Tmin/L), ceil50(1.5*A_Tmin/L); second at least first+50ps',
        initial_A_rule='max(3000,ceil100(1.25*new-model complete period at software-only 10000ps))',
        maximum_main_records=39,required_A=3,required_BCD=36,software_attributions=12,
        ABC_rule='reuse frozen ASAP7 RTL; platform/profile/ABC/SDC and physical evaluation are Nangate45',
        D_rule='frozen candidate/pressure/budget/inversion/ranking; new Nangate45 function package; no application feedback',
        physical_cap=3,threads=3,software_cap=2,extra_attribution_physical_tasks=0,
        files={str(p):sha(p) for p in sorted(set(inputs))})
    frozen(root/'protocol.json',protocol)
    for item in initial:
        selection=software.copy_selected(root,item['case'],1,item['period_ps'],'A',item['row'],None)
        admit(root,item['case'],1,item['period_ps'],[selection],reference=True)
    return protocol


def verify(root):
    d=read(Path(root)/'protocol.json')
    assert d['version']==VERSION and d['package_sha256']==sha(PACKAGE)
    for name,expected in d['files'].items():
        if sha(name)!=expected:raise ValueError('N7 frozen input changed: '+name)
    return d


def admit(root,case,L,target,selections,reference=False):
    root=Path(root);method_tag='A' if reference else ''.join(s['method'] for s in selections)
    grouped={}
    for s in selections:
        assert s['simulation_status']=='passed' and s['rtl_sha256']==sha(s['rtl'])
        grouped.setdefault(s['rtl_sha256'],[]).append(s)
    admitted=[]
    for digest,shared in grouped.items():
        folder=root/'backend'/f'matrix-nangate45-N7v2-{case}-L{L}-T{target}-{digest[:12]}'
        task_id=f'{case}-L{L}-T{target}-{digest[:12]}'
        if (folder/'admission.json').exists():
            old=read(folder/'admission.json')['tasks'][0]
            assert old['rtl_sha256']==digest and old['period_ps']==old['abc_target_ps']==target
            assert old['case']==case and old['L']==L and old['threads']==3
            for s in shared:
                frozen(root/'method-bindings'/f'{case}-L{L}-T{target}-{s["method"]}.json',dict(
                    case=case,L=L,T_ps=target,method=s['method'],batch=str(folder),task_id=task_id,rtl_sha256=digest,
                    selection_file=s['selection_file'],selection_sha256=sha(s['selection_file']),
                    existing_admission_sha256=sha(folder/'admission.json'),same_RTL_clock_profile_flow_and_threads=True))
            admitted.append(str(folder))
            continue
        memory=16384 if case=='mul128' else 4096
        task=dict(id=task_id,case=case,L=L,period_ps=target,abc_target_ps=target,methods=[s['method'] for s in shared],
            reference_A=reference,rtl=shared[0]['rtl'],rtl_sha256=digest,top='Workload',threads=3,memory_limit_MiB=memory,
            synth_timeout_s=1800 if case=='mul128' else 900,grt_timeout_s=7200 if case=='mul128' else 3600,
            support_timeout_s=600,selection_files=[s['selection_file'] for s in shared])
        files={str(root/'protocol.json'):sha(root/'protocol.json')}
        for s in shared:
            for name in ('workload.sv','state.json','owners.json','graph.json','view.json','functional-receipt.json','selection.json'):
                p=Path(s['rtl']).parent/name;files[str(p)]=sha(p)
        frozen(folder/'freeze.json',dict(version=VERSION,tasks=[task],files=files,application_PPA_for_selection=False))
        frozen(folder/'admission.json',dict(version=VERSION,id=folder.name,purpose='arithmetic_workload_final_comparison',
            role='final_evaluation',tasks=[task],freeze_sha256=sha(folder/'freeze.json'),policy_sha256=sha(POLICY),
            source_protocol_sha256=sha(root/'protocol.json'),threads_per_tool=3,automatic_retries=0,
            call_caps=dict(synth=1,grt=1,support=4)))
        admitted.append(str(folder))
    return admitted


def status(root):
    root=Path(root);doc=read(root/'protocol.json');from . import budget
    ledger=read(budget.LEDGER);claims={(j['admission_id'],j['task_id']):j for j in ledger['jobs']}
    physical=[]
    for p in sorted((root/'backend').glob('*/admission.json')):
        a=read(p)
        for task in a['tasks']:
            run=p.parent/'runs'/task['id'];outcome=run/'measurement-outcome.json';claim=claims.get((a['id'],task['id']))
            row=dict(task,batch=str(p.parent),run=str(run))
            row.update(read(outcome) if outcome.exists() else dict(status='running' if claim and claim['status'] in ('active','unsettled') else 'queued'))
            physical.append(row)
    for p in sorted((root/'method-bindings').glob('*.json')):
        binding=read(p);row=next(r for r in physical if r['batch']==binding['batch'] and r['id']==binding['task_id'])
        assert sha(Path(binding['batch'])/'admission.json')==binding['existing_admission_sha256']
        assert sha(binding['selection_file'])==binding['selection_sha256'] and row['rtl_sha256']==binding['rtl_sha256']
        if binding['method'] not in row['methods']:row['methods'].append(binding['method'])
    software=[]
    for case,depths in SCOPE.items():
        for L in depths:
            p=root/'software'/f'{case}-L{L}'/'software-status.json'
            software.append(dict(case=case,L=L,**(read(p) if p.exists() else dict(status='awaiting_A'))))
    ready=sum(r['status']=='completed' and r['reference_A'] for r in physical)
    measured=sum(len(r['methods']) for r in physical if r['status']=='completed' and not r['reference_A'])
    failures=[r for r in physical if r['status']=='failed']
    phase='completed' if ready==3 and measured==36 else 'needs_attention' if failures or any(s['status']=='error' for s in software) else 'running'
    result=dict(at=now(),version=VERSION,status=phase,scope=SCOPE,A_measured=ready,A_required=3,
        BCD_measured=measured,BCD_required=36,physical=physical,software=software,failures=failures,
        targets=[read(p) for p in sorted((root/'targets').glob('*.json'))],
        whole_setup_metric='full RR/IR/RO with 0.2T IO budget; ns converted to ps; threshold +/-0.1ps checked')
    write(root/'status.json',result)
    return result


def freeze_targets(root,case,A_run):
    root=Path(root);result=read(Path(A_run)/'clock-readout/result.json');A=result['full_setup_minimum_period_ps']
    records=[]
    for L in SCOPE[case]:
        pair=[int(math.ceil(f*A/L/50)*50) for f in (1.25,1.5)];pair[1]=max(pair[1],pair[0]+50)
        if not all(0<T<A for T in pair):raise ValueError('A-derived target does not improve on A')
        records.append(dict(case=case,L=L,targets_ps=pair,A_Tmin_ps=A,A_reference_run=str(A_run),
            A_reference_sha256=sha(Path(A_run)/'clock-readout/result.json'),factors=[1.25,1.5],quantum_ps=50,
            application_PPA_used_for_model=False,BCD_results_read_for_target=False))
    for r in records:frozen(root/'targets'/f'{case}-L{r["L"]}.json',r)
    return records


def _drive(root):
    root=Path(root);verify(root)
    from . import budget
    software_children={};physical_children={};attempts_path=root/'attempts.json'
    attempts=read(attempts_path) if attempts_path.exists() else dict(physical={},software={})
    while True:
        for kind,children in [('software',software_children),('physical',physical_children)]:
            for key,child in list(children.items()):
                if child.poll() is not None:
                    attempts[kind][key].update(exit_code=child.returncode,finished_at=now());del children[key]
        write(attempts_path,attempts)
        s=status(root)
        # MAC32 L2 is the first complete selection/physical integration pilot.
        mac_pilot=any(r['case']=='mac32' and r['L']==2 and not r['reference_A'] and 'D' in r['methods'] and r['status']=='completed' for r in s['physical'])
        for r in s['physical']:
            if r['reference_A'] and r['status']=='completed':freeze_targets(root,r['case'],r['run'])
        free=int(next(v.split()[1] for v in Path('/proc/meminfo').read_text().splitlines() if v.startswith('MemAvailable:')))//1024
        for case,depths in SCOPE.items():
            for L in depths:
                key=f'{case}-L{L}'
                if key in attempts['software'] or not (root/'targets'/f'{key}.json').exists():continue
                if not (case=='mac32' and L==2) and not mac_pilot:continue
                if len(software_children)>=2 or free<20480:break
                folder=root/'software-logs';folder.mkdir(exist_ok=True);logfile=folder/(key+'.log')
                with logfile.open('a') as log:
                    child=subprocess.Popen([sys.executable,'-B','-u','-m','experiments.arithmetic_dse.nangate45_n7_software','--root',str(root),'--case',case,'--L',str(L)],
                        cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
                        env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'))
                software_children[key]=child;attempts['software'][key]=dict(pid=child.pid,started_at=now(),log=str(logfile));free-=12288
        ledger=read(budget.LEDGER);active=[j for j in ledger['jobs'] if j['status'] in ('active','unsettled')]
        own=[j for j in active if j['admission_id'].startswith('matrix-nangate45-N7v2-')]
        claimed_ids={j['task_id'] for j in ledger['jobs'] if j['admission_id'].startswith('matrix-nangate45-N7v2-')}
        starting=sum(key not in claimed_ids for key in physical_children)
        if len(active)+starting<9 and len(own)+starting<3:
            candidates=[r for r in s['physical'] if r['status']=='queued' and r['id'] not in attempts['physical']]
            # A references first; then finish the selected MAC pilot, then groups
            # with more completed B/C/D records at their exact target.
            counts=Counter((r['case'],r['L'],r['period_ps']) for r in s['physical'] if r['status']=='completed')
            candidates.sort(key=lambda r:(not r['reference_A'],-counts[r['case'],r['L'],r['period_ps']],r['case']!='mac32',r['L'],r['period_ps'],r['methods']))
            for r in candidates:
                if free<r['memory_limit_MiB']+8192:continue
                logfile=root/'backend-logs'/(r['id']+'.log');logfile.parent.mkdir(exist_ok=True)
                with logfile.open('a') as log:
                    child=subprocess.Popen([sys.executable,'-B','-u','-m','experiments.arithmetic_dse.nangate45_n7_backend','--batch',r['batch'],'--task-id',r['id']],
                        cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
                        env=dict(os.environ,OMP_NUM_THREADS='3',OPENBLAS_NUM_THREADS='3'))
                physical_children[r['id']]=child;attempts['physical'][r['id']]=dict(pid=child.pid,started_at=now(),log=str(logfile));break
        write(attempts_path,attempts)
        status(root)
        if s['A_measured']==3 and s['BCD_measured']==36:return
        time.sleep(10)


def drive(root):
    import fcntl
    root=Path(root)
    with (root/'controller.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        write(root/'controller-start.json',dict(at=now(),pid=os.getpid()))
        return _drive(root)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('prepare','verify','drive','status'))
    p.add_argument('--root',type=Path,default=DEFAULT);a=p.parse_args()
    d=globals()[a.action](a.root)
    if a.action!='drive':print(json.dumps({k:v for k,v in d.items() if k in ('version','status','A_measured','BCD_measured','initial_A')},ensure_ascii=False,indent=2))
