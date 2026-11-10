"""Versioned raw escaped-name and physical-only-cell adaptation for real labels."""
from types import FunctionType
import re

from . import model_physical_labels_v2 as parent
from .model_fast_path import canonical as parent_canonical


def canonical(name):
    while True:
        value=parent_canonical(name)
        if value==name:return value
        name=value


def with_timing_arcs(pins,libraries):
    """Allow output-to-output timing only when explicitly present in Liberty."""
    import gzip
    from pathlib import Path
    from .model_reference_labels import blocks
    from .model_fast_preflight import sha
    result={name:dict(cell,timing_arcs=[]) for name,cell in pins.items()}
    for lib in libraries:
        path=Path(lib['path'])
        if sha(path)!=lib['sha256']:raise ValueError('actual Liberty changed')
        text=gzip.decompress(path.read_bytes()).decode() if path.suffix=='.gz' else path.read_text()
        for name,body in blocks(text,'cell'):
            if name not in result:continue
            edges=set()
            for output,pinbody in blocks(body,'pin'):
                normalized=re.sub(r'\btiming\s*\(\s*\)', 'timing(__anonymous_arc)', pinbody)
                for _,timing in blocks(normalized,'timing'):
                    related=re.search(r'\brelated_pin\s*:\s*"([^"]+)"',timing)
                    if related:
                        for source in related[1].split():edges.add((source,output))
            result[name]['timing_arcs']=[list(edge) for edge in sorted(edges)]
    return result


def extract(packet,nodes,banks):
    p=dict(packet)
    p['liberty']={}
    for name,cell in packet['liberty'].items():
        meta=dict(cell);inputs=[v for v in cell['pins'].values() if v['direction']=='input'];outputs=[v.get('function') for v in cell['pins'].values() if v['direction']=='output']
        if not cell['sequential'] and not inputs and outputs and all(v is not None and re.sub(r'[\s()]','',v) in ('0','1',"1'b0","1'b1") for v in outputs):
            meta['constant_driver']=True
        p['liberty'][name]=meta
    p['instances']={canonical(k):v for k,v in p['instances'].items()}
    p['connections']={canonical(k):dict(v,net=canonical(v['net'])) for k,v in p['connections'].items()}
    p['pin_logic']={canonical(k):v for k,v in p['pin_logic'].items()}
    p['clock_nets']=[canonical(n) for n in p['clock_nets']]
    p['nodes']={name:{**{k:[canonical(n) for n in row[k]] for k in ('inputs','outputs','constants')},
                      'output_paths':{canonical(end):[(canonical(pin),t) for pin,t in points] for end,points in row['output_paths'].items()}}
                for name,row in p['nodes'].items()}
    p['data_requests']={name:{kind:[canonical(n) for n in v] for kind,v in row.items()} for name,row in p['data_requests'].items()}
    p['data_paths']={name:dict(row,start=canonical(row['start']),end=canonical(row['end']),points=[(canonical(pin),t) for pin,t in row['points']]) for name,row in p['data_paths'].items()}
    bank_aliases={name:[canonical(n) for n in values] for name,values in banks.items()}
    result=parent.extract(p,nodes,bank_aliases)
    result['reader_adapter']='qualification-escaped-physical-name-v1'
    return result


def read_snapshot(*args,**kwargs):
    namespace=dict(parent.read_snapshot.__globals__);namespace['extract']=extract
    fn=FunctionType(parent.read_snapshot.__code__,namespace,closure=parent.read_snapshot.__closure__)
    fn.__kwdefaults__=parent.read_snapshot.__kwdefaults__
    return fn(*args,**kwargs)
