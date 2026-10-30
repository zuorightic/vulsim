from pathlib import Path
import hashlib,json,os,shutil,subprocess,tempfile
ROOT=Path.cwd();frel=Path('experiments/arithmetic/backend_freeze_v5.json')
freeze=json.loads((ROOT/frel).read_text())
results={}
with tempfile.TemporaryDirectory(prefix='vulsim-platform-portable-') as temporary:
    root=Path(temporary)
    files=[str(frel),*freeze['files_sha256'],*freeze['historical_freezes']]
    for rel in files:
        dest=root/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/rel,dest)
    ev=Path(freeze['evidence_directory']);shutil.copytree(ROOT/ev,root/ev,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    env=os.environ.copy();env.update(PATH='',PYTHONPATH='',PYTHONDONTWRITEBYTECODE='1')
    command=['/usr/bin/python3','-m','experiments.arithmetic_dse.platform_evidence']
    def check(label,expect_ok,needle=None):
        r=subprocess.run(command,cwd=root,env=env,text=True,capture_output=True)
        if (r.returncode==0)!=expect_ok or (needle and needle not in r.stderr):
            raise AssertionError(label+': '+r.stdout+r.stderr)
        results[label]={'exit_code':r.returncode,'expected_rejection':not expect_ok,
                        'diagnostic':r.stderr.splitlines()[-1] if r.stderr else json.loads(r.stdout)['status']}
    check('isolated_without_build_EDA_or_PATH',True)
    index=root/freeze['evidence_index'];original_index=index.read_bytes();original_freeze=(root/frel).read_bytes()
    def rebind_for_semantic_negative(relative):
        data=json.loads(original_index);data['files_sha256'][str(relative)]=hashlib.sha256((root/relative).read_bytes()).hexdigest()
        index.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
        f=json.loads(original_freeze);f['evidence_index_sha256']=hashlib.sha256(index.read_bytes()).hexdigest()
        (root/frel).write_text(json.dumps(f,ensure_ascii=False,indent=2)+'\n')
    relative=ev/'runs/sky130hd-mul-rcalias/reports/vulsim_synth_units.rpt'
    original=(root/relative).read_bytes();(root/relative).write_text(original.decode().replace('time 1ns','time 1ps'))
    rebind_for_semantic_negative(relative);check('wrong_report_time_unit_after_hash_rebinding',False,'disagree on time')
    (root/relative).write_bytes(original);index.write_bytes(original_index);(root/frel).write_bytes(original_freeze)
    relative=ev/'runs/nangate45-mul/reports/vulsim_synth_cells.tsv'
    original=(root/relative).read_bytes();lines=original.decode().splitlines();parts=lines[0].split('\t')
    parts[2]=str(float(parts[2])*1.1);lines[0]='\t'.join(parts);(root/relative).write_text('\n'.join(lines)+'\n')
    rebind_for_semantic_negative(relative);check('wrong_LEF_area_after_hash_rebinding',False,'Liberty/LEF area mismatch')
    (root/relative).write_bytes(original);index.write_bytes(original_index);(root/frel).write_bytes(original_freeze)
    relative=Path('experiments/arithmetic_dse/backend.py');(root/relative).write_text((root/relative).read_text()+'\n')
    check('changed_active_source',False,'evidence mismatch')
report={'status':'passed','checks':results,'mutations_confined_to_temporary_copy':True,'EDA_invocations':0}
(ROOT/'build/step3-platforms-20261030/portable_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
