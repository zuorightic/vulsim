"""Copy only frozen sources/evidence; exercise static checks without build/tools.

Run from the repository root with an absolute Python executable. All mutations
and hash rebinding happen in a temporary COPY. No Tcl or generated RTL executes.
"""
from pathlib import Path
import gzip,hashlib,json,os,shutil,subprocess,sys,tempfile
ROOT=Path.cwd(); OUT=ROOT/'build/step4-interfaces-20261030'
FREEZE='experiments/arithmetic/arithmetic_interfaces_freeze_v1.json'
EVIDENCE='experiments/arithmetic/evidence/step4_interfaces_v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
results=[]
with tempfile.TemporaryDirectory(prefix='vulsim-step4-portable-') as folder:
    root=Path(folder)
    def copy(relative):
        source=ROOT/relative;target=root/relative
        if source.is_file():target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    shutil.copytree(ROOT/'experiments/arithmetic',root/'experiments/arithmetic',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    freeze=json.loads((ROOT/FREEZE).read_text())
    # Current consumers of every parent remain available for explicit successor
    # validation; retired files stay absent. Snapshots live under evidence/.
    for path in (ROOT/'experiments/arithmetic').glob('*freeze*.json'):
        for relative in json.loads(path.read_text()).get('files_sha256',{}):copy(relative)
    for relative in freeze['files_sha256']:copy(relative)
    for relative in ('experiments/__init__.py','experiments/arithmetic_dse/__init__.py'):copy(relative)
    # The outer charged test itself is pending. This isolated root intentionally
    # contains the settled ledger bound to the tested archive, not that pending job.
    shutil.copy2(root/EVIDENCE/'usage_after.json',root/'experiments/arithmetic/backend_usage.json')
    assert not (root/'build').exists()
    env={'PATH':'','PYTHONPATH':'','PYTHONDONTWRITEBYTECODE':'1','LC_ALL':'C.UTF-8'}
    def run(label,expect=None):
        command=[sys.executable,'-m','experiments.arithmetic_dse.interfaces_evidence']
        p=subprocess.run(command,cwd=root,env=env,text=True,capture_output=True,timeout=90)
        if expect is None:
            if p.returncode:raise AssertionError(label+' unexpectedly failed: '+p.stderr[-4000:])
            parsed=json.loads(p.stdout);assert parsed['status']=='passed'
            results.append({'name':label,'status':'passed','parent_status':parsed['parent_status'],'evidence_index_sha256':sha(root/json.loads((root/FREEZE).read_text())['evidence_index'])})
        else:
            if p.returncode==0 or not any(part in p.stderr for part in expect):raise AssertionError(label+' was not rejected as expected: '+p.stderr[-3000:])
            results.append({'name':label,'status':'rejected','reason':p.stderr.strip().splitlines()[-1],'evidence_hashes_rebound':label!='current_source_modified'})
    baseline_freeze=(root/FREEZE).read_bytes();index_path=root/freeze['evidence_index'];baseline_index=index_path.read_bytes()
    def rebind(path):
        index=json.loads(baseline_index);index['files_sha256'][str(path.relative_to(root))]=sha(path);write(index_path,index)
        f=json.loads(baseline_freeze);f['evidence_index_sha256']=sha(index_path);write(root/FREEZE,f)
    def mutate_file(label,relative,mutate,expect):
        p=root/relative;original=p.read_bytes()
        try:
            mutate(p);rebind(p);run(label,expect)
        finally:
            p.write_bytes(original);index_path.write_bytes(baseline_index);(root/FREEZE).write_bytes(baseline_freeze)
    def mutate_report(label,name,edit,expect):
        def change(path):
            report=json.loads(path.read_text());edit(report)
            report['graph_identity_text']=json.dumps(report['graph'],ensure_ascii=False,separators=(',',':'),sort_keys=True)
            report['graph_sha256']=hashlib.sha256(report['graph_identity_text'].encode()).hexdigest()
            report['schedule_identity_text']=json.dumps({'stages':report['stages'],'protocol':report['protocol']},ensure_ascii=False,separators=(',',':'),sort_keys=True)
            report['schedule_sha256']=hashlib.sha256((report['graph_sha256']+report['schedule_identity_text']).encode()).hexdigest();write(path,report)
        mutate_file(label,EVIDENCE+'/accepted/generated/'+name+'.json',change,expect)
    run('isolated_original')
    source=root/'rtlzz/src/arithmetic_request.cpp';original=source.read_bytes()
    try:
        source.write_bytes(original+b'\n// negative provenance test\n');run('current_source_modified',['current source rtlzz/src/arithmetic_request.cpp'])
    finally:source.write_bytes(original)
    mul_kind=json.loads((root/'experiments/arithmetic_dse/configs/beir_cost_features_v1.json').read_text())['opcodes']['Mul']
    def zero_mul(report):
        node=next(n for n in report['graph']['nodes'] if n['opcode']==mul_kind);node['delay']=node['comb']=0
    mutate_report('wrong_Mul_cost','mul128',zero_mul,['node delay','node comb'])
    def wrong_ref(report):
        node=next(n for n in report['graph']['nodes'] if n['opcode']==mul_kind);node['operands'][0]['width']+=1
    mutate_report('wrong_reference_width','mul128',wrong_ref,['reference type'])
    def cut_fp(report):
        region=next(r for r in report['graph']['regions'] if r['template_id']=='softfloat3d-bitvector-mul-v1');i=int(region['members'][0]);report['stages'][i]=1
    mutate_report('cut_atomic_FP','mixed_fp',cut_fp,['backwards schedule dependency','atomic region cut by schedule'])
    def wrong_parameters(report):report['graph']['regions'][0]['parameters']['lhs_width']=64
    mutate_report('wrong_template_parameters','mul128',wrong_parameters,['template width parameters'])
    mutate_report('fake_D_success','mul128',lambda r:r['request'].__setitem__('cost_mode','backend-model'),['no fake D result'])
    mutate_report('wrong_reset_protocol','mul128',lambda r:r['protocol']['input_reset_values'].__setitem__('a',['0']),['integer outputs'])
    mutate_report('wrong_clock_protocol','mul128',lambda r:r['protocol'].__setitem__('clock_name','not_the_actual_clock'),['reported clock absent'])
    def flip_bit255(path):
        lines=gzip.decompress(path.read_bytes()).decode().splitlines()
        for i,line in enumerate(lines):
            values=[int(v,16) for v in line.split()]
            if values[0]==511:
                values[10]^=1<<255;lines[i]=' '.join(format(v,'x') for v in values);break
        else:raise AssertionError('missing valid transaction')
        path.write_bytes(gzip.compress(('\n'.join(lines)+'\n').encode(),mtime=0))
    mutate_file('flip_product_bit255',EVIDENCE+'/accepted/rtl-run.log.gz',flip_bit255,['integer outputs'])
    run('isolated_restored')
report={'status':'passed','version':'arithmetic-interfaces-portable-checks-v1','frozen_evidence_index_sha256':hashlib.sha256(baseline_index).hexdigest(),'checks':results,'negative_checks_rejected':sum(r['status']=='rejected' for r in results),'requires_build':False,'compiler_or_EDA_executed':False,'PATH':'','scope':'all copy mutations; full parent chain; semantic negatives rebind graph/schedule/evidence hashes; source negative checks immutable binding'}
(OUT/'portable_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
