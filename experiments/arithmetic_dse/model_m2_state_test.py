"""Independent state-bank collection and one frozen-parameter evaluation.

No fitting occurs here. Test source IDs were registered before collection;
the complete train/validation replay and byte-reproduced selection are bound
before the first test tool call. Failed attempts require a new admission.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import copy
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import shutil
from types import SimpleNamespace

from .budget import Ledger, POLICY, usage
from .model_collection import sha, write
from . import model_m2_state_collection as base
from .model_m2_state_collection_v2 import state_witness
from .model_m2_state_collection_v3 import rtl_ports
from .model_m2_state_fit import verify as verify_fit, quality, predict
from .model_m2_state_replay import RawAudit, reparse

ROOT, CONFIG, SUFFIX = base.ROOT, base.CONFIG, base.SUFFIX
VERSION = 'asap7-m2-state-independent-admission-v1'


def verify(folder):
    a = base.read(folder/'admission.json')
    selection = Path(a['selection_path'])
    f = verify_fit(selection.parent)
    if (a['version'] != VERSION or sha(selection) != a['selection_sha256']
        or f['status'] != 'frozen_awaiting_independent_test' or f['test_observed']
        or sha(CONFIG) != a['protocol_sha256'] or sha(POLICY) != a['policy_sha256']
        or sha(a['fitting_admission_path']) != a['fitting_admission_sha256']):
        raise ValueError('state independent freeze/admission changed')
    for name,h in a['sources'].items():
        if sha(ROOT/name) != h or sha(folder/'source'/name) != h:
            raise ValueError('state independent producer changed: '+name)
    for t in a['tasks']:
        if (t['split'] != 'test' or sha(t['rtl']) != t['rtl_sha256']
            or sha(t['sample_contract']) != t['sample_contract_sha256']):
            raise ValueError('independent state source/role changed')
    return a


def prepare(folder, fitting, selection, reproduced):
    from .model_m2_state_collection_v4 import verify as verify_collection
    original = verify_collection(fitting)
    f = verify_fit(selection.parent)
    cfg = base.read(CONFIG)
    if (f['status'] != 'frozen_awaiting_independent_test' or f['test_observed']
        or f['admission_sha256'] != sha(fitting/'admission.json')):
        raise ValueError('state validation/freeze not ready')
    for name in ('candidate.json','validation.json','selection-freeze.json'):
        if (selection.parent/name).read_bytes() != (reproduced/name).read_bytes():
            raise ValueError('state fit must reproduce byte-identically')
    tasks = copy.deepcopy([t for t in original['tasks'] if t['split']=='test'])
    if len(tasks) != 36 or any((fitting/'runs'/t['id']).exists() for t in tasks):
        raise ValueError('36 unobserved registered state tests required')
    ledger = base.read(Ledger().path)
    current, limits = usage(ledger['entries']), base.read(POLICY)['resources']
    later = cfg['later_work_reserved']
    envelope = len(tasks)*cfg['resources']['per_task_walltime_envelope_s']+600
    if (current['walltime_s']+envelope+later['walltime_s'] > limits['max_global_walltime_h']*3600
        or current['CPU_time_s']+4*envelope+later['CPU_time_s'] > limits['max_tool_CPU_time_h']*3600
        or current['synth']+36+later['synth'] > limits['max_synthesis_calls']
        or current['grt']+36+later['grt'] > limits['max_global_route_calls']
        or shutil.disk_usage(folder.parent).free < 36*cfg['resources']['storage_per_task_bytes']+later['storage_bytes']):
        raise ValueError('independent state cohort/later reserve not funded')
    folder.mkdir(parents=True,exist_ok=False)
    sources = dict(original['sources'])
    paths = [Path(__file__),Path(__file__).with_name('model_m2_state_replay.py'),
             Path(__file__).with_name('model_m2_state_fit.py'),Path(__file__).with_name('model_training.py')]
    sources.update({str(p.relative_to(ROOT)):sha(p) for p in paths})
    for name in sources:
        dst=folder/'source'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dst)
    base.exclusive(folder/'admission.json',{'version':VERSION,'id':folder.name,'tasks':tasks,'sources':sources,
        'protocol_sha256':sha(CONFIG),'policy_sha256':sha(POLICY),
        'selection_path':str(selection),'selection_sha256':sha(selection),
        'candidate_sha256':f['candidate_sha256'],'fitting_admission_path':str(fitting/'admission.json'),
        'fitting_admission_sha256':sha(fitting/'admission.json'),
        'measurement_static_identity_sha256':original['measurement_static_identity_sha256'],
        'capacity_pilot':cfg['independent_capacity_pilot'],
        'resource_plan':{'tasks':36,'leaf_walltime_envelope_s':envelope,'CPU_envelope_s':4*envelope,'later_reserved':later},
        'threads':4,'parallel_jobs':4,'automatic_retries':0,
        'evaluation':'frozen area gates per stage; frozen boundary >= max test H + max test control QD per exact target',
        'test_role':'new state packing/control/reset contexts at exposed widths; no fit or margin adaptation',
        'stage_composition_or_native_D_admitted':False})
    write(folder/'progress.json',{'phase':'independent_admitted','active':[],'completed':[],
        'waiting':[t['id'] for t in tasks],'errors':[],'capacity_qualified':False,'test_locked':False})
    verify(folder)
    print(json.dumps({'status':'independent_admitted','tasks':36,'selection_sha256':sha(selection),
                      'capacity_pilot':cfg['independent_capacity_pilot'],'walltime_envelope_s':envelope}),flush=True)


class TestLedger(Ledger):
    def __init__(self, folder, task):
        super().__init__()
        self.folder, self.task = folder, task

    def reserve(self, stage, timeout_s, threads, purpose, command, output, *, context=None):
        a = verify(self.folder)
        t = next(x for x in a['tasks'] if x['id']==self.task['id'])
        if t != self.task or threads != 4:
            raise ValueError('unregistered independent state tool call')
        return super().reserve(stage, timeout_s, threads, purpose, command, output,context={**(context or {}),
            'target_platform':'asap7','admission_id':a['id'],'task_id':t['id'],
            'admission_sha256':sha(self.folder/'admission.json'),'selection_freeze_sha256':a['selection_sha256'],
            'model_version':'asap7-m2-state-bank-independent-v1'})


def run_task(folder, t):
    from .backend import _evaluate, stage_metrics, verify_orfs_area
    from .model_m2_mux_collection import render_cts
    from .model_m2_live_cec_v3 import verify_proof
    from .model_m2_evaluate import measurement_identity
    from .model_samples import read_labels
    from .platforms import profile, verify_wire_readback, resolve_environment, validate_environment
    from .processes import run_command
    from . import backend, sdc
    # Match the qualified v4 singleton naming; no constraint is removed.
    backend.rtl_ports = sdc.rtl_ports = rtl_ports
    a = verify(folder)
    if t not in a['tasks'] or t['split'] != 'test':
        raise ValueError('only registered independent state tests may execute')
    out = folder/'runs'/t['id']
    if out.exists():
        raise ValueError('preserve independent state attempt; no automatic retry')
    ledger = TestLedger(folder,t)
    context = {'target_platform':'asap7','admission_id':a['id'],'task_id':t['id']}
    env=os.environ.copy();env.update(OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',YOSYS_MAX_THREADS='4',
        PYTHONDONTWRITEBYTECODE='1',QT_QPA_PLATFORM='offscreen',VULSIM_LABEL_REQUESTS=str(out/'label_requests.tcl'))
    with ledger.job(context):
        if t['mapping_source_task']:
            m, command = base.seed_mapping(folder,t,out)
        else:
            args=SimpleNamespace(out=out,platform='asap7',threads=4,stage='synth',memory_limit_mib=8192,
                period_ps=t['period_ps'],period_role='resource_trial',abc_target_ps=1500,io_delay_max_ps=None,
                budget_purpose='characterization',admission_id=a['id'],task_id=t['id'],sample_contract=Path(t['sample_contract']),
                admission=None,resume_synth_from=None,orfs=base.ORFS,rtl=Path(t['rtl']),top='ModelBundle',
                synth_timeout_s=300,route_timeout_s=1200,selection_freeze=None)
            _evaluate(args,ledger)
            m=base.read(out/'manifest.json')
            if m['status']!='completed':
                raise RuntimeError('independent state synthesis failed: '+str(m.get('failure_reason')))
            command=next(c['command'][:-1] for c in m['commands'] if c['log'].endswith('/synth.log'))
        m.update(status='running',stages_requested='grt',budget_job_id=ledger.job_id,
            admission_id=a['id'],task_id=t['id'],state_admission_sha256=sha(folder/'admission.json'),
            selection_freeze_sha256=a['selection_sha256'],candidate_sha256=a['candidate_sha256'])
        def save():
            write(out/'manifest.json',m)
        def execute(cmd,stem,timeout,stage=None):
            m['active_stage']=stem
            r=ledger.reserve(stage,timeout,4,'independent_state_test',cmd,out/stem,context=context)
            m['active_reservation']=r['id'];save()
            c=run_command(cmd,out,stem,timeout,env,8192,cpu_limit_s=r['CPU_time_s'])
            ledger.finish(r,c);c['budget_reservation_id']=r['id'];m['commands'].append(c);save()
            if c['exit_code']:
                raise RuntimeError(stem+': failed; timeout='+str(c['timed_out']))
        try:
            for name in ('model_m2_state_test.py','model_m2_state_samples.py'):
                path=Path(__file__).with_name(name);dst=out/'source'/path.relative_to(ROOT)
                dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dst)
                m['source_sha256'][str(path.relative_to(ROOT))]=sha(path)
            wrapper=out/'live-cec.py'
            wrapper.write_text('import sys\nsys.path.insert(0,'+repr(str(ROOT))+')\nfrom experiments.arithmetic_dse.model_m2_live_cec_v3 import main\nmain()\n')
            request=out/'live-cec-request.json'
            write(request,{'libraries':m['libraries'],'admission_sha256':sha(folder/'admission.json'),
                'collection_plan_sha256':sha(folder/'admission.json'),'selection_sha256':a['selection_sha256']})
            cts=out/'flow-scripts/cts.tcl';cts.unlink()
            cts.write_text(render_cts((base.ORFS/'flow/scripts/cts.tcl').read_text(),wrapper,request,
                out/'logs'/SUFFIX/'structural_cec'))
            m['files_sha256'].update({str(p):sha(p) for p in (cts,wrapper,request,out/'config.mk')})
            for asset in [*m['tools'].values(),*m['libraries']]:
                if sha(asset['path'])!=asset['sha256']:
                    raise ValueError('independent state physical identity changed')
            for name,h in m['files_sha256'].items():
                path=Path(name)
                if (path.is_relative_to(base.ORFS) or path.is_relative_to(ROOT/'experiments/arithmetic_dse/backend')) and sha(path)!=h:
                    raise ValueError('independent state physical asset changed')
            if t['mapping_source_task']:
                execute(command+['vulsim-environment','VULSIM_ENV_FILE='+str(out/'effective-environment.txt')],'environment',60)
                raw=dict(line.strip().split('=',1) for line in (out/'effective-environment.txt').read_text().splitlines() if line.strip())
                effective,origins=resolve_environment(raw);validate_environment(effective,profile('asap7'))
                for key in ('LIB_FILES','TECH_LEF','SC_LEF','CORNER','ASAP7_USE_VT','LIB_MODEL',
                            'TC_TEMPERATURE','ABC_DRIVER_CELL','ABC_LOAD_IN_FF','YOSYS_MAX_THREADS'):
                    if effective.get(key)!=m['effective_environment'].get(key):
                        raise ValueError('independent state mapping environment changed: '+key)
                m.update(raw_make_environment=raw,effective_environment=effective,asset_resolution=origins)
                execute(command+['synth'],'synth',300,'synth')
                execute(command+['run','RUN_SCRIPT='+str(ROOT/'experiments/arithmetic_dse/backend/snapshot.tcl'),
                    'RUN_LOG_NAME_STEM=vulsim_synth','VULSIM_EVAL_STAGE=synth',
                    'VULSIM_EVAL_DB=1_synth.odb','VULSIM_EVAL_SDC=1_synth.sdc'],'synth-snapshot',120)
                m['metrics']=[]
            p=profile('asap7')
            if p['profile_sha256']!=t['profile_sha256'] or measurement_identity(m)!=a['measurement_static_identity_sha256']:
                raise ValueError('independent state differs from fitting physical identity')
            cells=base.read(out/'liberty_cells.json')['cells']
            for stage in ('synth','grt'):
                if stage=='grt':
                    execute(command+['grt'],'grt',1200,'grt')
                    execute(command+['run','RUN_SCRIPT='+str(ROOT/'experiments/arithmetic_dse/backend/snapshot.tcl'),
                        'RUN_LOG_NAME_STEM=vulsim_grt','VULSIM_EVAL_STAGE=grt',
                        'VULSIM_EVAL_DB=5_1_grt.odb','VULSIM_EVAL_SDC=5_1_grt.sdc'],'grt-snapshot',120)
                reports=out/'reports'/SUFFIX
                g=stage_metrics(reports,stage,cells,t['period_ps'],selected=p)
                g['model_labels']=read_labels(reports/('vulsim_'+stage),out/'sample-contract.json',g['raw_report_units']['time']['to_ps'])
                g['state_witness']=state_witness(out,stage,cells)
                wire=verify_wire_readback(reports/('vulsim_'+stage+'_layer_rc.tsv'),p)
                if wire is not None:
                    g['wire_RC_readback']=wire
                stem={'synth':'1_synth','grt':'5_1_grt'}[stage]
                actual_sdc=out/'results'/SUFFIX/(stem+'.sdc')
                m['sdc_contracts'][stage]=sdc.verify_sdc(actual_sdc.read_text(),p,t['period_ps'],rtl_ports((out/'input.sv').read_text(),t['top']))
                native=base.read(out/'logs'/SUFFIX/(stem+'.json'))[('synth' if stage=='synth' else 'globalroute')+'__design__instance__area__stdcell']
                g['orfs_area_crosscheck']=verify_orfs_area(g['cell_area_um2'],native)
                if not g['timing_coverage_complete']:
                    raise ValueError('independent state timing coverage incomplete')
                m['metrics']=[x for x in m['metrics'] if x['stage']!=stage]+[g];save()
            verify_proof(out/'logs'/SUFFIX/'structural_cec/proof.json',
                out/'results'/SUFFIX/'4_before_rsz_lec.v',out/'results'/SUFFIX/'4_after_rsz_lec.v')
            m['status']='completed';write(out/'metrics.json',m['metrics'])
        except Exception as error:
            m.update(status='failed',failure_stage=m.get('active_stage','test_preflight'),failure_reason=str(error))
        finally:
            m['finished_at']=datetime.now(timezone.utc).isoformat()
            m['evidence_sha256']={str(p.relative_to(out)):sha(p) for name in ('logs','reports','results') for p in (out/name).rglob('*') if p.is_file()}
            save()
        print(json.dumps({'task':t['id'],'status':m['status'],'reason':m.get('failure_reason')}),flush=True)
        if m['status']!='completed':
            raise RuntimeError(t['id']+': '+m['failure_reason'])
    return t['id']


def run(folder):
    a=verify(folder);indexed={t['id']:t for t in a['tasks']}
    with (folder/'advance.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if any((folder/'runs'/tid).exists() for tid in indexed):
            raise ValueError('preserve independent attempts; explicit successor required')
        waiting=list(indexed);active={};completed=[];errors=[];capacity=False
        with ThreadPoolExecutor(max_workers=4) as pool:
            while waiting or active:
                if not capacity and a['capacity_pilot'] in completed:
                    d=folder/'runs'/a['capacity_pilot'];m=base.read(d/'manifest.json')
                    base.exclusive(folder/'capacity-proof.json',{'status':'passed','task_id':a['capacity_pilot'],
                        'manifest_sha256':sha(d/'manifest.json'),
                        'actual_register_bits':m['metrics'][-1]['state_witness']['actual_register_bits'],
                        'peak_RSS_MiB':max(c['sampled_process_tree_peak_rss_KiB'] for c in m['commands'])/1024,
                        'scope':'registered independent state bank only; no stage/D qualification'})
                    capacity=True
                while waiting and len(active)<4 and not errors:
                    ready=next((tid for tid in waiting if (capacity or tid==a['capacity_pilot'])
                        and (not indexed[tid]['mapping_source_task'] or indexed[tid]['mapping_source_task'] in completed)),None)
                    if ready is None:
                        break
                    waiting.remove(ready);active[pool.submit(run_task,folder,indexed[ready])]=ready
                write(folder/'progress.json',{'phase':'independent_collecting','active':list(active.values()),
                    'waiting':waiting,'completed':completed,'errors':errors,'capacity_qualified':capacity,'test_locked':False})
                if not active:
                    if waiting and not errors:
                        raise ValueError('independent mapping/capacity dependency deadlock')
                    break
                done,_=wait(active,timeout=1,return_when=FIRST_COMPLETED)
                for future in done:
                    tid=active.pop(future)
                    try:
                        completed.append(future.result())
                    except Exception as error:
                        errors.append({'task_id':tid,'reason':str(error)})
        write(folder/'progress.json',{'phase':'stopped_on_error' if errors else 'test_collection_complete',
            'active':[],'waiting':waiting,'completed':completed,'errors':errors,'capacity_qualified':capacity,'test_locked':False})
        if errors:
            raise RuntimeError(str(errors))


def evaluate(folder, out):
    """Exclusive once-only verdict; subsequent checking never selects/refits."""
    a=verify(folder);p=base.read(folder/'progress.json')
    if (p['phase']!='test_collection_complete' or set(p['completed'])!={t['id'] for t in a['tasks']}
        or p['active'] or p['waiting'] or p['errors']):
        raise ValueError('complete independent cohort required')
    out.mkdir(parents=True,exist_ok=False)
    base.exclusive(folder/'evaluation-claim.json',{'selection_sha256':a['selection_sha256'],
        'admission_sha256':sha(folder/'admission.json'),'output':str(out),
        'mode':'once-only frozen state evaluation; never algorithm or margin selection'})
    base.exclusive(out/'evaluation-started.json',{'selection_sha256':a['selection_sha256'],
        'admission_sha256':sha(folder/'admission.json'),'refit_or_margin_change':False})
    candidate=base.read(Path(a['selection_path']).parent/'candidate.json');cfg=base.read(CONFIG)
    fitting=base.read(base.read(a['selection_path'])['dataset_path'])
    fitting_sources={r['source_sha256'] for r in fitting['rows']}
    audit=RawAudit(base.read(Ledger().path)['entries']);rows=[]
    for t in a['tasks']:
        if t['rtl_sha256'] in fitting_sources:
            raise ValueError('test source crossed state fitting boundary')
        d=folder/'runs'/t['id'];audit.ancestry(d)
        m,metrics,identity=reparse(d,t)
        if (m['selection_freeze_sha256']!=a['selection_sha256'] or m['candidate_sha256']!=a['candidate_sha256']
            or identity!=a['measurement_static_identity_sha256']):
            raise ValueError('independent state selection/physical identity mismatch')
        for c in m['commands']:
            if audit.entries[c['budget_reservation_id']].get('selection_freeze_sha256')!=a['selection_sha256']:
                raise ValueError('independent state leaf missing frozen selection')
        for g in metrics:
            witness=g['state_witness']
            rows.append({'id':t['id']+'/'+g['stage'],'stage':g['stage'],'period_ps':t['period_ps'],
                'features':t['features'],'state_area_um2':g['cell_area_um2']-witness['excluded_observer_area_um2'],
                'paths':[{'H_ps':t['period_ps']-x['data_delay_ps']-x['slack_ps'],'QD_ps':x['data_delay_ps']} for x in g['model_labels']],
                'whole_setup_slack_ps':g['setup_worst_slack_ps'],'whole_hold_slack_ps':g['hold_worst_slack_ps'],
                'manifest_sha256':sha(d/'manifest.json')})
    result={}
    for stage in ('synth','grt'):
        group=[r for r in rows if r['stage']==stage];model=candidate['stages'][stage]
        area=quality(model['area_model'],group,cfg)
        b=model['boundary_model'];coverage={}
        for period in cfg['SDC_ps']:
            paths=[x for r in group if r['period_ps']==period for x in r['paths']]
            required=max(0.,max(x['H_ps'] for x in paths))+max(0.,max(x['QD_ps'] for x in paths))
            margin=min(b['input_overhead_ps'],b['register_overhead_ps'])-required
            coverage[str(period)]={'status':'passed' if margin>=0 else 'failed','required_H_plus_control_ps':required,
                'frozen_overhead_ps':b['register_overhead_ps'],'margin_ps':margin}
        passed=area['status']=='passed' and all(c['status']=='passed' for c in coverage.values())
        result[stage]={'status':'passed' if passed else 'failed','state_area':area,
            'state_area_by_exact_SDC':{str(t):quality(model['area_model'],[r for r in group if r['period_ps']==t],cfg) for t in cfg['SDC_ps']},
            'boundary_coverage':coverage,'whole_setup_failed':sum(r['whole_setup_slack_ps']<0 for r in group),
            'whole_hold_negative':sum(r['whole_hold_slack_ps']<0 for r in group)}
    write(out/'test-dataset.json',{'version':'asap7-m2-state-independent-dataset-v1','rows':rows,
        'admission_sha256':sha(folder/'admission.json'),'selection_sha256':a['selection_sha256']})
    write(out/'verdict.json',{'version':'asap7-m2-state-independent-verdict-v1',
        'status':result['grt']['status'],'stages':result,'selection_sha256':a['selection_sha256'],
        'candidate_sha256':a['candidate_sha256'],'admission_sha256':sha(folder/'admission.json'),
        'test_dataset_sha256':sha(out/'test-dataset.json'),'test_tasks':36,'stage_rows':len(rows),
        'PPA_calls_during_evaluation':0,'parameters_or_margins_changed':False,
        'state_bank_only':True,'native_state_binding_qualified':False,'full_D_ready':False})
    print(json.dumps({'status':result['grt']['status'],'stages':{k:{'status':v['status'],
        'area_median_relative_error':v['state_area']['median_relative_error'],
        'area_p95_relative_error':v['state_area']['p95_relative_error'],'boundary':v['boundary_coverage']} for k,v in result.items()}}),flush=True)


def status(folder):
    a,p=base.read(folder/'admission.json'),base.read(folder/'progress.json')
    counts=Counter()
    for t in a['tasks']:
        path=folder/'runs'/t['id']/'manifest.json';m=base.read(path) if path.exists() else {}
        counts[m.get('status','not_started')]+=1
        if m.get('status')=='running':
            print('任务：',t['id'],'阶段：',m.get('active_stage'))
    print(datetime.now().astimezone().isoformat(timespec='seconds'))
    print('ASAP7状态／边界独立测试：'+p['phase'])
    print(f'完成{counts["completed"]}/36；{dict(counts)}；容量准入：{p["capacity_qualified"]}')
    print('最多4任务×4线程／8GiB；参数与裕量已冻结，采完停止，不自动评价或发布。')
    print('错误：',p['errors'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('prepare','run','verify','status','evaluate'))
    parser.add_argument('--folder',type=Path,required=True)
    parser.add_argument('--fitting',type=Path)
    parser.add_argument('--selection',type=Path)
    parser.add_argument('--reproduced',type=Path)
    parser.add_argument('--out',type=Path)
    args=parser.parse_args();folder=args.folder.resolve()
    if args.action=='prepare':
        if None in (args.fitting,args.selection,args.reproduced):
            parser.error('prepare requires fitting/selection/reproduced')
        prepare(folder,args.fitting.resolve(),args.selection.resolve(),args.reproduced.resolve())
    elif args.action=='run':
        run(folder)
    elif args.action=='status':
        status(folder)
    elif args.action=='evaluate':
        if args.out is None:
            parser.error('evaluate requires out')
        evaluate(folder,args.out.resolve())
    else:
        verify(folder);print('verified independent state admission')


if __name__=='__main__':
    main()
