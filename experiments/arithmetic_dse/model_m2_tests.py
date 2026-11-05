"""One-shot frozen F4 collection, with exact t0 mapping reuse and structural CEC.

The original fitting producer and its hard test lock remain immutable. This
successor owns the 56 preregistered tests and verifies its selection before
using the generic synth evaluator or starting any physical continuation.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import copy
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
from types import SimpleNamespace

from .budget import Ledger, POLICY, usage
from .model_collection import sha, write
from .model_m2_fit_v2 import verify_fit

ROOT=Path(__file__).resolve().parents[2]
SUFFIX=Path('asap7/arithmetic_probe/base')
ORFS=Path('/home/zyrv/OpenROAD-flow-scripts')


def read(path):return json.loads(Path(path).read_text())


def exclusive(path,value):
    with Path(path).open('x') as stream:json.dump(value,stream,indent=2);stream.write('\n')


def prepare(plan,selection,folder,predecessor=None):
    from .model_m2_collection import verify_plan,sources,CONFIG
    from .model_m2_live_cec import YOSYS,ABC
    f=verify_fit(selection);p=verify_plan(plan)
    if not f['grt_validation_ready'] or f['plan_sha256']!=sha(plan):raise ValueError('test requires complete matching validated selection')
    reproduction=selection.parent.parent/'primitive-refit-v2/reproduction.json'
    if read(reproduction)!= {'status':'passed','parent_fit_sha256':sha(selection.parent/'fit-freeze.json'),'test_labels_read':False}:
        raise ValueError('exact fitting reproduction required')
    tasks=[t for t in p['tasks'] if t['split']=='test']
    if len(tasks)!=56 or any(t['capture_fanout']!=4 or t.get('inherited_run') for t in tasks):raise ValueError('changed preregistered test cohort')
    fitted=read(f['dataset_path'])
    if {t['rtl_sha256'] for t in tasks}&{r['source_sha256'] for r in fitted['rows']}:raise ValueError('test source overlaps fitting')
    lineage=None
    if predecessor:
        old=read(predecessor/'admission.json');progress=read(predecessor/'progress.json')
        if old['selection_sha256']!=sha(selection) or old['plan_sha256']!=sha(plan) or progress['phase']!='stopped_on_error':
            raise ValueError('parser continuation must preserve the identical untouched selection and cohort')
        failures=[]
        inherited=[];abandoned=[]
        for t in tasks:
            prior_task=next(x for x in old['tasks'] if x['id']==t['id'])
            origin=prior_task.get('inherited_run')
            source=Path(origin['directory']) if origin else predecessor/'runs'/t['id'];mp=source/'manifest.json'
            if not mp.exists():
                if source.exists():
                    paid=[e for e in read(Ledger().path)['entries'] if e.get('admission_id')==old['id'] and e.get('task_id')==t['id']]
                    if paid:raise ValueError('unsettled partial test task')
                    abandoned.append({'task_id':t['id'],'directory':str(source),'reason':'preflight only; no backend leaves'})
                continue
            m=read(mp);lec=source/'logs'/SUFFIX/'structural_cec/cec.log'
            if m['status']=='completed':
                if origin and (sha(mp)!=origin['manifest_sha256'] or sha(origin['admission_path'])!=origin['admission_sha256']):raise ValueError('changed inherited test origin')
                original_admission=Path(origin['admission_path']) if origin else predecessor/'admission.json'
                if m.get('test_admission_sha256')!=sha(original_admission) or m.get('selection_freeze_sha256')!=sha(selection):raise ValueError('unbound inherited test')
                t['inherited_run']={'directory':str(source),'manifest_sha256':sha(mp),'admission_path':str(original_admission),
                    'admission_sha256':sha(original_admission)};inherited.append(t['id']);continue
            proof=source/'logs'/SUFFIX/'structural_cec/proof.json'
            constant_failure=(old['id']=='independent-test-v3' and t['id']=='test-F4-binary32-w32-t0' and proof.exists()
                              and read(proof).get('reason')=='incomplete AIG map')
            if (m['status']!='failed' or m['failure_stage']!='grt' or t['mapping_source_task'] or
                not (constant_failure or lec.exists() and re.search(r'^Networks are equivalent after structural hashing\.',lec.read_text(),re.M))):
                raise ValueError('not a named valid-ABC-result parser failure')
            for name in ('4_1_post_repair_pre_lec.odb','4_1_post_repair_pre_lec.sdc','4_before_rsz_lec.v','4_after_rsz_lec.v'):
                path=source/'results'/SUFFIX/name
                if m['evidence_sha256'].get(str(path.relative_to(source)))!=sha(path):raise ValueError('changed test recovery checkpoint')
            t['checkpoint_resume']={'source':str(source),'manifest_sha256':sha(mp)};failures.append(t['id'])
        if (len(failures),len(inherited))==(1,49):
            cfg_path=Path(__file__).with_name('configs')/'model_asap7_m2_test_constant_resume_v1.json';contract=read(cfg_path)
            if (old['id']!=contract['parent'] or failures!=[contract['failed_task']] or set(progress['waiting'])!=set(contract['unstarted_task_ids'])):
                raise ValueError('constant-output continuation differs from frozen contract')
        elif (len(failures),len(inherited)) not in ((4,0),(0,4)):raise ValueError('unsupported explicit test continuation')
        lineage={'admission_path':str((predecessor/'admission.json').resolve()),'admission_sha256':sha(predecessor/'admission.json'),
                 'failed_tasks':failures,'inherited_tasks':inherited,'abandoned_preflight':abandoned,
                 'reason':'explicit parser/provenance continuation; keep completed physical stages and frozen numerical model unchanged'}
        if (len(failures),len(inherited))==(1,49):lineage['constant_output_contract']={'path':str(cfg_path),'sha256':sha(cfg_path)}
    cfg=read(CONFIG);limits=read(POLICY)['resources'];u=usage(read(Ledger().path)['entries']);later=cfg['later_work_reserved']
    allowance=len(tasks)*(300+1200+300)
    if (u['walltime_s']+allowance+later['walltime_s']>limits['max_global_walltime_h']*3600 or
        u['CPU_time_s']+4*allowance+later['CPU_time_s']>limits['max_tool_CPU_time_h']*3600 or
        any(u[s]+len(tasks)+later[s]>limits[k] for s,k in [('synth','max_synthesis_calls'),('grt','max_global_route_calls')])):
        raise ValueError('test cohort and later work not funded')
    folder.mkdir(parents=True,exist_ok=False)
    if shutil.disk_usage(folder).free<len(tasks)*cfg['resource_limits']['storage_per_task_bytes']+15*1024**3:raise ValueError('test storage reserve insufficient')
    paths=list(sources())+[Path(__file__),Path(__file__).with_name('model_m2_live_cec.py'),Path(__file__).with_name('model_m2_cec.py'),
        Path(__file__).with_name('model_m2_fit.py'),Path(__file__).with_name('model_m2_fit_v2.py'),Path(__file__).with_name('model_m2_cec_resume.py'),Path(__file__).with_name('configs')/'model_asap7_m2_fit_v1.json',
        Path(__file__).with_name('configs')/'model_asap7_m2_fit_v2.json',Path(__file__).with_name('model_m2_aig.py'),
        Path(__file__).with_name('configs')/'model_asap7_m2_test_constant_resume_v1.json']
    hashes={}
    for path in paths:
        name=str(path.relative_to(ROOT));dst=folder/'source'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dst);hashes[name]=sha(path)
    a={'version':'asap7-m2-independent-test-admission-v1','id':folder.name,'purpose':'arithmetic_m2_frozen_independent_test',
       'plan_path':str(plan),'plan_sha256':sha(plan),'selection_path':str(selection),'selection_sha256':sha(selection),
       'candidate_sha256':f['candidate_sha256'],'sources':hashes,'policy_sha256':sha(POLICY),'tasks':tasks,
       'parallel_jobs':4,'threads':4,'memory_limit_MiB':8192,'synth_timeout_s':300,'grt_timeout_s':1200,
       'mapping':'one synth t0 per source; later targets reuse exact mapped Verilog, fresh SDC/ODB and physical stages',
       'LEC':'structural complete-boundary CEC with top/D/CLK negative controls inside charged grt process tree',
       'solver_tools':{str(x):sha(x) for x in (YOSYS,ABC)},'sampling_or_quality_gates_changed':False,'automatic_retries':0,
       'walltime_envelope_s':allowance,'CPU_envelope_s':4*allowance,'later_work_reserved':later,'independence':'new F4 capture/source contexts at exposed widths',
       'predecessor':lineage,'root_admission':(old.get('root_admission') or old.get('predecessor') or {
            'admission_path':str((predecessor/'admission.json').resolve()),'admission_sha256':sha(predecessor/'admission.json')}) if predecessor else None}
    exclusive(folder/'admission.json',a)
    if not predecessor:
        exclusive(selection.parent/'test-consumption.json',{'admission_path':str((folder/'admission.json').resolve()),
            'admission_sha256':sha(folder/'admission.json'),'selection_sha256':sha(selection),'policy':'single cohort; failures retained; no automatic retry or tuning'})
    else:
        exclusive(selection.parent/('test-continuation-'+folder.name+'.json'),{'admission_path':str((folder/'admission.json').resolve()),
            'admission_sha256':sha(folder/'admission.json'),'parent_admission_sha256':lineage['admission_sha256'],'model_parameters_changed':False})
    write(folder/'progress.json',{'phase':'admitted','completed':[],'waiting':[t['id'] for t in tasks]})


def verify(folder):
    a=read(folder/'admission.json');f=verify_fit(Path(a['selection_path']))
    if (sha(a['plan_path'])!=a['plan_sha256'] or sha(a['selection_path'])!=a['selection_sha256'] or
        not f['grt_validation_ready'] or f['candidate_sha256']!=a['candidate_sha256'] or sha(POLICY)!=a['policy_sha256']):raise ValueError('changed frozen test identity')
    consumed=read(Path(a['selection_path']).parent/'test-consumption.json')
    owner=a.get('root_admission') or a.get('predecessor') or {'admission_path':str((folder/'admission.json').resolve()),'admission_sha256':sha(folder/'admission.json')}
    if consumed['admission_path']!=owner['admission_path'] or consumed['admission_sha256']!=owner['admission_sha256']:raise ValueError('wrong test consumption owner')
    if a.get('predecessor'):
        continuation=read(Path(a['selection_path']).parent/('test-continuation-'+folder.name+'.json'))
        if (sha(owner['admission_path'])!=owner['admission_sha256'] or continuation['admission_path']!=str((folder/'admission.json').resolve())
            or continuation['admission_sha256']!=sha(folder/'admission.json')):raise ValueError('changed explicit parser continuation')
        ancestor=a['predecessor']
        while ancestor:
            if sha(ancestor['admission_path'])!=ancestor['admission_sha256']:raise ValueError('changed test admission ancestor')
            ancestor=read(ancestor['admission_path']).get('predecessor')
    for name,h in a['sources'].items():
        if sha(ROOT/name)!=h or sha(folder/'source'/name)!=h:raise ValueError('changed test producer: '+name)
    for name,h in a['solver_tools'].items():
        if sha(name)!=h:raise ValueError('changed CEC tool')
    return a


class TestLedger(Ledger):
    def __init__(self,folder):super().__init__();self.folder=folder
    def reserve(self,stage,timeout_s,threads,purpose,command,output,*,context=None):
        a=verify(self.folder)
        return super().reserve(stage,timeout_s,threads,purpose,command,output,context={**context,
            'admission_sha256':sha(self.folder/'admission.json'),'selection_freeze_sha256':a['selection_sha256'],'model_version':'asap7-m2-primitives-candidate-v2'})


def render_cts(original,wrapper,request,proof):
    marker='    run_lec_test 4_rsz 4_before_rsz_lec.v 4_after_rsz_lec.v'
    if original.count(marker)!=1:raise ValueError('unsupported independent-test CTS')
    return original.replace(marker,'    orfs_write_db $::env(RESULTS_DIR)/4_1_post_repair_pre_lec.odb\n'
        '    orfs_write_sdc $::env(RESULTS_DIR)/4_1_post_repair_pre_lec.sdc\n'
        f'    exec {{{sys.executable}}} -B {{{wrapper}}} --request {{{request}}} --before $::env(RESULTS_DIR)/4_before_rsz_lec.v --after $::env(RESULTS_DIR)/4_after_rsz_lec.v --out {{{proof}}}\n'
        '    puts "Repair timing output passed complete structural CEC"')


def physical_base(manifest):
    # A continuation may inherit its synth metric and pay only CTS/grt leaves.
    # Its exact make configuration is equally available on the grt command.
    for stem in ('synth.log','grt.log'):
        matches=[c['command'][:-1] for c in manifest['commands'] if c['log'].endswith('/'+stem)]
        if matches:return matches[0]
    raise ValueError('no preserved physical make configuration')


def run_task(folder,t):
    from .backend import _evaluate,stage_metrics,verify_orfs_area
    from .processes import run_command
    from .model_samples import read_labels,verify_capture_banks
    from .sdc import verify_sdc,rtl_ports
    from .platforms import resolve_environment,validate_environment,profile,verify_wire_readback
    a=verify(folder);out=folder/'runs'/t['id'];out.parent.mkdir(exist_ok=True)
    if out.exists():raise ValueError('test attempt already exists; preserve it')
    if sha(t['rtl'])!=t['rtl_sha256'] or sha(t['sample_contract'])!=t['sample_contract_sha256']:raise ValueError('changed preregistered test source')
    ledger=TestLedger(folder);context={'target_platform':'asap7','admission_id':a['id'],'task_id':t['id']}
    env=os.environ.copy();env.update(OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',YOSYS_MAX_THREADS='4',QT_QPA_PLATFORM='offscreen',
        PYTHONDONTWRITEBYTECODE='1',VULSIM_LABEL_REQUESTS=str(out/'label_requests.tcl'))
    with ledger.job(context):
        checkpoint=t.get('checkpoint_resume')
        if checkpoint:
            source=Path(checkpoint['source']);old=read(source/'manifest.json')
            if sha(source/'manifest.json')!=checkpoint['manifest_sha256']:raise ValueError('changed parser-failure source')
            out.mkdir();m=copy.deepcopy(old);m.update(commands=[],status='running',metrics=[copy.deepcopy(old['metrics'][0])],
                admission_id=a['id'],budget_job_id=ledger.job_id,started_at=datetime.now(timezone.utc).isoformat())
            for k in ('failure_stage','failure_reason','failure_code','finished_at','evidence_sha256'):m.pop(k,None)
            for name in ('input.sv','sample-contract.json','liberty_cells.json','label_requests.tcl'):shutil.copy2(source/name,out/name)
            if sha(out/'input.sv')!=t['rtl_sha256'] or sha(out/'sample-contract.json')!=t['sample_contract_sha256']:raise ValueError('parser continuation changed original test source')
            shutil.copytree(source/'source',out/'source')
            for group in ('results','reports'):
                for path in (source/group).rglob('*'):
                    if not path.is_file():continue
                    rel=path.relative_to(source)
                    if old['evidence_sha256'].get(str(rel))!=sha(path):raise ValueError('changed retained test evidence')
                    dst=out/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dst)
            for path in (source/'logs'/SUFFIX).glob('1_synth*'):
                if not path.is_file():continue
                rel=path.relative_to(source)
                if old['evidence_sha256'].get(str(rel))!=sha(path):raise ValueError('changed retained synth log')
                dst=out/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dst)
            scripts=out/'flow-scripts';scripts.mkdir()
            for pth in (source/'flow-scripts').iterdir():
                if pth.is_symlink():(scripts/pth.name).symlink_to(pth.resolve())
                elif pth.is_file():shutil.copy2(pth,scripts/pth.name)
            (out/'config.mk').write_text((source/'config.mk').read_text().replace(str(source),str(out)))
            base=next(c['command'][:-1] for c in old['commands'] if c['log'].endswith('/grt.log'))
            base=[x.replace(str(source),str(out)) for x in base if not x.startswith('--assume-old=')]
            m['metrics'][0]['raw_reports_prefix']=str(out/'reports'/SUFFIX/'vulsim_synth')
            m['files_sha256']={name.replace(str(source),str(out)):h for name,h in old['files_sha256'].items()}
            m['checkpoint_reuse']={'mode':'exact_postrepair_ODB_parser_continuation','source_run':str(source),
                'source_manifest_sha256':checkpoint['manifest_sha256'],'no_CTS_repair_replay':True,'cold_runtime_claimed':False}
            reused=False
        elif not t['mapping_source_task']:
            args=SimpleNamespace(out=out,platform='asap7',threads=4,stage='synth',memory_limit_mib=8192,period_ps=t['period_ps'],
                period_role='resource_trial',abc_target_ps=1500,io_delay_max_ps=None,budget_purpose='characterization',admission_id=a['id'],task_id=t['id'],
                sample_contract=Path(t['sample_contract']),admission=None,resume_synth_from=None,orfs=ORFS,rtl=Path(t['rtl']),top='ModelBundle',
                synth_timeout_s=300,route_timeout_s=1200,selection_freeze=Path(a['selection_path']))
            _evaluate(args,ledger)
            m=read(out/'manifest.json')
            if m['status']!='completed':raise RuntimeError('test t0 synthesis failed: '+str(m.get('failure_reason')))
            base=next(c['command'][:-1] for c in m['commands'] if c['log'].endswith('/synth.log'))
            reused=False
        else:
            source_task=next(x for x in a['tasks'] if x['id']==t['mapping_source_task'])
            inherited=source_task.get('inherited_run')
            source=Path(inherited['directory']) if inherited else folder/'runs'/t['mapping_source_task'];old=read(source/'manifest.json')
            if inherited and sha(source/'manifest.json')!=inherited['manifest_sha256']:raise ValueError('changed inherited test t0')
            if old['status']!='completed':raise ValueError('test t0 mapping not complete')
            out.mkdir();m=copy.deepcopy(old);m.update(commands=[],metrics=[],task_id=t['id'],status='running',period_ps=t['period_ps'],
                started_at=datetime.now(timezone.utc).isoformat(),budget_job_id=ledger.job_id)
            m.pop('finished_at',None);m.pop('evidence_sha256',None)
            for name in ('input.sv','sample-contract.json','liberty_cells.json','label_requests.tcl'):
                shutil.copy2(source/name,out/name)
            shutil.copytree(source/'source',out/'source')
            scripts=out/'flow-scripts';scripts.mkdir()
            for p in (source/'flow-scripts').iterdir():
                if p.is_symlink():(scripts/p.name).symlink_to(p.resolve())
                elif p.is_file():shutil.copy2(p,scripts/p.name)
            (out/'config.mk').write_text(re.sub(r'export VULSIM_CLOCK_PERIOD_PS = [^\n]+','export VULSIM_CLOCK_PERIOD_PS = '+str(t['period_ps']),
                (source/'config.mk').read_text().replace(str(source),str(out))))
            results=out/'results'/SUFFIX;results.mkdir(parents=True)
            original=source/'results'/SUFFIX/'1_2_yosys.v'
            if sha(original)!=old['evidence_sha256'][str(original.relative_to(source))]:raise ValueError('changed test t0 mapped netlist')
            if sha(out/'input.sv')!=t['rtl_sha256'] or sha(out/'sample-contract.json')!=t['sample_contract_sha256']:raise ValueError('test mapping source changed RTL/contract')
            for tool in old['tools'].values():
                if sha(tool['path'])!=tool['sha256']:raise ValueError('changed test physical executable')
            for lib in old['libraries']:
                if sha(lib['path'])!=lib['sha256']:raise ValueError('changed test physical Liberty')
            for name,h in old['files_sha256'].items():
                path=Path(name)
                if (path.is_relative_to(ORFS) or path.is_relative_to(ROOT/'experiments/arithmetic_dse/backend')) and sha(path)!=h:
                    raise ValueError('changed test physical asset')
            shutil.copy2(original,results/original.name)
            base=physical_base(old)
            base=[x.replace(str(source),str(out)) for x in base if not x.startswith('--assume-old=')]
            base.append('--assume-old='+str(results/'1_2_yosys.v'))
            m['files_sha256']={name.replace(str(source),str(out)):h for name,h in old['files_sha256'].items()}
            m['mapping_context']['sdc_period_ps']=t['period_ps']
            m['mapping_context_sha256']=hashlib.sha256(json.dumps(m['mapping_context'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
            m['checkpoint_reuse']={'mode':'exact_t0_mapping_fresh_SDC_ODB','source_run':str(source),'source_manifest_sha256':sha(source/'manifest.json'),
                                  'source_netlist_sha256':sha(original),'old_ODB_or_SDC_copied':False,'Yosys_ABC_reexecuted':False}
            reused=True
        m.update(status='running',stages_requested='grt',admission_id=a['id'],budget_job_id=ledger.job_id,selection_freeze_sha256=a['selection_sha256'],test_admission_sha256=sha(folder/'admission.json'),
            active_stage='test_physical_preflight',test_collection_version=a['version'])
        def save():write(out/'manifest.json',m)
        def execute(command,stem,timeout,stage=None):
            r=ledger.reserve(stage,timeout,4,'characterization',command,out/stem,context=context);m['active_reservation']=r['id'];save()
            c=run_command(command,out,stem,timeout,env,8192,cpu_limit_s=r['CPU_time_s']);ledger.finish(r,c);c['budget_reservation_id']=r['id'];m['commands'].append(c);save()
            if c['exit_code']:raise RuntimeError(stem+': failed, timeout='+str(c['timed_out']))
        try:
            results=out/'results'/SUFFIX;reports=out/'reports'/SUFFIX;cells=read(out/'liberty_cells.json')['cells'];p=profile('asap7')
            if p['profile_sha256']!=t['profile_sha256']:raise ValueError('changed test platform')
            wrapper=out/'live-cec.py';wrapper.write_text('import sys\nsys.path.insert(0,'+repr(str(ROOT))+')\nfrom experiments.arithmetic_dse.model_m2_live_cec import main\nmain()\n')
            request=out/'live-cec-request.json';write(request,{'libraries':m['libraries'],'admission_sha256':sha(folder/'admission.json'),'selection_sha256':a['selection_sha256']})
            cts=out/'flow-scripts/cts.tcl';cts.unlink();cts.write_text(render_cts((ORFS/'flow/scripts/cts.tcl').read_text(),wrapper,request,out/'logs'/SUFFIX/'structural_cec'))
            m['files_sha256'].update({str(x):sha(x) for x in (cts,wrapper,request,out/'config.mk')})
            if checkpoint:
                from .model_m2_cec_resume import render_cts as render_tail
                m['active_stage']='complete_saved_CEC';save()
                execute([sys.executable,'-B',str(wrapper),'--request',str(request),'--before',str(results/'4_before_rsz_lec.v'),
                    '--after',str(results/'4_after_rsz_lec.v'),'--out',str(out/'logs'/SUFFIX/'structural_cec')],'saved-cec',180)
                verifier=out/'verify-live-pair.py';verifier.write_text('import sys\nfrom pathlib import Path\nsys.path.insert(0,'+repr(str(ROOT))+')\n'
                    'from experiments.arithmetic_dse.model_m2_live_cec import verify_proof\nverify_proof(*map(Path,sys.argv[1:]))\n')
                tail=out/'postrepair-tail.tcl';tail.write_text(render_tail((ORFS/'flow/scripts/cts.tcl').read_text(),
                    out/'logs'/SUFFIX/'structural_cec/proof.json',verifier,True))
                m['active_stage']='CTS_post_LEC';save();execute(base+['run','RUN_SCRIPT='+str(tail),'RUN_LOG_NAME_STEM=4_1_cts_resume'],'cts-post-lec',600,'grt')
                shutil.copy2(results/'4_1_cts.odb',results/'4_cts.odb')
                base+=['--assume-old='+str(results/n) for n in ('4_1_cts.odb','4_cts.odb','4_cts.sdc')]
                m['files_sha256'].update({str(x):sha(x) for x in (verifier,tail)})
            if reused:
                m['active_stage']='environment';execute(base+['vulsim-environment','VULSIM_ENV_FILE='+str(out/'effective-environment.txt')],'environment',60)
                raw=dict(line.strip().split('=',1) for line in (out/'effective-environment.txt').read_text().splitlines() if line.strip())
                effective,origins=resolve_environment(raw);validate_environment(effective,p)
                for k in ('LIB_FILES','TECH_LEF','SC_LEF','CORNER','ASAP7_USE_VT','LIB_MODEL','TC_TEMPERATURE','ABC_DRIVER_CELL','ABC_LOAD_IN_FF','YOSYS_MAX_THREADS'):
                    if effective.get(k)!=old['effective_environment'].get(k):raise ValueError('changed test mapping environment '+k)
                m.update(raw_make_environment=raw,effective_environment=effective,asset_resolution=origins)
            for stage in (('synth','1_synth.odb','1_synth.sdc',300),('grt','5_1_grt.odb','5_1_grt.sdc',1200)):
                name,db,sdc,timeout=stage
                if name=='synth' and not reused:continue
                m['active_stage']=name;save();execute(base+[name],name,timeout,name)
                m.setdefault('sdc_contracts',{})[name]=verify_sdc((results/sdc).read_text(),p,t['period_ps'],rtl_ports((out/'input.sv').read_text(),t['top']))
                execute(base+['run','RUN_SCRIPT='+str(ROOT/'experiments/arithmetic_dse/backend/snapshot.tcl'),'RUN_LOG_NAME_STEM=vulsim_'+name,
                    'VULSIM_EVAL_STAGE='+name,'VULSIM_EVAL_DB='+db,'VULSIM_EVAL_SDC='+sdc],name+'-snapshot',120)
                g=stage_metrics(reports,name,cells,t['period_ps'],selected=p)
                wire=verify_wire_readback(reports/('vulsim_'+name+'_layer_rc.tsv'),p)
                if wire is not None:g['wire_RC_readback']=wire
                g['model_labels']=read_labels(reports/('vulsim_'+name),out/'sample-contract.json',g['raw_report_units']['time']['to_ps'])
                banks=verify_capture_banks(reports/('vulsim_'+name),out/'sample-contract.json',cells)
                if banks:g['model_capture_banks']=banks
                g.update(abc_target_ps=1500,mapping_context_sha256=m['mapping_context_sha256'],target_dependent_measurement=True)
                native=read(out/'logs'/SUFFIX/({'synth':'1_synth.json','grt':'5_1_grt.json'}[name]))[('synth' if name=='synth' else 'globalroute')+'__design__instance__area__stdcell']
                g['orfs_area_crosscheck']=verify_orfs_area(g['cell_area_um2'],native);g['orfs_stdcell_area_um2']=native
                if not g['timing_coverage_complete']:raise ValueError('test timing coverage incomplete')
                m['metrics'].append(g);save()
            proof=read(out/'logs'/SUFFIX/'structural_cec/proof.json')
            if proof['status']!='passed':raise ValueError('test CEC not passed')
            m['status']='completed';write(out/'metrics.json',m['metrics'])
        except Exception as error:m.update(status='failed',failure_stage=m['active_stage'],failure_reason=str(error))
        finally:
            m['finished_at']=datetime.now(timezone.utc).isoformat()
            m['evidence_sha256']={str(x.relative_to(out)):sha(x) for name in ('logs','reports','results') for x in (out/name).rglob('*') if x.is_file()};save()
        print(json.dumps({'task':t['id'],'status':m['status'],'reason':m.get('failure_reason')}),flush=True)
        if m['status']!='completed':raise RuntimeError(t['id']+': '+m['failure_reason'])
    return t['id']


def run(folder):
    a=verify(folder);indexed={t['id']:t for t in a['tasks']}
    with (folder/'advance.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        completed=[tid for tid,t in indexed.items() if t.get('inherited_run')]
        waiting=[tid for tid in indexed if tid not in completed];active={};errors=[]
        with ThreadPoolExecutor(max_workers=4) as pool:
            while waiting or active:
                while waiting and len(active)<4 and not errors:
                    ready=next((tid for tid in waiting if not indexed[tid]['mapping_source_task'] or indexed[tid]['mapping_source_task'] in completed),None)
                    if ready is None:break
                    waiting.remove(ready);active[pool.submit(run_task,folder,indexed[ready])]=ready
                write(folder/'progress.json',{'phase':'test_collecting','active':list(active.values()),'waiting':waiting,'completed':completed,'errors':errors})
                if not active:break
                done,_=wait(active,timeout=1,return_when=FIRST_COMPLETED)
                for future in done:
                    tid=active.pop(future)
                    try:completed.append(future.result())
                    except Exception as error:errors.append({'task_id':tid,'reason':str(error)})
        write(folder/'progress.json',{'phase':'stopped_on_error' if errors else 'test_collection_complete','completed':completed,'waiting':waiting,'errors':errors})
        if errors:raise RuntimeError(str(errors))


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['prepare','run','verify'])
    for name in ('folder','plan','selection','predecessor'):ap.add_argument('--'+name,type=Path)
    a=ap.parse_args()
    if a.action=='prepare':prepare(a.plan.resolve(),a.selection.resolve(),a.folder.resolve(),a.predecessor.resolve() if a.predecessor else None)
    elif a.action=='run':run(a.folder.resolve())
    else:verify(a.folder.resolve());print('verified')


if __name__=='__main__':main()
