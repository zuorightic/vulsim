"""Finite compatible shared train collection, real numerical ABC=SDC target.

No automatic retries. Validation requires an immutable train-fit freeze. The
outer controller only coordinates; every tool and report leaf uses Ledger.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
import inspect
import math
from pathlib import Path
import shutil
from types import SimpleNamespace

from .model_fast_preflight import read,write,sha
from .budget import Ledger,POLICY,usage
from . import stage67_physical_probe_v1 as physical
from . import stage67_mapped_state_v3 as mapped
from . import stage67_state_semantics_v1 as semantics
from . import stage67_physical_readout_v2 as readout
from . import stage67_shared_fit_v1 as fitting

ROOT=fitting.ROOT


def admit(root,preparation,role,freeze=None):
    if root.exists():raise ValueError('preserve admission attempt')
    protocol=read(preparation/'protocol.json');structures=read(preparation/'structures.json')
    if read(preparation/'simulation.json')['status']!='passed':raise ValueError('cycle proof missing')
    if role not in ('train','validation'):raise ValueError('locked_test remains locked')
    if role=='validation':
        if freeze is None:raise ValueError('validation requires parameter freeze')
        f=read(freeze)
        for n,h in f['files'].items():
            if sha(n)!=h:raise ValueError('fit freeze drift')
    tasks=[]
    for row in structures['rows']:
        if row['role']!=role:continue
        original=Path(row['native']);source=read(original.parent/'request.json')
        for t in protocol['targets_ps']:
            ident=row['source']+'-T'+str(t);dest=root/'inputs'/ident;dest.mkdir(parents=True)
            text=Path(row['rtl']).read_text();tops=__import__('re').findall(r'\bmodule\s+(Stage7_\w+)\s*\(',text)
            if len(tops)!=1 or sha(row['rtl'])!=row['rtl_sha256']:raise ValueError('RTL identity drift')
            rtl=dest/'input.sv';rtl.write_text(text.replace('module '+tops[0]+'(','module ModelBundle('))
            for name in ('export.json','features.json','endpoints.json'):shutil.copy2(original/name,dest/name)
            write(dest/'source.json',source)
            tasks.append(dict(id=ident,source=row['source'],source_role=role,placement=row['placement'],period_ps=t,
                rtl=str(rtl),rtl_sha256=sha(rtl),endpoint_contract=str(dest/'endpoints.json'),endpoint_sha256=sha(dest/'endpoints.json'),input_directory=str(dest)))
    if len(tasks)!=(24 if role=='train' else 9):raise ValueError('registered exact request count differs')
    later=dict(synth=688,grt=688,walltime_s=86400,CPU_time_s=172800,storage_bytes=30*1024**3)
    budget=dict(synth=len(tasks),grt=len(tasks),support=12*len(tasks),walltime_s=len(tasks)*(300+1200+12*120),storage_bytes=6*1024**3)
    budget['CPU_time_s']=4*budget['walltime_s'];used=usage(read(Ledger().path)['entries']);limits=read(POLICY)['resources']
    for stage,lim in [('synth','max_synthesis_calls'),('grt','max_global_route_calls')]:
        if used[stage]+budget[stage]+later[stage]>limits[lim]:raise ValueError('call reserve not funded')
    if used['walltime_s']+budget['walltime_s']+later['walltime_s']>limits['max_global_walltime_h']*3600 or used['CPU_time_s']+budget['CPU_time_s']+later['CPU_time_s']>limits['max_tool_CPU_time_h']*3600:raise ValueError('time reserve not funded')
    if shutil.disk_usage(root).free<later['storage_bytes']+budget['storage_bytes']:raise ValueError('storage reserve not funded')
    from .operator_collection import measurement_sources
    names=set(measurement_sources())
    names|={str(p.relative_to(ROOT)) for p in (ROOT/'experiments/arithmetic_dse').glob('stage67*.py')}
    names|={'experiments/arithmetic_dse/model_m2_live_cec_v4.py','experiments/arithmetic_dse/stage7_physical_prepare.py',
        'experiments/arithmetic_dse/reference_assets/stage67_context_v1.tcl','experiments/arithmetic_dse/reference_assets/stage7_readout_v1.tcl',
        'rtlzz/testv2/arithmetic_shared_export.cpp'}
    hashes={}
    for name in sorted(names):
        d=root/'source'/name;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,d);hashes[name]=sha(d)
    write(root/'admission.json',dict(version='shared-compatible-collection-v1',id=root.name,tasks=tasks,sources=hashes,
        model=protocol['dependencies']['node'],S_binding=protocol['dependencies']['S_binding'],protocol_path=str(preparation/'protocol.json'),protocol_sha256=sha(preparation/'protocol.json'),
        synth_max=len(tasks),grt_max=len(tasks),support_max=12*len(tasks),synth_timeout_s=300,grt_timeout_s=1200,
        automatic_retries=0,parallel_jobs=4,threads=4,memory_limit_MiB=8192,batch_budget=budget,later_work_reserved=later,
        role=role,freeze_path=str(freeze) if freeze else None,freeze_sha256=sha(freeze) if freeze else None,full_D_ready=False,created_at=datetime.now(timezone.utc).isoformat()))
    write(root/'progress.json',dict(phase='admitted',completed=[],errors=[],active=[]))
    print('SHARED_FINITE_ADMISSION role='+role+' requests='+str(len(tasks)),flush=True)


class SharedLedger(physical.PilotLedger):
    def reserve(self,stage,*args,**kwargs):
        a=read(self.root/'admission.json')
        if sha(a['protocol_path'])!=a['protocol_sha256'] or sha(self.task['endpoint_contract'])!=self.task['endpoint_sha256']:raise ValueError('shared protocol/endpoints drift')
        if a['freeze_path'] and sha(a['freeze_path'])!=a['freeze_sha256']:raise ValueError('frozen candidate drift')
        entries=[e for e in read(self.path)['entries'] if e.get('admission_sha256')==sha(self.root/'admission.json')]
        if stage and sum(e['stage']==stage for e in entries)>=a[stage+'_max']:raise ValueError('shared physical capacity exceeded')
        return super().reserve(stage,*args,**kwargs)


def verify_state(design,pins,contract,source,rtl):
    result=mapped.verify(design,pins,contract,source,rtl)
    # Parent supported zero input resets. Numeric resets are source properties,
    # not prices; complete exact Boolean qualification below is mandatory.
    for word in result['words']:
        if word['owner']=='input_service' and not word['valid']:
            name=word['name'].split('/')[-1];word['reset']=int(next(p for p in source['inputs'] if p['name']==name)['reset_hex'],16)
    for rows in result['physical_alias_groups'].values():
        for row in rows:
            word=next(w for w in result['words'] if w['name']==row['word']);row['reset_bit']=word['reset']>>row['bit']&1
        if len({(r['owner'],r['stage'],r['enable'],r['reset_bit'],r['valid'],r['logical_output_inverted']) for r in rows})!=1:raise ValueError('numeric reset aliases differ')
    result['version']='shared-compatible-numeric-reset-census-v1';return result


def point(root,task):
    text=inspect.getsource(physical.point)
    if text.count('model_m2_live_cec_v3')!=2 or text.count('1500')!=4:raise ValueError('frozen physical callsite drift')
    def verify(d,p,c,s):return verify_state(d,p,c,s,Path(task['rtl']).read_text())
    ns=dict(physical.point.__globals__);ns.update(mapped=SimpleNamespace(verify=verify),PilotLedger=SharedLedger)
    text=text.replace('model_m2_live_cec_v3','model_m2_live_cec_v4').replace('1500',"task['period_ps']")
    exec(compile(text,__file__,'exec'),ns);ns['point'](root,task)


def run(root):
    a=read(root/'admission.json');p=read(root/'progress.json')
    if p['errors'] or p['completed'] or p['active']:raise ValueError('preserve finite attempt; explicit successor required')
    p.update(phase='running',active=[t['id'] for t in a['tasks']]);write(root/'progress.json',p)
    # Exceptions are collected, never retried; already admitted independent
    # tasks may settle. The finite batch never auto-enqueues another batch.
    with ThreadPoolExecutor(max_workers=4) as pool:
        pending={pool.submit(point,root,t):t for t in a['tasks']}
        for future in as_completed(pending):
            task=pending[future]
            try:future.result();p['completed'].append(task['id'])
            except Exception as error:p['errors'].append(dict(task=task['id'],reason=str(error)))
            p['active'].remove(task['id']);write(root/'progress.json',p)
    p['phase']='physical_batch_complete' if not p['errors'] else 'stopped_on_errors';write(root/'progress.json',p)
    print('SHARED_BATCH_SETTLED completed='+str(len(p['completed']))+' errors='+str(len(p['errors'])),flush=True)


def extract(root,out):
    if out.exists():raise ValueError('preserve label extraction')
    out.mkdir(parents=True);a=read(root/'admission.json');p=read(root/'progress.json');rows=[]
    if p['phase']!='physical_batch_complete':raise ValueError('all admitted physical tasks must settle successfully before dataset')
    for task in a['tasks']:
        directory=root/'runs'/task['id'];state=read(directory/'mapped-state.json');contract=read(task['endpoint_contract'])
        proof=semantics.verify(directory,state,Path(task['rtl']).read_text(),contract);write(out/(task['id']+'-state.json'),proof)
        owners=readout.certificate(directory,directory,'grt',contract)
        # No sampling adapter/observer exists here: all seven owners belong to
        # the final compatible wrapper. Every root cell is kept exactly once.
        labels={n:0. for n in ('shared_clock','shared_physical','root_repair')};allareas={}
        for instance,master in owners['instances'].items():
            n=owners['owners'][instance];area=owners['liberty'][master]['area_um2'];allareas[n]=allareas.get(n,0)+area
            if n in labels:labels[n]+=area
        metrics=read(directory/'pilot-metrics.json')[-1]
        if not math.isclose(sum(allareas.values()),metrics['cell_area_um2'],rel_tol=1e-8,abs_tol=1e-5):raise ValueError('owned cell area differs from OpenDB')
        pred=next(t for t in read(Path(task['input_directory'])/'features.json')['predictions'] if t['target_ps']==task['period_ps'])
        expectedFF=pred['features']['total_FF_bits'];logical=state['logical_FF_bit_references'];actual=state['unique_physical_FF_bits']
        if expectedFF!=logical:raise ValueError('model semantic FF projection differs from actual compiler words')
        write(out/(task['id']+'-ownership.json'),owners)
        rows.append(dict(source=task['source'],role=task['source_role'],target_ps=task['period_ps'],features=pred['features'],labels=labels,
            predicted_state_areas=pred['state_areas'],node_predictions=pred['node_prices'],actual_owner_areas=allareas,total_area_um2=metrics['cell_area_um2'],
            logical_FF_references=logical,physical_FF_bits=actual,setup_slack_ps=metrics.get('setup_worst_slack_ps'),
            owner_certificate_sha256=sha(out/(task['id']+'-ownership.json')),state_proof_sha256=sha(out/(task['id']+'-state.json')),
            measured_functional_area_used_as_input=False))
    write(out/'dataset.json',dict(version='shared-compatible-dataset-v1',rows=rows,admission_sha256=sha(root/'admission.json'),protocol_sha256=a['protocol_sha256'],full_D_ready=False))
    print('SHARED_LABELS_EXTRACTED role='+a['role']+' rows='+str(len(rows)),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('admit','run','extract'));p.add_argument('--root',type=Path,required=True);p.add_argument('--preparation',type=Path);p.add_argument('--role');p.add_argument('--freeze',type=Path);p.add_argument('--out',type=Path);a=p.parse_args()
    if a.action=='admit':admit(a.root.resolve(),a.preparation.resolve(),a.role,a.freeze.resolve() if a.freeze else None)
    elif a.action=='run':run(a.root.resolve())
    else:extract(a.root.resolve(),a.out.resolve())


if __name__=='__main__':main()
