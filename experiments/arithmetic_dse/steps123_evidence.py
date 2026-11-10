"""Frozen steps 1--3 evidence: saved report replay, never EDA or model fitting."""
import argparse
import ast
from collections import Counter
from copy import deepcopy
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'build/step7-steps123-20261110'
CORPUS=RUN/'corpus-v4'
SUFFIX=Path('asap7/arithmetic_probe/base')


def digest(data):return hashlib.sha256(data).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def write(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def encode(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()


def capacity(out):
    """Measured envelope and a limited next-batch plan, not stage4 admission."""
    from .budget import usage,POLICY
    from .operator_collection import measurement_sources
    a=read(RUN/'qualification-v6/admission.json');rows=[]
    ledger=read(ROOT/'experiments/arithmetic/backend_usage.json')
    for task in a['tasks']:
        path=Path(task['inherit_completed']['directory']) if task.get('inherit_completed') else RUN/'qualification-v6/runs'/task['id']
        # The first synthesis checkpoint was inherited without re-execution.
        synth=RUN/'qualification-v1/runs/mul-load-1500' if task['id']=='mul-load-1500' else path
        records=[read(synth/'synth.command.json'),read(path/'grt.command.json')]
        ids={str(synth),str(path)}
        leaves=[e for e in ledger['entries'] if any(str(e.get('output','')).startswith(p+'/') for p in ids)]
        rows.append(dict(id=task['id'],synth_wall_s=records[0]['walltime_s'],grt_wall_s=records[1]['walltime_s'],
            all_associated_leaf_wall_s=sum(e['walltime_s'] for e in leaves),all_associated_leaf_CPU_s=sum(e['CPU_time_s'] for e in leaves),
            peak_tree_rss_MiB=max(r['sampled_process_tree_peak_rss_KiB']/1024 for r in records),
            logical_working_bytes=sum(p.stat().st_size for p in path.rglob('*') if p.is_file()),
            receipt_paths=[str(synth/'synth.command.json'),str(path/'grt.command.json')]))
    later=read(CORPUS/'protocol.json')['later_work_reserved'];u=usage(ledger['entries']);limits=read(POLICY)['resources']
    max_wall=max(r['all_associated_leaf_wall_s'] for r in rows)
    max_cpu=max(r['all_associated_leaf_CPU_s'] for r in rows)
    max_bytes=max(r['logical_working_bytes'] for r in rows)
    point_wall=max(600,2*max_wall);point_cpu=max(1200,2*max_cpu);point_bytes=max(256*1024**2,2*max_bytes)
    available=dict(synth=limits['max_synthesis_calls']-u['synth']-later['synth'],grt=limits['max_global_route_calls']-u['grt']-later['grt'],
        walltime_s=limits['max_global_walltime_h']*3600-u['walltime_s']-later['walltime_s'],
        CPU_time_s=limits['max_tool_CPU_time_h']*3600-u['CPU_time_s']-later['CPU_time_s'],
        disk_bytes=shutil.disk_usage(RUN).free-later['storage_bytes'])
    result=dict(version='steps123-measured-capacity-and-storage-v1',physical_admission_allowed=False,measured_points=rows,
        source_counts=dict(train=30,validation=14,locked_test=14),target_limit_per_source=13,
        train_validation_target_ceiling=572,locked_test_target_ceiling=182,total_target_ceiling=754,
        ceiling_is_not_batch_authorization=True,later_work_reserved=later,available_after_later_reserve=available,
        proposed_first_stage4_batch=dict(max_source_targets=12,roles=['train','validation'],parallel_jobs=3,threads_per_tool=4,memory_limit_MiB=8192,
            point_timeout_envelope_wall_s=300+1200+12*120,batch_timeout_envelope_wall_s=12*(300+1200+12*120),
            batch_timeout_envelope_CPU_s=4*12*(300+1200+12*120),
            point_planning_wall_s=point_wall,point_planning_CPU_s=point_cpu,point_planning_working_bytes=point_bytes,
            planning_wall_s=12*point_wall,planning_CPU_s=12*point_cpu,planning_working_bytes=12*point_bytes,
            admission='separate exact source/target/sampler requests, runtime hashes, qualification proof and live funding/storage check; no automatic full-corpus launch'),
        full_ceiling_extrapolation=dict(points=754,observed_leaf_wall_range_s=[754*min(r['all_associated_leaf_wall_s'] for r in rows),754*max_wall],
            observed_CPU_range_s=[754*min(r['all_associated_leaf_CPU_s'] for r in rows),754*max_cpu],
            observed_working_bytes_range=[754*min(r['logical_working_bytes'] for r in rows),754*max_bytes],
            limitation='four diagnostics are not capacity qualification for all widths/consumers/tighter targets; extrapolation excludes unobserved failures and fitting/evidence support'),
        source_snapshot_policy='one shared immutable source freeze per admission; no repeated entire parent evidence or ledger per case',
        required_measurement_paths=measurement_sources(),
        storage=dict(small_evidence_target_bytes=5*1024**2,file_limit_bytes=1024**2,chunk_limit_bytes=512*1024,
            full_artifacts='existing ignored local build cache; indexed with bytes and SHA256; not a durable delivery location',
            persistent_location=None,persistent_restore_verified=False,
            stage4_gate='exact batch storage inventory and a real recoverable destination/restore receipt before claiming durable full collection; do not treat a hash or local cache as delivery'))
    write(out,result);print(json.dumps(dict(status='planned',rows=rows,available=available,first_batch=result['proposed_first_stage4_batch'])),flush=True)


def load(folder):
    m=read(folder/'manifest.json');parts=[]
    for name,h in m['chunks'].items():
        if Path(name).name!=name:raise ValueError('unsafe chunk')
        data=(folder/name).read_bytes()
        if digest(data)!=h:raise ValueError('chunk changed')
        parts.append(data)
    raw=gzip.decompress(b''.join(parts))
    if digest(raw)!=m['pool_sha256']:raise ValueError('pool changed')
    pool=json.loads(raw)
    for name,h in m['review_sha256'].items():
        if digest((folder/name).read_bytes())!=h:raise ValueError('review file changed')
    return m,pool


def restore(pool,tree):
    for name,h in pool['files'].items():
        path=tree/name
        if Path(name).is_absolute() or '..' in Path(name).parts:raise ValueError('unsafe content path')
        data=pool['blobs'][h].encode('utf-8')
        if digest(data)!=h:raise ValueError('member changed')
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)


def pack(folder):
    files={};blobs={};external={}
    def add(name,data):
        h=digest(data);files[name]=h;blobs[h]=data.decode('utf-8')
    def include(path,name=None):add(name or str(path.relative_to(ROOT)),path.read_bytes())
    def ext(path):
        data=path.read_bytes();external[str(path)]=dict(sha256=digest(data),bytes=len(data),encoding='original',available_at_pack=True,storage_class='local_working_cache')
    # Replay dependencies are actual bytes, including import-only modules.
    for directory in ('experiments/arithmetic_dse','regression'):
        for p in (ROOT/directory).glob('*.py'):include(p)
    for p in (ROOT/'experiments/arithmetic_dse').rglob('__init__.py'):include(p)
    for p in (ROOT/'experiments/arithmetic_dse/configs').rglob('*.json'):include(p)
    for p in (ROOT/'experiments/arithmetic_dse/backend').iterdir():
        if p.is_file():include(p)
    for name in ('context_readout_v2.tcl','boundary_census.tcl'):
        include(ROOT/'experiments/arithmetic_dse/reference_assets'/name)
    # Source roles are regenerated from preregistered arithmetic requirements.
    for name in ('step7_fast_loads_v1/loads.json','step7_fast_preflight_v3/requirements.json'):
        include(ROOT/'experiments/arithmetic/evidence'/name)
    import subprocess
    for base in (ROOT,ROOT/'rtlzz'):
        names=set(subprocess.check_output(['git','diff','--name-only'],cwd=base).decode().splitlines())
        names.update(subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=base).decode().splitlines())
        for name in names:
            p=base/name
            if p.is_file() and p.suffix in ('.cpp','.hpp','.h','.txt') and (name.startswith(('src/','testv2/')) or p.name=='CMakeLists.txt'):include(p)
    for p in CORPUS.rglob('*'):
        if p.is_file():include(p,'corpus/'+str(p.relative_to(CORPUS)))
    for name in ('collection-contract-v6','physical-readback-v1','boundary-request-v2'):
        include(RUN/name/'results/proof.json','proofs/'+name+'.json')
    for name in ('shell-cycles-v1/shell-cycles.log','corpus-cycles-v1/corpus-cycles.log','pipeline-compat-v1/pipeline-compat.log',
                 'interface-compat-v1/interface-compat.log'):
        p=RUN/name
        if p.exists():include(p,'proofs/'+p.name)
    for dirname in ('software-v2','corpus-software-v1'):
        for p in (RUN/dirname).rglob('*'):
            if p.is_file():include(p,'software/'+dirname+'/'+str(p.relative_to(RUN/dirname)))
    for p in (RUN/'public-sources-v2').rglob('*'):
        if p.is_file():include(p,'public/sources/'+str(p.relative_to(RUN/'public-sources-v2')))
    for p in (RUN/'public-generated-v2').rglob('*'):
        if p.is_file() and 'obj_dir' not in p.parts and (p.suffix in ('.sv','.json','.log','.cpp','.h','.hpp') or p.name=='run.sh'):
            include(p,'public/generated/'+str(p.relative_to(RUN/'public-generated-v2')))
    a=read(RUN/'qualification-v6/admission.json');tasks=[];summary=[]
    for task in a['tasks']:
        path=Path(task['inherit_completed']['directory']) if task.get('inherit_completed') else RUN/'qualification-v6/runs'/task['id']
        tasks.append({k:v for k,v in task.items() if k not in ('inherit_completed','inherit_synth')})
        prefix='qualification/runs/'+task['id']+'/'
        for name in ('input.sv','mapped-contract.json','operator-port-contract.json','liberty-pins.json','query-contract.json','query-contract.tcl','synth-labels.json','grt-labels.json','manifest.json','live-cec-request.json'):
            include(path/name,prefix+name)
        original=read(path/'mapped.json');pins=read(path/'liberty-pins.json');top=original['modules']['ModelBundle'];projection={'modules':{'ModelBundle':{'cells':top['cells'],'ports':top['ports']}}}
        for cell in top['cells'].values():
            typ=cell['type']
            if typ not in original['modules']:continue
            mod=original['modules'][typ];children={}
            for n,c in mod.get('cells',{}).items():
                outputs={pin:bits for pin,bits in c['connections'].items() if pins[c['type']]['pins'].get(pin,{}).get('direction')=='output'}
                children[n]=dict(type=c['type'],connections=c['connections'] if typ in (top['cells']['launch']['type'],top['cells']['capture']['type']) else outputs)
            projection['modules'][typ]=dict(ports=mod['ports'],cells=children)
        add(prefix+'mapped.json',encode(projection));ext(path/'mapped.json')
        reports=path/'reports'/SUFFIX
        for p in reports.iterdir():
            if p.is_file() and (p.name.startswith(('context_','vulsim_','boundary_'))) and p.suffix!='.v':include(p,prefix+'reports/'+str(SUFFIX/p.name))
        for stage,stem in (('synth','1_synth'),('grt','5_1_grt')):
            include(path/'results'/SUFFIX/(stem+'.sdc'),prefix+'results/'+str(SUFFIX/(stem+'.sdc')))
            saved=read(path/(stage+'-labels.json'))
            summary.append(dict(id=task['id'],stage=stage,operator_delay_ps=saved['operator_delay_ps'],comb_area_um2=saved['comb_area_um2'],
                data_setup_slack_ps=saved['data_setup_slack_ps'],hold_slack_ps=saved['metrics']['hold_worst_slack_ps'],source_role=saved['source_role']))
        cec=path/'logs'/SUFFIX/'structural_cec'
        for name in ('proof.json','cec.log','negative-top_output.log','negative-register_D.log','negative-register_CLK.log','state-correspondence.json'):
            include(cec/name,prefix+'CEC/'+name)
        # Full CEC and ODB remain explicitly external. Verify all hash-bound
        # original files now; portable replay reports the narrower capability.
        from .model_m2_live_cec_v3 import verify_proof
        verify_proof(cec/'proof.json',path/'results'/SUFFIX/'4_before_rsz_lec.v',path/'results'/SUFFIX/'4_after_rsz_lec.v')
        for p in path.rglob('*'):
            if p.is_file() and 'source' not in p.relative_to(path).parts:ext(p)
    add('qualification/admission.json',encode(dict(tasks=tasks)))
    # Keep all failed attempts and paid ancestry receipts without rewriting them.
    for p in RUN.rglob('*'):
        if p.is_file() and (p.name in ('admission.json','progress.json','commands.json','qualification-commands.json') or p.name.endswith('.command.json')):
            include(p,'attempts/'+str(p.relative_to(RUN)))
    capacity_plan=read(RUN/'capacity-plan-v3/plan.json')
    pool=dict(files=files,blobs=blobs,external=external,scope='actual physical raw tables, semantic projections and saved software executions; no fitting or new EDA')
    raw=encode(pool);compressed=gzip.compress(raw,mtime=0);folder.mkdir(parents=True,exist_ok=False);chunks={}
    for i,start in enumerate(range(0,len(compressed),512*1024)):
        name=f'pool-{i:03d}.gzpart';data=compressed[start:start+512*1024];(folder/name).write_bytes(data);chunks[name]=digest(data)
    review={'qualification-summary.json':summary,'capacity-plan.json':capacity_plan,'source-manifest.json':read(CORPUS/'manifest.json'),
        'protocol.json':read(CORPUS/'protocol.json'),'external-index.json':external}
    # External index can be large; its bytes already live in the deduplicated pool.
    review.pop('external-index.json')
    for name,value in review.items():write(folder/name,value)
    source_hashes={name:h for name,h in files.items() if name.startswith(('experiments/','regression/','rtlzz/','src/'))}
    write(folder/'manifest.json',dict(version='steps123-evidence-v1',chunks=chunks,pool_sha256=digest(raw),compressed_bytes=len(compressed),
        review_sha256={name:digest((folder/name).read_bytes()) for name in review},source_sha256=source_hashes,
        mapped_JSON_scope='actual semantic projection: complete launch/capture cells; arithmetic output drivers and ports; full original indexed externally',
        portable_scope='raw paths/areas/FF/bank/port certificates, integer and public cycle replay, role/protocol/negative guards; CEC conclusion/log receipts only',
        external_scope='full original mapped JSON, raw ODB/netlists, complete CEC proof artifacts and original tools; checked only with --external',
        formal_training_rows=0,full_D_ready=False))
    if sum(p.stat().st_size for p in folder.iterdir())>5*1024**2:raise ValueError('new evidence exceeds 5MiB; preserve provisional package and revise content layering')
    print(json.dumps(dict(status='packed',compressed_bytes=len(compressed),chunks=len(chunks),members=len(files),external_files=len(external))),flush=True)


def verify(folder,external=False):
    manifest,pool=load(folder)
    for name,h in manifest['source_sha256'].items():
        if digest((ROOT/name).read_bytes())!=h:raise ValueError('active source differs from frozen replay '+name)
    with tempfile.TemporaryDirectory(prefix='steps123-replay-') as name:
        tree=Path(name);restore(pool,tree)
        from regression.arithmetic_physical_label_contract import verify as physical
        from regression.arithmetic_collection_contract import verify as collection
        from regression.arithmetic_public_hierarchy import verify as public
        physical(tree/'qualification',tree/'physical-proof')
        if read(tree/'physical-proof/proof.json')!=read(tree/'proofs/physical-readback-v1.json'):raise ValueError('actual raw replay differs')
        collection(tree/'corpus',tree/'collection-proof')
        if read(tree/'collection-proof/proof.json')!=read(tree/'proofs/collection-contract-v6.json'):raise ValueError('collection guard differs')
        expected_public=read(tree/'public/generated/public-proof.json')
        public(tree/'public/sources',tree/'public/generated',tree/'public/generated')
        if read(tree/'public/generated/public-proof.json')!=expected_public:raise ValueError('saved public cycle result differs')
        for dirname in ('software-v2','corpus-software-v1'):
            from .model_context_samples import layout,evaluate
            from .model_sampling_v2 import source,geometry_contract
            cohort=read(tree/'software'/dirname/'sources.json')
            for row in cohort['rows']:
                here=tree/'software'/dirname;f=row['features'];g=layout(f);n,r=g['input_bits'],g['output_bits'];old=0;valid=0
                if source(f)!=(here/'sources'/row['id']/'input.sv').read_text() or geometry_contract(f)!=read(here/'sources'/row['id']/'contract.json'):raise ValueError('shell regeneration differs')
                for index,line in enumerate((here/(row['id']+'.hex')).read_text().splitlines()):
                    word=int(line,16);ov=word&1;result=(word>>1)&((1<<r)-1);iv=word>>(r+1)&1;rstn=word>>(r+2)&1;value=word>>(r+3)
                    if value>=1<<n or result!=evaluate(f,old) or ov!=(0 if not rstn else valid):raise ValueError('functional cycle reference differs')
                    if not rstn:old=0;valid=0
                    else:
                        valid=iv
                        if iv:old=value
                if index!=127:raise ValueError('incomplete 128-cycle trace')
        from .model_m2_live_cec_v3 import check_result
        for task in read(tree/'qualification/admission.json')['tasks']:
            cec=tree/'qualification/runs'/task['id']/'CEC';proof=read(cec/'proof.json')
            if proof['status']!='passed' or set(proof['negative_controls'])!={'top_output','register_D','register_CLK'}:raise ValueError('CEC receipts incomplete')
            check_result((cec/'cec.log').read_text(),True)
            for control in proof['negative_controls']:check_result((cec/('negative-'+control+'.log')).read_text(),False)
    if external:
        for name,meta in pool['external'].items():
            p=Path(name)
            if not p.is_file() or p.stat().st_size!=meta['bytes'] or digest(p.read_bytes())!=meta['sha256']:raise ValueError('external artifact unavailable/changed '+name)
        from .model_m2_live_cec_v3 import verify_proof
        for task in read(RUN/'qualification-v6/admission.json')['tasks']:
            path=Path(task['inherit_completed']['directory']) if task.get('inherit_completed') else RUN/'qualification-v6/runs'/task['id']
            verify_proof(path/'logs'/SUFFIX/'structural_cec/proof.json',path/'results'/SUFFIX/'4_before_rsz_lec.v',path/'results'/SUFFIX/'4_after_rsz_lec.v')
    result=dict(status='passed',physical_points=4,stages=8,physical_corruptions_rejected=8,sources=58,role_counts=dict(train=30,validation=14,locked_test=14),
        shell_vector_cycles=(90+58)*128,public_groups=3,public_cycles=3*144,external_full_artifact_checks=external,new_EDA_calls=0,new_training_rows=0,full_D_ready=False)
    print(json.dumps(result),flush=True);return result


def isolated(folder,out):
    manifest,pool=load(folder);out.mkdir(parents=True,exist_ok=False);tree=out/'tree';tree.mkdir();restore(pool,tree)
    shutil.copytree(folder,tree/'evidence');script=tree/'isolated.py'
    script.write_text('''import os,sys
from pathlib import Path
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root));os.chdir(root)
def audit(event,args):
    if event in ('subprocess.Popen','os.system','os.posix_spawn'):raise RuntimeError('replay subprocess forbidden')
    if event=='open' and isinstance(args[0],(str,bytes)):
        p=Path(os.fsdecode(args[0])).resolve()
        if str(p).startswith('/home/') and not p.is_relative_to(root):raise RuntimeError('original home/project/build forbidden')
sys.addaudithook(audit)
from experiments.arithmetic_dse.steps123_evidence import verify
verify(root/'evidence')
''')
    # This child is inside the enclosing paid support leaf; no nested charge.
    from .processes import run_command
    env=os.environ.copy();env.update(PATH='',PYTHONDONTWRITEBYTECODE='1')
    record=run_command([sys.executable,'-I','-S',str(script)],out,'isolated',180,env,8192)
    if record['exit_code']:raise ValueError('isolated replay failed '+record['log'])
    name=next(iter(manifest['chunks']));p=tree/'evidence'/name;data=p.read_bytes();bad=bytearray(data);bad[len(bad)//2]^=1;p.write_bytes(bad)
    try:load(tree/'evidence')
    except ValueError:pass
    else:raise ValueError('changed content accepted')
    finally:p.write_bytes(data)
    proof=dict(status='passed',original_home_project_build_denied=True,PATH_empty=True,replay_subprocess_denied=True,content_tamper_rejected=True)
    write(out/'proof.json',proof);print(json.dumps(proof),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('capacity','pack','verify','isolated'));p.add_argument('--folder',type=Path);p.add_argument('--out',type=Path);p.add_argument('--external',action='store_true');a=p.parse_args()
    if a.action=='capacity':capacity(a.out.resolve())
    elif a.action=='pack':pack(a.folder.resolve())
    elif a.action=='isolated':isolated(a.folder.resolve(),a.out.resolve())
    else:verify(a.folder.resolve(),a.external)
