"""Finite fresh independent evidence after a frozen ownership-reader repair.

Four new whole sources, sixteen fixed source/T requests. No fitting, reserve or
support change; old independent results remain separate and retain failures.
"""
import argparse
from copy import deepcopy
from pathlib import Path
import shutil
import sys
import time

from .model_fast_preflight import read,write,sha,key
from . import operator_collection as collection,operator_stage4 as stages,model_sampling_v2 as samples
from . import model_logical_qualification_v1 as qualification,operator_condition_model as model
from . import model_logical_stage_v1,model_logical_labels_v1,model_logical_ownership_v1,model_logical_ownership_v2
from . import operator_ownership_replay_v1,operator_ownership_replay_v2
from .budget import Ledger,usage,POLICY

ROOT=Path(__file__).resolve().parents[2]
CLOCKS=(500,1000,1500,3000)


def sources():
    rows=[]
    for op,a,b,r,shift,zero in [('mul',10,14,24,12,'0x0'),('mul',14,18,32,8,'0x0'),('add',24,40,41,0,'0xff'),('add',40,56,57,0,'0x0')]:
        f=collection.canonical_features(dict(producer=dict(operation=op,lhs_width=a,rhs_width=b,result_width=r,rhs_zero_hex=zero),
            consumers=[dict(spec=dict(operation='add',lhs_width=64,rhs_width=64,result_width=64,lhs_zero_hex=hex(((1<<64)-1)^(((1<<r)-1)<<shift))),
                bindings=[dict(operand_index=0,result_bit_map=['0']*shift+list(range(r))+['0']*(64-r-shift))],
                other_dynamic_inputs='independent_launch; source correlations require G validation')],captures=[]))
        signature=key(f);rows.append(dict(id='s'+signature[:16],source_group=signature,role='locked_test',features=f,
            purpose='fresh independent evidence for frozen reader and unchanged conditional function',boundary_policy='unsigned-op-hierarchy-v1'))
    return rows


def prepare(out,node_root,recovery):
    if out.exists():raise ValueError('preserve successor version')
    if read(recovery/'qualification.json')['status']!='passed_saved_snapshot_qualification':raise ValueError('reader qualification required')
    if read(recovery/'all-fitting-labels.json')['status']!='passed_all_fitting_labels_unchanged':raise ValueError('full original fitting identity required')
    out.mkdir(parents=True);(out/'restore').mkdir();rows=sources();old=read(node_root/'corpus/manifest.json')
    forbidden={r['source_group'] for r in old['sources']}
    if any(r['source_group'] in forbidden for r in rows):raise ValueError('fresh source collides with prior role')
    candidate=node_root/'fit-v2/candidate.json';frozen=read(candidate)
    if sha(candidate)!=read(node_root/'fit-v2/selection-freeze.json')['model_sha256']:raise ValueError('node candidate changed')
    tasks=[]
    for r in rows:
        d=out/'sources'/r['id'];d.mkdir(parents=True);rtl=d/'input.sv';rtl.write_text(samples.source(r['features']));write(d/'contract.json',samples.geometry_contract(r['features']))
        r.update(rtl=str(rtl),rtl_sha256=sha(rtl))
        for t in CLOCKS:
            answer=model.query(frozen,collection.descriptor(r,t),True)
            if answer['status']!='covered':raise ValueError('prospective independent source outside unchanged model support: '+str(answer))
            tasks.append(dict(id=r['id']+'-T'+str(t),source_id=r['id'],source_role='locked_test',period_ps=t,features=r['features'],rtl=str(rtl),rtl_sha256=sha(rtl)))
    names=set(collection.measurement_sources())|set(read(recovery/'protocol.json')['implementation'])
    names.update(str(Path(m.__file__).relative_to(ROOT)) for m in (qualification,model_logical_stage_v1,model_logical_labels_v1,
        model_logical_ownership_v1,model_logical_ownership_v2,operator_ownership_replay_v1,operator_ownership_replay_v2))
    names.add(str(Path(__file__).relative_to(ROOT)))
    names.add('regression/arithmetic_operator_ownership.py');names.add('regression/arithmetic_operator_ownership_dataset.py')
    manifest=read(node_root/'fit-v2/selection-freeze.json');names.update(manifest['implementation_sources'])
    hashes={n:sha(ROOT/n) for n in sorted(names)}
    for name,h in hashes.items():
        dest=out/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest)
    shutil.copy2(candidate,out/'frozen-function.json')
    write(out/'sources.json',dict(version='operator-ownership-fresh-independent-sources-v1',sources=rows))
    write(out/'admission.json',dict(version='logical-ownership-independent-physical-admission-v1',id=out.name,tasks=tasks,source_sha256=hashes,
        physical_training_admitted=True,physical_admission_allowed=False,synth_timeout_s=300,grt_timeout_s=1200,support_max=384,
        role='locked_test',source_group_rule='all clocks/stages of each complete source stay locked_test; no retuning',max_synth=16,max_grt=16,max_concurrent_tasks=1,
        model_sha256=sha(candidate),parent_selection_sha256=sha(node_root/'fit-v2/selection-freeze.json'),
        reader_qualification_sha256=sha(recovery/'qualification.json'),all_fitting_labels_sha256=sha(recovery/'all-fitting-labels.json'),
        parent_collection=str(node_root),recovery_root=str(recovery),
        later_work_reserved=dict(synth=688,grt=688,walltime_s=86400,CPU_time_s=172800,storage_bytes=32212254720),
        independent_acceptance=dict(delay_area_source_macro_median_max=.15,delay_area_source_macro_P95_max=.35,
            all_source_target_coverage_required=True,acquisition_failures_allowed=0,exact1000ps_separately=True,
            unchanged_frozen_parameters_domain_reserve_required=True,new_test_cannot_erase_old_test_failures=True),
        first_failure='stop whole source and retain paid points; do not retry; other admitted sources may continue',
        full_D_ready=False))
    write(out/'progress.json',dict(phase='prepared_software_pending',completed=[],failures=[],full_D_ready=False))
    print(dict(status='prepared_fresh_successor',sources=4,source_targets=16,physical_admission_allowed=False),flush=True)


def admit(out,software):
    a=read(out/'admission.json');rows=read(out/'sources.json')['sources']
    if a['physical_admission_allowed']:raise ValueError('admission already released')
    for n,h in a['source_sha256'].items():
        if sha(ROOT/n)!=h or sha(out/'source'/n)!=h:raise ValueError('successor implementation changed')
    logs={name:read(software/name/'commands.json')[0] for name in ('generate','iverilog','simulate')}
    if any(r['exit_code'] for r in logs.values()) or 'INDEPENDENT_OBSERVERS_PASS sources=4 cycles=128' not in Path(logs['simulate']['log']).read_text():raise ValueError('software shell proof missing')
    for r in rows:
        path=software/'generated/sources'/r['id']/'input.sv'
        if sha(path)!=r['rtl_sha256']:raise ValueError('software and admitted source differ')
    a.update(physical_admission_allowed=True,software_proof={str(software/name/'commands.json'):sha(software/name/'commands.json') for name in logs})
    write(out/'admission.json',a);stages.atomic(out/'progress.json',dict(phase='admitted_waiting_for_parent',completed=[],failures=[],full_D_ready=False))


def run(out,max_wait=7200):
    a=read(out/'admission.json')
    if not a['physical_admission_allowed']:raise ValueError('software admission required')
    parent=Path(a['parent_collection']);started=time.monotonic()
    while True:
        phase=read(parent/'v2-work-status.json')['phase']
        if phase in ('isolated_functions_passed','failed_independent'):break
        if phase in ('stopped_preserve_failure','bounded_independent_still_pending','validation_failed_test_locked'):raise ValueError('parent not fully evaluated; preserve successor waiting')
        if time.monotonic()-started>max_wait:raise ValueError('bounded parent wait elapsed; successor unchanged')
        time.sleep(15)
    if sha(parent/'fit-v2/candidate.json')!=a['model_sha256'] or sha(parent/'fit-v2/selection-freeze.json')!=a['parent_selection_sha256']:raise ValueError('parent numerical freeze changed')
    if not (parent/'test-v2/independent-test.json').exists():raise ValueError('parent verdict not available')
    policy=read(POLICY)['resources'];u=usage(read(Ledger().path)['entries']);later=a['later_work_reserved'];n=len(a['tasks'])
    if (u['synth']+n+later['synth']>policy['max_synthesis_calls'] or u['grt']+n+later['grt']>policy['max_global_route_calls']
        or u['walltime_s']+2940*n+later['walltime_s']>policy['max_global_walltime_h']*3600
        or u['CPU_time_s']+11760*n+later['CPU_time_s']>policy['max_tool_CPU_time_h']*3600
        or shutil.disk_usage(out).free<later['storage_bytes']+n*391451120+1024**3):raise ValueError('fresh finite independent tasks not funded')
    progress=read(out/'progress.json')
    if progress['completed'] or progress['failures']:raise ValueError('successor already started, preserve checkpoint')
    stages.atomic(out/'progress.json',dict(progress,phase='running',parent_verdict=phase))
    failed=set()
    for task in a['tasks']:
        if task['source_id'] in failed:continue
        progress.update(phase='running',current_task=task['id']);stages.atomic(out/'progress.json',progress)
        try:qualification.task_run(out,task)
        except Exception as error:
            failed.add(task['source_id']);progress['failures'].append(dict(task=task['id'],source=task['source_id'],reason=str(error)))
            print('FRESH_INDEPENDENT_FAILED '+task['id']+' '+str(error),flush=True)
        else:progress['completed'].append(task['id']);print('FRESH_INDEPENDENT_COMPLETE '+task['id'],flush=True)
        stages.atomic(out/'progress.json',progress)
        stages.support(out,'archive-'+task['id'],[sys.executable,'-B','-m','experiments.arithmetic_dse.operator_ownership_successor_v1','archive',
            '--out',str(out),'--task',task['id']],300)
    stages.atomic(out/'progress.json',dict(progress,phase='collection_complete'))
    stages.support(out,'independent-evaluation',[sys.executable,'-B','-m','experiments.arithmetic_dse.operator_ownership_successor_v1','evaluate','--out',str(out)],180)


def evaluate(out):
    if (out/'independent-evaluation-consumed.json').exists():raise ValueError('fresh test already evaluated')
    a=read(out/'admission.json');frozen=read(out/'frozen-function.json');sources={r['id']:r for r in read(out/'sources.json')['sources']};rows=[];failures=read(out/'progress.json')['failures']
    from .operator_condition_fit import metrics
    for task in a['tasks']:
        path=out/'runs'/task['id']/'grt-labels.json'
        if not path.exists():continue
        label=read(path)
        if not label['physical_training_label_eligible'] or label['source_role']!='locked_test':raise ValueError('fresh label qualification differs')
        descriptor=collection.descriptor(sources[task['source_id']],task['period_ps'])
        rows.append(dict(source_id=task['source_id'],target_ps=task['period_ps'],operation=descriptor['local_context']['producer']['operation'],
            descriptor=descriptor,features=model.features(descriptor),operator_delay_ps=label['operator_delay_ps'],comb_area_um2=label['comb_area_um2'],label_sha256=sha(path)))
    write(out/'independent-evaluation-consumed.json',dict(model_sha256=a['model_sha256'],source_manifest_sha256=sha(out/'sources.json'),permanently_excluded_from_future_fitting=True))
    reports={}
    for op,entry in frozen['operations'].items():
        group=[r for r in rows if r['operation']==op];sub=[r for r in group if r['target_ps']==1000]
        stats={label:metrics(group,entry[label],field,floor) for label,field,floor in (('delay','operator_delay_ps',10.),('area','comb_area_um2',.01))}
        exact={label:metrics(sub,entry[label],field,floor) for label,field,floor in (('delay','operator_delay_ps',10.),('area','comb_area_um2',.01))}
        refused=[dict(source=r['source_id'],T=r['target_ps'],reason=model.query(frozen,r['descriptor'],True).get('reason')) for r in group if model.query(frozen,r['descriptor'],True)['status']!='covered']
        passed=len(group)==8 and len(sub)==2 and all(s['passed'] for s in stats.values()) and all(s['passed'] for s in exact.values()) and not refused
        reports[op]=dict(status='passed' if passed else 'failed',**stats,exact1000ps=exact,refused=refused,rows=len(group))
    status='passed_fresh_reader_function_check' if not failures and all(r['status']=='passed' for r in reports.values()) else 'failed_fresh_reader_function_check'
    write(out/'independent-result.json',dict(status=status,operations=reports,failures=failures,rows=rows,model_sha256=a['model_sha256'],parameters_changed=False,
        old_test_verdict_retained=True,formal_full_domain_release=False,S_G_joint_qualified=False,full_D_ready=False))
    stages.atomic(out/'progress.json',dict(read(out/'progress.json'),phase=status))
    print(dict(status=status,operations={op:r['status'] for op,r in reports.items()},full_D_ready=False),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','admit','run','archive','evaluate'));p.add_argument('--out',type=Path,required=True)
    for n in ('node-root','recovery','software'):p.add_argument('--'+n,type=Path)
    p.add_argument('--task');a=p.parse_args();out=a.out.resolve()
    if a.action=='prepare':prepare(out,a.node_root.resolve(),a.recovery.resolve())
    elif a.action=='admit':admit(out,a.software.resolve())
    elif a.action=='run':run(out)
    elif a.action=='archive':stages.archive(out,[out/'runs'/a.task,out/'progress.json'],a.task+'.tar.gz')
    else:evaluate(out)
