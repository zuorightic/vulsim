"""Two finite mapped-boundary probes, not training or production qualification.

Compare a software-validated local shell with its module keep_hierarchy removed.
Only synthesis and report-only census are admitted here; no physical routing.
"""
import argparse
from collections import Counter
import csv
import json
import os
from pathlib import Path
import shutil
from types import FunctionType,SimpleNamespace

from .budget import Ledger,POLICY,usage
from .model_fast_preflight import read,write,sha
from . import model_context_samples as shells
from . import model_fast_sdc

ROOT=Path(__file__).resolve().parents[2]
SUFFIX=Path('asap7/arithmetic_probe/base')
ASSET=Path(__file__).with_name('reference_assets')/'boundary_census.tcl'


def prepare(folder):
    from regression.arithmetic_target_round1 import capacity_sources
    from .platforms import profile
    row=capacity_sources()[0];features=row['features'];rtl=shells.source(features)
    # The exact protected source was already simulated in round one.
    from .model_target_round1_evidence import load
    _,pool=load(ROOT/'experiments/arithmetic/evidence/step7_target_round1_v2')
    saved=pool['inputs']['source_outputs']['capacity0']['rtl']
    if rtl!=saved:raise ValueError('capacity shell differs from accepted round-one source')
    flattened=rtl.replace('(* keep_hierarchy=1 *) ','')
    if flattened==rtl:raise ValueError('no hierarchy protection to compare')
    folder.mkdir(parents=True,exist_ok=False);tasks=[]
    for name,text in (('protected',rtl),('flat',flattened)):
        path=folder/(name+'.sv');path.write_text(text)
        tasks.append(dict(id=name,rtl=str(path),rtl_sha256=sha(path),top='ModelBundle',period_ps=1500,ABC_ps=1500,role='not_training'))
    ledger=Ledger();state=read(ledger.path);u=usage(state['entries']);limits=read(POLICY)['resources'];later=pool['inputs']['capacity']['later_work_reserved']
    if (any(e['status']=='reserved' and e.get('task_id')!='boundary-prepare' for e in state['entries'])
            or any(j['status'] in ('active','unsettled') and j.get('task_id')!='boundary-prepare' for j in state.get('jobs',[]))):
        raise ValueError('probe requires a settled starting boundary except its own preparation leaf')
    wall=2*(300+360);cpu=4*wall
    if (u['synth']+2+later['synth']>limits['max_synthesis_calls'] or u['grt']+later['grt']>limits['max_global_route_calls']
            or u['walltime_s']+wall+later['walltime_s']>limits['max_global_walltime_h']*3600
            or u['CPU_time_s']+cpu+later['CPU_time_s']>limits['max_tool_CPU_time_h']*3600
            or shutil.disk_usage(folder).free<later['storage_bytes']+1024**3):raise ValueError('bounded probes and later work not funded')
    sources=[Path(__file__),ASSET,Path(shells.__file__),Path(model_fast_sdc.__file__),POLICY,
             Path(__file__).with_name('backend.py'),Path(__file__).with_name('platforms.py'),Path(__file__).with_name('budget.py'),Path(__file__).with_name('processes.py')]
    for path in sources:
        dest=folder/'source'/path.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
    write(folder/'admission.json',dict(version='operator-boundary-diagnosis-admission-v1',id=folder.name,tasks=tasks,
        features=features,profile_sha256=profile('asap7')['profile_sha256'],source_sha256={str(p.relative_to(ROOT)):sha(p) for p in sources},
        synth_max=2,grt_max=0,final_max=0,support_max=8,walltime_envelope_s=wall,CPU_envelope_s=cpu,memory_limit_MiB=8192,
        later_work_reserved=later,source_role='not_training',automatic_retries=0,fit_allowed=False,production_binding_implemented=False,
        replaces_original_capacity_slots='two of six planned complete-target runs; remaining grt not admitted here',
        change='module keep_hierarchy attributes only; all arithmetic/FF/IO/target settings identical',physical_node_label_qualification=False))
    print('admitted two finite synth-only not_training mapped-boundary probes',flush=True)


class ProbeLedger(Ledger):
    def __init__(self,folder,task):super().__init__();self.folder=folder;self.task=task
    def reserve(self,stage,timeout_s,threads,purpose,command,output,*,context=None):
        a=read(self.folder/'admission.json')
        if self.task not in a['tasks'] or threads!=4 or stage not in (None,'synth'):raise ValueError('unregistered boundary task or stage')
        for name,h in a['source_sha256'].items():
            if sha(ROOT/name)!=h or sha(self.folder/'source'/name)!=h:raise ValueError('probe producer changed')
        if sha(self.task['rtl'])!=self.task['rtl_sha256']:raise ValueError('probe source changed')
        previous=[e for e in read(self.path)['entries'] if e.get('admission_id')==a['id']]
        if stage and (timeout_s>300 or any(e['stage']=='synth' and e.get('task_id')==self.task['id'] for e in previous)):raise ValueError('probe synth cap or no-retry guard')
        if not stage and (timeout_s>120 or sum(e['stage'] is None for e in previous)>=a['support_max']):raise ValueError('probe support bound')
        return super().reserve(stage,timeout_s,threads,purpose,command,output,context={**(context or {}),'target_platform':'asap7','admission_id':a['id'],
            'task_id':self.task['id'],'admission_sha256':sha(self.folder/'admission.json'),'model_version':'not_training-boundary-diagnosis-v1'})


def run(folder):
    from . import backend
    from .processes import run_command
    a=read(folder/'admission.json');before=read(Ledger().path);records=[]
    env=os.environ.copy();env.update(OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',YOSYS_MAX_THREADS='4',PYTHONDONTWRITEBYTECODE='1')
    namespace=dict(backend._evaluate.__globals__);namespace.update(rtl_ports=model_fast_sdc.rtl_ports,verify_sdc=model_fast_sdc.verify_sdc,
        os=SimpleNamespace(environ=env))
    evaluate=FunctionType(backend._evaluate.__code__,namespace,closure=backend._evaluate.__closure__)
    try:
        for task in a['tasks']:
            ledger=ProbeLedger(folder,task);ctx=dict(target_platform='asap7',admission_id=a['id'],task_id=task['id']);out=folder/'runs'/task['id']
            with ledger.job(ctx):
                args=SimpleNamespace(out=out,platform='asap7',threads=4,stage='synth',memory_limit_mib=8192,period_ps=1500,period_role='resource_trial',
                    abc_target_ps=1500,io_delay_max_ps=None,budget_purpose='characterization',admission_id=a['id'],task_id=task['id'],sample_contract=None,
                    admission=None,resume_synth_from=None,orfs=Path('/home/zyrv/OpenROAD-flow-scripts'),rtl=Path(task['rtl']),top=task['top'],
                    synth_timeout_s=300,route_timeout_s=1200,selection_freeze=None)
                if evaluate(args,ledger):raise ValueError('boundary synth failed; preserve logs and costs')
                m=read(out/'manifest.json');base=next(c['command'][:-1] for c in m['commands'] if c['log'].endswith('/synth.log'))
                command=base+['run','RUN_SCRIPT='+str(ASSET),'RUN_LOG_NAME_STEM=boundary_census','VULSIM_EVAL_DB=1_synth.odb','VULSIM_EVAL_SDC=1_synth.sdc']
                r=ledger.reserve(None,120,4,'not_training_boundary_census',command,out/'boundary-census',context=ctx)
                record=run_command(command,out,'boundary-census',120,env,8192,cpu_limit_s=r['CPU_time_s']);ledger.finish(r,record)
                records.append(dict(**record,budget_reservation_id=r['id']));write(folder/'commands.json',records)
                if record['exit_code']:raise ValueError('report-only boundary census failed')
                for name,h in m['evidence_sha256'].items():
                    if sha(out/name)!=h:raise ValueError('report-only probe changed original synthesis evidence')
            print('completed mapped-boundary census '+task['id'],flush=True)
    finally:
        after=read(Ledger().path);write(folder/'resource-increment.json',dict(entries=after['entries'][len(before['entries']):],usage=usage(after['entries']),new_training_rows=0))
    analyze(folder)


def analyze(folder):
    a=read(folder/'admission.json');rows=[]
    for task in a['tasks']:
        out=folder/'runs'/task['id'];m=read(out/'manifest.json');reports=out/'reports'/SUFFIX
        cells=[line.split('\t')[:2] for line in (reports/'boundary_instances.tsv').read_text().splitlines()]
        connections=list(csv.DictReader((reports/'boundary_connections.tsv').read_text().splitlines(),delimiter='\t'))
        by_net={}
        for pin in connections:by_net.setdefault(pin['net'],[]).append(pin)
        scopes={}
        for owner in ('core','consumer0','launch','capture','observer'):
            owned={n for n,master in cells if n.startswith(owner+'/')};crossin=[];crossout=[]
            for pin in connections:
                if pin['instance'] not in owned:continue
                if any(other['instance'] not in owned for other in by_net[pin['net']]):
                    if pin['direction']=='input':crossin.append(pin['instance']+'/'+pin['pin'])
                    if pin['direction']=='output':crossout.append(pin['instance']+'/'+pin['pin'])
            scopes[owner]=dict(cells=len(owned),boundary_inputs=len(crossin),boundary_outputs=len(crossout))
        exposed=bool(scopes['core']['cells'] and scopes['consumer0']['cells'] and scopes['core']['boundary_inputs'] and scopes['core']['boundary_outputs'] and scopes['consumer0']['boundary_inputs'] and scopes['consumer0']['boundary_outputs'])
        rows.append(dict(id=task['id'],scopes=scopes,total_instances=len(cells),operator_scopes_identifiable_by_declared_prefix=exposed,
            synthesis_metrics=m['metrics'][0],manifest_sha256=sha(out/'manifest.json'),RTL_sha256=task['rtl_sha256'],
            source_role='not_training',reports_sha256={p.name:sha(p) for p in reports.glob('boundary_*') if p.is_file()},
            independent_per_output_timing_qualified=False,area_label_qualified=False))
    write(folder/'boundary-audit.json',dict(version='operator-boundary-diagnosis-v1',rows=rows,
        conclusion='mapped scope census only; final D compatible strategy and all dynamic endpoints/constant aliases still require validation',
        synthesis_only=True,grt_calls=0,training_rows=0,full_D_ready=False))
    print(json.dumps(read(folder/'boundary-audit.json')),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','run','analyze'));p.add_argument('--folder',type=Path,required=True);args=p.parse_args();globals()[args.action](args.folder.resolve())
