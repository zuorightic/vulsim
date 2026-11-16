"""Finite, backend-free nine-case preparation and balanced native schedules.

Static C retains the published abstract table. Global list scheduling adds
legal candidates to the archived beam pool; every proposed placement is
validated and materialized by RTLzz. No physical results enter this module.
"""
import argparse
from copy import deepcopy
import gzip
import json
import os
from pathlib import Path
import tempfile

from .sampling_time_contract import ROOT,canonical
from .workload_abcd import read,write,sha,static_node,static_cost,static_score
from .workload_v10_replay import old_structure,read_archive,PARENT,retarget
from .workload_v10 import binding
from .workload_contracts import load
from .workload_demand import Graph
from .workload_software_validation import bench,run as command

BINARY=ROOT/'build/workload-v10-20261115/rtlzz-workload'
VERSION='equivalent-nine-case-software-v1'
ENV=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')


def balanced(raw,units,L,weights):
    """Contract units, then find the smallest greedy per-stage capacity.

    Internal weighted longest paths define indivisible unit work. Dependent
    units may share a stage; a capacity overflow starts the next stage.
    Fixed port placement takes precedence over constant/wiring treatment.
    """
    nodes=raw['nodes'];membership={n:k for k,u in enumerate(units) for n in u['members']}
    dependencies=[];work=[]
    for k,u in enumerate(units):
        members=set(u['members']);cache={}
        def local(i):
            if i not in cache:
                cache[i]=weights.get(i,0.)+max((local(a['node']) for a in nodes[i]['operands'] if a['node'] in members),default=0.)
            return cache[i]
        dependencies.append(sorted({membership[a['node']] for n in members for a in nodes[n]['operands']
            if a['node'] is not None and a['node'] not in members}))
        if any(d>=k for d in dependencies[-1]):raise ValueError('native units are not dependency ordered')
        work.append(max(map(local,members),default=0.))
    def schedule(cap):
        stages=[];ends=[]
        for k,u in enumerate(units):
            ds=dependencies[k];s=max((stages[d] for d in ds),default=0)
            start=max((ends[d] for d in ds if stages[d]==s),default=0.)
            if u['fixed']:
                s=0 if all(nodes[n]['operation']=='input' for n in u['members']) else L-1
                start=max((ends[d] for d in ds if stages[d]==s),default=0.)
            elif u['constant']:s=0;start=0.
            elif work[k]>0 and start+work[k]>cap+1e-8:
                s+=1;start=0.
            stages.append(s);ends.append(start+work[k])
        return stages
    low=max(work,default=0.);high=sum(work)+1.
    for _ in range(48):
        mid=(low+high)/2;s=schedule(mid)
        if max(s,default=0)<L:high=mid
        else:low=mid
    results=[]
    for scale in (1.,1.08,1.25):
        s=schedule(high*scale+1e-6);placement=[0]*len(nodes)
        for k,u in enumerate(units):
            for n in u['members']:placement[n]=s[k]
        if max(placement,default=0)>=L:raise ValueError('balanced placement exceeds L')
        if placement not in results:results.append(placement)
    return results


def export(root,case,block,limb,T,L,placements=None,tag='beam'):
    out=root/case['id']/f'{tag}-b{block}-w{limb}-T{T}-L{L}'
    if (out/'inventory.json').exists():return out
    cmd=[BINARY,ROOT,root/case['id']/'source/request.json',L,limb,1,200000,out,block,T,'owned',root/'bindings.json']
    if placements:
        probe=export(root,case,block,limb,T,L)
        request=out.with_suffix('.placements.json');write(request,dict(version='workload-explicit-schedules-v1',
            L=L,T_clk_ps=T,graph_export_sha256=sha(probe/'graph.json'),placements=placements));cmd.append(request)
    command(cmd,out.with_suffix('.log'),ENV,timeout=600)
    return out


def record(path,view,structure,L,origin):
    graph=Graph(read(path/'graph.json'));state=read(path/view['directory']/'state.json')
    r=dict(structure=structure,view=view['directory'],folder=str(path/view['directory']),graph=str(path/'graph.json'),
        placement=view['placement'],artifact=view['artifact'],L=L,origin=origin,
        static=static_cost(graph,view,state,L),rtl_sha256=sha(path/view['directory']/'workload.sv'))
    Graph.origins.cache_clear();Graph.roots.cache_clear();return r


def simulate(root,case,row):
    folder=Path(row['folder']);receipt=folder/'functional-receipt.json'
    if receipt.exists():return read(receipt)
    spec=read(root/case['id']/'source/semantics.json');tb,checks=bench(spec,row['artifact'],row['L'],cycles=192)
    (folder/'tb.sv').write_text(tb)
    with tempfile.TemporaryDirectory(prefix='vulsim-final-sim-') as tmp:
        sim=Path(tmp)/'sim.vvp'
        command(['iverilog','-g2012','-s','tb','-o',sim,folder/'workload.sv',folder/'tb.sv'],folder/'iverilog.log',ENV,timeout=600)
        output=command(['vvp',sim],folder/'simulation.log',ENV,timeout=600)
    if 'PASS' not in output:raise ValueError('integer/cycle/reset/stall failure')
    r=dict(status='passed',rtl_sha256=sha(folder/'workload.sv'),testbench_sha256=sha(folder/'tb.sv'),
        log_sha256=sha(folder/'simulation.log'),cycles=192,integer_cycle_checks=checks,L=row['L'],II=1,
        additional_input_service_cycles=1)
    write(receipt,r);return r


def prepare(root,ids=None):
    root=Path(root).resolve();root.mkdir(parents=True,exist_ok=True);doc=load();write(root/'bindings.json',binding())
    protocol=dict(version=VERSION,contracts=doc,source_sha256=sha(__file__),binary_sha256=sha(BINARY),
        calibration_rule=dict(probe='minimum static_score over archived beam plus global balanced schedules',
            initial_target='max(1000, ceil(static-balanced software complete period / 100)*100)',
            final_tight='ceil(1.05 * measured full RR/IR/RO C threshold / 100)*100 ps',
            final_loose='ceil(1.45 * measured full RR/IR/RO C threshold / 100)*100 ps',
            MAC32='fixed 500/750/1000 ps; L3',one_probe_per_other_case=True),
        no_case_specific_response=True,application_PPA_feedback=False,old_queue_resumed=False,
        structures='all predeclared cross-product grammars; three globally balanced capacity variants per structure',
        qualification='diagnostic_only')
    if (root/'protocol.json').exists():
        if read(root/'protocol.json')!=protocol:raise ValueError('software protocol changed')
    else:write(root/'protocol.json',protocol)
    for case in doc['cases']:
        cid=case['id']
        if ids and cid not in ids:continue
        result=root/cid/'static-pool.json'
        if result.exists():continue
        cr=root/cid;cr.mkdir(exist_ok=True)
        for name,data in read_archive(PARENT/f'cases/{cid}.tar.gz').items():
            if name.startswith('source/'):
                p=cr/name;p.parent.mkdir(exist_ok=True);p.write_bytes(data)
        L=case['formal_targets'][0]['L'];T=case['formal_targets'][0]['T_ps'];policy=case['structural_search'];rows=[]
        grammar=[(b,w) for b in policy['mul_block_widths'] for w in policy['add_sub_limb_widths']]
        for number,(block,limb) in enumerate(grammar):
            # Restore the exact archived native candidate bytes, including all
            # views, as software-only seeds. Sources have archive SHA checks.
            old=old_structure(cid,number);path=cr/f'archive-{number}';path.mkdir(exist_ok=True)
            for name,data in old.items():
                p=path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
            for v in read(path/'inventory.json')['views']:rows.append(record(path,v,number,L,'archived_beam'))
            native=export(root,case,block,limb,T,L)
            if (native/'graph.json').read_bytes()!=old['graph.json']:raise ValueError('native/archived graph differs')
            raw=read(native/'graph.json');g=Graph(raw);weights={n['id']:static_node(g,n) for n in g.nodes}
            placements=balanced(raw,read(native/'scheduling-units.json')['units'],L,weights)
            Graph.origins.cache_clear();Graph.roots.cache_clear()
            new=export(root,case,block,limb,T,L,placements,'balanced')
            for v in read(new/'inventory.json')['views']:rows.append(record(new,v,number,L,'balanced_static'))
        A=export(root,case,0,0,T,1,tag='A');a=record(A,read(A/'inventory.json')['views'][0],0,1,'original_no_pipeline')
        b=min((r for r in rows if r['structure']==0),key=static_score);c=min(rows,key=static_score)
        for r in (a,b,c):simulate(root,case,r)
        write(result,dict(case=cid,grammar=grammar,candidates=rows,A=a,B=b,C=c,candidate_PPA_calls=0))
        print(json.dumps(dict(case=cid,candidates=len(rows),C=[c['structure'],c['view'],c['origin']],
            stage_weights=c['static']['stage_delay_weights'],state_bits=c['static']['saved_bits'])),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--cases',nargs='*')
    a=p.parse_args();prepare(a.root,a.cases)
