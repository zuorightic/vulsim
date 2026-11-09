"""Small, portable round-one evidence; no EDA, training or test-label reads."""
import argparse
import ast
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return json.dumps(value,sort_keys=True,separators=(',',':')).encode()


def write(path,value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def load(folder):
    manifest=json.loads((folder/'manifest.json').read_text());parts=[]
    for name,h in manifest['chunks'].items():
        if Path(name).name!=name:raise ValueError('invalid evidence chunk path')
        raw=(folder/name).read_bytes()
        if digest(raw)!=h:raise ValueError('evidence content changed')
        parts.append(raw)
    for name,h in manifest.get('review_files',{}).items():
        if Path(name).name!=name or digest((folder/name).read_bytes())!=h:raise ValueError('reviewable plan changed')
    compressed=b''.join(parts)
    if digest(compressed)!=manifest['compressed_sha256']:raise ValueError('evidence pool order changed')
    raw=gzip.decompress(compressed)
    if digest(raw)!=manifest['pool_sha256']:raise ValueError('evidence pool changed')
    pool=json.loads(raw)
    for name,text in pool['sources'].items():
        if name not in manifest['source_sha256'] or digest(text.encode())!=manifest['source_sha256'][name]:raise ValueError('source pool mismatch')
    return manifest,pool


def pack(run,checks,folder):
    from regression import arithmetic_target_round1 as regression
    from . import model_context_samples as shells
    from . import model_context_labels as labels
    from . import model_three_region_scan as scan
    software=run/'software';cohort=json.loads((software/'cohort.json').read_text());design=json.loads((software/'generic.json').read_text())
    projection={'modules':{}};geometries={};comb_census={}
    for row in cohort['sources']+cohort['capacity_sources']:
        module=design['modules'][row['module']];projection['modules'][row['module']]=module
        for instance in ('launch','capture','core',*['consumer'+str(i) for i in range(len(row['features']['consumers']))]):
            name=module['cells'][instance]['type'];body=design['modules'][name]
            if instance in ('launch','capture'):
                projection['modules'][name]=body
            else:
                # Ports are sufficient for constant/alias inspection; the full
                # netlist remains an explicitly external, hash-bound artifact.
                projection['modules'][name]={'ports':body['ports']}
                counts={}
                for cell in body['cells'].values():counts[cell['type']]=counts.get(cell['type'],0)+1
                if any('DFF' in typ.upper() or 'LATCH' in typ.upper() for typ in counts):raise ValueError('unexpected state inside arithmetic core')
                comb_census[name]=counts
        geometries[row['id']]=shells.generic_geometry(design,row['module'],row['features'])
    # Final AST/JSON check is part of this paid evidence leaf.
    paths=[Path(__file__),Path(regression.__file__),Path(shells.__file__),Path(labels.__file__),Path(scan.__file__),
           regression.CONFIG,scan.CONFIG,regression.ASSET]
    for module in list(sys.modules.values()):
        name=getattr(module,'__file__',None)
        if name:
            p=Path(name)
            if p.is_relative_to(ROOT) and p.suffix=='.py' and p.is_file():paths.append(p)
    paths=list(dict.fromkeys(paths))
    for path in paths:
        if path.suffix=='.py':ast.parse(path.read_text(),filename=str(path))
        elif path.suffix=='.json':json.loads(path.read_text())
    sources={str(path.relative_to(ROOT)):path.read_text() for path in paths}
    pool=dict(sources=sources,inputs=dict(loads=json.loads((regression.LOADS/'loads.json').read_text()),
        cohort=cohort,coverage=json.loads((software/'coverage.json').read_text()),capacity=json.loads((software/'capacity-plan.json').read_text()),
        state_stage=json.loads((software/'state-stage-requirements.json').read_text()),
        source_outputs={r['id']:dict(rtl=(software/(r['id']+'.sv')).read_text(),vectors=(software/(r['id']+'.hex')).read_text()) for r in cohort['sources']+cohort['capacity_sources']},
        generic_projection=projection,comb_primitive_census=comb_census,geometries=geometries,
        reader=json.loads((checks/'reader.json').read_text()),scanner=json.loads((checks/'scanner.json').read_text()),
        functional_execution=dict(marker=(run/'simulate.log').read_text(),verilator_warnings='%Warning' in (run/'verilator.log').read_text(),
            testbench_source=(software/'testbench.sv').read_text(),combined_kernel_source=(software/'kernels.sv').read_text(),
            commands=json.loads((run/'commands.json').read_text())),
        baseline_proof=json.loads((run/'round1-proof.json').read_text()),
        final_software_proof=json.loads((checks/'proof.json').read_text())),
        external=dict(full_generic_json=str(software/'generic.json'),full_generic_sha256=digest((software/'generic.json').read_bytes()),
            original_run=str(run),extra_reader_checks=str(checks)),
        scope='generic FF/port projection and actual saved RTL execution; synthetic reader/scanner fixtures; no physical endpoint/model qualification')
    raw=encode(pool);compressed=gzip.compress(raw,mtime=0);folder.mkdir(parents=True,exist_ok=False);chunks={}
    for i,start in enumerate(range(0,len(compressed),512*1024)):
        name=f'pool-{i:03d}.gzpart';data=compressed[start:start+512*1024];(folder/name).write_bytes(data);chunks[name]=digest(data)
    review_values={'coverage.json':pool['inputs']['coverage'],'capacity-plan.json':pool['inputs']['capacity'],
        'source-index.json':dict(role_policy='complete source graph grouped, all targets/stages/repeats keep role',
            physical_admission_allowed=False,sources=[dict(id=r['id'],source_group=r['source_group'],role=r['role'],
                producer=r['features']['producer'],consumer_count=len(r['features']['consumers']),input_bits=r['input_bits'],
                output_bits=r['output_bits'],rtl_sha256=r['rtl_sha256']) for r in cohort['sources']])}
    for name,value in review_values.items():write(folder/name,value)
    write(folder/'manifest.json',dict(version='arithmetic-target-round1-evidence-v1',chunks=chunks,compressed_sha256=digest(compressed),pool_sha256=digest(raw),
        review_files={name:digest((folder/name).read_bytes()) for name in review_values},
        source_sha256={name:digest(text.encode()) for name,text in sources.items()},compressed_bytes=len(compressed),
        physical_endpoint_qualification=False,physical_admission_allowed=False,fitting_allowed=False,independent_test_allowed=False,full_D_ready=False))
    verify(folder)
    print(json.dumps(dict(status='packed',bytes=len(compressed),chunks=len(chunks),sources=len(sources))),flush=True)


def verify(folder,external=False):
    from regression import arithmetic_target_round1 as regression
    from . import model_context_samples as shells
    from . import model_context_labels as labels
    from . import model_three_region_scan as scan
    manifest,pool=load(folder);inputs=pool['inputs'];cohort=inputs['cohort']
    for name,h in manifest['source_sha256'].items():
        if digest((ROOT/name).read_bytes())!=h:raise ValueError('active replay producer differs from snapshot: '+name)
    if digest(regression.CONFIG.read_bytes())!=cohort['protocol_sha256'] or digest(scan.CONFIG.read_bytes())!=cohort['sampler_sha256']:
        raise ValueError('cohort protocol/sampler freeze differs from registered bytes')
    base=regression.cohort(inputs['loads'])
    for name,key in (('coverage.json','coverage'),('capacity-plan.json','capacity')):
        if json.loads((folder/name).read_text())!=inputs[key]:raise ValueError('review plan does not match frozen inputs')
    source_index=json.loads((folder/'source-index.json').read_text())
    if [(r['id'],r['source_group'],r['role']) for r in source_index['sources']]!=[(r['id'],r['source_group'],r['role']) for r in cohort['sources']]:raise ValueError('source index role differs')
    for a,b in zip(base,cohort['sources'],strict=True):
        if any(a[k]!=b[k] for k in a):raise ValueError('source role or requirement coverage does not replay')
    if regression.capacity_sources()!=[{k:v for k,v in row.items() if k not in ('module','input_bits','output_bits','vector_sha256','rtl_sha256')} for row in cohort['capacity_sources']]:
        # JSON round-trip normalizes tuple periods to lists.
        if encode(regression.capacity_sources())!=encode([{k:v for k,v in row.items() if k not in ('module','input_bits','output_bits','vector_sha256','rtl_sha256')} for row in cohort['capacity_sources']]):raise ValueError('capacity plan changed')
    hashes={};roles={}
    for row in cohort['sources']+cohort['capacity_sources']:
        generated=shells.source(row['features']);saved=inputs['source_outputs'][row['id']]
        if generated!=saved['rtl'] or digest(generated.encode())!=row['rtl_sha256']:raise ValueError('actual source bytes do not regenerate')
        h=row['rtl_sha256']
        if h in roles and roles[h]!=row['role']:raise ValueError('identical RTL leaks across roles')
        roles[h]=row['role'];hashes[row['id']]=h
        geometry=shells.generic_geometry(inputs['generic_projection'],row['module'],row['features'])
        if geometry!=inputs['geometries'][row['id']]:raise ValueError('generic FF/constant/pass-through projection changed')
        if digest(saved['vectors'].encode())!=row['vector_sha256']:raise ValueError('actual functional vectors changed')
        # Independently replay every saved cycle against the integer reference.
        g=shells.layout(row['features']);n,r=g['input_bits'],g['output_bits'];old=0;valid=0
        for index,line in enumerate(saved['vectors'].splitlines()):
            word=int(line,16);ov=word&1;result=(word>>1)&((1<<r)-1);iv=word>>(r+1)&1;rstn=word>>(r+2)&1;value=word>>(r+3)
            if value >= 1<<n or result!=shells.evaluate(row['features'],old) or ov!=(0 if not rstn else valid):raise ValueError('cycle reference replay differs')
            if not rstn:old=0;valid=0
            else:
                valid=iv
                if iv:old=value
        if index!=95:raise ValueError('incomplete cycle vector')
    reader=regression.reader_checks()
    for name in reader:
        if encode(reader[name])!=encode(inputs['reader'][name]):raise ValueError('reader fixture or negative checks do not replay')
    if encode(regression.scanner_checks())!=encode(inputs['scanner']):raise ValueError('scanner trajectories do not replay')
    log=inputs['functional_execution']
    if 'CONTEXT_RTL_PASS sources=90 cycles=96 comparisons=8640' not in log['marker'] or log['verilator_warnings']:raise ValueError('actual RTL execution not accepted')
    expected_kernels='\n'.join(shells.source(r['features'],r['module']) for r in cohort['sources']+cohort['capacity_sources'])
    if expected_kernels!=log['combined_kernel_source']:raise ValueError('executed combined kernels do not regenerate')
    for i,row in enumerate(cohort['sources']+cohort['capacity_sources']):
        r=row['output_bits']
        if f'dut{i}.observed!==v{i}[j][{r}:1]' not in log['testbench_source'] or f'ov{i}!==v{i}[j][0]' not in log['testbench_source']:
            raise ValueError('executed testbench missing data or valid comparator')
    if len(inputs['coverage']['required_context_to_source'])!=63 or len(hashes)!=90:raise ValueError('incomplete requirement coverage')
    external_status='not_requested'
    if external:
        path=Path(pool['external']['full_generic_json'])
        if digest(path.read_bytes())!=pool['external']['full_generic_sha256']:raise ValueError('full generic artifact unavailable or changed')
        full=json.loads(path.read_text())
        for row in cohort['sources']+cohort['capacity_sources']:
            if shells.generic_geometry(full,row['module'],row['features'])!=inputs['geometries'][row['id']]:raise ValueError('full generic geometry differs')
        for module,expected in inputs['comb_primitive_census'].items():
            counts={}
            for cell in full['modules'][module]['cells'].values():counts[cell['type']]=counts.get(cell['type'],0)+1
            if counts!=expected:raise ValueError('full arithmetic primitive census differs')
        external_status='full_generic_hash_geometry_and_census_replayed'
    result=dict(status='passed',required_contexts=63,software_sources=90,cycle_comparisons=8640,
        independent_reader_negatives=len(reader['negative_checks']),sampler_trajectories=inputs['scanner']['trajectories'],
        generic_scope='saved FF/port projections and primitive census; full netlist external',external=external_status,
        physical_endpoint_qualification=False,model_test_labels_consumed=0,PPA_calls=0,full_D_ready=False)
    print(json.dumps(result),flush=True);return result


def isolated(folder,out):
    manifest,pool=load(folder)
    out.mkdir(parents=True,exist_ok=False)
    tree=out/'tree';tree.mkdir()
    for name,text in pool['sources'].items():
        p=tree/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    copied=tree/'evidence';shutil.copytree(folder,copied)
    script=tree/'isolated.py'
    script.write_text('''import sys,os
from pathlib import Path
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root))
def audit(event,args):
    if event in ('subprocess.Popen','os.system','os.posix_spawn'):raise RuntimeError('isolated replay subprocess forbidden')
    if event=='open' and isinstance(args[0],(str,bytes)):
        p=Path(os.fsdecode(args[0])).resolve()
        if str(p).startswith('/home/') and not p.is_relative_to(root):raise RuntimeError('original home/project/build read forbidden: '+str(p))
sys.addaudithook(audit)
from experiments.arithmetic_dse.model_target_round1_evidence import verify
verify(root/'evidence')
''')
    from .processes import run_command
    # This function is itself invoked as a paid support leaf. The internal
    # replay is part of that leaf; it is not separately charged.
    env=os.environ.copy();env.update(PATH='',PYTHONDONTWRITEBYTECODE='1')
    record=run_command([sys.executable,'-I','-S',str(script)],out,'isolated',180,env,8192)
    if record['exit_code']:raise ValueError('isolated replay failed: '+record['log'])
    print(Path(record['log']).read_text(),flush=True)
    # Restore one-byte changes after each negative; original evidence untouched.
    name=next(iter(manifest['chunks']));path=copied/name;original=path.read_bytes();changed=bytearray(original);changed[len(changed)//2]^=1;path.write_bytes(changed)
    try:load(copied)
    except ValueError:tamper=True
    else:raise ValueError('corrupt pool accepted')
    finally:path.write_bytes(original)
    write(out/'proof.json',dict(status='passed',original_home_project_build_denied=True,PATH_empty=True,replay_subprocess_denied=True,
                               pool_tamper_rejected=tamper,PPA_calls=0))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=('pack','verify','isolated'))
    parser.add_argument('--folder',type=Path,required=True);parser.add_argument('--run',type=Path);parser.add_argument('--checks',type=Path);parser.add_argument('--out',type=Path);parser.add_argument('--external',action='store_true');args=parser.parse_args()
    if args.action=='pack':
        if not args.run or not args.checks:parser.error('--run and --checks required')
        pack(args.run.resolve(),args.checks.resolve(),args.folder.resolve())
    elif args.action=='isolated':
        if not args.out:parser.error('--out required')
        isolated(args.folder.resolve(),args.out.resolve())
    else:verify(args.folder.resolve(),args.external)
