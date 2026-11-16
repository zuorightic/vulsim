"""User-confirmed A/L clock rule and a fresh tight-target D/ABCD run.

The C-based clock experiment is retained as superseded history. A is the
original unsplit L1 source, measured at a software-scaled reference request.
Its fixed-implementation full RR/IR/RO Tmin sets two targets at 1.25/1.5 A/L.
The final A implementations are also measured at each actual comparison T.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import math
from pathlib import Path
import shutil
import time

from .sampling_time_contract import ROOT
from .workload_abcd import read,write,sha,static_node,static_score
from .workload_contracts import load
from .workload_demand import Graph
from .workload_final_software import export,record,balanced,simulate,BINARY
from .workload_final_selection import select_case,metadata,BASE
from .workload_final_prices import CachedPrices
from .workload_diagnostic import evaluate
from .workload_final_driver import drive,final_tasks,report
from . import workload_final_backend as physical

LEGACY=ROOT.parent/'vulsim-artifacts/workload-equivalent-steps678-v1'
DEFAULT=ROOT.parent/'vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A'
VERSION='nine-case-A-over-L-tight-targets-v2'


def initialize(root):
    root=Path(root).resolve();root.mkdir(parents=True,exist_ok=True);soft=root/'software';soft.mkdir(exist_ok=True)
    policy=dict(version=VERSION,clock_basis='unsplit_A',user_confirmed_factors=[1.25,1.5],quantum_ps=50,
        reference_A=dict(L=1,software_reference_request_ps=1000,
            requested_period_rule='max(1000, ceil(1.10 * unsplit_A_software_period_at_1000ps / 100)*100) ps',
            scope='fixed grt full RR/IR/RO Tmin; IOmax=0.2T',
            note='uniform software-only rule avoids extreme infeasible A repair; not a proof of global mapping optimum'),
        final_clock_rule='ceil(factor * measured_reference_A_Tmin / declared_L / 50) * 50 ps',
        rounded_collision_rule='second target at least first+50ps to retain two distinct groups',
        MAC32=dict(targets_ps=[500,750,1000],L=3,unchanged_by_user=True),
        no_C_based_clock_relaxation=True,unreachable_target='retain closest complete prediction; do not change final T',
        finite_grammar_extensions=dict(add512_limbs=[8,16],mul128_blocks=[4],horner64_blocks=[4,8],
            dot16_blocks=[8],barrett64_blocks=[8],karatsuba256_blocks=[8],montgomery256_blocks=[8],ntt8x64_blocks=[8]),
        models='original frozen responses and common diagnostic shell; no refit',
        maximum_structures_per_case=16,case_specific_model_prices=False,application_PPA_for_D_selection=False,
        original_independent_sources_locked=True,superseded_C_based_experiment=str(LEGACY),
        source_sha256=sha(__file__),native_compiler_sha256=sha(BINARY))
    protocol=soft/'protocol.json'
    if protocol.exists() and read(protocol)!=policy:raise ValueError('tight-target protocol changed')
    if not protocol.exists():write(protocol,policy)
    for n in ('bindings.json','characterization-contract.json'):
        if not (soft/n).exists():shutil.copyfile(LEGACY/'software'/n,soft/n)
    for case in load()['cases']:
        cid=case['id'];cr=soft/cid;cr.mkdir(exist_ok=True)
        if not (cr/'source').exists():shutil.copytree(LEGACY/'software'/cid/'source',cr/'source')
        if not (cr/'static-pool.json').exists():shutil.copyfile(LEGACY/'software'/cid/'static-pool.json',cr/'static-pool.json')
    # Preserve the confirmed MAC32 pool and exact selected implementations.
    # Its old four shell families and all numerical responses are unchanged.
    source=LEGACY/'software/selected/mac32';dest=soft/'selected/mac32'
    if not dest.exists():dest.parent.mkdir(exist_ok=True);shutil.copytree(source,dest)
    selection=read(LEGACY/'software/mac32/final-selections.json')
    for row in selection['records']:
        for method,m in row['methods'].items():
            folder=dest/f"T{row['target']['T_ps']}-L{m['L']}"/method
            m.update(rtl=str(folder/'workload.sv'),simulation_receipt=str(folder/'functional-receipt.json'))
    if not (soft/'mac32/final-selections.json').exists():write(soft/'mac32/final-selections.json',selection)
    targets=root/'targets';targets.mkdir(exist_ok=True)
    if not (targets/'mac32.json').exists():write(targets/'mac32.json',dict(case='mac32',L=3,targets_ps=[500,750,1000],role='confirmed_requests'))
    return policy


def prepare_A(root):
    soft=root/'software';tasks=[];prices=CachedPrices(read(BASE/'diagnostic-model.json'))
    for case in load()['cases']:
        cid=case['id']
        if cid=='mac32':continue
        old=read(soft/cid/'static-pool.json')['A']
        g,v,s,o=metadata(old,1000);prediction=evaluate(g,v,s,o,prices)
        requested=max(1000,math.ceil(1.10*prediction['critical_required_ps']/100)*100)
        native=export(soft,case,0,0,requested,1,tag='unsplit-A-reference')
        view=read(native/'inventory.json')['views'][0];row=record(native,view,0,1,'unsplit_A_reference')
        if row['rtl_sha256']!=old['rtl_sha256'] or any(row['placement']):raise ValueError('reference A must remain original unsplit L1 RTL')
        simulate(soft,case,row);folder=Path(row['folder'])
        tasks.append(dict(id=cid+'-A-reference',case=cid,method='A',L=1,rtl=str(folder/'workload.sv'),period_ps=requested,
            software_reference_period_ps=prediction['critical_required_ps'],software_reference_request_ps=1000,
            simulation_status='passed',simulation_receipt=str(folder/'functional-receipt.json'),large=cid!='add512'))
        print('A_REFERENCE_READY '+cid+' request='+str(requested),flush=True)
        Graph.origins.cache_clear();Graph.roots.cache_clear()
    return tasks


def extend_pool(root,case):
    soft=root/'software';cid=case['id'];pool=read(soft/cid/'static-pool.json')
    if pool.get('tight_extensions_complete'):return
    grammar=[tuple(g) for g in pool['grammar']];new=[]
    if cid=='add512':new=[(0,w) for w in (8,16)]
    else:
        blocks=[4] if cid=='mul128' else [4,8] if cid=='horner64' else [8]
        new=[(b,w) for b in blocks for w in case['structural_search']['add_sub_limb_widths']]
    for pair in new:
        if pair not in grammar:grammar.append(pair)
    if len(grammar)>16:raise ValueError('finite structural grammar cap exceeded')
    old_count=len(pool['grammar']);T=case['formal_targets'][0]['T_ps'];L=case['formal_targets'][0]['L'];rows=pool['candidates']
    for number in range(old_count,len(grammar)):
        block,limb=grammar[number];native=export(soft,case,block,limb,T,L)
        inv=read(native/'inventory.json')
        for view in inv['views']:rows.append(record(native,view,number,L,'tight_new_structure'))
        raw=read(native/'graph.json');graph=Graph(raw);weights={n['id']:static_node(graph,n) for n in graph.nodes}
        placements=balanced(raw,read(native/'scheduling-units.json')['units'],L,weights)
        dest=export(soft,case,block,limb,T,L,placements,tag='balanced-tight')
        for view in read(dest/'inventory.json')['views']:rows.append(record(dest,view,number,L,'balanced_static'))
        Graph.origins.cache_clear();Graph.roots.cache_clear()
    pool.update(grammar=[list(g) for g in grammar],candidates=rows,tight_extensions_complete=True,
        original_structures=old_count,new_structures=len(grammar)-old_count)
    pool['C']=min(rows,key=static_score);simulate(soft,case,pool['C'])
    write(soft/cid/'static-pool.json',pool)
    print('TIGHT_POOL_READY '+cid+' '+str(len(grammar))+' structures '+str(len(rows))+' placements',flush=True)


def freeze_target(root,case):
    cid=case['id'];p=root/'A-reference/runs'/(cid+'-A-reference')/'clock-readout/result.json';r=read(p)
    L=case['formal_targets'][0]['L'];A=r['full_setup_minimum_period_ps'];raw=[A/L*f for f in (1.25,1.5)]
    targets=[math.ceil(t/50)*50 for t in raw];targets[1]=max(targets[1],targets[0]+50)
    if not all(0<t<A for t in targets):raise ValueError('derived pipeline target is not tighter than measured A')
    task=next(t for t in read(root/'A-reference/admission.json')['tasks'] if t['case']==cid)
    value=dict(case=cid,L=L,targets_ps=targets,raw_target_ps=raw,A_reference_Tmin_ps=A,A_reference_request_ps=task['period_ps'],
        ideal_A_over_L_ps=A/L,factors=[1.25,1.5],quantum_ps=50,role='A_clock_calibration_only',
        clock_readout_sha256=sha(p),application_PPA_for_model=False,final_D_PPA_for_clock=False)
    out=root/'targets'/(cid+'.json')
    if out.exists() and read(out)!=value:raise ValueError('tight targets changed after freeze')
    if not out.exists():write(out,value)
    print('TIGHT_TARGETS '+cid+' A='+str(A)+' L='+str(L)+' T='+str(targets),flush=True)
    return targets


def software_worker(root):
    cases=[c for c in load()['cases'] if c['id']!='mac32'];pending={c['id']:c for c in cases}
    # The finite grammar is declared before A measurement. Its C selection and
    # all later D choices use software only, with no A label as a price.
    for case in cases:extend_pool(root,case)
    while pending:
        progress=read(root/'A-reference/progress.json');ready=[]
        for cid,case in pending.items():
            task=cid+'-A-reference'
            if any(e['task']==task for e in progress['errors']):raise RuntimeError('A reference failed: '+cid)
            if task in progress['completed']:ready.append(case)
        if not ready:time.sleep(5);continue
        for case in ready:
            targets=freeze_target(root,case);select_case(root/'software',case['id'],targets);del pending[case['id']]
    rows=[read(root/'targets'/(c['id']+'.json')) for c in load()['cases']]
    write(root/'target-matrix.json',dict(version=VERSION,rows=rows,groups=sum(len(r['targets_ps']) for r in rows),
        user_confirmed=True,clock_basis='unsplit_A',factors=[1.25,1.5],quantum_ps=50,
        no_C_based_clock_relaxation=True,application_PPA_for_model=False,final_D_PPA_for_clock=False))


def run(root):
    root=Path(root).resolve();initialize(root);tasks=prepare_A(root)
    # Existing C-probe commands are allowed to settle and retain their costs;
    # their stopped controller cannot launch any more wide-target work.
    while read(LEGACY/'calibration-first-five/progress.json')['status']!='batch_settled':time.sleep(5)
    A=root/'A-reference'
    if not A.exists():physical.admit(A,tasks,'clock_calibration')
    mac=final_tasks(root,['mac32'],'final-mac32')
    with ThreadPoolExecutor(max_workers=1) as executor:
        future=executor.submit(software_worker,root);drive([A,mac]);future.result()
    final=final_tasks(root,[c['id'] for c in load()['cases'] if c['id']!='mac32'],'final-tight-eight')
    drive([final]);return report(root,('final-mac32','final-tight-eight'))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['run','report']);p.add_argument('--root',type=Path,default=DEFAULT)
    a=p.parse_args();print(run(a.root) if a.action=='run' else report(a.root,('final-mac32','final-tight-eight')))
