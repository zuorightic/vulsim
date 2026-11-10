"""Finite not-training qualification before steps 4--5 collection.

Four successor sample points fit the six-target preparation envelope including
the earlier two boundary synth probes. No train/test labels or fitting here.
"""
import argparse
import csv
from datetime import datetime,timezone
import os
from pathlib import Path
import shutil
import sys
from types import FunctionType,SimpleNamespace

from .budget import Ledger,POLICY,usage
from .model_fast_preflight import read,write,sha
from . import model_sampling_v2 as samples
from . import model_fast_sdc
from .model_mapped_contract import mapped_contract,operator_port_contract,render_query_contract

ROOT=Path(__file__).resolve().parents[2];ORFS=Path('/home/zyrv/OpenROAD-flow-scripts');SUFFIX=Path('asap7/arithmetic_probe/base')
READOUT=Path(__file__).with_name('reference_assets')/'context_readout_v2.tcl'
CENSUS=Path(__file__).with_name('reference_assets')/'boundary_census.tcl'


def prepare(folder,software,simlog,parent=None):
    from regression.arithmetic_target_round1 import capacity_sources
    from .platforms import profile
    if 'INDEPENDENT_OBSERVERS_PASS sources=90 cycles=128' not in simlog.read_text():raise ValueError('independent observer RTL acceptance missing')
    cfg=read(software/'sources.json')
    if cfg['source_sha256']!=sha(Path(samples.__file__)):raise ValueError('sampling producer changed after software execution')
    candidates={r['id']:r for r in cfg['rows']};tasks=[]
    for name,source,t in [('mul-load-1500','capacity0',1500),('mul-load-750','capacity0',750),('sparse-add-250','capacity2',250),('wide-add-750','capacity1',750)]:
        row=candidates[source];rtl=software/'sources'/source/'input.sv'
        if rtl.read_text()!=samples.source(row['features']):raise ValueError('physical RTL differs from accepted software source')
        tasks.append(dict(id=name,source_group=row['source_group'],features=row['features'],rtl=str(rtl),rtl_sha256=sha(rtl),period_ps=t,abc_target_ps=t,source_role='not_training'))
    inheritance=None
    if parent:
        old=read(parent/'admission.json');progress=read(parent/'progress.json')
        if progress['phase']!='stopped_on_error' or len(progress['errors'])!=1:raise ValueError('one diagnosed predecessor stop required')
        for task in tasks:
            prior=parent/'runs'/task['id']
            if not prior.exists():continue
            m=read(prior/'manifest.json')
            if (prior/'grt-labels.json').exists() and (prior/'logs'/SUFFIX/'structural_cec/proof.json').exists():
                from .model_m2_live_cec_v3 import verify_proof
                verify_proof(prior/'logs'/SUFFIX/'structural_cec/proof.json',prior/'results'/SUFFIX/'4_before_rsz_lec.v',prior/'results'/SUFFIX/'4_after_rsz_lec.v')
                for stage in ('synth','grt'):
                    label=read(prior/(stage+'-labels.json'))
                    if label['source_role']!='not_training' or not all(label[k] for k in ('operator_maximum_covered','data_through_operator_covered','ownership_complete')):
                        raise ValueError('saved qualification labels incomplete')
                old_task=next(t for t in old['tasks'] if t['id']==task['id'])
                for name,h in old_task.get('inherit_synth',{}).get('files_sha256',{}).items():
                    if sha(prior/name)!=h:raise ValueError('inherited synthesis changed before complete diagnostic recovery')
                task['inherit_completed']=dict(directory=str(prior),synth_label_sha256=sha(prior/'synth-labels.json'),grt_label_sha256=sha(prior/'grt-labels.json'),
                    CEC_sha256=sha(prior/'logs'/SUFFIX/'structural_cec/proof.json'),parent_admission_sha256=sha(parent/'admission.json'),
                    reason='all physical reads/CEC passed; only final legacy evidence dictionary lookup stopped; no synthesis or grt repeated')
                continue
            if m['status']!='completed' or [x['stage'] for x in m['metrics']]!=['synth'] or any(c['log'].endswith('/grt.log') for c in read(prior/'qualification-commands.json')):
                raise ValueError('only complete untouched pre-grt mapped checkpoint may continue')
            previous=next(t for t in old['tasks'] if t['id']==task['id'])
            if any(task[k]!=previous[k] for k in ('rtl_sha256','period_ps','features')):raise ValueError('reader continuation changed physical task')
            for name,h in m['evidence_sha256'].items():
                if sha(prior/name)!=h:raise ValueError('parent checkpoint changed')
            task['inherit_synth']=dict(directory=str(prior),manifest_sha256=sha(prior/'manifest.json'),files_sha256={str(p.relative_to(prior)):sha(p) for p in (prior/'results'/SUFFIX).iterdir() if p.is_file()})
        inheritance=dict(admission_sha256=sha(parent/'admission.json'),directory=str(parent),reason='mapped state can use an explicit inverted Q alias; reader records polarity; RTL/targets/passes unchanged, no repeat synthesis')
    ledger=Ledger();state=read(ledger.path);u=usage(state['entries']);limits=read(POLICY)['resources'];later=dict(synth=688,grt=688,walltime_s=86400,CPU_time_s=172800,storage_bytes=32212254720)
    wall=4*(300+1200+6*120)+600
    if (u['synth']+4+later['synth']>limits['max_synthesis_calls'] or u['grt']+4+later['grt']>limits['max_global_route_calls']
            or u['walltime_s']+wall+later['walltime_s']>limits['max_global_walltime_h']*3600 or u['CPU_time_s']+4*wall+later['CPU_time_s']>limits['max_tool_CPU_time_h']*3600
            or shutil.disk_usage(folder.parent).free<later['storage_bytes']+4*1024**3):raise ValueError('finite qualification and later work not funded')
    folder.mkdir(parents=True,exist_ok=False)
    paths=[Path(__file__),Path(samples.__file__),Path(model_fast_sdc.__file__),READOUT,CENSUS,POLICY,
        *[Path(__file__).with_name(name) for name in ('model_mapped_contract.py','model_qualification_labels.py','model_physical_labels_v2.py','model_physical_path_v2.py','model_context_labels.py','model_fast_path.py','backend.py','platforms.py','budget.py','processes.py')]]
    for p in paths:
        dest=folder/'source'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    write(folder/'admission.json',dict(version='steps123-finite-qualification-v2',id='steps123-qualification-20261110-'+folder.name,tasks=tasks,parent=inheritance,
        source_sha256={str(p.relative_to(ROOT)):sha(p) for p in paths},software_sources_sha256=sha(software/'sources.json'),simlog_sha256=sha(simlog),
        profile_sha256=profile('asap7')['profile_sha256'],synth_max=4,grt_max=4,final_max=0,support_max=40,
        synth_timeout_s=300,grt_timeout_s=1200,memory_limit_MiB=8192,threads=4,later_work_reserved=later,walltime_envelope_s=wall,
        training_allowed=False,test_labels_allowed=False,automatic_retries=0,prior_boundary_points=2,total_preparation_points_max=6,
        production_binding_implemented=False,full_D_ready=False))
    write(folder/'progress.json',dict(completed=[],phase='admitted',errors=[]));print('finite qualification admitted: 4 not_training source/targets; no formal collection',flush=True)


class QualificationLedger(Ledger):
    def __init__(self,folder,task):super().__init__();self.folder=folder;self.task=task
    def reserve(self,stage,timeout_s,threads,purpose,command,output,*,context=None):
        a=read(self.folder/'admission.json')
        if self.task not in a['tasks'] or threads!=4 or stage not in (None,'synth','grt'):raise ValueError('unregistered qualification leaf')
        for name,h in a['source_sha256'].items():
            if sha(ROOT/name)!=h or sha(self.folder/'source'/name)!=h:raise ValueError('qualification producer drift')
        if sha(self.task['rtl'])!=self.task['rtl_sha256']:raise ValueError('qualification RTL drift')
        prior=[e for e in read(self.path)['entries'] if e.get('admission_sha256')==sha(self.folder/'admission.json')]
        if stage=='synth' and self.task.get('inherit_synth'):raise ValueError('paid predecessor synthesis may not run again')
        if stage and (timeout_s>a[stage+'_timeout_s'] or any(e['stage']==stage and e.get('task_id')==self.task['id'] for e in prior)):raise ValueError('no retries or excess stage timeout')
        if not stage and (timeout_s>120 or sum(e['stage'] is None for e in prior)>=a['support_max']):raise ValueError('support bound')
        return super().reserve(stage,timeout_s,threads,purpose,command,output,context={**(context or {}),'target_platform':'asap7','admission_id':a['id'],
            'task_id':self.task['id'],'admission_sha256':sha(self.folder/'admission.json'),'model_version':samples.VERSION})


def task_run(folder,t):
    from . import backend
    from .model_reference_labels import liberty
    from .platforms import profile
    from .model_m2_mux_collection import render_cts
    from .model_m2_live_cec_v3 import verify_proof
    from . import model_qualification_labels as labels
    from .processes import run_command
    a=read(folder/'admission.json');out=folder/'runs'/t['id'];ledger=QualificationLedger(folder,t);ctx=dict(target_platform='asap7',admission_id=a['id'],task_id=t['id'])
    role=t['source_role']
    if role not in ('not_training','train','validation','locked_test') or (role!='not_training' and not a.get('physical_training_admitted')):
        raise ValueError('immutable physical source role requires a valid collection admission')
    env=os.environ.copy();env.update(OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',YOSYS_MAX_THREADS='4',PYTHONDONTWRITEBYTECODE='1',QT_QPA_PLATFORM='offscreen')
    namespace=dict(backend._evaluate.__globals__);namespace.update(rtl_ports=model_fast_sdc.rtl_ports,verify_sdc=model_fast_sdc.verify_sdc,os=SimpleNamespace(environ=env))
    evaluate=FunctionType(backend._evaluate.__code__,namespace,closure=backend._evaluate.__closure__)
    with ledger.job(ctx):
        args=SimpleNamespace(out=out,platform='asap7',threads=4,stage='synth',memory_limit_mib=8192,period_ps=t['period_ps'],period_role='resource_trial',abc_target_ps=t['period_ps'],io_delay_max_ps=None,
            budget_purpose='characterization',admission_id=a['id'],task_id=t['id'],sample_contract=None,admission=None,resume_synth_from=None,orfs=ORFS,rtl=Path(t['rtl']),top='ModelBundle',synth_timeout_s=300,route_timeout_s=1200,selection_freeze=None)
        if t.get('inherit_synth'):
            from .model_fast_probe import seed_synth
            seed_synth(out,t)
        elif evaluate(args,ledger):raise ValueError('qualification synth failed')
        m=read(out/'manifest.json');base=m.get('continuation_base_command') or next(c['command'][:-1] for c in m['commands'] if c['log'].endswith('/synth.log'));commands=[]
        write(out/'qualification-status.json',dict(phase='synth_complete',source_role='not_training'))
        def execute(cmd,name,timeout=120,stage=None):
            r=ledger.reserve(stage,timeout,4,'steps123_not_training_qualification',cmd,out/name,context=ctx)
            record=run_command(cmd,out,name,timeout,env,8192,cpu_limit_s=r['CPU_time_s']);ledger.finish(r,record);commands.append(dict(**record,budget_reservation_id=r['id']));write(out/'qualification-commands.json',commands)
            if record['exit_code']:raise ValueError('qualification leaf failed '+record['log'])
        libs=read(out/'liberty_cells.json')['cells'];pins=labels.with_timing_arcs(liberty(m['libraries'],libs),m['libraries']);write(out/'liberty-pins.json',pins)
        script=out/'mapped.ys';json_path=out/'mapped.json';mapped_v=out/'results'/SUFFIX/'1_2_yosys.v'
        script.write_text('\n'.join(['read_liberty -lib '+p['path'] for p in m['libraries']]+['read_verilog '+str(mapped_v),'hierarchy -top ModelBundle','write_json '+str(json_path)])+'\n')
        execute([m['tools']['yosys']['path'],'-s',str(script)],'mapped-json')
        design=read(json_path);contract=mapped_contract(design,t['features'],pins);write(out/'mapped-contract.json',contract);write(out/'operator-port-contract.json',operator_port_contract(design,t['features'],pins))
        execute(base+['run','RUN_SCRIPT='+str(CENSUS),'RUN_LOG_NAME_STEM=bank_census','VULSIM_EVAL_DB=1_synth.odb','VULSIM_EVAL_SDC=1_synth.sdc'],'mapped-census')
        connections=list(csv.DictReader((out/'reports'/SUFFIX/'boundary_connections.tsv').read_text().splitlines(),delimiter='\t'))
        setup,scopes,banks=render_query_contract(contract,connections,t['features']);(out/'query-contract.tcl').write_text(setup);write(out/'query-contract.json',dict(nodes=scopes,banks=banks))
        wrapper=out/'live-cec.py';wrapper.write_text('import sys\nsys.path.insert(0,'+repr(str(ROOT))+')\nfrom experiments.arithmetic_dse.model_m2_live_cec_v3 import main\nmain()\n')
        request=out/'live-cec-request.json';write(request,dict(libraries=m['libraries'],admission_sha256=sha(folder/'admission.json'),collection_plan_sha256=sha(folder/'admission.json')))
        cts=out/'flow-scripts/cts.tcl';cts.unlink();cts.write_text(render_cts((ORFS/'flow/scripts/cts.tcl').read_text(),wrapper,request,out/'logs'/SUFFIX/'structural_cec'))
        # The loader is source-local and is read-only after opening this target.
        load=out/'read-context.tcl';load.write_text('source $::env(SCRIPTS_DIR)/load.tcl\nload_design $::env(VULSIM_EVAL_DB) $::env(VULSIM_EVAL_SDC)\nif {$::env(VULSIM_EVAL_STAGE) eq "grt"} {set_propagated_clock [all_clocks];estimate_parasitics -global_routing}\nsource {'+str(out/'query-contract.tcl')+'}\nset context_prefix $::env(REPORTS_DIR)/context_$::env(VULSIM_EVAL_STAGE)\nsource {'+str(READOUT)+'}\n')
        results=[]
        for stage,stem in (('synth','1_synth'),('grt','5_1_grt')):
            if stage=='grt':execute(base+['grt'],'grt',1200,'grt')
            execute(base+['run','RUN_SCRIPT='+str(backend.ASSETS/'snapshot.tcl'),'RUN_LOG_NAME_STEM=qual_'+stage,'VULSIM_EVAL_STAGE='+stage,'VULSIM_EVAL_DB='+stem+'.odb','VULSIM_EVAL_SDC='+stem+'.sdc'],'qual-'+stage+'-snapshot')
            execute(base+['run','RUN_SCRIPT='+str(load),'RUN_LOG_NAME_STEM=context_'+stage,'VULSIM_EVAL_STAGE='+stage,'VULSIM_EVAL_DB='+stem+'.odb','VULSIM_EVAL_SDC='+stem+'.sdc'],'context-'+stage)
            reports=out/'reports'/SUFFIX;prefix=reports/('context_'+stage);g=backend.stage_metrics(reports,stage,libs,t['period_ps'],selected=profile('asap7'))
            # Physical-only cells are explicit zero-signal owners. Filler area
            # follows the established standard-cell exclusion, never a node.
            all_pins=dict(pins)
            for line in Path(str(reports/('vulsim_'+stage))+'_cells.tsv').read_text().splitlines():
                name,count,area,filler,kind=line.split('\t')
                if name not in all_pins:all_pins[name]=dict(sequential=False,buffer_or_inverter=False,physical_only=True,data_pins=[],pins={},area_um2=0 if filler=='1' else float(area))
            result=labels.read_snapshot(prefix,t['period_ps'],g['raw_report_units']['time']['to_ps'],all_pins,scopes,banks)
            stored=out/'results'/SUFFIX/(stem+'.sdc')
            sdc_check=model_fast_sdc.verify_sdc(stored.read_text(),profile('asap7'),t['period_ps'],model_fast_sdc.rtl_ports((out/'input.sv').read_text(),'ModelBundle'))
            from .platforms import verify_wire_readback
            rc=verify_wire_readback(Path(str(reports/('vulsim_'+stage))+'_layer_rc.tsv'),profile('asap7'))
            native=read(out/'logs'/SUFFIX/(stem+'.json'))[('synth' if stage=='synth' else 'globalroute')+'__design__instance__area__stdcell']
            backend.verify_orfs_area(g['cell_area_um2'],native)
            if abs(result['total_cell_area_um2']-g['cell_area_um2'])>1e-5:raise ValueError('exclusive area differs from whole actual stage')
            result.update(stage=stage,source_role=role,physical_training_label_eligible=False,mapped_contract_sha256=sha(out/'mapped-contract.json'),metrics=g,stored_SDC_check=sdc_check,wire_RC_check=rc)
            write(out/(stage+'-labels.json'),result);results.append(result)
        verify_proof(out/'logs'/SUFFIX/'structural_cec/proof.json',out/'results'/SUFFIX/'4_before_rsz_lec.v',out/'results'/SUFFIX/'4_after_rsz_lec.v')
        if role!='not_training':
            for stage in ('synth','grt'):
                label=read(out/(stage+'-labels.json'));label['physical_training_label_eligible']=True;label['CTS_CEC_sha256']=sha(out/'logs'/SUFFIX/'structural_cec/proof.json');write(out/(stage+'-labels.json'),label)
        for name,h in m.get('evidence_sha256',{}).items():
            if name.startswith('results/') and sha(out/name)!=h:raise ValueError('completed synth checkpoint changed during continuation')
        for name,h in t.get('inherit_synth',{}).get('files_sha256',{}).items():
            if sha(out/name)!=h:raise ValueError('inherited paid synthesis checkpoint changed')
        write(out/'qualification-status.json',dict(phase='qualified_diagnostic_complete',source_role='not_training',stages=['synth','grt'],operator_boundary_policy='unsigned-op-hierarchy-v1',formal_training_allowed=False,
            proof_sha256=sha(out/'logs'/SUFFIX/'structural_cec/proof.json')))
    print(t['id']+' complete diagnostic synth/grt labels and bank/CEC checks',flush=True)


def run(folder,task=None):
    a=read(folder/'admission.json');before=read(Ledger().path);progress=read(folder/'progress.json')
    chosen=[t for t in a['tasks'] if task is None or t['id']==task]
    try:
        for t in chosen:
            if t['id'] in progress['completed']:continue
            if t.get('inherit_completed'):
                ref=t['inherit_completed'];prior=Path(ref['directory'])
                if sha(prior/'grt-labels.json')!=ref['grt_label_sha256'] or sha(prior/'synth-labels.json')!=ref['synth_label_sha256']:raise ValueError('completed diagnostic labels changed')
                progress['completed'].append(t['id']);write(folder/'progress.json',progress);continue
            if (folder/'runs'/t['id']).exists():raise ValueError('earlier attempt exists; no automatic retry')
            try:task_run(folder,t)
            except Exception as e:progress['errors'].append(dict(task=t['id'],error=str(e)));progress['phase']='stopped_on_error';write(folder/'progress.json',progress);raise
            progress['completed'].append(t['id']);progress['phase']='finite_qualification_complete' if len(progress['completed'])==len(a['tasks']) else 'partially_complete';write(folder/'progress.json',progress)
    finally:
        after=read(Ledger().path);write(folder/('resource-increment-'+str(len(progress['completed']))+'.json'),dict(entries=after['entries'][len(before['entries']):],usage=usage(after['entries']),training_rows=0))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','run'));p.add_argument('--folder',type=Path,required=True);p.add_argument('--software',type=Path);p.add_argument('--simlog',type=Path);p.add_argument('--task');p.add_argument('--parent',type=Path);a=p.parse_args()
    if a.action=='prepare':prepare(a.folder.resolve(),a.software.resolve(),a.simlog.resolve(),a.parent.resolve() if a.parent else None)
    else:run(a.folder.resolve(),a.task)
