"""Finite report-only node boundary diagnosis on paid saved grt databases."""
import argparse
import csv
import json
import math
import os
from pathlib import Path
import shutil

from .budget import Ledger, usage
from .model_fast_preflight import read, write, sha
from .processes import run_command

ROOT = Path(__file__).resolve().parents[2]
ASSET = Path(__file__).with_name('reference_assets')/'fast_node_probe.tcl'
REFERENCE = ASSET.with_name('snapshot.tcl')


def table(path):
    return list(csv.DictReader(Path(path).read_text().splitlines(), delimiter='\t'))


def verify(out, original):
    before=out/'node_before_reference_paths.tsv'; after=out/'node_after_reference_paths.tsv'
    if before.read_bytes()!=after.read_bytes():
        raise ValueError('internal probe changed normal launch/capture path labels')
    if before.read_bytes()!=(original/'reports/asap7/arithmetic_probe/base/vulsim_grt_reference_paths.tsv').read_bytes():
        raise ValueError('saved original stage path labels do not reproduce')
    a={r['pin']:r['slew_before'] for r in table(out/'node_boundaries.tsv')}
    b={r['pin']:r['slew_after'] for r in table(out/'node_slews_after.tsv')}
    if a!=b:
        raise ValueError('internal probe changed original boundary slews')
    paths=[(name,float(v)) for name,v in (line.split('\t') for line in (out/'node_points.tsv').read_text().splitlines())]
    node=table(out/'node_node.tsv')
    if len(node)!=1:
        raise ValueError('missing internal node path')
    node=node[0]; bounds={r['pin']:r for r in table(out/'node_boundaries.tsv')}
    if (paths[0][0]!=node['start'] or paths[-1][0]!=node['end'] or node['start'] not in bounds or node['end'] not in bounds
            or bounds[node['start']]['kind']!='inputs' or bounds[node['end']]['kind']!='outputs'
            or abs(float(node['start_arrival']))>1e-5 or any(not name.startswith('core/') or not math.isfinite(t) for name,t in paths)):
        raise ValueError('node probe lacks independent zero-origin input/output boundary')
    delay=float(node['end_arrival'])-float(node['start_arrival'])
    if not delay>0 or not math.isclose(delay,paths[-1][1]-paths[0][1],abs_tol=1e-6):
        raise ValueError('invalid internal node delay')
    return dict(status='passed',node_delay_ps=delay,inputs=int(node['inputs']),outputs=int(node['outputs']),
                excluded_constant_input_pins=int(node['constants']),normal_Q_to_D_reports_unchanged=True,
                boundary_slews_unchanged=True,internal_zero_origin=True,source_role='not_training',
                operator_maximum_coverage_qualified=False,
                qualification_note='successful pinned-tool mechanism probe; full multi-node/consumer coverage and negative controls still required')


def run(out, cohort):
    admission=read(cohort/'admission.json');out.mkdir(parents=True,exist_ok=False)
    ledger=Ledger(); before=read(ledger.path);records=[];results=[]
    # Four finite reader contexts exercise mapped response, bank fanout and a
    # sparse/constant output shape. No sample changes roles and no EDA is optimized.
    selected=('mul32_capture1-t0','mul32_capture1-t1','mul32_capture4-t0','sparse_add_low64-t0')
    write(out/'readback-plan.json',dict(version='fast-node-report-only-v1',source_role='not_training',
          tasks=list(selected),source_admission_sha256=sha(cohort/'admission.json'),PPA_calls=0,
          synth=0,grt=0,per_reader_timeout_s=120,threads=4,memory_limit_MiB=8192,
          sources={str(p.relative_to(ROOT)):sha(p) for p in (Path(__file__),ASSET,REFERENCE)}))
    for p in (Path(__file__),ASSET,REFERENCE):
        d=out/'source'/p.relative_to(ROOT);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d)
    env=os.environ.copy();env.update(OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',PYTHONDONTWRITEBYTECODE='1',QT_QPA_PLATFORM='offscreen')
    try:
        for task_id in selected:
            task=next(t for t in admission['tasks'] if t['id']==task_id)
            original=Path(task['inherit_completed']['directory']) if task.get('inherit_completed') else cohort/'runs'/task_id
            m=read(original/'manifest.json')
            if m['status']!='completed' or m['data_role']!='not_training' or m['model_fit_allowed']:
                raise ValueError('only paid complete diagnostic checkpoint may be read')
            checkpoint=m['evidence_sha256']
            for name in ('results/asap7/arithmetic_probe/base/5_1_grt.odb','results/asap7/arithmetic_probe/base/5_1_grt.sdc'):
                if sha(original/name)!=checkpoint[name]:
                    raise ValueError('original saved checkpoint changed')
            folder=out/task_id;folder.mkdir()
            old=next(c['command'] for c in m['commands'] if c['log'].endswith('fast-grt-snapshot.log'))
            command=old[:old.index('run')]+['run','RUN_SCRIPT='+str(ASSET),'RUN_LOG_NAME_STEM=node_readback',
                'REPORTS_DIR='+str(folder/'reports'),'LOG_DIR='+str(folder/'logs'),'OBJECTS_DIR='+str(folder/'objects'),
                'VULSIM_EVAL_DB=5_1_grt.odb','VULSIM_EVAL_SDC=5_1_grt.sdc',
                'VULSIM_NODE_PREFIX='+str(folder/'node'),'VULSIM_NODE_SCOPE=core/',
                'VULSIM_NODE_TARGET='+str(task['period_ps']),'VULSIM_REFERENCE_ASSET='+str(REFERENCE),
                'VULSIM_REFERENCE_REQUESTS='+str(original/'requests.tcl')]
            ctx=dict(target_platform='asap7',admission_id=out.name,task_id=task_id)
            with ledger.job(ctx):
                reservation=ledger.reserve(None,120,4,'fast_node_report_only_diagnosis',command,folder/'readback',context=ctx)
                record=run_command(command,folder,'readback',120,env,8192,cpu_limit_s=reservation['CPU_time_s']);ledger.finish(reservation,record)
                records.append(dict(**record,budget_reservation_id=reservation['id']));write(out/'commands.json',records)
                if record['exit_code']:
                    raise RuntimeError('node report-only readback failed: '+record['log'])
            result=verify(folder,original);result['task_id']=task_id;results.append(result);write(out/'results.json',results)
            # Report-only job must not rewrite any original frozen evidence.
            for name,h in checkpoint.items():
                if sha(original/name)!=h:
                    raise ValueError('report-only readback modified original physical evidence')
            print(json.dumps(result),flush=True)
    finally:
        after=read(ledger.path)
        write(out/'resource-increment.json',dict(entries=after['entries'][len(before['entries']):],usage=usage(after['entries']),PPA_calls=0))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--cohort',type=Path,required=True);args=parser.parse_args()
    run(args.out.resolve(),args.cohort.resolve())
