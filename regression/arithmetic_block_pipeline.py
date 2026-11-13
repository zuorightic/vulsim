"""Generic block-pipeline fixtures, integer semantics and emitted RTL checks.

These are software validation graphs, never physical training sources or prices.
The common C++ API accepts the source request and structural policy separately.
"""
import argparse
from pathlib import Path
import random

from experiments.arithmetic_dse.model_fast_preflight import read, write, sha
from regression.arithmetic_fused_d import evaluate_graph
from regression.portable_fused_d import rtl_check


def specifications():
    return [
        dict(id='rectangular', widths=dict(a=20,b=28,c=48), result=48, operation='mul_add'),
        dict(id='truncated', widths=dict(a=12,b=20,c=21), result=21, operation='mul_add'),
        dict(id='different_width', widths=dict(a=24,b=24,c=48), result=48, operation='mul_add'),
        dict(id='two_products', widths=dict(a=8,b=8,c=12,d=12), result=25, operation='two_products', L=2),
        dict(id='renamed', widths=dict(a=32,b=32,c=64), result=64, operation='mul_add', prefix='separate_', top='AnotherApplication'),
    ]


def prepare(folder):
    folder.mkdir(parents=True, exist_ok=False)
    cases=[]
    for spec in specifications():
        d=folder/spec['id'];d.mkdir();prefix=spec.get('prefix','__vul_port_');top=spec.get('top','GenericKernel')
        declarations=['#include <fixint.hpp>'];resets={}
        for name,width in spec['widths'].items():
            port=prefix+name;declarations += [f'#pragma input_port {port}',f'Int<{width}> {port};']
            resets[port]=[format(((1<<(width-1))+0x35)&((1<<width)-1),'x')]
        iv,ov,y=prefix+'iv',prefix+'ov',prefix+'y';R=spec['result']
        declarations += [f'#pragma input_port {iv}',f'bool {iv};',f'#pragma output_port {ov}',f'bool {ov};',f'#pragma output_port {y}',f'Int<{R}> {y};']
        p='Int<'+str(R)+'>'
        first=p+'('+prefix+'a*'+prefix+'b)'
        second=p+'('+prefix+'c)' if spec['operation']=='mul_add' else p+'('+prefix+'c*'+prefix+'d)'
        declarations.append(f'void {top}(){{ {y}={first}+{second}; }}')
        source=d/'source.cpp';source.write_text('\n'.join(declarations)+'\n');resets[iv]=['0']
        metadata=dict(name=spec['id'],source='source.cpp',source_label=spec['id']+'.cpp',top=top,N=1,iv=iv,ov=ov,reset=resets,generated_source_sha256=sha(source))
        write(d/'request.json',dict(version='D-source-metadata-v1',source=metadata))
        cases.append(dict(spec,request=str(d/'request.json'),L=spec.get('L',3)))
    write(folder/'cases.json',dict(version='block-pipeline-software-fixtures-v1',cases=cases,physical_training_role=False))


def reference(spec,values):
    prefix=spec.get('prefix','__vul_port_')
    v={name:values[prefix+name] for name in spec['widths']}
    second=v['c'] if spec['operation']=='mul_add' else v['c']*v['d']
    return (v['a']*v['b']+second)&((1<<spec['result'])-1)


def verify(entries,out):
    tests=read(entries)['entries'];semantics=[];rtl=[];summaries=[]
    for entry in tests:
        directory=Path(entry['output']);inventory=read(directory/'inventory.json');spec=entry['spec']
        if inventory['model_coverage_granted'] or inventory['selection_performed']:
            raise ValueError('software inventory cannot grant prices or select D')
        if bool(inventory['complete'])==bool(entry.get('expected_incomplete',False)):
            raise ValueError('unexpected structural completeness state')
        if not inventory['complete'] and not inventory['reason']:
            raise ValueError('incomplete search needs an explicit reason')
        rows=[read(directory/x['file']) for x in inventory['views']]
        graph_files={r['graph_file'] for r in rows};rng=random.Random(20261112)
        for filename in sorted(graph_files):
            exported=read(directory/filename);graph=exported['graph'];ports=exported['ports']
            inputs=[p for p in ports if p['input'] and p['name']!=read(entry['request'])['source']['iv']]
            outputs=[p for p in ports if not p['input'] and p['name']!=read(entry['request'])['source']['ov']]
            if len(outputs)!=1:raise ValueError('reference fixture has one data result')
            for i in range(132):
                values={p['name']:(0 if i==0 else (1<<p['width'])-1 if i==1 else 1 if i==2 else rng.getrandbits(p['width'])) for p in inputs}
                nodes={p['nodes'][0]:values[p['name']] for p in inputs}
                actual=evaluate_graph(graph,nodes,outputs[0]['nodes'][0])
                if actual!=reference(spec,values):raise ValueError('carry/shift/truncation semantics changed')
            semantics.append(dict(case=entry['id'],graph_file=filename,vectors=132))
        by_file={x['file']:r for x,r in zip(inventory['views'],rows)}
        for emitted in inventory['emitted']:
            row=dict(by_file[emitted['view_file']]);exported=read(directory/row['graph_file']);row.update(exported)
            report=dict(L=entry['L'],selected_view=row['view'],candidates=[row],artifact=emitted['artifact'])
            rtl.append((directory/emitted['directory'],report))
        three=sum(all(c['mul']+c['add']>0 for c in r['stage_counts']) for r in rows)
        summaries.append(dict(case=entry['id'],structures=inventory['structures'],views=len(rows),
                              assignments=inventory['assignments'],complete=inventory['complete'],
                              three_arithmetic_stage_views=three))
    cycles=rtl_check(rtl,out/'simulation')
    write(out/'acceptance.json',dict(status='passed',cases=summaries,semantics=semantics,rtl=cycles,
                                    physical_model_qualification=False,source_specific_pricing=False))
    print('BLOCK_PIPELINE_SOFTWARE_PASS graphs='+str(len(semantics))+' RTL='+str(len(rtl)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','verify']);p.add_argument('--out',type=Path,required=True);p.add_argument('--entries',type=Path);a=p.parse_args()
    if a.action=='prepare':prepare(a.out.resolve())
    else:verify(a.entries.resolve(),a.out.resolve())
