"""Finite L4/L5 successor requested after the padded Dot16 L8 schedules.

Original frozen runs and controllers are untouched. Every selected pipelined
implementation must contain live arithmetic in each declared stage. Original
atomic operators define B; C/D share the existing twelve structural grammars.
The original equivalent-period selector runs in an isolated process with an
explicitly registered, occupancy-checked schedule generator. No PPA feedback
or model refit is permitted. Physical execution waits for the older wave.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import fcntl
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from unittest.mock import patch

from .sampling_time_contract import ROOT
from .workload_abcd import read, write, sha, static_node, static_score
from .workload_contracts import load
from .workload_demand import Graph
from .workload_final_software import balanced, export, record, simulate, BINARY
from . import workload_final_selection as selector
from . import workload_final_backend as physical
from .workload_tight_run import DEFAULT as PARENT
from .budget import Ledger

DEFAULT = ROOT.parent / 'vulsim-artifacts/workload-equivalent-dot16-L45-v1'
EVIDENCE = ROOT / 'experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/dot16-L45'
SOURCE = Path(__file__).resolve()
VERSION = 'dot16-active-L4-L5-v1'


def active_stages(raw, placement, weights):
    return sorted({placement[n['id']] for n in raw['nodes'] if weights.get(n['id'], 0.) > 0})


def depth_schedule(raw, units, L, weights):
    """Spread a path of indivisible live arithmetic units over the real L.

    Zero-cost wiring does not create arithmetic depth. The native compiler
    independently validates grouping, dependency and fixed-port legality.
    """
    nodes = raw['nodes']; membership = {n:k for k,u in enumerate(units) for n in u['members']}
    depths = []; dependencies = []; live = []
    for k, unit in enumerate(units):
        deps = sorted({membership[a['node']] for n in unit['members'] for a in nodes[n]['operands']
                       if a['node'] is not None and membership[a['node']] != k})
        if any(d >= k for d in deps):
            raise ValueError('scheduling units are not dependency ordered')
        positive = any(weights.get(n, 0.) > 0 for n in unit['members'])
        dependencies.append(deps); live.append(positive)
        depths.append(max((depths[d] for d in deps), default=0) + int(positive))
    span = max((d for d,p in zip(depths, live) if p), default=0)
    if span < L:
        raise ValueError('atomic arithmetic depth cannot fill the requested stages')
    stages = []; placement = [0] * len(nodes)
    for k, unit in enumerate(units):
        s = min(L-1, max(0, (depths[k]-1) * L // span))
        s = max(s, max((stages[d] for d in dependencies[k]), default=0))
        if unit['fixed']:
            s = 0 if all(nodes[n]['operation'] == 'input' for n in unit['members']) else L-1
        elif unit['constant']:
            s = 0
        stages.append(s)
        for n in unit['members']:
            placement[n] = s
    if active_stages(raw, placement, weights) != list(range(L)):
        raise ValueError('depth schedule still contains an arithmetic-empty stage')
    return placement


def active_balanced(raw, units, L, weights):
    # Use static liveness for occupancy even when model weights are supplied.
    graph = Graph(raw); live_weights = {n['id']:static_node(graph,n) for n in graph.nodes}
    rows = [p for p in balanced(raw,units,L,weights)
            if active_stages(raw,p,live_weights) == list(range(L))]
    p = depth_schedule(raw,units,L,live_weights)
    if p not in rows:
        rows.append(p)
    Graph.origins.cache_clear(); Graph.roots.cache_clear()
    return rows


def frozen(path, value):
    if path.exists() and read(path) != value:
        raise ValueError('immutable successor input changed: ' + str(path))
    if not path.exists():
        path.parent.mkdir(parents=True,exist_ok=True); write(path,value)


def initialize(root):
    root = Path(root).resolve(); root.mkdir(parents=True,exist_ok=True)
    old_target = PARENT/'targets/dot16.json'; old = read(old_target)
    readout = PARENT/'A-reference/runs/dot16-A-reference/clock-readout/result.json'
    A = read(readout)['full_setup_minimum_period_ps']
    if sha(readout) != old['clock_readout_sha256'] or A != old['A_reference_Tmin_ps']:
        raise ValueError('reference A identity changed')
    grammar = read(PARENT/'software/dot16/static-pool.json')['grammar']
    targets = []
    for L in (4,5):
        values = [math.ceil(f*A/L/50)*50 for f in (1.25,1.5)]
        values[1] = max(values[1],values[0]+50)
        targets.append(dict(L=L,targets_ps=values))
    inputs = [SOURCE, old_target, readout, BINARY, selector.BASE/'diagnostic-model.json',
              PARENT/'software/characterization-contract.json', PARENT/'software/bindings.json']
    inputs += [Path(selector.__file__), ROOT/'experiments/arithmetic_dse/workload_final_software.py',
               ROOT/'experiments/arithmetic_dse/workload_tight_equivalent.py',
               ROOT/'experiments/arithmetic_dse/workload_final_prices.py']
    doc = dict(version=VERSION,case='dot16',variants=targets,grammar=grammar,
        user_authorization='可以把dot16调整成4-5级流水试试',
        A_reference_Tmin_ps=A,reference_readout=str(readout),factors=[1.25,1.5],quantum_ps=50,
        required_main_records=16,required_attribution_records=4,
        B='original atomic operators; registers only',C='original fixed abstract table',
        D='joint body budgets -> equivalent training T -> unchanged frozen responses',
        occupancy='every stage must contain live non-wiring arithmetic; checked before and after selection',
        candidates='native beam plus active balanced and dependency-depth schedules; same grammar and credit for C/D',
        schedule_override='isolated selector.balanced = active_balanced; original selector source unchanged',
        qualification='diagnostic_only',model_refitted=False,application_PPA_for_selection=False,
        target_relaxation_after_PPA=False,original_L8_records_retained=True,
        parallel_jobs=4,threads_per_tool=4,memory_limit_MiB=8192,
        physical_start='wait until all previously admitted parent tasks settle and ledger is idle',
        inputs={str(p):sha(p) for p in inputs})
    frozen(root/'protocol.json',doc)
    for v in targets:
        soft = root/f"L{v['L']}"/'software'; soft.mkdir(parents=True,exist_ok=True)
        for name in ('bindings.json','characterization-contract.json'):
            source = PARENT/'software'/name; dest = soft/name
            if dest.exists() and sha(dest) != sha(source):
                raise ValueError('copied software input changed')
            if not dest.exists():
                shutil.copyfile(source,dest)
        frozen(soft/'protocol.json',dict(doc,variant=v))
        dest = soft/'dot16/source'
        if not dest.exists():
            shutil.copytree(PARENT/'software/dot16/source',dest)
        target = dict(case='dot16',L=v['L'],targets_ps=v['targets_ps'],
            A_reference_Tmin_ps=A,clock_readout_sha256=sha(readout),factors=[1.25,1.5],
            quantum_ps=50,application_PPA_for_model=False)
        frozen(soft.parent/'targets/dot16.json',target)
    return doc


def prepare(root, L):
    doc = initialize(root); variant = next(v for v in doc['variants'] if v['L']==L)
    soft = root/f'L{L}'/'software'; case = next(c for c in load()['cases'] if c['id']=='dot16')
    result = soft/'dot16/static-pool.json'
    if result.exists():
        return soft
    T = variant['targets_ps'][0]; rows = []; rejected = []
    for number,(block,limb) in enumerate(doc['grammar']):
        native = export(soft,case,block,limb,T,L)
        raw = read(native/'graph.json'); graph = Graph(raw)
        weights = {n['id']:static_node(graph,n) for n in graph.nodes}
        for view in read(native/'inventory.json')['views']:
            if active_stages(raw,view['placement'],weights)==list(range(L)):
                rows.append(record(native,view,number,L,'active_native_beam'))
            else:
                rejected.append(dict(structure=number,view=view['directory'],
                    active_stages=active_stages(raw,view['placement'],weights)))
        placements = active_balanced(raw,read(native/'scheduling-units.json')['units'],L,weights)
        dest = export(soft,case,block,limb,T,L,placements,tag='active-balanced')
        for view in read(dest/'inventory.json')['views']:
            rows.append(record(dest,view,number,L,'balanced_static'))
        print(f'ACTIVE_POOL L{L} {number+1}/{len(doc["grammar"])}',flush=True)
        Graph.origins.cache_clear(); Graph.roots.cache_clear()
    native = export(soft,case,0,0,T,1,tag='A')
    a = record(native,read(native/'inventory.json')['views'][0],0,1,'original_no_pipeline')
    b = min((r for r in rows if r['structure']==0),key=static_score)
    c = min(rows,key=static_score)
    for row in (a,b,c):
        simulate(soft,case,row)
    write(result,dict(case='dot16',grammar=doc['grammar'],candidates=rows,A=a,B=b,C=c,
        rejected_empty_arithmetic_stages=rejected,required_live_stages=list(range(L)),candidate_PPA_calls=0))
    return soft


def selected_occupancy(soft):
    rows = []
    for r in read(soft/'dot16/final-selections.json')['records']:
        for name,m in r['methods'].items():
            folder = Path(m['rtl']).parent; raw = read(folder/'graph.json'); graph = Graph(raw)
            weights = {n['id']:static_node(graph,n) for n in graph.nodes}
            active = active_stages(raw,m['placement'],weights)
            if active != list(range(m['L'])):
                raise ValueError('selected arithmetic stage occupancy differs: '+name)
            by_stage = [dict(stage=s,live_arithmetic_nodes=sum(
                m['placement'][n['id']]==s and weights[n['id']]>0 for n in raw['nodes']))
                for s in range(m['L'])]
            rows.append(dict(method=name,T_ps=m['T_clk_ps'],L=m['L'],grammar=m['grammar'],
                active_stages=active,stages=by_stage,rtl_sha256=m['rtl_sha256']))
            Graph.origins.cache_clear(); Graph.roots.cache_clear()
    frozen(soft/'stage-occupancy.json',dict(status='passed',rows=rows,
        criterion='live arithmetic excludes dead nodes, constants and zero-cost wiring'))
    return rows


def select(root, L):
    soft = prepare(root,L); targets = read(soft.parent/'targets/dot16.json')['targets_ps']
    with patch.object(selector,'balanced',active_balanced):
        selector.select_case(soft,'dot16',targets)
    selected_occupancy(soft)
    return soft


def assemble(root):
    soft = root/'software'; soft.mkdir(exist_ok=True)
    for name in ('bindings.json','characterization-contract.json','protocol.json'):
        src = root/'L4/software'/name; dst = soft/name
        if not dst.exists():
            shutil.copyfile(src,dst)
    records = []
    for L in (4,5):
        source = root/f'L{L}/software'; records += read(source/'dot16/final-selections.json')['records']
        # Keep native paths, score files, and traces in each isolated variant.
        # The aggregate uses hard links for identical immutable selected files.
        for src in (source/'selected/dot16').rglob('*'):
            if src.is_file():
                dest = soft/'selected/dot16'/f'variant-L{L}'/src.relative_to(source/'selected/dot16')
                dest.parent.mkdir(parents=True,exist_ok=True)
                if dest.exists() and sha(dest)!=sha(src):
                    raise ValueError('aggregate selected collision')
                if not dest.exists():
                    os.link(src,dest)
    frozen(soft/'dot16/final-selections.json',dict(version=VERSION,case='dot16',records=records,
        targets_ps=sorted({r['target']['T_ps'] for r in records}),qualified=False,
        application_PPA_for_selection=False,latency_groups=4))
    frozen(root/'targets/dot16.json',dict(variants=read(root/'protocol.json')['variants'],
        A_reference_Tmin_ps=read(root/'protocol.json')['A_reference_Tmin_ps']))


def earlier_wave_settled():
    # progress.active contains queued tasks as well as actual jobs. Both must
    # settle before this independent controller can consume all four slots.
    for path in PARENT.glob('*/progress.json'):
        if (path.parent/'admission.json').exists() and read(path)['status']!='batch_settled':
            return False
    state = read(Ledger().path)
    return not any(j['status'] in ('active','unsettled') for j in state.get('jobs',[])) and not Ledger().summary()['pending']


def launch(batch, task):
    path = batch/'dispatch-logs'/(task['id']+'.log'); path.parent.mkdir(exist_ok=True)
    with path.open('w') as log:
        result = subprocess.run([sys.executable,'-m','experiments.arithmetic_dse.workload_dot16_latency',
            'task','--root',str(batch),'--task-id',task['id']],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError('physical child failed; see '+str(path))


def drive(root, batch):
    a = physical.verify(batch); progress = read(batch/'progress.json')
    if progress['status']!='admitted':
        raise ValueError('no automatic physical retry')
    progress.update(status='running',active=[t['id'] for t in a['tasks']]); write(batch/'progress.json',progress)
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(launch,batch,t):t for t in a['tasks']}
        for future in as_completed(futures):
            task = futures[future]
            try:
                future.result(); progress['completed'].append(task['id'])
                print('DOT_PHYSICAL_PASS '+task['id'],flush=True)
            except Exception as error:
                progress['errors'].append(dict(task=task['id'],reason=str(error)))
                print('DOT_PHYSICAL_FAIL '+task['id']+' '+str(error),flush=True)
            progress['active'].remove(task['id']); write(batch/'progress.json',progress); publish(root)
    progress['status']='batch_settled'; write(batch/'progress.json',progress); publish(root)


def publish(root):
    EVIDENCE.mkdir(parents=True,exist_ok=True); rows = []; occupancy = []
    methods = root/'final-dot16-L45-methods.json'
    if methods.exists():
        for row in read(methods)['records']:
            for name,m in row['methods'].items():
                run = root/'final-dot16-L45/runs'/m['task_id']; readout = run/'clock-readout/result.json'
                item = dict(case='dot16',T_ps=row['target']['T_ps'],comparison_L=row['target']['L'],
                    actual_L=m['L'],method=name,grammar=m['grammar'],task_id=m['task_id'],
                    rtl_sha256=m['rtl_sha256'],prediction=m['prediction'])
                manifest = read(run/'manifest.json') if (run/'manifest.json').exists() else {}
                item.update(status=manifest.get('status','not_started'),failure_reason=manifest.get('failure_reason'))
                if readout.exists():
                    result = read(readout); T = result['full_setup_minimum_period_ps']
                    item.update(status='measured_grt',Tmin_ps=T,area_um2=result['area_um2'],
                        frequency_MHz=1e6/T,setup_met=T<=item['T_ps'],hold_WNS_ps=result['hold_WNS_ps'],
                        hold_met=result['hold_WNS_ps']>=0,clock_readout_sha256=sha(readout))
                rows.append(item)
    for L in (4,5):
        p = root/f'L{L}/software/stage-occupancy.json'
        if p.exists():
            occupancy += read(p)['rows']
    main = [r for r in rows if r['method'] in ('A','B','C','D')]
    summary = dict(version=VERSION,required_main_records=16,
        main_measured=sum(r['status']=='measured_grt' for r in main),records=rows,occupancy=occupancy,
        physical_comparison_complete=len(main)==16 and all(r['status']=='measured_grt' for r in main),
        qualification='diagnostic_only',original_L8_replaced=False,
        no_PPA_for_selection=True,source_sha256=sha(SOURCE),ledger=Ledger().summary())
    write(root/'comparison.json',summary); write(EVIDENCE/'comparison.json',summary)
    lines = ['# Dot16：L=4／5 的独立重新拆分比较','',
        f'主方法已实测 {summary["main_measured"]}/16。原 L=8 结果保留；本表不据结果选择较好的一档替代原矩阵。','',
        '| 比较L | T ps | 方法 | 实际L | 块宽/limb | Tmin ps | 面积 µm² | setup | hold ps | 状态 |',
        '| --- | ---: | --- | ---: | --- | ---: | ---: | --- | ---: | --- |']
    for r in rows:
        numbers = ([f'{r["Tmin_ps"]:.3f}',f'{r["area_um2"]:.3f}',str(r['setup_met']),f'{r["hold_WNS_ps"]:.3f}']
                   if r['status']=='measured_grt' else ['—']*4)
        lines.append('| '+' | '.join(map(str,[r['comparison_L'],r['T_ps'],r['method'],r['actual_L'],
            '/'.join(map(str,r['grammar'])),*numbers,r['status']]))+' |')
    lines += ['', 'B 保留完整乘法／加法；C 采用原静态表；D 使用本体预算及等效训练T。',
        '每份 B／C／D 及归因 RTL 都检查每级含活跃算术，再通过192周期整数、时序、复位和停顿验证。',
        '模型仍为诊断身份，实际 ABC 使用整机目标T，setup 与 hold 分别判定。','',
        '目标：L4 为850／1050ps，L5 为700／850ps，来自同一未拆分 A 的2705.125456ps实测与预登记A/L公式。',
        f'本地完整目录：`{root}`。后端4并行，每任务最多4线程，等待原波次结清后发射，保留全部失败与累计费用。']
    (root/'comparison.md').write_text('\n'.join(lines)+'\n'); shutil.copyfile(root/'comparison.md',EVIDENCE/'README.md')
    for name in ('protocol.json','software-validation.json'):
        if (root/name).exists():
            shutil.copyfile(root/name,EVIDENCE/name)
    shutil.copyfile(SOURCE,EVIDENCE/SOURCE.name)
    return summary


def run(root):
    root = Path(root).resolve(); initialize(root)
    with (root/'controller.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (root/'controller-start.json').exists():
            raise ValueError('successor already launched; preserve previous attempt')
        write(root/'controller-start.json',dict(pid=os.getpid(),started_at=datetime.now(timezone.utc).isoformat(),
            source_sha256=sha(SOURCE),automatic_retries=0))
        validations = []
        for L in (4,5):
            soft = select(root,L)
            from .workload_final_replay import replay
            from .workload_final_audit import audit
            replayed = replay(soft); audited = audit(soft)
            if replayed['targets']!=2 or audited['records']!=10:
                raise ValueError('incomplete variant software audit')
            validations.append(dict(L=L,replay_status=replayed['status'],replayed_targets=2,
                owner_audit_status=audited['status'],owner_audit_records=10,
                owner_audit_sha256=sha(soft/'all-selected-owner-audit.json'),
                replay_sha256=sha(soft/'selected-replay.json')))
            write(root/'software-validation.json',dict(variants=validations,EDA_calls=0,model_refitted=False))
            publish(root)
        assemble(root)
        # Restore tool PATH after the software selector's EDA sentinel.
        os.environ['PATH'] = os.pathsep.join(p for p in os.environ['PATH'].split(os.pathsep)
            if not p.endswith('/no-eda-bin'))
        frozen(root/'waiting-for-backend.json',dict(status='software_frozen_waiting_for_prior_wave',
            concurrency=4,threads=4,original_measurement_sources_modified=False))
        print('DOT_SOFTWARE_FROZEN; waiting for earlier physical wave',flush=True)
        while not earlier_wave_settled():
            time.sleep(15)
        from .workload_final_driver import final_tasks
        batch = final_tasks(root,['dot16'],'final-dot16-L45')
        a = physical.verify(batch); f = read(batch/'freeze.json')
        for p in (SOURCE,root/'protocol.json',root/'software-validation.json'):
            f['files'][str(p)] = sha(p)
        write(batch/'freeze.json',f); a.update(parallel_jobs=4,freeze_sha256=sha(batch/'freeze.json'))
        write(batch/'admission.json',a); physical.verify(batch); publish(root); drive(root,batch)
        return publish(root)


def task(batch, task_id):
    a = physical.verify(batch); t = next(t for t in a['tasks'] if t['id']==task_id)
    with patch.object(physical.predecessor,'verify_admission',physical.verify_admission):
        return physical.run_task(batch,t)


if __name__=='__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('action',choices=('run','task','report'))
    parser.add_argument('--root',type=Path,default=DEFAULT); parser.add_argument('--task-id')
    args = parser.parse_args()
    result = run(args.root) if args.action=='run' else task(args.root,args.task_id) if args.action=='task' else publish(args.root)
    if isinstance(result,dict):
        print({k:result[k] for k in ('main_measured','physical_comparison_complete')})
