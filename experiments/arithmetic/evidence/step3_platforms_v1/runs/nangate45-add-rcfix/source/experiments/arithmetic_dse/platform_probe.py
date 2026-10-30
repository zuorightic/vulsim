"""Bounded platform-connection probes; no training or main-case evaluation."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import sys

from .budget import Ledger,POLICY,usage
from .platforms import profile
from .processes import run_command

ROOT=Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')


def revise_admission(parent_path,destination,revision_id,replacements,reason):
    """Explicit correction after a diagnosed defect, preserving original trials.

    replacements maps old task IDs to fresh IDs. Period/RTL/stage cannot change
    here; a correction is not a timing-point search or an automatic retry.
    The original physical-call envelope remains shared across the lineage.
    """
    parent_path,destination=Path(parent_path).resolve(),Path(destination).resolve()
    if destination.exists() or not reason.strip():raise ValueError('new revision path and reason required')
    parent=json.loads(parent_path.read_text())
    if revision_id==parent['id'] or len(set(replacements.values()))!=len(replacements):
        raise ValueError('fresh revision and task IDs required')
    tasks=[]
    for old,new in replacements.items():
        candidates=[t for t in parent['tasks'] if t['id']==old]
        if len(candidates)!=1 or new==old:raise ValueError('unknown or reused task ID')
        task=dict(candidates[0],id=new)
        task['supersedes_task_id']=old
        task['profile_sha256']=profile(task['platform'])['profile_sha256']
        tasks.append(task)
    revised=dict(parent,id=revision_id,tasks=tasks,
                 created_at=datetime.now(timezone.utc).isoformat(),correction_reason=reason,
                 parent_admission={'path':str(parent_path),'sha256':digest(parent_path),'id':parent['id']},
                 related_admission_ids=list(dict.fromkeys(parent.get('related_admission_ids',[parent['id']])+[revision_id])),
                 starting_usage=Ledger().summary())
    write_json(destination,revised)
    return revised


def verify_admission(args,p,rtl,ledger):
    path=args.admission.resolve()
    frozen=json.loads(path.read_text())
    if (frozen['id']!=args.admission_id or frozen['purpose']!='platform_connection_only'
            or frozen['policy_sha256']!=digest(POLICY)):
        raise ValueError('admission identity/policy mismatch')
    tasks=[t for t in frozen['tasks'] if t['id']==args.task_id]
    if len(tasks)!=1:raise ValueError('task not in frozen admission list')
    task=tasks[0]
    if (task['platform']!=p['platform'] or task['profile_sha256']!=p['profile_sha256']
            or task['rtl_sha256']!=digest(rtl) or task['top']!=args.top
            or task['period_ps']!=args.period_ps or task['abc_target_ps']!=args.abc_target_ps
            or task['stage']!=args.stage or task['purpose']!=args.budget_purpose
            or args.period_role!='resource_trial' or args.io_delay_max_ps is not None):
        raise ValueError('requested physical task differs from frozen list')
    state=json.loads(ledger.path.read_text())
    if usage(state['entries'])['pending']:raise ValueError('unsettled global ledger')
    parent=frozen.get('parent_admission')
    if parent and digest(parent['path'])!=parent['sha256']:
        raise ValueError('parent admission identity changed')
    previous=[e for e in state['entries'] if e.get('admission_id') in frozen.get('related_admission_ids',[frozen['id']])]
    if any(e.get('admission_id')==frozen['id'] and e.get('task_id')==task['id'] for e in previous):
        raise ValueError('connection task already attempted; amend manifest explicitly, never automatic retry')
    # Capacity is unknown on a new platform: only these named finite probes are
    # admitted, with the existing per-job limits and cumulative funding intact.
    for stage in ('synth','grt','final'):
        already=sum(e['stage']==stage for e in previous)
        required=int(stage in ['synth','grt','final'][:['synth','grt','final'].index(args.stage)+1])
        if already+required>frozen['call_caps'][stage]:
            raise ValueError('bounded probe call cap exhausted')
    return digest(path)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--prepare',action='store_true')
    ap.add_argument('--task',help='execute one previously frozen task')
    ap.add_argument('--admission',type=Path,help='explicit correction manifest; defaults to OUT/admission.json')
    args=ap.parse_args();out=args.out.resolve()
    ledger=Ledger();env=os.environ.copy();env.update(MAKEFLAGS='-j2')
    if args.prepare:
        if out.exists():ap.error('use a new output directory')
        out.mkdir(parents=True)
        write_json(out/'usage_before.json',json.loads(ledger.path.read_text()))
        commands=[]
        def run(command,stem,timeout=120):
            r=ledger.reserve(None,timeout,2,'platform_probe_generation_validation',command,out/stem,
                             context={'target_platform':'common','admission_id':'step3-preparation-v1','task_id':stem})
            record=run_command(command,out,stem,timeout,env,cpu_limit_s=r['CPU_time_s'])
            ledger.finish(r,record);commands.append({**record,'reservation_id':r['id']})
            write_json(out/'preparation.json',{'commands':commands})
            if record['exit_code']:raise RuntimeError(f'{stem}: see {record["log"]}')
        sources=ROOT/'experiments/arithmetic/backend_probe'
        for kind in ('add','mul'):
            d=out/kind;d.mkdir()
            for name in ('header.uh','Main.utb','MulProbe.vul'):
                text=(sources/name).read_text()
                if kind=='add':
                    if name=='MulProbe.vul':text=text.replace('product = a * b','product = a + b')
                    if name=='Main.utb':text=text.replace('static_cast<uint64_t>(a) * static_cast<uint64_t>(b)',
                                                         'static_cast<uint64_t>(a) + static_cast<uint64_t>(b)')
                (d/name).write_text(text)
            for mode,tool in [('software','vulsimgen'),('native','vulrtlgen')]:
                target=out/(kind+'-'+mode)
                run([str(ROOT/'build'/tool),'-m',str(d/'Main.utb'),'-f','-o',str(target)],kind+'-'+mode+'-generate')
                run(['bash',str(target/'run.sh')],kind+'-'+mode+'-validate',300)
        tasks=[]
        for platform in ('asap7','nangate45','sky130hd','gf180'):
            p=profile(platform)
            for kind,stage in [('add','grt'),('mul','final')]:
                rtl=out/(kind+'-native')/'sim/top.sv'
                tasks.append({'id':platform+'-'+kind,'platform':platform,'kernel':kind+'_u32',
                              'rtl':str(rtl),'rtl_sha256':digest(rtl),'top':'MulProbe_sim_top',
                              'profile_sha256':p['profile_sha256'],'period_ps':p['trial_period_ps'],
                              'abc_target_ps':p['trial_period_ps'],'stage':stage,'purpose':'prototype',
                              'L':3,'II':1,'size_scope':'32bit_input; complete_result_64bit'})
        state=json.loads(ledger.path.read_text());total=usage(state['entries'])
        caps={'synth':8,'grt':8,'final':4}
        limits=json.loads(POLICY.read_text())['resources']
        names={'synth':'max_synthesis_calls','grt':'max_global_route_calls','final':'max_detailed_route_calls'}
        if any(total[s]+caps[s]>limits[names[s]] for s in caps):raise ValueError('insufficient cumulative probe funding')
        # Worst-case physical stage windows 8*300 + 8*1200 + 4*1200,
        # plus 2h support/snapshots; retained remaining time remains explicit.
        estimate=8*300+12*1200+7200
        if total['walltime_s']+estimate>limits['max_global_walltime_h']*3600:raise ValueError('probe time envelope unfunded')
        admission={'version':'platform-connection-admission-v1','id':'step3-four-platforms-v1',
                   'created_at':datetime.now(timezone.utc).isoformat(),'purpose':'platform_connection_only',
                   'policy_sha256':digest(POLICY),'starting_usage':total,'tasks':tasks,'call_caps':caps,
                   'worst_case_leaf_walltime_s':estimate,'CPU_envelope_s':2*estimate,
                   'threads':2,'physical_jobs':1,'memory_limit_MiB':8192,
                   'sample_split':'not_applicable; connection probes not admitted as model training',
                   'stops':['failed_stage','timeout','memory_limit','unsettled_ledger','unexpected_units_or_assets'],
                   'automatic_retries':0,'main_case_targets':False,'later_bulk_or_model_work_authorized':False}
        write_json(out/'admission.json',admission)
        print(json.dumps({'status':'prepared','admission':str(out/'admission.json'),'tasks':len(tasks)},indent=2))
        return 0
    if not args.task:ap.error('--task required unless --prepare')
    admission_path=(args.admission or out/'admission.json').resolve()
    admission=json.loads(admission_path.read_text())
    matches=[t for t in admission['tasks'] if t['id']==args.task]
    if len(matches)!=1:ap.error('unknown task')
    t=matches[0]
    # Outer driver is excluded from accounting; the backend records every leaf.
    command=[sys.executable,'-m','experiments.arithmetic_dse.backend','--platform',t['platform'],
             '--rtl',t['rtl'],'--top',t['top'],'--out',str(out/'runs'/t['id']),
             '--period-ps',str(t['period_ps']),'--stage',t['stage'],
             '--admission',str(admission_path),'--admission-id',admission['id'],'--task-id',t['id']]
    import subprocess
    return subprocess.call(command,cwd=ROOT)


if __name__=='__main__':raise SystemExit(main())
