"""Portable W2 owner/provider/RTL evidence replay. No EDA or label access."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
import os
from pathlib import Path
import shlex
import tempfile
import tarfile
from . import workload_contracts as contracts, workload_demand as demand
from . import workload_evidence as predecessor
from .workload_software_validation import bench, run
from .workload_owned import read, shared_models, verify_plan

REPO = Path(__file__).resolve().parents[2]
DEFAULT = REPO / 'experiments/arithmetic/evidence/workload_owners_v2'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def check(condition, message):
    if not condition:
        raise ValueError(message)


def edge_bench():
    return '''module tb;
reg [12:0] x,y;reg iv;wire [13:0] s;wire [12:0] m0,m1;wire ov;
owner_edges dut(.x(x),.y(y),.iv(iv),.s(s),.m0(m0),.m1(m1),.ov(ov));
integer i;reg [13:0] expected;
initial begin
for(i=0;i<4096;i=i+1)begin
x=(i*997+8191)&8191;y=(i*617+1)&8191;iv=i&1;
#1;expected={1'b0,x}+{1'b0,y}+(x<y);
if(s!==expected||m0!==(x<y?13'h1555:x)||m1!==(x<y?y:13'haaa)||ov!==iv)begin
$display("FAIL %d %h %h",i,x,y);$fatal;end
end
$display("PASS owner_edges vectors=4096 L=1 carry_and_selector");$finish;
end
endmodule
'''


def verify_observations(graph,stages,state,plan):
    """Rebuild consumers/captures from graph bits, without trusting Query counts."""
    specs={}
    for node in graph.nodes:
        n=node['id']
        if node['operation'] in demand.ARITHMETIC and graph.demand[n] and not node['constant']:
            if not any(graph.origins(n)[b]==(n,b) for b in graph.demand[n]):continue
            spec=graph.spec(n)
            if node['operation']=='mux':
                for suffix in ('width','zero_hex','one_hex'):
                    spec['lhs_'+suffix],spec['rhs_'+suffix]=spec['rhs_'+suffix],spec['lhs_'+suffix]
            specs[n]=spec
    members={n for r in plan['G_regions'] for n in r['members']}
    operators={r['node']:r for r in plan['operators']}
    check(set(operators)==specs.keys()-members,'arithmetic owner omitted or invented')
    functional={node['id'] for node in graph.nodes if node['operation'] not in demand.ARITHMETIC|demand.WIRE|{'input'}
                and graph.demand[node['id']] and not node['constant'] and
                any(graph.origins(node['id'])[b]==(node['id'],b) for b in graph.demand[node['id']])}
    check(functional==set(plan['functional_logic']),'functional owner omitted or invented')
    groups={n:{} for n in operators};captures={n:[] for n in operators}
    for node in graph.nodes:
        sink=node['id'];op=node['operation']
        if not graph.demand[sink] or node['constant'] or op=='input' or graph.wire_equivalent(sink) or sink in members:continue
        for pin,arg in enumerate(node['operands']):
            raw=(graph.operand(arg)+('0',)*arg['width'])[:arg['width']]
            sources={b[0] for b in raw if isinstance(b,tuple)} & operators.keys()
            for source in sources:
                if stages[source]!=stages[sink]:continue
                role='carry' if op=='adc' and pin==2 else 'selector' if op=='mux' and pin==0 else 'data'
                index=(0 if pin==2 else 1) if op=='mux' and role=='data' else pin
                limit=specs[sink]['lhs_width' if index==0 else 'rhs_width'] if role=='data' and sink in specs else len(raw)
                mapping=[b[1] if isinstance(b,tuple) and b[0]==source else 'external' if isinstance(b,tuple) else b for b in raw[:limit]]
                mapping+=['0']*(limit-len(mapping))
                for bit,value in enumerate(mapping):
                    if sink in specs and role=='data' and op not in ('mux','ult','ule','eq') and bit>=specs[sink]['result_width']:
                        mapping[bit]='undemanded'
                    elif type(value) is int and value>=specs[source]['result_width']:mapping[bit]='undemanded'
                if any(type(b) is int for b in mapping):
                    groups[source].setdefault(sink,[]).append(dict(operand_index=index,role=role,result_bit_map=mapping))
    for region in plan['G_regions']:
        used={}
        for term in region['terms']:
            for source,bit,_ in term:used.setdefault(source,set()).add(bit)
        for source,bits in used.items():
            if source not in operators or stages[source]!=region['stage']:continue
            mapping=[b if b in bits else 'undemanded' for b in range(graph.nodes[source]['width'])]
            groups[source][region['root']]=[dict(operand_index=0,role='data',result_bit_map=mapping)]
    for slot in state['slots']:
        if slot['valid'] or not slot['variable_bits']:continue
        bits=graph.origins(slot['origin'])
        sources={b[0] for pos,b in enumerate(bits) if pos in graph.demand[slot['origin']] and isinstance(b,tuple)} & operators.keys()
        for source in sources:
            if slot['stage']!=stages[source]+1:continue
            mapping=['undemanded' if pos not in graph.demand[slot['origin']] else b[1] if isinstance(b,tuple) and b[0]==source else
                     'external' if isinstance(b,tuple) else b for pos,b in enumerate(bits)]
            captures[source].append(dict(banks=1,declared_width=slot['declared_width'],result_bit_map=mapping))
    for n,row in operators.items():
        expected=[]
        for sink,bindings in sorted(groups[n].items()):
            is_g=sink in members
            expected.append(dict(operation='reduction' if is_g else graph.nodes[sink]['operation'] if graph.nodes[sink]['operation'] in demand.ARITHMETIC else 'functional',
                spec=specs[sink] if sink in specs and not is_g else None,bindings=bindings,
                other_dynamic_inputs='independent_launch; source correlations require G validation'))
        local=row['query']['local_context']
        check(local['consumers']==expected and local['captures']==captures[n],f'actual consumer/capture observations differ at {n}')


def replay_predecessor(evidence):
    """Restore frozen source bytes; do not edit or bypass the v1 manifest."""
    old = REPO / 'experiments/arithmetic/evidence/workloads_software_v1'
    original = predecessor.REPO
    with tempfile.TemporaryDirectory(prefix='w2-predecessor-source-') as tmp:
        temp=Path(tmp);archive=read(evidence/'archives.json')
        entry=next(a for a in archive if a['kind']=='predecessor-sources')
        predecessor.unpack(evidence,entry,temp)
        for name,digest in read(old/'manifest.json')['implementation_sources'].items():
            dest=temp/name
            if not dest.exists():
                dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((REPO/name).read_bytes())
            check(sha(dest.read_bytes())==digest,'frozen predecessor source differs: '+name)
        try:
            predecessor.REPO=temp
            return predecessor.replay(old)
        finally:
            predecessor.REPO=original


def replay(evidence=DEFAULT, *, simulate=False, include_predecessor=False):
    evidence=Path(evidence).resolve();manifest=read(evidence/'manifest.json')
    check(manifest['version']=='workload-owners-evidence-v2','unknown evidence version')
    for name,digest in manifest['implementation_sources'].items():
        check(sha((REPO/name).read_bytes())==digest,'implementation changed: '+name)
    for name,digest in manifest['evidence_files'].items():
        check(sha((evidence/name).read_bytes())==digest,'evidence changed: '+name)
    models=read(evidence/'models.json')
    check(models==shared_models(),'frozen common parameters changed')
    total=Counter();structures=placements=cycles=executed=inherited=0
    with tempfile.TemporaryDirectory(prefix='w2-owner-replay-') as tmp:
        temp=Path(tmp);members=0
        for archive in read(evidence/'archives.json'):
            if archive['kind']=='structure':dest=temp/archive['case']/f"structure-{archive['structure']}"
            elif archive['kind']=='case':dest=temp/archive['case']
            elif archive['kind']=='predecessor-sources':continue
            else:raise ValueError('unexpected archive kind')
            members+=predecessor.unpack(evidence,archive,dest)
        sentinels=temp/'no-eda-bin';sentinels.mkdir();marker=temp/'backend-attempt'
        for name in ('yosys','abc','yosys-abc','openroad','opensta','sta'):
            p=sentinels/name;p.write_text('#!/bin/sh\nprintf forbidden > '+shlex.quote(str(marker))+'\nexit 97\n');p.chmod(0o755)
        env=dict(os.environ,PATH=str(sentinels)+os.pathsep+os.environ['PATH'])
        for case in contracts.load()['cases']:
            root=temp/case['id'];report=read(root/'report.json');target=case['formal_targets'][0]
            check(report['case']==case and report['target']==target,'effective contract changed')
            check(not report['full_D_ready'] and not report['independent_labels_read'] and report['new_EDA_calls']==0,'qualification changed')
            spec=read(root/'source/semantics.json');counts=Counter()
            canonical=REPO/'experiments/arithmetic/examples/workloads_v1'/case['id']/'source.cpp'
            check((root/'source/source.cpp').read_bytes()==canonical.read_bytes(),'mathematical source changed')
            for row in report['structures']:
                dest=root/f"structure-{row['structure']}";inv=read(dest/'inventory.json');graph=demand.Graph(read(dest/'graph.json'))
                check(inv['boundary_mode']=='owned' and inv['diagnostic_T_ps']==target['T_ps'],'wrong boundary/T')
                check(not inv['search']['budget_exhausted'] and inv['search']==row['search'],'search trace changed')
                check(len(inv['views'])==inv['search']['returned_placements']==len(row['functional']),'placement denominator changed')
                for view,functional in zip(inv['views'],row['functional'],strict=True):
                    counts.update(verify_plan(dest,view,graph,models));v=dest/view['directory']
                    verify_observations(graph,view['placement'],read(v/'state.json'),read(v/'owners.json'))
                    check(sha((v/'workload.sv').read_bytes())==view['artifact']['sha256'],'RTL identity changed')
                    expected,checks=bench(spec,view['artifact'],target['L'])
                    check((v/'tb.sv').read_text()==expected and functional['result_checks']==checks,'transaction reference changed')
                    check(functional['cycles']==96 and 'PASS' in (v/'simulation.log').read_text(),'successful simulation missing')
                    if functional['simulation']=='byte_identical_inheritance':
                        receipt=read(v/'simulation-inheritance.json')
                        for name,digest in receipt['identical_files'].items():
                            check(sha((v/name).read_bytes())==digest,'inherited RTL/state/bench changed')
                        check(sha((v/'simulation.log').read_bytes())==receipt['log_sha256'],'inherited receipt changed')
                        inherited+=1
                    else:
                        check(functional['simulation']=='executed','unknown simulation provenance');executed+=1
                    if simulate:
                        run(['iverilog','-g2012','-s','tb','-o',v/'sim.out',v/'workload.sv',v/'tb.sv'],v/'replay-iverilog.log',env)
                        check('PASS' in run(['vvp',v/'sim.out'],v/'replay-simulation.log',env),'RTL replay failed')
                    placements+=1;cycles+=96
                structures+=1;graph.origins.cache_clear();graph.roots.cache_clear()
            check(dict(counts)==report['counts'],'owner/price/check denominator changed');total.update(counts)
        edge=evidence/'owner-edges'
        check((edge/'tb.sv').read_text()==edge_bench(),'edge reference changed')
        check('WORKLOAD_OWNER_CONTRACT_PASS' in (edge/'contract-test.log').read_text(),'C++ negative checks missing')
        check('PASS' in (edge/'simulation.log').read_text(),'edge RTL simulation missing')
        if simulate:
            run(['iverilog','-g2012','-s','tb','-o',temp/'edge.out',edge/'design.sv',edge/'tb.sv'],temp/'edge-compile.log',env)
            check('PASS' in run(['vvp',temp/'edge.out'],temp/'edge-simulation.log',env),'edge RTL replay failed')
        check(not marker.exists(),'backend startup attempted')
    check((structures,placements,cycles)==(64,502,48192),'nine-case acceptance totals changed')
    regression=read(evidence/'v1-regression.json')
    check(regression['status']=='passed' and regression['checks']==6144 and regression['groups']==19,'v1 regression incomplete')
    old=REPO/'experiments/arithmetic/evidence/workloads_software_v1'
    for row in regression['rows']:
        blob=(evidence/'v1-regression'/(Path(row['case']).stem+'.json.gz')).read_bytes()
        check(sha(blob)==row['sha256'],'native regression result changed')
        with tarfile.open(old/'diagnostics'/row['case'],'r:gz') as tf:
            retained=json.loads(tf.extractfile('native-queries.json').read())
        check(json.loads(gzip.decompress(blob))==retained and len(retained)==row['queries'],
              'predecessor feature/Core output differs')
    result=dict(status='passed',structures=structures,placements=placements,cycles=cycles,counts=dict(total),
        archive_members_verified=members,simulation_receipts_executed=executed,simulation_receipts_inherited=inherited,
        RTL_simulations_rerun=placements+1 if simulate else 0,edge_vectors=4096,v1_CPP_Query_Core_checks=6144,
        target_scope='first registered T per case; software coverage only',new_EDA_calls=0,
        independent_labels_read=False,full_D_ready=False)
    if include_predecessor:result['predecessor']=replay_predecessor(evidence)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--evidence',type=Path,default=DEFAULT)
    p.add_argument('--simulate',action='store_true');p.add_argument('--predecessor',action='store_true')
    args=p.parse_args();print(json.dumps(replay(args.evidence,simulate=args.simulate,include_predecessor=args.predecessor),indent=2))
