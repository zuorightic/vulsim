"""Verify exactly Git-visible working-tree files, including submodule files.

The main/submodule Git snapshots must later be committed and pushed together.
Ignored files, root build/, and the artifact store never enter the copy.
"""
from pathlib import Path
import argparse,gzip,hashlib,json,os,shutil,subprocess,sys,tempfile

R=Path.cwd();B=R/'build/step6-git-delivery-20261102'
B.mkdir(parents=True,exist_ok=True)
PREFIX='experiments/arithmetic/evidence/step3_budget/historical_manifests/build/'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def git_files(repo,prefix=''):
    raw=subprocess.check_output(['git','-C',str(repo),'ls-files','--cached','--others','--exclude-standard','-z'])
    paths=set()
    for name in set(x.decode() for x in raw.split(b'\0') if x):
        p=repo/name
        if p.is_dir() and (p/'.git').exists():paths.update(git_files(p,prefix+name+'/'))
        elif p.is_file() or p.is_symlink():paths.add(prefix+name)
    return paths
def output(p,value):p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

parser=argparse.ArgumentParser();parser.add_argument('--before-fix',action='store_true');a=parser.parse_args()
files=git_files(R)
protected=json.loads(gzip.decompress((R/'experiments/arithmetic/evidence/step6_review_v2/preservation.json.gz').read_bytes()))
required=sorted(p for p in protected if p.startswith(PREFIX))
assert len(required)==17 and sum((R/p).stat().st_size for p in required)==1084989
assert all(sha(R/p)==protected[p] for p in required)
missing=sorted(set(required)-files)
assert len(missing)==(17 if a.before_fix else 0),missing
assert not any(p.startswith(('build/','experiments/arithmetic/artifact_store/')) for p in files)
inventory={p:sha(R/p) for p in sorted(files) if not (R/p).is_symlink()}
inventory_hash=hashlib.sha256(json.dumps(inventory,sort_keys=True,separators=(',',':')).encode()).hexdigest()
with tempfile.TemporaryDirectory(prefix='step6-actual-Git-delivery-') as tmp:
    root=Path(tmp)
    for name in sorted(files):
        source=R/name;dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True)
        if source.is_symlink():dest.symlink_to(os.readlink(source))
        else:shutil.copy2(source,dest)
    assert not (root/'build').exists() and not (root/'experiments/arithmetic/artifact_store').exists()
    env=os.environ.copy();env.update(PATH='',PYTHONPATH=str(root),PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
    def verify():
        return subprocess.run([sys.executable,'-m','experiments.arithmetic_dse.whole_graph_evidence'],cwd=root,env=env,text=True,capture_output=True)
    result=verify()
    common={'scope':'cached and nonignored untracked working-tree files; recursive submodules; content for a pending commit, not a claim that it is already committed',
        'Git_visible_files':len(files),'Git_regular_file_inventory_sha256':inventory_hash,
        'root_build_copied':False,'artifact_store_copied':False,'PATH':'empty','EDA_invocations':0,
        'required_manifest_count':len(required),'required_manifest_bytes':1084989,
        'required_manifests':[{'path':p,'sha256':protected[p],'bytes':(R/p).stat().st_size} for p in required]}
    if a.before_fix:
        assert result.returncode and 'historical_manifests/build/' in result.stderr,result.stderr
        report={**common,'status':'expected_delivery_failure_reproduced','missing_Git_files':missing,
                'diagnostic':result.stderr.splitlines()[-1]}
        output(B/'before-fix.json',report);print(json.dumps({k:v for k,v in report.items() if k!='required_manifests'},indent=2))
    else:
        assert result.returncode==0,result.stderr
        positive=json.loads(result.stdout);assert positive['status']=='passed' and positive['parent_status']=='passed' and positive['backend_completion']
        for name in required:(root/name).unlink()
        negative=verify();assert negative.returncode and 'historical_manifests/build/' in negative.stderr,negative.stderr
        examples=['build/step6-any/results/5_1_grt.odb',PREFIX+'future/run/5_1_grt.odb',PREFIX+'future/run/large.spef',PREFIX+'future/run/synth.log']
        ignored={name:subprocess.run(['git','check-ignore','--quiet','--no-index','--',name],cwd=R).returncode==0 for name in examples}
        assert all(ignored.values()),ignored
        report={**common,'status':'passed','missing_Git_files':[],'parent_status':positive['parent_status'],
                'backend_completion':positive['backend_completion'],'negative_missing_manifest':'rejected',
                'negative_diagnostic':negative.stderr.splitlines()[-1],'large_and_runtime_files_still_ignored':ignored,
                'compiled_or_RTL_tests_rerun':False,'frozen_evidence_bytes_changed':False}
        output(B/'after-fix.json',report);print(json.dumps({k:v for k,v in report.items() if k!='required_manifests'},indent=2))
