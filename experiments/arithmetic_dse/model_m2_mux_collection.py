"""Frozen Mux-only source-context collection; independent test remains locked."""
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
CONFIG=Path(__file__).with_name('configs')/'model_asap7_m2_mux_context_v1.json'
def read(path):return json.loads(Path(path).read_text())
def exclusive(path,value):
    with Path(path).open('x') as f:json.dump(value,f,indent=2);f.write('\n')


def prepare(parent_plan,parent_selection,parent_result,folder):
    from .model_m2_collection import verify_plan,run_directory,sources,CONFIG as LEGACY
    from .model_m2_fit_v4 import verify_fit
    from .model_m2_f5_evaluate import verify_result
    from .model_m2_mux_samples import source
    from .platforms import profile
    p=verify_plan(parent_plan);f=verify_fit(parent_selection);result=verify_result(parent_result);cfg=read(CONFIG)
    if result['selection_sha256']!=sha(parent_selection) or f['plan_sha256']!=sha(parent_plan):raise ValueError('Mux successor parent mismatch')
    candidate=read(parent_selection.parent/'candidate.json');ops=candidate['stages']['grt']['operations']
    keep=[op for op in ops if op!='mux']
    if len(keep)!=11 or any(result['stages']['grt']['operations'][op]['status']!='passed' for op in keep):raise ValueError('unchanged11 components not independently qualified')
    inherited={'version':'asap7-m2-unchanged11-inheritance-v1','source_selection_sha256':sha(parent_selection),
        'source_candidate_sha256':f['candidate_sha256'],'source_F5_result_sha256':sha(parent_result),
        'source_F5_overall_status':result['quality_status'],'target_platform':'asap7','ABC_ps':1500,'IO':'0.2T',
        'scope':'only unmodified11 grt components and their exact domains; not standalone publication or full D',
        'operations':{op:{'model':ops[op],'independent_quality':result['stages']['grt']['operations'][op]} for op in keep},
        'mux_test_labels_present':False,'all12_required_for_composite_release':True}
    sampling=read(LEGACY);selected=profile('asap7');excluded={t['rtl_sha256'] for t in p['tasks']}
    # Only source hashes of prior F5 are consumed here, never its numeric Mux
    # labels. The old numerical result above is used solely for kept classes.
    F5_admission=parent_result.parent.parent/'independent-F5-v2/admission.json'
    excluded.update(t['rtl_sha256'] for t in read(F5_admission)['tasks'])
    periods=sorted({t['period_ps'] for t in p['tasks'] if t['family']=='control'},reverse=True)
    if periods!=cfg['SDC_ps']:raise ValueError('Mux successor changed registered clocks')
    resources=read(POLICY)['resources'];u=usage(read(Ledger().path)['entries']);later=sampling['later_work_reserved']
    total=sum(cfg['task_counts'].values());wall=total*cfg['resources']['per_task_envelope_s']+cfg['support_walltime_envelope_s']
    if (u['walltime_s']+wall+later['walltime_s']>resources['max_global_walltime_h']*3600 or
        u['CPU_time_s']+4*wall+later['CPU_time_s']>resources['max_tool_CPU_time_h']*3600 or
        u['synth']+total+later['synth']>resources['max_synthesis_calls'] or u['grt']+total+later['grt']>resources['max_global_route_calls']):
        raise ValueError('full Mux train/validation/new-test and later work not funded')
    folder.mkdir(parents=True,exist_ok=False)
    if shutil.disk_usage(folder).free<total*cfg['resources']['storage_per_task_bytes']+15*1024**3:raise ValueError('Mux full-cohort storage reserve insufficient')
    exclusive(folder/'inherited11.json',inherited);tasks=[];seen={}
    for split,context in cfg['splits'].items():
        replicas=context['independent_muxes_per_source']
        for fanout in context['capture_fanouts']:
            for width in cfg['widths']:
                group=f'mux-{split}-P{replicas}-F{fanout}-w{width}';d=folder/'sources'/group;d.mkdir(parents=True)
                text,labels=source(width,fanout,replicas,sampling);(d/'input.sv').write_text(text)
                exclusive(d/'contract.json',{'version':'arithmetic-mux-context-labels-v1','split':split,'source_group':group,
                    'protocol_sha256':sha(CONFIG),'labels':labels,'diagnostic_input_arcs':['select','data_a','data_b']})
                ins=sum(sum(s['input_widths']) for s in labels);caps=sum(s['capture_width']*fanout for s in labels);h=sha(d/'input.sv')
                if ins>640 or caps>2048 or h in excluded or h in seen:raise ValueError('Mux source capacity or partition independence violation')
                seen[h]=split
                for i,period in enumerate(periods):
                    tasks.append({'id':group+f'-t{i}','source_group':group,'split':split,'family':'mux_context','width':width,
                        'replicas':replicas,'capture_fanout':fanout,'platform':'asap7','profile_sha256':selected['profile_sha256'],'top':'ModelBundle',
                        'stage':'grt','period_ps':period,'abc_target_ps':1500,'rtl':str((d/'input.sv').resolve()),'rtl_sha256':h,
                        'sample_contract':str((d/'contract.json').resolve()),'sample_contract_sha256':sha(d/'contract.json'),
                        'samples':len(labels),'input_bits':ins,'capture_bits':caps,'mapping_source_task':group+'-t0' if i else None})
    counts={split:sum(t['split']==split for t in tasks) for split in cfg['splits']}
    if counts!=cfg['task_counts'] or not set(cfg['capacity_pilots'])<={t['id'] for t in tasks if t['split']!='test'}:raise ValueError('incomplete prospective Mux design')
    paths=list(sources())+[Path(__file__),CONFIG,Path(__file__).with_name('model_m2_mux_labels.py'),Path(__file__).with_name('model_m2_mux_samples.py'),
        Path(__file__).with_name('model_m2_live_cec_v3.py'),Path(__file__).with_name('model_m2_state.py'),Path(__file__).with_name('model_m2_aig.py')]
    hashes={}
    for path in paths:
        name=str(path.relative_to(ROOT));dst=folder/'source'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dst);hashes[name]=sha(path)
    reference=next(t for t in p['tasks'] if t['split']=='train');physical_tools=read(run_directory(parent_plan.parent,reference)/'manifest.json')['tools']
    a={'version':'asap7-m2-mux-context-collection-v1','id':folder.name,'tasks':tasks,'sources':hashes,'protocol_sha256':sha(CONFIG),'policy_sha256':sha(POLICY),
        'parent_plan':str(parent_plan),'parent_plan_sha256':sha(parent_plan),'parent_selection':str(parent_selection),'parent_selection_sha256':sha(parent_selection),
        'parent_candidate_sha256':f['candidate_sha256'],'inherited11_sha256':sha(folder/'inherited11.json'),'capacity_pilots':cfg['capacity_pilots'],
        'excluded_old_source_sha256':sorted(excluded),'task_counts':counts,'test_locked':True,'automatic_retries':0,
        'resource_plan':{'walltime_envelope_s':wall,'CPU_envelope_s':4*wall,'synth_calls':total,'grt_calls':total,'later_work_reserved':later},
        'physical_tools':physical_tools}
    for tool in a['physical_tools'].values():
        if sha(tool['path'])!=tool['sha256']:raise ValueError('changed registered physical tool')
    exclusive(folder/'admission.json',a);write(folder/'progress.json',{'phase':'admitted','completed':[],
        'waiting':[t['id'] for t in tasks if t['split'] in ('train','validation')],'test_locked':True})
    print(json.dumps({'status':'admitted','task_counts':counts,'source_groups':len(seen),'all12_release_required':True,'test_locked':True}),flush=True)


def verify(folder):
    a=read(folder/'admission.json')
    if (a['version']!='asap7-m2-mux-context-collection-v1' or sha(CONFIG)!=a['protocol_sha256'] or sha(POLICY)!=a['policy_sha256']
        or sha(a['parent_plan'])!=a['parent_plan_sha256'] or sha(a['parent_selection'])!=a['parent_selection_sha256']
        or sha(folder/'inherited11.json')!=a['inherited11_sha256'] or not a['test_locked']):raise ValueError('changed Mux collection admission')
    for name,h in a['sources'].items():
        if sha(ROOT/name)!=h or sha(folder/'source'/name)!=h:raise ValueError('changed Mux sampling producer: '+name)
    for tool in a['physical_tools'].values():
        if sha(tool['path'])!=tool['sha256']:raise ValueError('changed Mux physical tool')
    return a

class TestLedger(Ledger):
    def __init__(self,folder):super().__init__();self.folder=folder
    def reserve(self,stage,timeout_s,threads,purpose,command,output,*,context=None):
        a=verify(self.folder)
        return super().reserve(stage,timeout_s,threads,purpose,command,output,context={**context,
            'admission_sha256':sha(self.folder/'admission.json'),'model_version':'asap7-m2-mux-context-collect-v1'})

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
    if t['split'] not in ('train','validation'):raise ValueError('new Mux independent test is locked until validated frozen fit')
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
                synth_timeout_s=300,route_timeout_s=1200,selection_freeze=None)
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
        m.update(status='running',stages_requested='grt',admission_id=a['id'],budget_job_id=ledger.job_id,mux_admission_sha256=sha(folder/'admission.json'),
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
        for name in ('model_m2_mux_collection.py','model_m2_mux_labels.py','model_m2_mux_samples.py','model_m2_live_cec_v3.py','model_m2_state.py'):
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
    exclusive(folder/'capacity-proof.json',{'version':'asap7-m2-mux-fitting-capacity-v1','status':'passed',
        'admission_sha256':sha(folder/'admission.json'),'scope':'only new P2/P3 Mux fitting contexts; P4 independent topology remains locked and separately admitted',
        'runs':runs})


def run(folder):
    a=verify(folder);indexed={t['id']:t for t in a['tasks'] if t['split'] in ('train','validation')}
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
                write(folder/'progress.json',{'phase':'fitting_collecting','active':list(active.values()),'waiting':waiting,'completed':completed,
                    'errors':errors,'capacity_qualified':capacity,'test_locked':True})
                if not active:
                    if waiting and not errors:raise ValueError('Mux scheduling dependency deadlock')
                    break
                done,_=wait(active,timeout=1,return_when=FIRST_COMPLETED)
                for future in done:
                    tid=active.pop(future)
                    try:completed.append(future.result())
                    except Exception as error:errors.append({'task_id':tid,'reason':str(error)})
        write(folder/'progress.json',{'phase':'stopped_on_error' if errors else 'fitting_collection_complete','completed':completed,
            'waiting':waiting,'errors':errors,'capacity_qualified':capacity,'test_locked':True})
        if errors:raise RuntimeError(str(errors))


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['prepare','run','verify'])
    for name in ('folder','parent-plan','parent-selection','parent-result'):ap.add_argument('--'+name,type=Path)
    a=ap.parse_args()
    if a.action=='prepare':prepare(a.parent_plan.resolve(),a.parent_selection.resolve(),a.parent_result.resolve(),a.folder.resolve())
    elif a.action=='run':run(a.folder.resolve())
    else:verify(a.folder.resolve());print('verified')


if __name__=='__main__':main()
