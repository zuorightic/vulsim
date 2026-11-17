"""Finite N5/N6 offline micro-compositions; frozen D and live ASAP7 are read-only."""
from copy import deepcopy
import json
import math
from pathlib import Path
import re
import shutil

from .nangate45_samples import ROOT, read, write, sha
from . import budget, workload_nine_runtime as runtime
from . import workload_platform_entry as entry
from .workload_final_software import BINARY
from .workload_demand import Graph
from . import workload_diagnostic as diagnostic
from .stage7_physical_prepare import wrapper
from .platforms import profile

VERSION = 'nangate45-N56-micro-compositions-v1'
MODEL = ROOT/'experiments/arithmetic/evidence/nangate45_pressure_refit_v1/model.json'
DEFAULT = ROOT.parent/'vulsim-artifacts/nangate45-n56-20261117-v3'
# Each complete mathematical source has one role, across all clocks/positions.
DEFINITIONS = [
    ('train-add64', 'train', 'add', 64, 2, 0, 16),
    ('train-add128', 'train', 'add', 128, 4, 0, 32),
    ('train-mul16', 'train', 'mul', 16, 2, 8, 0),
    ('train-mul32', 'train', 'mul', 32, 4, 16, 0),
    ('train-mac12', 'train', 'mac', 12, 3, 0, 0),
    ('train-mac24', 'train', 'mac', 24, 2, 12, 0),
    ('validation-add96', 'validation', 'add', 96, 4, 0, 24),
    ('validation-mul24', 'validation', 'mul', 24, 4, 12, 0),
    ('validation-mac20', 'validation', 'mac', 20, 3, 10, 0),
    ('test-add160', 'test', 'add', 160, 4, 0, 40),
    ('test-mac16', 'test', 'mac', 16, 3, 8, 0),
]
CLOCKS = (1500, 3000)


def request(root, ident, kind, width):
    folder=root/'sources'/ident;folder.mkdir(parents=True)
    result=width+1 if kind=='add' else 2*width
    inputs=dict(a=width,b=width)
    if kind=='mac':inputs['c']=result
    expression=(f'Int<{result}>(a)+Int<{result}>(b)' if kind=='add' else
                f'(Int<{result}>(a)*Int<{result}>(b))'+(f'+Int<{result}>(c)' if kind=='mac' else ''))
    text='#include <fixint.hpp>\n'+''.join(f'#pragma input_port {n}\nInt<{w}> {n};\n' for n,w in inputs.items())
    text+=f'#pragma input_port iv\nbool iv;\n#pragma output_port y\nInt<{result}> y;\n#pragma output_port ov\nbool ov;\nvoid workload_top(){{y={expression};}}\n'
    path=folder/'source.cpp';path.write_text(text)
    doc=dict(version='D-source-metadata-v1',source=dict(source='source.cpp',source_label='workload.cpp',top='workload_top',iv='iv',ov='ov',
        reset={n:['0']*math.ceil(w/64) for n,w in dict(inputs,iv=1).items()},generated_source_sha256=sha(path)))
    write(folder/'request.json',doc)
    write(folder/'semantics.json',dict(operation=kind,lhs_bits=width,rhs_bits=width,result_bits=result,carry=False,inputs=inputs))
    return folder,dict(id=ident.replace('-','_'),inputs=[dict(name=n,width=w,reset_hex='0') for n,w in inputs.items()],outputs=[dict(name='y',width=result)])


def projection(folder, target):
    graph=Graph(read(folder/'graph.json'));state=read(folder/'state.json')
    result=diagnostic.state_projection(graph,state,state['internal_stages']+1,target)
    Graph.origins.cache_clear();Graph.roots.cache_clear()
    return result


def prepare(root):
    root=Path(root).resolve()
    if root.exists() or root.is_relative_to(ROOT):raise ValueError('new external directory required')
    root.mkdir(parents=True);sources=[];tasks=[]
    for ident,role,kind,width,L,block,limb in DEFINITIONS:
        folder,source=request(root,ident,kind,width)
        native=root/'native'/ident
        entry.native_export(BINARY,folder/'request.json',native,platform='nangate45',L=L,limb=limb,block=block,target_ps=1500)
        inventory=read(native/'inventory.json')
        # The choice is structural only; no fitted price or physical label.
        def structural(v):
            d=native/v['directory'];o=read(d/'owners.json');s=read(d/'state.json')
            active={v['placement'][r['node']] for r in o['operators']}|{v['placement'][r['root']] for r in o['G_regions']}
            return (-len(active),s['features']['state_bits'],int(v['directory']))
        views=sorted(inventory['views'],key=structural)
        chosen=[views[0]]
        if ident=='train-mac12' and len(views)>1:chosen.append(views[-1])
        for index,view in enumerate(chosen):
            dest=folder/('placement-'+str(index));dest.mkdir()
            native_view=native/view['directory']
            for n in ('state.json','owners.json'):shutil.copy2(native_view/n,dest/n)
            shutil.copy2(native/'graph.json',dest/'graph.json')
            original=(native_view/'workload.sv').read_text()
            core=original[:original.index('module Workload(')]
            core=core.replace('module WorkloadCore(', 'module stage7_top(',1)
            (dest/'core.sv').write_text(core)
            v=dict(id='p'+str(index),rtl_file='core.sv')
            top,text=wrapper(source,v,dest)
            (dest/'input.sv').write_text(text.replace('module '+top+'(', 'module ModelBundle(',1))
            state=read(dest/'state.json');owners=read(dest/'owners.json')
            if owners['functional_logic']:raise ValueError('micro-probe requires explicitly priced arithmetic owners')
            # Match hierarchy emitted by the frozen native owner exporter.
            scopes=[]
            for row in owners['operators']:
                node=row['node'];matches=re.findall(r'\b(\w+)\s+rtlzz_owner_'+str(node)+r'\s*\(',core)
                if len(matches)!=1:raise ValueError('native operator scope missing')
                scopes.append(dict(node=node,scope='core/rtlzz_owner_'+str(node)))
            for row in owners['G_regions']:
                node=row['root'];matches=re.findall(r'\b(\w+)\s+(rtlzz_\w*'+str(node)+r')\s*\(',core)
                # G regions carry their actual hierarchy in the owner record.
                name=row.get('instance',row.get('scope'))
                if not name:
                    options=[m[1] for m in matches if 'reduce' in m[1] or 'region' in m[1]]
                    if len(options)!=1:raise ValueError('G scope needs explicit native binding: '+repr(row.keys()))
                    name=options[0]
                scopes.append(dict(node=node,scope=name if name.startswith('core/') else 'core/'+name))
            contract=dict(state_slots=state['slots'],operator_scopes=scopes)
            write(dest/'endpoints.json',contract);write(dest/'source.json',source)
            write(dest/'view.json',view)
            sid=ident+'-p'+str(index)
            sources.append(dict(id=sid,source_group=ident,role=role,kind=kind,width=width,L=L,folder=str(dest),
                native=str(native_view),rtl=str(dest/'input.sv'),rtl_sha256=sha(dest/'input.sv'),
                endpoint_contract=str(dest/'endpoints.json'),endpoint_sha256=sha(dest/'endpoints.json'),
                projection=projection(dest,1500),native_artifact=view['artifact'],semantics=str(folder/'semantics.json')))
            for target in CLOCKS:
                tasks.append(dict(id=sid+'-T'+str(target),source=sid,role=role,period_ps=target))
    tasks.sort(key=lambda t:({'train':0,'validation':1,'test':2}[t['role']],t['source'],t['period_ps']))
    n=len(tasks);limits=read(runtime.POLICY)['resources'];used=budget.usage(read(budget.LEDGER)['entries']);wall=n*(300+1200+12*120)
    if (used['walltime_s']+wall>limits['max_global_walltime_h']*3600 or used['CPU_time_s']+2*wall>limits['max_tool_CPU_time_h']*3600 or
        used['synth']+n>limits['max_synthesis_calls'] or used['grt']+n>limits['max_global_route_calls'] or shutil.disk_usage(root).free<15*1024**3):
        raise ValueError('finite N56 package exceeds shared budget/storage')
    files=[*Path(__file__).parent.glob('*.py'),*Path(__file__).parent.joinpath('reference_assets').glob('*.tcl'),runtime.POLICY,runtime.BRIDGE,budget.POLICY,budget.CHECKPOINT,MODEL,BINARY]
    files.append(ROOT/'experiments/arithmetic_dse/configs/platforms/nangate45.json')
    write(root/'admission.json',dict(version=VERSION,id='matrix-'+root.name,platform='nangate45',profile_sha256=profile('nangate45')['profile_sha256'],
        sources=sources,tasks=tasks,files={str(p):sha(p) for p in files},model=dict(path=str(MODEL),sha256=sha(MODEL)),
        G_acceptance=dict(user_instruction='好，G算作通过，请完成N5/N6',accepted=True,original_gate_passed=False,old_validation_APE=.1660,parameters_changed=False),
        call_caps=dict(synth=n,grt=n,final=0,support=12*n),serial_workers=1,threads=2,memory_limit_MiB=4096,minimum_available_MiB=12288,
        synth_timeout_s=300,grt_timeout_s=1200,support_timeout_s=120,worst_case_leaf_walltime_s=wall,CPU_envelope_s=2*wall,
        starting_usage=used,ledger=str(budget.LEDGER),automatic_retries=0,
        sampling_layout_overrides=dict(minimum_core_side_um=60,core_utilization_percent=40,core_margin_um=5),
        model_fit='train-only shared NNLS state/shared areas, fixed ridge control responses, source-median data boundary and owner wire; freeze before validation/test',
        precision_gates=dict(source_median_APE=.15,source_P95_APE=.35),
        application_PPA_used=False,R1_R5_modified=False,stop='first failed physical/ownership/unit leaf; preserve attempts; no automatic retry'))
    write(root/'progress.json',dict(phase='admitted',completed=[],errors=[]))
    return dict(sources=len(sources),logical_sources=len(DEFINITIONS),tasks=n)


def verify(root):
    a=read(Path(root)/'admission.json')
    if a['version']!=VERSION:raise ValueError('N56 admission version')
    for p,h in a['files'].items():
        if sha(p)!=h:raise ValueError('N56 frozen source drift: '+p)
    for s in a['sources']:
        if sha(s['rtl'])!=s['rtl_sha256'] or sha(s['endpoint_contract'])!=s['endpoint_sha256']:raise ValueError('N56 input drift')
    return a
