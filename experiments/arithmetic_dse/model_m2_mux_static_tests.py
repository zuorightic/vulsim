"""Frozen P4 independent sampling for the validated Mux static-context model."""
import argparse
from concurrent.futures import ThreadPoolExecutor,wait,FIRST_COMPLETED
import copy
from datetime import datetime,timezone
import fcntl,hashlib,json,os,re,shutil,sys
from pathlib import Path
from types import SimpleNamespace
from .budget import Ledger,POLICY,usage
from .model_collection import sha,write
ROOT=Path(__file__).resolve().parents[2]
SUFFIX=Path('asap7/arithmetic_probe/base')
ORFS=Path('/home/zyrv/OpenROAD-flow-scripts')
CONFIG=Path(__file__).with_name('configs')/'model_asap7_m2_mux_static_test_v1.json'
def read(path):return json.loads(Path(path).read_text())
def exclusive(path,value):
    with Path(path).open('x') as f:json.dump(value,f,indent=2);f.write('\n')


def prepare(parent,selection,folder):
    from .model_m2_mux_collection import verify as verify_parent
    from .model_m2_mux_static_fit import verify_fit
    from .model_m2_mux_static_features import descriptor,context_features,VERSION
    a=verify_parent(parent);f=verify_fit(selection);cfg=read(CONFIG)
    if not f['grt_validation_ready'] or f['collection_admission_sha256']!=sha(parent/'admission.json'):raise ValueError('new independent test requires matching qualified validation freeze')
    reproduction=selection.parent.parent/'mux-static-refit-v1/reproduction.json';proof=read(reproduction)
    if proof!={'status':'passed','parent_fit_sha256':sha(selection.parent/'fit-freeze.json'),'independent_labels_read':False}:raise ValueError('static Mux byte-identical refit required')
    parity_path=selection.parent.parent/'mux-static-query-v1/parity.json';parity=read(parity_path)
    if parity['status']!='passed' or parity['model_sha256']!=f['candidate_sha256'] or parity['fitting_rows']!=384 or parity['candidate_PPA_calls']!=0:
        raise ValueError('native context and numeric parity not complete')
    tasks=copy.deepcopy([t for t in a['tasks'] if t['split']=='test'])
    if len(tasks)!=48 or any((parent/'runs'/t['id']).exists() for t in tasks):raise ValueError('new P4 cohort changed or already measured')
    fit_data=read(f['dataset_path']);used={r['source_sha256'] for r in fit_data['rows']}
    for t in tasks:
        if t['rtl_sha256'] in used or sha(t['rtl'])!=t['rtl_sha256'] or sha(t['sample_contract'])!=t['sample_contract_sha256']:raise ValueError('P4 independent source overlap or mutation')
        cut=descriptor(read(t['sample_contract'])['labels'])
        for o in cut['operations']:context_features(cut,o['id'])
    limits=read(POLICY)['resources'];u=usage(read(Ledger().path)['entries']);later=a['resource_plan']['later_work_reserved'];wall=48*1920+1800
    if (u['walltime_s']+wall+later['walltime_s']>limits['max_global_walltime_h']*3600 or u['CPU_time_s']+4*wall+later['CPU_time_s']>limits['max_tool_CPU_time_h']*3600
        or u['synth']+48+later['synth']>limits['max_synthesis_calls'] or u['grt']+48+later['grt']>limits['max_global_route_calls']):raise ValueError('new independent cohort/later work not funded')
    folder.mkdir(parents=True,exist_ok=False)
    if shutil.disk_usage(folder).free<48*512*1024**2+15*1024**3:raise ValueError('independent storage reserve insufficient')
    source_paths=[ROOT/name for name in a['sources']]+[ROOT/name for name in f['sources']]
    source_paths += [Path(__file__),CONFIG,Path(__file__).with_name('model_m2_mux_static_query.py'),ROOT/'rtlzz/testv2/arithmetic_mux_static_predict.cpp']
    hashes={}
    for path in source_paths:
        name=str(path.relative_to(ROOT));dst=folder/'source'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dst);hashes[name]=sha(path)
    result={'version':'asap7-m2-mux-static-independent-admission-v1','id':folder.name,'tasks':tasks,'sources':hashes,
        'parent_collection_path':str((parent/'admission.json').resolve()),'parent_collection_sha256':sha(parent/'admission.json'),
        'selection_path':str(selection.resolve()),'selection_sha256':sha(selection),'candidate_sha256':f['candidate_sha256'],
        'protocol_sha256':sha(CONFIG),'policy_sha256':sha(POLICY),'feature_schema':VERSION,'capacity_pilots':[cfg['capacity_pilot']],
        'native_parity_path':str(parity_path),'native_parity_sha256':sha(parity_path),'inherited11_path':f['inherited11_path'],'inherited11_sha256':f['inherited11_sha256'],
        'prospective_release_scope':cfg['prospective_release_scope'],'physical_tools':a['physical_tools'],'test_locked':False,'automatic_retries':0,
        'resource_plan':{'walltime_envelope_s':wall,'CPU_envelope_s':4*wall,'synth':48,'grt':48,'later_work_reserved':later}}
    exclusive(folder/'admission.json',result)
    exclusive(selection.parent/'mux-static-independent-consumption.json',{'admission_path':str((folder/'admission.json').resolve()),'admission_sha256':sha(folder/'admission.json'),
        'selection_sha256':sha(selection),'cohort':'original48 P4 sources, once only; no tuning from their measurements'})
    write(folder/'progress.json',{'phase':'admitted','completed':[],'waiting':[t['id'] for t in tasks],'test_locked':False})
    print(json.dumps({'status':'admitted','test_tasks':48,'capacity_pilot':cfg['capacity_pilot'],'original_sources_and_clocks_preserved':True}),flush=True)


def verify(folder):
    from .model_m2_mux_static_fit import verify_fit
    a=read(folder/'admission.json');f=verify_fit(Path(a['selection_path']))
    if (a['version']!='asap7-m2-mux-static-independent-admission-v1' or sha(CONFIG)!=a['protocol_sha256'] or sha(POLICY)!=a['policy_sha256']
        or sha(a['parent_collection_path'])!=a['parent_collection_sha256'] or sha(a['selection_path'])!=a['selection_sha256']
        or f['candidate_sha256']!=a['candidate_sha256'] or not f['grt_validation_ready'] or sha(a['inherited11_path'])!=a['inherited11_sha256']):
        raise ValueError('changed independent static-Mux admission/selection')
    for name,h in a['sources'].items():
        if sha(ROOT/name)!=h or sha(folder/'source'/name)!=h:raise ValueError('changed independent static-Mux producer')
    for tool in a['physical_tools'].values():
        if sha(tool['path'])!=tool['sha256']:raise ValueError('changed independent physical executable')
    receipt=read(Path(a['selection_path']).parent/'mux-static-independent-consumption.json')
    if receipt['admission_path']!=str((folder/'admission.json').resolve()) or receipt['admission_sha256']!=sha(folder/'admission.json'):
        raise ValueError('wrong independent cohort consumption owner')
    if sha(a['native_parity_path'])!=a['native_parity_sha256']:raise ValueError('changed native feature/numeric parity')
    return a

class TestLedger(Ledger):
    def __init__(self,folder):super().__init__();self.folder=folder
    def reserve(self,stage,timeout_s,threads,purpose,command,output,*,context=None):
        a=verify(self.folder)
        return super().reserve(stage,timeout_s,threads,purpose,command,output,context={**context,
            'admission_sha256':sha(self.folder/'admission.json'),'selection_freeze_sha256':a['selection_sha256'],'model_version':'asap7-m2-mux-static-candidate-v1'})

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
    from .model_m2_mux_labels import read_labels,verify_capture_banks,render_label_requests
    from .sdc import verify_sdc,rtl_ports
    from .platforms import resolve_environment,validate_environment,profile,verify_wire_readback
    a=verify(folder)
    if t['split']!='test':raise ValueError('independent Mux admission accepts test only')
    out=folder/'runs'/t['id'];out.parent.mkdir(exist_ok=True)
    if out.exists():raise ValueError('test attempt already exists; preserve it')
    if sha(t['rtl'])!=t['rtl_sha256'] or sha(t['sample_contract'])!=t['sample_contract_sha256']:raise ValueError('changed preregistered test source')
    ledger=TestLedger(folder);context={'target_platform':'asap7','admission_id':a['id'],'task_id':t['id']}
    env=os.environ.copy();env.update(OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',YOSYS_MAX_THREADS='4',QT_QPA_PLATFORM='offscreen',
        PYTHONDONTWRITEBYTECODE='1',VULSIM_LABEL_REQUESTS=str(out/'label_requests.tcl'))
    with ledger.job(context):
        if not t['mapping_source_task']:
            args=SimpleNamespace(out=out,platform='asap7',threads=4,stage='synth',memory_limit_mib=8192,period_ps=t['period_ps'],
                period_role='resource_trial',abc_target_ps=1500,io_delay_max_ps=None,budget_purpose='characterization',admission_id=a['id'],task_id=t['id'],
                sample_contract=None,admission=None,resume_synth_from=None,orfs=ORFS,rtl=Path(t['rtl']),top='ModelBundle',
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
        m.update(status='running',stages_requested='grt',admission_id=a['id'],budget_job_id=ledger.job_id,mux_admission_sha256=sha(folder/'admission.json'),selection_freeze_sha256=a['selection_sha256'],mux_static_independent=True,
            active_stage='mux_physical_preflight',mux_collection_version=a['version'])
        shutil.copy2(t['sample_contract'],out/'sample-contract.json')
        (out/'label_requests.tcl').write_text(render_label_requests(out/'sample-contract.json'))
        m['sample_contract_sha256']=t['sample_contract_sha256']
        if not reused:
            m['initial_unlabeled_synth_metrics']=copy.deepcopy(m['metrics']);m['metrics']=[]
            initial={}
            for group in ('reports','logs'):
                for path in (out/group/SUFFIX).glob('vulsim_synth*'):
                    if path.is_file():
                        relative=path.relative_to(out);dst=out/'initial-synth-observation'/relative
                        dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dst);initial[str(dst.relative_to(out))]=sha(dst)
            m['initial_synth_observation_sha256']=initial
        for name in ('model_m2_mux_static_tests.py','model_m2_mux_labels.py','model_m2_mux_samples.py','model_m2_live_cec_v3.py','model_m2_state.py','model_m2_mux_static_features.py'):
            pth=Path(__file__).with_name(name);relative=pth.relative_to(ROOT)
            dst=out/'source'/relative;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(pth,dst)
            m['source_sha256'][str(relative)]=sha(pth)
        if reused:
            m.pop('initial_synth_observation_sha256',None);m.pop('initial_unlabeled_synth_metrics',None)
        def save():write(out/'manifest.json',m)
        def execute(command,stem,timeout,stage=None):
            r=ledger.reserve(stage,timeout,4,'characterization',command,out/stem,context=context);m['active_reservation']=r['id'];save()
            c=run_command(command,out,stem,timeout,env,8192,cpu_limit_s=r['CPU_time_s']);ledger.finish(r,c);c['budget_reservation_id']=r['id'];m['commands'].append(c);save()
            if c['exit_code']:raise RuntimeError(stem+': failed, timeout='+str(c['timed_out']))
        try:
            results=out/'results'/SUFFIX;reports=out/'reports'/SUFFIX;cells=read(out/'liberty_cells.json')['cells'];p=profile('asap7')
            if p['profile_sha256']!=t['profile_sha256']:raise ValueError('changed test platform')
            wrapper=out/'live-cec.py';wrapper.write_text('import sys\nsys.path.insert(0,'+repr(str(ROOT))+')\nfrom experiments.arithmetic_dse.model_m2_live_cec_v3 import main\nmain()\n')
            request=out/'live-cec-request.json';write(request,{'libraries':m['libraries'],'admission_sha256':sha(folder/'admission.json'),'collection_plan_sha256':sha(folder/'admission.json')})
            cts=out/'flow-scripts/cts.tcl';cts.unlink();cts.write_text(render_cts((ORFS/'flow/scripts/cts.tcl').read_text(),wrapper,request,out/'logs'/SUFFIX/'structural_cec'))
            m['files_sha256'].update({str(x):sha(x) for x in (cts,wrapper,request,out/'config.mk')})
            if reused:
                m['active_stage']='environment';execute(base+['vulsim-environment','VULSIM_ENV_FILE='+str(out/'effective-environment.txt')],'environment',60)
                raw=dict(line.strip().split('=',1) for line in (out/'effective-environment.txt').read_text().splitlines() if line.strip())
                effective,origins=resolve_environment(raw);validate_environment(effective,p)
                for k in ('LIB_FILES','TECH_LEF','SC_LEF','CORNER','ASAP7_USE_VT','LIB_MODEL','TC_TEMPERATURE','ABC_DRIVER_CELL','ABC_LOAD_IN_FF','YOSYS_MAX_THREADS'):
                    if effective.get(k)!=old['effective_environment'].get(k):raise ValueError('changed test mapping environment '+k)
                m.update(raw_make_environment=raw,effective_environment=effective,asset_resolution=origins)
            for stage in (('synth','1_synth.odb','1_synth.sdc',300),('grt','5_1_grt.odb','5_1_grt.sdc',1200)):
                name,db,sdc,timeout=stage
                m['active_stage']=name;save()
                if name!='synth' or reused:execute(base+[name],name,timeout,name)
                m.setdefault('sdc_contracts',{})[name]=verify_sdc((results/sdc).read_text(),p,t['period_ps'],rtl_ports((out/'input.sv').read_text(),t['top']))
                execute(base+['run','RUN_SCRIPT='+str(ROOT/'experiments/arithmetic_dse/backend/snapshot.tcl'),'RUN_LOG_NAME_STEM=vulsim_'+name,
                    'VULSIM_EVAL_STAGE='+name,'VULSIM_EVAL_DB='+db,'VULSIM_EVAL_SDC='+sdc],name+'-label-snapshot',120)
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

def seal_capacity(folder,a):
    from .model_m2_mux_labels import verify_capture_banks
    runs=[]
    for tid in a['capacity_pilots']:
        d=folder/'runs'/tid;m=read(d/'manifest.json')
        if m['status']!='completed' or len(m['metrics'])!=2:raise ValueError('Mux fitting capacity task incomplete')
        cells=read(d/'liberty_cells.json')['cells']
        for stage in m['metrics']:
            banks=verify_capture_banks(d/'reports'/SUFFIX/('vulsim_'+stage['stage']),d/'sample-contract.json',cells)
            if banks!=stage.get('model_capture_banks',{}):raise ValueError('Mux fitting capacity banks differ')
        runs.append({'task_id':tid,'manifest_sha256':sha(d/'manifest.json'),
            'bank_counts':{s['stage']:s.get('model_capture_banks',{}) for s in m['metrics']},
            'peak_RSS_MiB':max(c['sampled_process_tree_peak_rss_KiB'] for c in m['commands'])/1024})
    exclusive(folder/'capacity-proof.json',{'version':'asap7-m2-mux-P4-independent-capacity-v1','status':'passed',
        'admission_sha256':sha(folder/'admission.json'),'scope':'named P4-F3-w64-t0 independent source at this platform/grt; retain all task limits',
        'runs':runs})

def run(folder):
    a=verify(folder);indexed={t['id']:t for t in a['tasks'] if t['split']=='test'}
    with (folder/'advance.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if any((folder/'runs'/tid).exists() for tid in indexed):raise ValueError('preserve prior Mux attempts; use explicit successor')
        waiting=list(indexed);active={};completed=[];errors=[];capacity=False
        with ThreadPoolExecutor(max_workers=4) as pool:
            while waiting or active:
                if not capacity and set(a['capacity_pilots'])<=set(completed):seal_capacity(folder,a);capacity=True
                while waiting and len(active)<4 and not errors:
                    ready=next((tid for tid in waiting if (capacity or tid in a['capacity_pilots'])
                        and (not indexed[tid]['mapping_source_task'] or indexed[tid]['mapping_source_task'] in completed)),None)
                    if ready is None:break
                    waiting.remove(ready);active[pool.submit(run_task,folder,indexed[ready])]=ready
                write(folder/'progress.json',{'phase':'test_collecting','active':list(active.values()),'waiting':waiting,'completed':completed,
                    'errors':errors,'capacity_qualified':capacity,'test_locked':False})
                if not active:
                    if waiting and not errors:raise ValueError('Mux scheduling dependency deadlock')
                    break
                done,_=wait(active,timeout=1,return_when=FIRST_COMPLETED)
                for future in done:
                    tid=active.pop(future)
                    try:completed.append(future.result())
                    except Exception as error:errors.append({'task_id':tid,'reason':str(error)})
        write(folder/'progress.json',{'phase':'stopped_on_error' if errors else 'test_collection_complete','completed':completed,
            'waiting':waiting,'errors':errors,'capacity_qualified':capacity,'test_locked':False})
        if errors:raise RuntimeError(str(errors))


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['prepare','run','verify'])
    for name in ('parent','selection','folder'):ap.add_argument('--'+name,type=Path)
    a=ap.parse_args()
    if a.action=='prepare':prepare(a.parent.resolve(),a.selection.resolve(),a.folder.resolve())
    elif a.action=='run':run(a.folder.resolve())
    else:verify(a.folder.resolve());print('verified')


if __name__=='__main__':main()
