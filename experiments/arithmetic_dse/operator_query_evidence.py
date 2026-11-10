"""Portable software-query and mapped-boundary diagnosis, no fitting or EDA."""
import argparse
from collections import Counter
import csv
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]


def digest(data):return hashlib.sha256(data).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def write(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def compress(value):return gzip.compress(json.dumps(value,sort_keys=True,separators=(',',':')).encode(),mtime=0)


def load(folder):
    manifest=read(folder/'manifest.json');pieces=[]
    for name,h in manifest['chunks'].items():
        data=(folder/name).read_bytes()
        if Path(name).name!=name or digest(data)!=h:raise ValueError('evidence content changed')
        pieces.append(data)
    raw=gzip.decompress(b''.join(pieces))
    if digest(raw)!=manifest['pool_sha256']:raise ValueError('evidence pool changed')
    if manifest.get('summary_sha256') and digest((folder/'summary.json').read_bytes())!=manifest['summary_sha256']:raise ValueError('evidence summary changed')
    return manifest,json.loads(raw)


def pack(run,boundary,contracts,folder):
    from regression import arithmetic_operator_query as regression
    from . import operator_query as query
    from .model_target_round1_evidence import load as parent_load
    native=read(run/'native/queries.json');_,parent=parent_load(ROOT/'experiments/arithmetic/evidence/step7_target_round1_v2')
    executed_sources=read(run/'source-freeze.json')
    for name,h in executed_sources.items():
        if digest((ROOT/name).read_bytes())!=h or digest((run/'source'/name).read_bytes())!=h:
            raise ValueError('executed native/software source differs from final frozen producer: '+name)
    a=read(boundary/'admission.json');reports={};summary=read(boundary/'boundary-audit.json');ff_summary=[]
    for task in a['tasks']:
        path=boundary/'runs'/task['id'];m=read(path/'manifest.json');d=path/'reports/asap7/arithmetic_probe/base'
        files={}
        for name in ('boundary_instances.tsv','boundary_connections.tsv','vulsim_synth_cells.tsv','vulsim_synth_setup.rpt','vulsim_synth_hold.rpt','vulsim_synth_coverage.rpt'):
            files[name]=(d/name).read_text()
        libs=read(path/'liberty_cells.json')['cells'];seq={name for name,v in libs.items() if v['sequential']}
        counts=Counter(n.split('/')[0] for n,master in (line.split('\t')[:2] for line in files['boundary_instances.tsv'].splitlines()) if master in seq)
        expected=parent['inputs']['geometries']['capacity0']['owner_FF_bits']
        ff_summary.append(dict(id=task['id'],actual_sequential_cells_by_scope=dict(counts),
            generic_expected_owner_FF_bits=expected,mapped_bank_geometry_qualified=False,
            note='observed cell census differs; constants, aliases and independent banks require mapped bit reconciliation, never silently assume generic geometry survives'))
        reports[task['id']]=dict(files=files,liberty_cells=libs,manifest=m,rtl=Path(task['rtl']).read_text())
    paths=[Path(__file__),Path(regression.__file__),Path(query.__file__),ROOT/'experiments/arithmetic_dse/model_boundary_probe.py',
        ROOT/'regression/arithmetic_operator_boundary_resume.py',ROOT/'experiments/arithmetic_dse/reference_assets/boundary_census.tcl',
        ROOT/'rtlzz/src/backend/arithmetic_operator_query.cpp',ROOT/'rtlzz/src/backend/arithmetic_operator_query.hpp',ROOT/'rtlzz/src/backend/pipeline.cpp',
        ROOT/'rtlzz/src/backend/pipeline.hpp',ROOT/'rtlzz/testv2/arithmetic_operator_query_export.cpp',ROOT/'rtlzz/testv2/arithmetic_operator_query_contract_test.cpp',
        ROOT/'rtlzz/src/backend/rtlgen.cpp',ROOT/'rtlzz/src/backend/rtlgen.hpp',ROOT/'experiments/arithmetic_dse/configs/operator_boundary_policy_v1.json']
    for module in list(sys.modules.values()):
        path=getattr(module,'__file__',None)
        if path:
            p=Path(path)
            if p.is_relative_to(ROOT) and p.is_file() and p.suffix=='.py':paths.append(p)
    paths=list(dict.fromkeys(paths));sources={str(p.relative_to(ROOT)):p.read_text() for p in paths}
    pool=dict(sources=sources,request=read(run/'input/request.json'),public_generated_source=(run/'input/source.cpp').read_text(),executed_sources_sha256=executed_sources,
        native=native,proof=read(run/'query-proof.json'),contracts=read(contracts/'proof.json'),
        rtl={v['rtl_file']:(run/'native'/v['rtl_file']).read_text() for v in native['variants']},
        cycles=dict(vectors=(run/'cycles.hex').read_text(),tb=(run/'cycles-tb.sv').read_text(),marker=(run/'simulate.log').read_text(),
                    verilator_warning='%Warning' in (run/'verilator.log').read_text()),
        boundary=summary,boundary_raw=reports,FF_followup=ff_summary,
        native_commands=read(run/'commands.json'),boundary_admission=a,
        emission_policy=read(ROOT/'experiments/arithmetic_dse/configs/operator_boundary_policy_v1.json'),
        qualification=dict(software_query=True,mapped_scope_census_only=True,independent_node_physical_labels=False,full_D_ready=False))
    raw=json.dumps(pool,sort_keys=True,separators=(',',':')).encode();compressed=gzip.compress(raw,mtime=0);folder.mkdir(parents=True,exist_ok=False);chunks={}
    for i,start in enumerate(range(0,len(compressed),512*1024)):
        name=f'pool-{i:03d}.gzpart';data=compressed[start:start+512*1024];(folder/name).write_bytes(data);chunks[name]=digest(data)
    write(folder/'manifest.json',dict(version='operator-query-boundary-software-evidence-v1',chunks=chunks,pool_sha256=digest(raw),compressed_bytes=len(compressed),
        sources_sha256={name:digest(text.encode()) for name,text in sources.items()},full_D_ready=False))
    write(folder/'summary.json',dict(software=pool['proof'],boundary=summary,FF_followup=ff_summary,
        feature_schema=dict(version=query.VERSION,numeric_features=sorted(native['variants'][0]['target_rows'][0]['queries'][0]['features']),
                            descriptor='semantic operator, demanded result, masks, exact connections and precomputed topology; identities only in trace'),
        arithmetic_boundary_emission=native.get('arithmetic_boundary_emission',False),emission_policy=pool['emission_policy'],no_training=True,no_production_binding=True))
    manifest=read(folder/'manifest.json');manifest['summary_sha256']=digest((folder/'summary.json').read_bytes());write(folder/'manifest.json',manifest)
    verify(folder)
    print(json.dumps(dict(status='packed',bytes=len(compressed),chunks=len(chunks))),flush=True)


def verify(folder):
    from regression import arithmetic_operator_query as regression
    from . import operator_query as query
    manifest,pool=load(folder)
    if digest(pool['public_generated_source'].encode())!=pool['request']['source']['generated_source_sha256']:
        raise ValueError('executed public source bytes do not match request')
    for name,h in pool['executed_sources_sha256'].items():
        if digest(pool['sources'][name].encode())!=h:raise ValueError('frozen source pool does not contain executed producer')
    for name,h in manifest['sources_sha256'].items():
        if digest(pool['sources'][name].encode())!=h or digest((ROOT/name).read_bytes())!=h:raise ValueError('replay source differs: '+name)
    with tempfile.TemporaryDirectory(prefix='operator-query-replay-') as td:
        out=Path(td);(out/'input').mkdir();(out/'native').mkdir();write(out/'input/request.json',pool['request']);write(out/'native/queries.json',pool['native'])
        for name,text in pool['rtl'].items():
            if Path(name).name!=name:raise ValueError('bad RTL member path')
            (out/'native'/name).write_text(text)
        regression.verify(out)
        if read(out/'query-proof.json')!=pool['proof']:raise ValueError('fixed query proof differs')
    for row in pool['contracts']['queries']:regression.compare(query.features(row['descriptor']),row['features'],'unseen_parameters_native_Python')
    if pool['native'].get('arithmetic_boundary_emission'):
        for text in pool['rtl'].values():
            if '(* keep_hierarchy=1 *) module ' not in text:raise ValueError('declared hierarchy policy missing arithmetic modules')
        if pool['emission_policy']['version']!='unsigned-op-hierarchy-v1':raise ValueError('unknown common emission policy')
    # Replay independent arithmetic inputs, separate from saved simulator marker.
    nvalid=0
    for line in pool['cycles']['vectors'].splitlines():
        word=int(line,16);expected=word&((1<<64)-1);iv=word>>64&1;rstn=word>>65&1;c=word>>66&((1<<64)-1);b=word>>130&((1<<32)-1);a=word>>162
        if a>>32 or expected!=(a*b+c)&((1<<64)-1):raise ValueError('integer transaction reference differs')
        nvalid+=iv*rstn
    if 'QUERY_ALL_VIEWS_RTL_PASS views=44 cycles=160' not in pool['cycles']['marker'] or pool['cycles']['verilator_warning']:raise ValueError('actual RTL simulation incomplete or warned')
    boundary_summaries={r['id']:r for r in pool['boundary']['rows']}
    ff_followup={r['id']:r for r in pool['FF_followup']}
    for name,raw in pool['boundary_raw'].items():
        instances=[line.split('\t')[:2] for line in raw['files']['boundary_instances.tsv'].splitlines()];nets={}
        for row in csv.DictReader(raw['files']['boundary_connections.tsv'].splitlines(),delimiter='\t'):nets.setdefault(row['net'],[]).append(row)
        scopes={}
        for owner in ('core','consumer0','launch','capture','observer'):
            own={n for n,m in instances if n.startswith(owner+'/')};inputs=outputs=0
            for members in nets.values():
                for pin in members:
                    if pin['instance'] in own and any(other['instance'] not in own for other in members):
                        inputs+=pin['direction']=='input';outputs+=pin['direction']=='output'
            scopes[owner]=dict(cells=len(own),boundary_inputs=inputs,boundary_outputs=outputs)
        if scopes!=boundary_summaries[name]['scopes']:raise ValueError('mapped boundary census does not replay')
        seq={name for name,v in raw['liberty_cells'].items() if v['sequential']}
        ff_counts=Counter(n.split('/')[0] for n,master in instances if master in seq)
        if dict(ff_counts)!=ff_followup[name]['actual_sequential_cells_by_scope'] or ff_followup[name]['mapped_bank_geometry_qualified']:
            raise ValueError('mapped FF census differs or qualification overstated')
        if raw['manifest']['status']!='completed':raise ValueError('incomplete mapped probe')
        for key in ('vulsim_synth_setup.rpt','vulsim_synth_hold.rpt'):
            if not raw['files'][key]:raise ValueError('missing raw STA report')
    if pool['boundary_raw']['protected']['rtl'].replace('(* keep_hierarchy=1 *) ','')!=pool['boundary_raw']['flat']['rtl']:raise ValueError('probe changed more than module hierarchy protection')
    result=dict(status='passed',native_Python_queries=2064,materialized_views=44,RTL_cycles=44*160,valid_data_comparisons=44*nvalid,
        unseen_parameter_contexts=4,arithmetic_boundary_emission=pool['native'].get('arithmetic_boundary_emission',False),boundary_synth_probes=2,boundary_raw_replay=True,new_physical_training_labels=0,full_D_ready=False)
    print(json.dumps(result),flush=True);return result


def isolated(folder,out):
    manifest,pool=load(folder);out.mkdir(parents=True,exist_ok=False);tree=out/'tree';tree.mkdir()
    for name,text in pool['sources'].items():
        p=tree/name
        if not p.is_relative_to(tree):raise ValueError('unsafe source member')
        p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    shutil.copytree(folder,tree/'evidence');script=tree/'isolate.py'
    script.write_text('''import sys,os
from pathlib import Path
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root))
os.chdir(root)
def audit(event,args):
    if event in ('subprocess.Popen','os.system','os.posix_spawn'):raise RuntimeError('subprocess forbidden')
    if event=='open' and isinstance(args[0],(str,bytes)):
        p=Path(os.fsdecode(args[0])).resolve()
        if str(p).startswith('/home/') and not p.is_relative_to(root):raise RuntimeError('original home/project/build forbidden')
sys.addaudithook(audit)
from experiments.arithmetic_dse.operator_query_evidence import verify
verify(root/'evidence')
''')
    from .processes import run_command
    env=os.environ.copy();env.update(PATH='',PYTHONDONTWRITEBYTECODE='1');record=run_command([sys.executable,'-I','-S',str(script)],out,'isolated',180,env,8192)
    if record['exit_code']:raise ValueError('isolated replay failed: '+record['log'])
    name=next(iter(manifest['chunks']));path=tree/'evidence'/name;old=path.read_bytes();corrupt=bytearray(old);corrupt[len(corrupt)//2]^=1;path.write_bytes(corrupt)
    try:load(tree/'evidence')
    except ValueError:rejected=True
    else:raise ValueError('changed pool accepted')
    finally:path.write_bytes(old)
    write(out/'proof.json',dict(status='passed',original_home_project_build_denied=True,PATH_empty=True,replay_subprocess_denied=True,content_tamper_rejected=rejected))
    print(Path(record['log']).read_text()[-1400:],flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('pack','verify','isolated'));p.add_argument('--folder',type=Path,required=True)
    p.add_argument('--run',type=Path);p.add_argument('--boundary',type=Path);p.add_argument('--contracts',type=Path);p.add_argument('--out',type=Path);a=p.parse_args()
    if a.action=='pack':pack(a.run.resolve(),a.boundary.resolve(),a.contracts.resolve(),a.folder.resolve())
    elif a.action=='isolated':isolated(a.folder.resolve(),a.out.resolve())
    else:verify(a.folder.resolve())
