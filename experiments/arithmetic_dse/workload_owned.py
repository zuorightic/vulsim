"""W2 common owner/provider/RTL path, using actual compiler plans.

No EDA is started and no model support is enlarged. The public consumer keeps
cost_uncovered; diagnostic prices are checked against the same Python functions.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import random
import shlex
import shutil
from . import workload_contracts as contracts, workload_sources as sources
from . import workload_demand as demand, wide_arithmetic as arithmetic
from . import operator_function_successor as operator, reduction_mapping_model as reduction
from .workload_software_validation import bench, run

REPO = Path(__file__).resolve().parents[2]


def read(p):
    return json.loads(Path(p).read_text())


def shared_models():
    """Read only the already frozen parameter objects, never query labels."""
    base = REPO / 'experiments/arithmetic/evidence/common_model_repair_v1'
    models = {key: json.loads(gzip.decompress((base / f'final-consumption-v3--{kind}-prices-input.json.gz').read_bytes()))['model']
              for key, kind in [('operators', 'operator'), ('G', 'G')]}
    return dict(models, version='workload-model-bindings-v2', profile_sha256=models['operators']['profile_sha256'])


def close(a, b):
    if type(a) in (int, float) and type(b) in (int, float):
        return math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-8)
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(close(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(close(x,y) for x,y in zip(a,b))
    return a == b


def projection(q):
    out = json.loads(json.dumps(q));out['version']='arithmetic-wide-query-v1'
    for consumer in out['local_context']['consumers']:
        for binding in consumer['bindings']:
            if binding.pop('role') != 'data':
                raise ValueError('carry/selector cannot be projected into v1')
        consumer.pop('operation')
    demand.wide.features(out)
    return out


def features(q):
    local=q['local_context'];p=local['producer'];arithmetic.validate(p)
    f={n:p[n] for n in ('lhs_width','rhs_width','arithmetic_width','result_width')}
    T=q['flow_context']['target_period_ps']
    f.update(target_ps=T,clock_pressure=1500/T,consumer_count=len(local['consumers']),
             capture_count=len(local['captures']),data_pin_uses=0,carry_pin_uses=0,selector_pin_uses=0,capture_pin_uses=0)
    for consumer in local['consumers']:
        for binding in consumer['bindings']:
            f[binding['role']+'_pin_uses']+=sum(type(b) is int for b in binding['result_bit_map'])
    f['capture_pin_uses']=sum(sum(type(b) is int for b in c['result_bit_map']) for c in local['captures'])
    return f


def verify_plan(root, view, graph, models):
    dest=root/view['directory'];plan=read(dest/'owners.json');stages=view['placement']
    state=read(dest/'state.json');counts=Counter()
    if plan['graph_sha256'] != state['graph_sha256'] or plan['layout_sha256'] != state['layout_sha256']:
        raise ValueError('owner plan is not bound to actual graph/state')
    owned=set();operators={};regions={}
    for region in plan['G_regions']:
        if owned & set(region['members']):raise ValueError('duplicate G owner')
        owned.update(region['members']);regions[region['root']]=region
        if region['query']['terms'] != region['terms']:raise ValueError('G price/emitter terms differ')
        sources=sorted({source for term in region['terms'] for source,_,_ in term})
        shared=sum(bool(graph.roots(a)&graph.roots(b)) for a,b in itertools.combinations(sources,2))
        if region['query']['shared_input_root_pairs']!=shared:raise ValueError('G correlation context differs')
        counts['correlated_G_regions']+=shared>0
        counts['G_regions']+=1
    for row in plan['operators']:
        n=row['node'];q=row['query'];p=q['local_context']['producer']
        if n in owned or stages[n]!=row['stage']:raise ValueError('duplicate/stale operator owner')
        owned.add(n);operators[n]=row;counts['operators']+=1
        expected=graph.spec(n)
        if graph.nodes[n]['operation']=='mux':
            for suffix in ('width','zero_hex','one_hex'):
                expected['lhs_'+suffix],expected['rhs_'+suffix]=expected['rhs_'+suffix],expected['lhs_'+suffix]
        if expected!=p:raise ValueError(f'compiler spec differs from independent graph extraction at {n}')
        if not close(features(q),row['interface_features']):raise ValueError('Python/C++ v2 interface features differ')
        try:old=projection(q)
        except (ValueError,TypeError,KeyError):old=None
        if old != row['predecessor_projection']:raise ValueError('v1 projection dropped/changed a real observation')
        counts['exact_v1_projections']+=old is not None
        counts['carry_pin_uses']+=row['interface_features']['carry_pin_uses']
        counts['selector_pin_uses']+=row['interface_features']['selector_pin_uses']
        counts['multiple_consumers']+=len(q['local_context']['consumers'])>1
    for n in plan['functional_logic']:
        if n in owned:raise ValueError('functional logic has another owner')
        owned.add(n);counts['functional_owners']+=1
    for seed in range(4):
        rng=random.Random(975+seed)
        values=graph.evaluate({p['name']:rng.getrandbits(p['width']) for p in graph.ports if p['input']})
        for n,row in operators.items():
            node=graph.nodes[n];q=row['query'];p=q['local_context']['producer'];args=node['operands']
            def value(a):return values[a['node']] if a['node'] is not None else int(a['literal_hex'],16)
            if node['operation']=='mux':a,b,c=value(args[2]),value(args[1]),value(args[0])
            else:a,b=value(args[0]),value(args[1]);c=value(args[2]) if node['operation']=='adc' else 0
            if arithmetic.evaluate(p,a,b,c) != values[n]&((1<<p['result_width'])-1):
                raise ValueError(f'owner scalar semantics changed at {n}')
            counts['scalar_integer_checks']+=1
        for n,region in regions.items():
            total=sum(((values[source]>>bit)&1)<<col for term in region['terms'] for source,bit,col in term)
            mask=(1<<region['output_bits'])-1
            if total&mask!=values[n]&mask:raise ValueError('G replacement changes arithmetic')
            counts['G_integer_checks']+=1
    rtl=(dest/'workload.sv').read_text()
    for n in operators:
        if f' rtlzz_owner_{n}(' not in rtl:raise ValueError('priced owner not installed in RTL')
    for n in regions:
        if f' rtlzz_reduce_{n}(' not in rtl:raise ValueError('G owner not installed in RTL')
        for m in regions[n]['members']:
            if f' rtlzz_owner_{m}(' in rtl:raise ValueError('G member still independently emitted')
    for mode,diagnostic in [('public',False),('diagnostic',True)]:
        report=read(dest/f'costs-{mode}.json')
        if report['stage_status']!='cost_uncovered' or report['static_fallback'] or report['full_D_ready']:
            raise ValueError('unqualified complete stage accepted')
        for owner in report['owners']:
            n=owner['node'];actual=owner['result']
            if owner['owner']=='operator':
                q=operators[n]['predecessor_projection']
                expected=operator.predict(models['operators'],q,diagnostic=diagnostic) if q is not None else None
            elif owner['owner']=='G':
                q=regions[n]['query']
                expected=reduction.predict(models['G'],q,diagnostic=diagnostic) if not q['shared_input_root_pairs'] else None
            else:expected=None
            accepted=actual['status'] in ('covered','diagnostic_estimate')
            if expected is not None:
                if accepted != (expected['status'] in ('covered','diagnostic_estimate')):raise ValueError('Python/C++ cost coverage differs')
                if accepted:
                    for key in ('operator_delay_ps','comb_area_um2'):
                        if not close(actual[key],expected[key]):raise ValueError('shared function price differs')
            elif accepted:raise ValueError('missing context/functional price replaced by a value')
            counts[mode+'_covered']+=accepted
            counts[mode+'_uncovered']+=not accepted
        if len(report['owners'])!=len(operators)+len(regions)+len(plan['functional_logic']):
            raise ValueError('pricing owner denominator differs from emitter')
    return counts


def inventory(out,binary,case_id,models_path,*,verify_rtl=True,reuse_rtl_from=None,timeout=180):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    case=next(c for c in contracts.load()['cases'] if c['id']==case_id)
    spec=sources.prepare_case(out/'source',case_id);models=read(models_path)
    noeda=out/'no-eda-bin';noeda.mkdir();marker=out/'backend-attempt'
    for name in ('yosys','abc','yosys-abc','openroad','opensta','sta'):
        p=noeda/name;p.write_text('#!/bin/sh\nprintf forbidden > '+shlex.quote(str(marker))+'\nexit 97\n');p.chmod(0o755)
    env=dict(os.environ,PATH=str(noeda)+os.pathsep+os.environ['PATH'])
    policy=case['structural_search'];target=case['formal_targets'][0];rows=[];total=Counter()
    for number,(block,limb) in enumerate(itertools.product(policy['mul_block_widths'],policy['add_sub_limb_widths'])):
        root=out/f'structure-{number}'
        run([binary,REPO,out/'source/request.json',target['L'],limb,policy['beam_width'],policy['max_extensions_per_structure'],root,block,target['T_ps'],'owned',models_path],out/f'structure-{number}.log',env,timeout)
        inv=read(root/'inventory.json');graph=demand.Graph(read(root/'graph.json'));counts=Counter();functional=[]
        previous=Path(reuse_rtl_from)/case_id/f'structure-{number}' if reuse_rtl_from else None
        if previous:
            old=read(previous/'inventory.json')
            if old['views']!=inv['views'] or (previous/'graph.json').read_bytes()!=(root/'graph.json').read_bytes():
                raise ValueError('RTL reuse requires identical graph/placement/artifact identities')
        for view in inv['views']:
            counts.update(verify_plan(root,view,graph,models));dest=root/view['directory']
            if verify_rtl:
                tb,checks=bench(spec,view['artifact'],target['L']);(dest/'tb.sv').write_text(tb)
                if previous:
                    src=previous/view['directory'];identities={}
                    for name in ('workload.sv','state.json','tb.sv'):
                        data=(src/name).read_bytes()
                        if data!=(dest/name).read_bytes():raise ValueError('RTL reuse changed '+name)
                        identities[name]=hashlib.sha256(data).hexdigest()
                    for name in ('iverilog.log','simulation.log'):
                        shutil.copyfile(src/name,dest/name)
                    output=(dest/'simulation.log').read_text()
                    (dest/'simulation-inheritance.json').write_text(json.dumps(dict(parent=str(src),identical_files=identities,
                        log_sha256=hashlib.sha256((src/'simulation.log').read_bytes()).hexdigest()),indent=2)+'\n')
                else:
                    run(['iverilog','-g2012','-s','tb','-o',dest/'sim.out',dest/'workload.sv',dest/'tb.sv'],dest/'iverilog.log',env,timeout)
                    output=run(['vvp',dest/'sim.out'],dest/'simulation.log',env,timeout)
                if 'PASS' not in output:raise ValueError('simulation did not finish')
                functional.append(dict(view=view['directory'],cycles=96,result_checks=checks,
                                       simulation='byte_identical_inheritance' if previous else 'executed'))
        row=dict(structure=number,mul_block_width=block,limb_width=limb,search=inv['search'],counts=dict(counts),functional=functional)
        rows.append(row);total.update(counts)
        # The v1 helper caches methods globally. Do not retain prior large graphs.
        graph.origins.cache_clear();graph.roots.cache_clear()
        print(json.dumps(dict(case=case_id,structure=number,placements=len(inv['views']),status='passed')),flush=True)
    if marker.exists():raise ValueError('backend startup attempted')
    report=dict(version='workload-owned-inventory-v2',case=case,structures=rows,counts=dict(total),
                binary_sha256=hashlib.sha256(Path(binary).read_bytes()).hexdigest(),
                model_bindings_sha256=hashlib.sha256(Path(models_path).read_bytes()).hexdigest(),
                target=target,status='passed',new_EDA_calls=0,independent_labels_read=False,full_D_ready=False)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True);g.add_argument('--case',choices=sorted(contracts.CASE_IDS));g.add_argument('--all',action='store_true')
    p.add_argument('--binary',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    p.add_argument('--models',type=Path);p.add_argument('--no-simulate',action='store_true')
    p.add_argument('--reuse-rtl-from',type=Path,help='Reuse successful simulation only after RTL/state/bench/placement byte checks')
    args=p.parse_args();out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    models=args.models.resolve() if args.models else out/'models.json'
    if not args.models:models.write_text(json.dumps(shared_models(),indent=2)+'\n')
    cases=[c['id'] for c in contracts.load()['cases']] if args.all else [args.case]
    reports=[inventory(out/c,args.binary.resolve(),c,models,verify_rtl=not args.no_simulate,reuse_rtl_from=args.reuse_rtl_from) for c in cases]
    (out/'summary.json').write_text(json.dumps([dict(case=r['case']['id'],counts=r['counts'],structures=len(r['structures']),placements=sum(x['search']['returned_placements'] for x in r['structures'])) for r in reports],indent=2)+'\n')
