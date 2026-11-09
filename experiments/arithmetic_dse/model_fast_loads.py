"""Exact local consumer/capture bit maps from static typed graphs.

Only graph semantics are consumed. Local contexts omit whole-case identity and
retain declared masks, bit positions, and independent dynamic consumer inputs.
This inventory is not a model, a data split, or physical sampling admission.
"""
import argparse
from collections import Counter
from pathlib import Path

from .model_fast_preflight import read,write,key,sha,bits,demanded_bits,operator_shape
from .model_fast_samples import from_shape


def bit_origins(nodes,at,stack=frozenset()):
    if at in stack:
        raise ValueError('cyclic static bit wiring')
    n=nodes[at];width=n['width'];op=n['operation'];args=n['operands']
    z,o=bits(n['known_zero_hex']),bits(n['known_one_hex'])
    def argument(a):
        if a['kind']=='literal':
            value=bits(a['limbs_hex']);return [str(value>>i&1) for i in range(a['width'])]
        if a['kind']=='symbol':
            return bit_origins(nodes,a['node'],stack|{at})
        raise ValueError('typed bit mapping requires symbol or literal')
    def resize(row,size):
        return (row+['0']*size)[:size]
    if op in ('mul','add','addcarry','input'):
        result=[(at,i) for i in range(width)]
    elif n['constant']:
        if (z|o)&((1<<width)-1)!=(1<<width)-1:
            raise ValueError('constant node lacks complete bit constants')
        result=[str(o>>i&1) for i in range(width)]
    elif op=='wire':
        kind=n['wiring_kind']
        if kind=='concat':
            result=[b for a in reversed(args) for b in argument(a)]
            if len(result)!=width:
                raise ValueError('concat bit mapping width differs')
        elif kind=='slice':
            if n['hi']-n['lo']+1!=width or n['lo']<0:
                raise ValueError('invalid static slice')
            result=argument(args[0])[n['lo']:n['hi']+1]
        elif kind=='bit_select':
            if n['bit']<0:
                raise ValueError('dynamic bit selection has no static map')
            result=argument(args[0])[n['bit']:n['bit']+1]
        elif kind in ('assign','cast','trunc','zext'):
            result=resize(argument(args[0]),width)
        else:
            raise ValueError('unregistered local bit wiring: '+kind)
    else:
        raise ValueError('unregistered local producer operation')
    if len(result)!=width:
        raise ValueError('static bit mapping is incomplete')
    return ['0' if z>>i&1 else '1' if o>>i&1 else b for i,b in enumerate(result)]


def contexts(exports):
    inventory={};old_contexts={};shapes={};counts=Counter()
    for export in exports:
        if export['PPA_calls'] or export['D_selection_completed']:
            raise ValueError('only static preselection native graphs allowed')
        nodes={n['id']:n for n in export['nodes']};demand=demanded_bits(nodes,export['ports'])
        local={at:operator_shape(n,nodes,demand) for at,n in nodes.items()
               if n['operation'] in ('mul','add','addcarry') and not n['constant'] and demand[at]}
        # Memoization is per graph; NodeIds never enter predictive features.
        maps={at:bit_origins(nodes,at) for at in nodes}
        for at,s in local.items():
            shapes[key(s)]=s
        for view in export['views']:
            for stage in view['stages']:
                inside=set(stage['semantic_members']);paid=inside & local.keys()
                for producer in paid:
                    consumers=[];captures=[];legacy=[]
                    def project(row):
                        return [b[1] if isinstance(b,tuple) and b[0]==producer else b if isinstance(b,str) else 'external' for b in row]
                    for child in paid:
                        if child==producer:
                            continue
                        n=nodes[child];bindings=[]
                        for index,a in enumerate(n['operands'][:2]):
                            if a['kind']=='literal':
                                value=bits(a['limbs_hex']);mapped=[str(value>>i&1) for i in range(a['width'])]
                            else:
                                mapped=maps[a['node']]
                            mapped=project(mapped[:a.get('billing_width',a['width'])])
                            # Unsigned low-r output bits do not observe input
                            # bits at r or above. Retain the declared position,
                            # but do not request a trimmed producer's high carry.
                            mapped=[b if i<local[child]['result_width'] else 'undemanded' for i,b in enumerate(mapped)]
                            if any(type(b) is int for b in mapped):
                                bindings.append(dict(operand_index=index,result_bit_map=mapped))
                                legacy.append(dict(shape_id=key(local[child]),operand_index=index))
                        if bindings:
                            consumers.append(dict(spec=from_shape(local[child]),bindings=bindings,
                                other_dynamic_inputs='independent_launch; source correlations require G validation'))
                    for capture in stage['captures']:
                        # A capture after another arithmetic node belongs to that
                        # node. Wiring is followed, arithmetic nodes stop traversal.
                        mapped=[b if demand[capture['value']]>>i&1 else 'undemanded'
                                for i,b in enumerate(project(maps[capture['value']]))]
                        if any(type(b) is int for b in mapped):
                            captures.append(dict(banks=capture['banks'],declared_width=capture['declared_width'],
                                                 result_bit_map=mapped))
                    consumers.sort(key=key);captures.sort(key=key)
                    spec=from_shape(local[producer]);features=dict(producer=spec,consumers=consumers,captures=captures)
                    signature=key(features);entry=inventory.setdefault(signature,dict(features=features,occurrences=0,legacy_context_ids=[]))
                    entry['occurrences']+=1
                    old=dict(operator_shape_id=key(local[producer]),internal_consumers=sorted(legacy,key=lambda v:(v['shape_id'],v['operand_index'])),
                             semantic_consumer_edges=len(legacy),
                             direct_capture_banks=sum(c['banks'] for c in stage['captures'] if c['value']==producer),
                             through_wiring_capture_banks=sum(c['banks'] for c in captures))
                    old_id=key(old);old_contexts[old_id]=old
                    if old_id not in entry['legacy_context_ids']:
                        entry['legacy_context_ids'].append(old_id)
                    counts['producer_occurrences']+=1
    return dict(version='arithmetic-fast-local-load-inventory-v1',contexts=inventory,legacy_contexts=old_contexts,
                operator_shapes=shapes,counts=dict(counts),local_context_count=len(inventory),legacy_context_count=len(old_contexts),
                source_role='static_software_requirement_only',physical_labels_read=False,role_assignment_frozen=False,
                physical_admission_allowed=False,full_D_ready=False,
                feature_identity='actual operator parameters, masks and bit maps; no case, split, NodeId or hash as prediction feature')


def prepare(native,requirements,out):
    index=read(native/'index.json');exports=[];files=[]
    if index['PPA_calls']:
        raise ValueError('static-only source index required')
    # Use the explicit index, rather than discovering arbitrary neighboring files.
    for case in index['cases']:
        for candidate in case['candidates']:
            if Path(candidate['file']).name!=candidate['file']:
                raise ValueError('native source reference escapes explicit input directory')
            path=native/candidate['file']
            if sha(path)!=candidate['sha256']:
                raise ValueError('native static source differs from indexed hash')
            d=read(path)
            if d.get('version')!='D-candidate-static-requirements-v1' or 'views' not in d or 'nodes' not in d:
                raise ValueError('unsupported static native source')
            exports.append(d);files.append(path)
    if not exports:
        raise ValueError('explicit static native graphs required')
    result=contexts(exports);required=read(requirements)
    if set(result['operator_shapes'])!=set(required['operator_shapes']) or set(result['legacy_contexts'])!=set(required['load_contexts']):
        missing=set(required['load_contexts'])-set(result['legacy_contexts']);extra=set(result['legacy_contexts'])-set(required['load_contexts'])
        raise ValueError('exact wiring inventory differs from audited P0 demand: missing='+str(len(missing))+' extra='+str(len(extra)))
    out.mkdir(parents=True,exist_ok=False)
    result.update(native_files_sha256={p.name:sha(p) for p in files},requirements_sha256=sha(requirements))
    write(out/'loads.json',result)
    print('PASS exact local load contexts='+str(result['local_context_count'])+'; legacy contexts='+str(result['legacy_context_count'])+'; physical labels=0',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--native',type=Path,required=True)
    parser.add_argument('--requirements',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    prepare(args.native.resolve(),args.requirements.resolve(),args.out.resolve())
