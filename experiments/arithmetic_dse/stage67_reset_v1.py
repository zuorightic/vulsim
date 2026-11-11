"""Read compatible train reset paths without altering physical snapshots.

All FF-D targets must have reset paths; one strict worst path per exclusive
state owner is saved. Numerical model fitting never reads validation labels.
"""
import argparse
from collections import defaultdict
from copy import deepcopy
import math
import os
from pathlib import Path
import shutil

from .model_fast_preflight import read,write,sha
from .budget import Ledger,POLICY,usage
from . import stage67_physical_readout_v4 as paths
from .stage67_analyze_v1 import verify_ownership_packet,path_partition
from .stage67_physical_probe_v1 import SUFFIX
from . import stage67_multiclock_v1 as stage

ROOT=stage.ROOT
PARENT=stage.PARENT
TRAIN_FEATURES=['one','sqrt_total_FF_bits','sqrt_reset_one_bits','clock_pressure']


def admit(root,role='train',freeze=None):
    if root.exists():raise ValueError('preserve reset report admission')
    if role not in ('train','validation'):raise ValueError('independent tests remain locked')
    if role=='validation' and freeze is None:raise ValueError('freeze before fresh validation readout')
    data=read(PARENT/('train-labels-v1/dataset.json' if role=='train' else 'validation-labels-v1/dataset.json'))
    tasks=[];sources={};batches=['train-batch-v1','train-repair-batch-v1'] if role=='train' else ['validation-batch-v1']
    for name in batches:
        bank=PARENT/name;a=read(bank/'admission.json');p=read(bank/'progress.json')
        for t in a['tasks']:
            if t['id'] not in p['completed']:continue
            rows=[r for r in data['rows'] if r['source']==t['source'] and r['target_ps']==t['period_ps']]
            if not rows:continue
            row=rows[0]
            if row['role']!=role:raise ValueError('source role reassignment prohibited')
            directory=bank/'runs'/t['id'];item=deepcopy(t);item.update(physical_directory=str(directory),features=row['features'])
            item['original_files']={str(f):sha(f) for f in directory.rglob('*') if f.is_file() and (f.is_relative_to(directory/'results') or f.name in ('mapped-state.json','liberty-pins.json','manifest.json') or f.name.startswith('census-grt'))}
            tasks.append(item)
    if len(tasks)!=(24 if role=='train' else 9):raise ValueError('complete predeclared reset cohort required')
    root.mkdir(parents=True)
    names=stage.dependencies()
    for n,h in names.items():
        d=root/'source'/n;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/n,d);sources[n]=h
    for n,h in read(stage.FREEZE)['files'].items():
        if sha(n)!=h:raise ValueError('published functions changed '+n)
    if freeze:
        for n,h in read(freeze)['files'].items():
            if sha(n)!=h:raise ValueError('reset function freeze drift '+n)
    later=dict(synth=688,grt=688,walltime_s=86400,CPU_time_s=172800,storage_bytes=30*1024**3);budget=dict(synth=0,grt=0,support=len(tasks)+8,walltime_s=len(tasks)*120+8*300,CPU_time_s=4*(len(tasks)*120+8*300),storage_bytes=1024**3)
    u=usage(read(Ledger().path)['entries']);lim=read(POLICY)['resources']
    if u['walltime_s']+budget['walltime_s']+86400>lim['max_global_walltime_h']*3600 or u['CPU_time_s']+budget['CPU_time_s']+172800>lim['max_tool_CPU_time_h']*3600 or shutil.disk_usage(root).free<later['storage_bytes']+budget['storage_bytes']:raise ValueError('reset reports and later reserve not funded')
    write(root/'admission.json',dict(version='compatible-reset-report-admission-v1',id=root.name,tasks=tasks,sources=sources,role=role,features=TRAIN_FEATURES,
        target_ps=[500,1500,3000],numerical_T=True,reset_launch='actual rstn input port',capture='every actual unique state FF-D across input_service/native/external',
        label='0.8*T minus minimum reset setup slack; includes actual state gating, clock-Q/setup/uncertainty per original constraints',
        predicted_features='total semantic FF, variable reset-one bits and numerical T; no source, placement, shape or measured load',
        fit='one common train-only source-equal nonnegative linear function; no owner/source intercepts',
        upper_guard='maximum positive train residual plus fixed 25ps engineering margin; no validation tuning',
        gates=dict(point_median=.15,point_P95=.35,no_undercovered_endpoint=True,false_feasible_max=0),
        support='train numerical feature bounds intersect T=[500,3000], native depth=1; no exact-T/source whitelist',
        independent_test='fresh source/shape/connection responsibilities must be frozen after validation, exact1000 stays reserved until joint freeze',
        freeze_path=str(freeze) if freeze else None,freeze_sha256=sha(freeze) if freeze else None,budget=budget,later_work_reserved=later,physical_calls=0,full_D_ready=False))
    print('RESET_REPORT_ADMITTED role='+role+' snapshots='+str(len(tasks))+' new_EDA=0',flush=True)


def verify(root):
    a=read(root/'admission.json')
    for n,h in a['sources'].items():
        if sha(ROOT/n)!=h or sha(root/'source'/n)!=h:raise ValueError('reset report producer drift '+n)
    for t in a['tasks']:
        if sha(t['rtl'])!=t['rtl_sha256'] or sha(t['endpoint_contract'])!=t['endpoint_sha256']:raise ValueError('source/endpoint drift')
        for n,h in t['original_files'].items():
            if sha(n)!=h:raise ValueError('original physical snapshot changed '+n)
    if a['freeze_path']:
        if sha(a['freeze_path'])!=a['freeze_sha256']:raise ValueError('reset freeze changed')
        for n,h in read(a['freeze_path'])['files'].items():
            if sha(n)!=h:raise ValueError('reset inference/parameter changed '+n)
    return a


def render(folder,state,owners):
    groups={n:set() for n in ('input_service','native_state','external_state')}
    for w in state['words']:
        for row in w['rows']:
            if 'cell' in row:groups[w['owner']].add(row['cell']+'/'+row['D'])
    actual={n for n,m in owners['instances'].items() if owners['liberty'][m]['sequential']}
    expected={r['cell'] for w in state['words'] for r in w['rows'] if 'cell' in r}
    if actual!=expected:raise ValueError('reset capture inventory differs from actual FFs')
    if sum(map(len,groups.values()))!=len(actual):raise ValueError('duplicate or missing exclusive FF reset targets')
    code=(ROOT/'experiments/arithmetic_dse/reference_assets/stage7_readout_v1.tcl').read_text().split('if {![info exists stage7_requests]}')[0]
    code=code.replace('set stage7_prefix','set stage7_prefix')
    code+='\nset f [open '+paths.tcl(folder/'endpoints.tsv')+' w]\nputs $f "owner\\tendpoint\\tslack"\nset summary [open '+paths.tcl(folder/'worst.tsv')+' w]\nputs $summary "owner\\tendpoint\\tslack\\tpoints"\n'
    code+='set from [get_ports rstn]\nif {[llength $from]!=1} {error "reset port absent"}\n'
    for owner,targets in groups.items():
        if not targets:raise ValueError('missing state owner reset targets')
        code+='set worst 1e30\nset worstpath {}\nset worstend {}\nforeach endpoint '+paths.tcl(sorted(targets))+' {\n'
        code+='set to [lindex [s7_pins [list $endpoint]] 0]\nset found [find_timing_paths -from $from -to $to -path_delay max -group_path_count 1]\nif {[llength $found]!=1} {error "uncovered reset endpoint $endpoint"}\nset path [lindex $found 0]\nset slack [get_property $path slack]\nputs $f "'+owner+'\\t$endpoint\\t$slack"\nif {$slack<$worst} {set worst $slack;set worstpath $path;set worstend $endpoint}\n}\n'
        p=folder/(owner+'-points.tsv');code+='set p [open '+paths.tcl(p)+' w]\nforeach point [get_property $worstpath points] {puts $p "[get_full_name [get_property $point pin]]\\t[format %.12g [get_property $point arrival]]"}\nclose $p\nputs $summary "'+owner+'\\t$worstend\\t$worst\\t'+p.name+'"\n'
    code+='close $f\nclose $summary\nputs "RESET_ALL_ENDPOINTS_CHECKED"\n'
    return code,{k:sorted(v) for k,v in groups.items()}


def collect(root):
    from .processes import run_command
    a=verify(root);out=root/'readout'
    if out.exists():raise ValueError('preserve reset report attempt')
    out.mkdir(parents=True);records=[]
    for task in a['tasks']:
        d=Path(task['physical_directory']);folder=out/task['id'];folder.mkdir(parents=True);state=read(d/'mapped-state.json');owners=paths.certificate(d,d,'grt',read(task['endpoint_contract']),task['period_ps'])
        write(folder/'ownership.json',owners);verify_ownership_packet(owners)
        code,targets=render(folder,state,owners);write(folder/'targets.json',targets)
        script=folder/'readout.tcl';script.write_text('source $::env(SCRIPTS_DIR)/load.tcl\nload_design $::env(VULSIM_EVAL_DB) $::env(VULSIM_EVAL_SDC)\nset_propagated_clock [all_clocks]\nestimate_parasitics -global_routing\n'+code)
        m=read(d/'manifest.json');base=next(c['command'][:-1] for c in m['commands'] if c['log'].endswith('/synth.log'));command=base+['run','RUN_SCRIPT='+str(script),'RUN_LOG_NAME_STEM=reset_only','VULSIM_EVAL_DB=5_1_grt.odb','VULSIM_EVAL_SDC=5_1_grt.sdc']
        env=os.environ.copy();env.update(OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',PYTHONDONTWRITEBYTECODE='1',QT_QPA_PLATFORM='offscreen');ctx=dict(target_platform='asap7',admission_id=root.name+'-reset-read',task_id=task['id']);ledger=Ledger()
        with ledger.job(ctx):
            v=ledger.reserve(None,120,4,'compatible_reset_report_only',command,folder/'readout',context=ctx);rec=run_command(command,folder,'readout',120,env,8192,cpu_limit_s=v['CPU_time_s']);ledger.finish(v,rec)
        records.append(dict(**rec,budget_reservation_id=v['id']));write(out/'commands.json',records)
        if rec['exit_code']:raise ValueError('reset report failed '+rec['log'])
        print('RESET_SAVED_SNAPSHOT_READ '+task['id'],flush=True)
    write(out/'status.json',dict(status='completed',snapshots=len(a['tasks']),new_physical_calls=0))


def extract(root,out):
    if out.exists():raise ValueError('preserve reset scalar dataset')
    a=verify(root);rows=[];count=0
    if read(root/'readout/status.json')['status']!='completed':raise ValueError('complete cohort reports required')
    for t in a['tasks']:
        folder=root/'readout'/t['id'];owners=read(folder/'ownership.json');verify_ownership_packet(owners);expected=read(folder/'targets.json');endpoints=paths.table(folder/'endpoints.tsv');actual=defaultdict(dict)
        for e in endpoints:
            if e['endpoint'] in actual[e['owner']]:raise ValueError('duplicate reset timing endpoint')
            actual[e['owner']][e['endpoint']]=float(e['slack'])
        if set(actual)!=set(expected) or any(set(actual[n])!=set(v) for n,v in expected.items()):raise ValueError('reset endpoint census incomplete')
        worst=paths.table(folder/'worst.tsv');paths_checked=[]
        for w in worst:
            n=w['owner'];slack=min(actual[n].values())
            if abs(float(w['slack'])-slack)>1e-6 or actual[n][w['endpoint']]!=float(w['slack']):raise ValueError('worst reset path differs from all endpoints')
            points=[x.split('\t') for x in (folder/w['points']).read_text().splitlines()]
            part=path_partition(points,owners,['rstn'],w['endpoint']);paths_checked.append(dict(owner=n,slack_ps=slack,required_intrinsic_ps=.8*t['period_ps']-slack,partition=part))
        f=t['features'];ff=f['total_FF_bits'];ones=f['reset_one_bits'];count+=sum(map(len,actual.values()));worst_slack=min(float(x['slack']) for x in endpoints)
        rows.append(dict(source=t['source'],role=a['role'],target_ps=t['period_ps'],features=dict(one=1.,sqrt_total_FF_bits=math.sqrt(ff),sqrt_reset_one_bits=math.sqrt(ones),clock_pressure=1500/t['period_ps'],total_FF_bits=ff,reset_one_bits=ones),
            reset_required_ps=.8*t['period_ps']-worst_slack,worst_slack_ps=worst_slack,endpoint_checks=sum(map(len,actual.values())),owner_paths=paths_checked,
            owners_sha256=sha(folder/'ownership.json'),physical_target_unchanged=True))
    write(out,dict(version='reset-compatible-dataset-v1',rows=rows,endpoint_checks=count,role=a['role'],admission_sha256=sha(root/'admission.json'),no_new_synthesis_or_grt=True,full_D_ready=False))
    print('RESET_LABELS_EXTRACTED role='+a['role']+' rows='+str(len(rows))+' endpoints='+str(count),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('admit','collect','extract'));p.add_argument('--root',type=Path,required=True);p.add_argument('--role',default='train');p.add_argument('--freeze',type=Path);p.add_argument('--out',type=Path);a=p.parse_args()
    if a.action=='admit':admit(a.root.resolve(),a.role,a.freeze.resolve() if a.freeze else None)
    elif a.action=='collect':collect(a.root.resolve())
    else:extract(a.root.resolve(),a.out.resolve())
