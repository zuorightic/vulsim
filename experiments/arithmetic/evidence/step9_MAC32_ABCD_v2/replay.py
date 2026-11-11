"""Seal whole-design PPA/clock evidence; granular C diagnostics stay separate."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import sys
import tarfile
import tempfile

ROOT=Path(__file__).resolve().parents[2]
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')


def archive(root):
    from .stage9_continue_v1 import verify_admission
    verify_admission(root/'continuation-v1')
    result=read(root/'results-v2/results.json')
    if not result['all_minimum_period_brackets_passed'] or not result['all_whole_design_STA_CEC_state_passed']:raise ValueError('whole-design measurement incomplete')
    for p in (ROOT/'experiments/arithmetic_dse').glob('stage9*.py'):
        dest=root/'final-source'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    for name in ('regression/arithmetic_abcd_final.py','rtlzz/testv2/arithmetic_abcd_export.cpp'):
        dest=root/'final-source'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest)
    shutil.copytree(ROOT/'build/step9-ABCD-20261111',root/'support-receipts-before-archive')
    members={}
    for item in root.iterdir():
        if item.name in ('archives','restore'):continue
        for p in item.rglob('*') if item.is_dir() else [item]:
            if p.is_file():members[str(p.relative_to(root))]=p
    index={n:dict(sha256=sha(p),bytes=p.stat().st_size) for n,p in members.items()};target=root/'archives/ABCD-raw-v2.tar.gz';target.parent.mkdir(exist_ok=True);(root/'restore').mkdir(exist_ok=True)
    with target.open('xb') as raw:
        with gzip.GzipFile(fileobj=raw,mode='wb',mtime=0,compresslevel=1) as compressed:
            with tarfile.open(fileobj=compressed,mode='w|',dereference=True) as bundle:
                for n,p in sorted(members.items()):bundle.add(p,arcname=n,recursive=False)
    # Materialize and hash each member, then release the temporary restored
    # file, keeping peak additional storage below the original8GiB envelope.
    with tempfile.TemporaryDirectory(prefix='ABCD-every-member-restore-',dir=root/'restore') as tmp:
        out=Path(tmp)/'member';seen=set()
        with tarfile.open(target,'r|gz') as bundle:
            for member in bundle:
                n=Path(member.name)
                if not member.isfile() or member.name not in index or member.name in seen or n.is_absolute() or '..' in n.parts:raise ValueError('unexpected raw archive member')
                seen.add(member.name)
                with bundle.extractfile(member) as src,out.open('wb') as dst:shutil.copyfileobj(src,dst)
                if out.stat().st_size!=index[member.name]['bytes'] or sha(out)!=index[member.name]['sha256']:raise ValueError('actual restored raw member differs')
                out.unlink()
        if seen!=set(index):raise ValueError('raw member inventory differs')
    write(str(target)+'.index.json',dict(status='passed',members=index,archive_bytes=target.stat().st_size,archive_sha256=sha(target),logical_bytes=sum(v['bytes'] for v in index.values()),actual_restore_and_every_member_hash_checked=True,
        restore_strategy='each member materialized and SHA-checked before releasing its temporary restored copy',no_original_artifacts_deleted=True,storage_class='local same-disk archive'))
    print('ABCD_MEASUREMENT_RAW_RESTORED members='+str(len(index))+' bytes='+str(target.stat().st_size),flush=True)


def package(root,evidence):
    if evidence.exists():raise ValueError('preserve whole-design measurement evidence')
    pool={}
    def add(p,n=None):pool[n or 'data/'+str(p.relative_to(root))]=p.read_text()
    for n in ('methods.json','protocol.json','selection-freeze.json','repeat-protocol.json','repeat-decision.json','repeat-basis.json','results-v2/results.json','results-v2/ABCD.csv','results-v2/RESULTS.md','clock-admission.json','clock-admission-v2.json','clock-readout-v2/status.json','simulation/status.json','state-qualification-v3/qualification.json','physical-state-projections-v1/qualification.json'):
        add(root/n)
    for p in (ROOT/'experiments/arithmetic_dse').glob('stage9*.py'):add(p,'source/'+str(p.relative_to(ROOT)))
    for method in read(root/'methods.json')['rows']:
        for key in ('rtl','endpoint_contract','selection_snapshot'):add(Path(method[key]))
    tasks=read(root/'methods.json')['tasks']+read(root/'repeats-v1/admission.json')['tasks']
    for task in tasks:
        d=Path(task['physical_directory']) if 'physical_directory' in task else root/'runs'/task['id']
        for n in ('pilot-metrics.json','pilot-status.json','exact-state-proof.json','liberty_cells.json','logs/asap7/arithmetic_probe/base/structural_cec/proof.json'):add(d/n)
        reports=d/'reports/asap7/arithmetic_probe/base'
        for suffix in ('cells.tsv','units.rpt','setup.rpt','hold.rpt','setup_tns.rpt','hold_tns.rpt','coverage.rpt','period.rpt'):add(reports/('vulsim_grt_'+suffix))
        if task['id'].startswith('implementation'):
            for n in ('period.tsv','result.json','command.json','period.tcl'):add(root/'clock-readout-v2'/task['id']/n)
    for p in (root/'repeats-v1').glob('*.json'):add(p)
    receipt=read(ROOT/'build/step9-ABCD-20261111/a9-sim-run-02/commands.json');pool['data/simulation-receipt.json']=json.dumps(receipt);pool['data/simulation.log']=Path(receipt[0]['log']).read_text()
    raw=read(root/'archives/ABCD-raw-v2.tar.gz.index.json');pool['data/raw-restore.json']=json.dumps({k:v for k,v in raw.items() if k!='members'}|dict(members=len(raw['members']),full_index_sha256=sha(root/'archives/ABCD-raw-v2.tar.gz.index.json')))
    paths={};blobs={}
    for n,value in pool.items():h=hashlib.sha256(value.encode()).hexdigest();paths[n]=h;blobs[h]=value
    payload=json.dumps(dict(paths=paths,blobs=blobs),sort_keys=True,separators=(',',':')).encode();compressed=gzip.compress(payload,mtime=0);evidence.mkdir(parents=True);chunks={}
    for i,start in enumerate(range(0,len(compressed),512*1024)):
        p=evidence/f'pool-{i:03d}.gzpart';p.write_bytes(compressed[start:start+512*1024]);chunks[p.name]=sha(p)
    shutil.copy2(Path(__file__),evidence/'replay.py');write(evidence/'manifest.json',dict(version='ABCD-whole-design-minimum-period-evidence-v2',members=len(pool),unique_blobs=len(blobs),chunks=chunks,payload_sha256=hashlib.sha256(payload).hexdigest(),replay_sha256=sha(evidence/'replay.py'),original_root=str(root),
        replay_scope='all21 method rows and19 complete grt PPA reports;17 full-boundary minimum-period class calculations and threshold checks;sealed state/CEC/cycle receipts;granular C diagnostics not replayed',full_D_ready=False))
    sizes=[p.stat().st_size for p in evidence.iterdir() if p.is_file()]
    if sum(sizes)>5*1024**2 or max(sizes)>1024**2:raise ValueError('portable evidence limit exceeded')
    print('ABCD_MEASUREMENT_EVIDENCE_SEALED members='+str(len(pool))+' bytes='+str(sum(sizes)),flush=True)


def replay(evidence):
    m=read(evidence/'manifest.json');compressed=b''
    if sha(evidence/'replay.py')!=m['replay_sha256']:raise ValueError('clock replay implementation differs')
    for n,h in m['chunks'].items():
        if sha(evidence/n)!=h:raise ValueError('clock evidence chunk differs')
        compressed+=(evidence/n).read_bytes()
    payload=gzip.decompress(compressed)
    if hashlib.sha256(payload).hexdigest()!=m['payload_sha256']:raise ValueError('clock payload differs')
    packet=json.loads(payload);pool={n:packet['blobs'][h] for n,h in packet['paths'].items()}
    if len(pool)!=m['members']:raise ValueError('clock evidence inventory differs')
    for n,h in packet['paths'].items():
        if hashlib.sha256(pool[n].encode()).hexdigest()!=h:raise ValueError('clock member differs')
    def data(n):return json.loads(pool['data/'+n])
    def close(a,b):
        if not math.isclose(a,b,abs_tol=.00001,rel_tol=1e-9):raise ValueError('raw numerical evidence differs '+str((a,b)))
    result=data('results-v2/results.json');methods=data('methods.json');physical={};tasks=methods['tasks']+data('repeats-v1/admission.json')['tasks']
    for task in tasks:
        path=('repeats-v1/runs/' if task['id'].startswith('repeat') else 'runs/')+task['id'];metric=data(path+'/pilot-metrics.json')[-1];prefix='data/'+path+'/reports/asap7/arithmetic_probe/base/vulsim_grt_';area=0;FF=0;cells=data(path+'/liberty_cells.json')['cells']
        for line in pool[prefix+'cells.tsv'].splitlines():
            master,count,size,filler,kind=line.split('\t');count=int(count);size=float(size)
            if filler!='1':area+=count*size
            if master in cells:
                close(size,cells[master]['area_um2'])
                if cells[master]['sequential']:FF+=count
        close(area,metric['cell_area_um2'])
        if FF!=metric['sequential_cells'] or pool[prefix+'coverage.rpt'].strip():raise ValueError('raw FF/coverage evidence differs')
        for suffix,pattern,key in [('setup.rpt',r'worst slack max\s+([-+\d.eE]+)','setup_worst_slack_ps'),('hold.rpt',r'worst slack min\s+([-+\d.eE]+)','hold_worst_slack_ps'),('setup_tns.rpt',r'tns max\s+([-+\d.eE]+)','setup_tns_ps'),('hold_tns.rpt',r'tns min\s+([-+\d.eE]+)','hold_tns_ps')]:
            close(float(re.search(pattern,pool[prefix+suffix])[1]),metric[key])
        if data(path+'/exact-state-proof.json')['status']!='passed_exact_Boolean_state_functions' or not data(path+'/pilot-status.json')['CEC']:raise ValueError('actual state/CEC success receipt missing')
        if not task['id'].startswith('repeat'):
            rows=[r.split('\t') for r in pool['data/clock-readout-v2/'+task['id']+'/period.tsv'].splitlines()[1:]];classes={n:(float(s),float(p)) for n,s,p in rows};limits=[]
            for name,slope in [('register_to_register',1),('input_to_register',.8),('register_to_output',.8)]:
                slack,limit=classes[name];close(limit,task['period_ps']-slack/slope);limits.append(limit)
            close(min(classes[n][0] for n in ('register_to_register','input_to_register','register_to_output')),metric['setup_worst_slack_ps']);limit=max(limits);clock=data('clock-readout-v2/'+task['id']+'/result.json');close(limit,clock['full_setup_minimum_period_ps']);close(1e6/limit,clock['maximum_frequency_MHz'])
            for delta in (-.1,.1):
                s,p=classes['threshold_check_'+str(delta)];close(p,limit+delta)
                if (s>=0)!=(delta>0):raise ValueError('actual STA threshold bracket sign differs')
            if data('clock-readout-v2/'+task['id']+'/command.json')['exit_code']:raise ValueError('actual clock STA failed')
            physical[task['id']]=clock
    for row in result['rows']:
        actual=physical[row['physical_task']]
        for key,source in [('area_um2','area_um2'),('minimum_setup_period_ps','full_setup_minimum_period_ps'),('maximum_setup_frequency_MHz','maximum_frequency_MHz'),('setup_WNS_ps','original_setup_WNS_ps'),('hold_WNS_ps','hold_WNS_ps')]:close(row[key],actual[source])
        method=next(x for x in methods['rows'] if x['id']==row['method']);name='data/'+str(Path(method['rtl']).relative_to(m['original_root']))
        if hashlib.sha256(pool[name].encode()).hexdigest()!=row['rtl_sha256']:raise ValueError('frozen method RTL changed')
    if data('simulation-receipt.json')[0]['exit_code'] or 'ABCD_RTL_PASS unique=5 cycles=320' not in pool['data/simulation.log']:raise ValueError('actual cycles success missing')
    if not data('raw-restore.json')['actual_restore_and_every_member_hash_checked'] or result['full_D_ready'] or m['full_D_ready']:raise ValueError('restore/scope differs')
    print(dict(status='passed_isolated_ABCD_PPA_minimum_period_replay',methods=21,physical_PPA_reports=19,clock_brackets=17,granular_C_diagnostics_replayed=False,full_D_ready=False),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('archive','package','replay'));p.add_argument('--root',type=Path);p.add_argument('--evidence',type=Path);a=p.parse_args()
    if a.action=='archive':archive(a.root.resolve())
    elif a.action=='package':package(a.root.resolve(),a.evidence.resolve())
    else:replay(a.evidence.resolve())
