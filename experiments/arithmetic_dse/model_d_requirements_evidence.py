"""Portable static D-demand audit, frozen accounting requirements, and actual receipts."""
import argparse
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
VERSION='asap7-D-static-requirements-evidence-v1'


def read(path):return json.loads(Path(path).read_text())
def digest(raw):return hashlib.sha256(raw).hexdigest()
def sha(path):return digest(Path(path).read_bytes())
def write(path,value):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
def pack(path,files):
    value={name:{'sha256':sha(source),'text':source.read_text()} for name,source in sorted(files.items())}
    path.write_bytes(gzip.compress(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode(),mtime=0))
def unpack(path,root):
    value=json.loads(gzip.decompress(path.read_bytes()))
    for name,item in value.items():
        if Path(name).is_absolute() or '..' in Path(name).parts:raise ValueError('unsafe pool member')
        data=item['text'].encode()
        if digest(data)!=item['sha256']:raise ValueError('pool member identity mismatch')
        dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    return len(value)


def seal(audit,review,folder):
    folder.mkdir(parents=True,exist_ok=False)
    source={str(p.relative_to(ROOT)):p for p in (ROOT/'rtlzz/src').rglob('*') if p.is_file()}
    for name in ('rtlzz/CMakeLists.txt','rtlzz/testv2/arithmetic_d_requirements_export.cpp',
                 'experiments/arithmetic_dse/model_d_requirements.py','experiments/arithmetic_dse/model_d_requirements_evidence.py',
                 'experiments/arithmetic_dse/configs/target_rules_v2.json','experiments/arithmetic_dse/configs/model_asap7_m2_joint_requirements_v1.json',
                 'experiments/arithmetic/evidence/step7_m2_mux_static_v1/asap7-primitives.json',
                 'experiments/arithmetic/evidence/step7_native_state_v1/asap7-native-state.json'):
        source[name]=ROOT/name
    parent=ROOT/'experiments/arithmetic/evidence/step7_m2_native_integration_v1/public-nine'
    for p in parent.glob('*.json'):source[str(p.relative_to(ROOT))]=p
    pack(folder/'source-pool.json.gz',source)
    artifacts={str(p.relative_to(audit)):p for p in (audit/'native').glob('*.json')}
    for name in ('cases.json','reference-requirements.json','gap-audit.json','next-protocol.json'):artifacts[name]=audit/name
    for entry in read(audit/'cases.json')['cases']:
        source_path=Path(entry['source'])
        if sha(source_path)!=entry['generated_source_sha256']:raise ValueError('public generated source changed')
        artifacts['sources/'+entry['name']+'.cpp']=source_path
        for filename,h in entry['public_VUL_source_sha256'].items():
            p=ROOT/'experiments/arithmetic/evidence/step7_m2_native_integration_v1/public-source'/entry['name']/filename
            if sha(p)!=h:raise ValueError('public VUL changed')
            artifacts['public-source/'+entry['name']+'/'+filename]=p
    pack(folder/'audit-pool.json.gz',artifacts)
    receipts={}
    for label,origin in [('first-failure',audit.parent/'audit-v1'),('identity-correction',audit.parent/'audit-v2'),('latest',audit),('regressions',review)]:
        for p in origin.glob('*'):
            if p.is_file() and (p.name.endswith(('.command.json','.log'))):receipts[label+'/'+p.name]=p
    for name in ('primitives/parity.json','state/parity.json'):receipts['regressions/'+name]=review/name
    pack(folder/'receipts-pool.json.gz',receipts)
    index=read(audit/'native/index.json');gap=read(audit/'gap-audit.json');protocol=read(audit/'next-protocol.json')
    summary={k:gap[k] for k in ('candidate_count','view_count','illegal_move_proposals','state_condition_view_counts',
        'state_feature_ranges','observed_state_word_widths','semantic_operation_inventory','stage_shape_count',
        'production_C_graph_and_order_parity','independent_K16_order_checked','placement_scope')}
    summary.update(version=VERSION,status='static_requirements_frozen',observed_template_sets=len(gap['template_group_sets']),
        conservative_template_interval_sets=len(gap['template_interval_envelope']),required_reference_labels=17,
        numerical_targets_frozen=False,physical_admission_allowed=False,full_D_ready=False,PPA_calls=0)
    write(folder/'summary.json',summary);write(folder/'next-protocol.json',protocol)
    external={str(p.resolve()):sha(p) for p in artifacts.values()}
    # Preserve the executed exporter before a future build replaces the binary.
    binary=ROOT/'build/step4-rtlzz/testv2/arithmetic-d-requirements-export';frozen=audit.parent/'frozen-exporter'/sha(binary)
    frozen.mkdir(parents=True,exist_ok=True)
    if (frozen/binary.name).exists():
        if sha(frozen/binary.name)!=sha(binary):raise ValueError('preserved exporter identity changed')
    else:shutil.copy2(binary,frozen/binary.name)
    external[str(frozen/binary.name)]=sha(binary)
    write(folder/'provenance.json',{'version':VERSION,'audit':str(audit),'review':str(review),
        'original_artifacts':external,'active_source_hashes_required_for_historical_replay':False,
        'frozen_source_pool_is_producer_identity':True,'prior_analysis_failure_retained':True,
        'no_new_physical_measurements':True,'independent_PPA_labels_used_for_selection':False})
    write(folder/'manifest.json',{'version':VERSION,'files':{str(p.relative_to(folder)):sha(p) for p in folder.iterdir() if p.is_file()}})
    print(json.dumps({'status':'sealed','source_files':len(source),'audit_files':len(artifacts),'receipt_files':len(receipts),
        'bytes':sum(p.stat().st_size for p in folder.iterdir() if p.is_file())}),flush=True)


def verify(folder,external=False):
    manifest=read(folder/'manifest.json')
    if manifest['version']!=VERSION:raise ValueError('requirements evidence schema mismatch')
    for name,h in manifest['files'].items():
        if sha(folder/name)!=h:raise ValueError('requirements evidence content identity mismatch: '+name)
    with tempfile.TemporaryDirectory(prefix='D-static-replay-') as tmp:
        tmp=Path(tmp);source=tmp/'source';audit=tmp/'audit';receipts=tmp/'receipts'
        ns=unpack(folder/'source-pool.json.gz',source);na=unpack(folder/'audit-pool.json.gz',audit);nr=unpack(folder/'receipts-pool.json.gz',receipts)
        script=source/'experiments/arithmetic_dse/model_d_requirements.py'
        spec=importlib.util.spec_from_file_location('frozen_D_requirements',script);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        previous=(audit/'gap-audit.json').read_bytes();previous_protocol=(audit/'next-protocol.json').read_bytes();module.analyze(audit)
        if (audit/'gap-audit.json').read_bytes()!=previous or (audit/'next-protocol.json').read_bytes()!=previous_protocol:raise ValueError('static requirements do not reproduce')
        if read(audit/'next-protocol.json')!=read(folder/'next-protocol.json'):raise ValueError('requirements protocol copy differs')
        protocol=read(audit/'next-protocol.json')
        if protocol['physical_admission_allowed'] or protocol['full_D_ready'] or protocol['target_reference']['numerical_targets_frozen']:
            raise ValueError('static audit falsely promoted to model/target/physical admission')
        if read(source/'experiments/arithmetic_dse/configs/model_asap7_m2_joint_requirements_v1.json')!=protocol:raise ValueError('active requirements differ from frozen producer')
        if 'production graph shape changed' not in (receipts/'first-failure/analyze.log').read_text():raise ValueError('first identity failure missing')
        for name,token in [('ordinary','Arithmetic model native checks: 250'),('pipeline-test','pipeline tests passed'),
                          ('pipeline-reset-test','pipeline reset API tests passed'),('pipeline-valid-test','pipeline valid API and IR tests passed')]:
            if token not in (receipts/f'regressions/{name}.log').read_text():raise ValueError('production regression receipt missing')
        for name,count in [('primitives',436),('state',175)]:
            parity=read(receipts/'regressions'/name/'parity.json')
            if parity['status']!='passed' or parity.get('native_queries',parity.get('state_queries'))!=count or parity['maximum_native_Python_delta']!=0:
                raise ValueError('component inference regression failed')
        gap=read(audit/'gap-audit.json');summary=read(folder/'summary.json')
        for k in ('candidate_count','view_count','stage_shape_count','state_condition_view_counts'):
            if summary[k]!=gap[k]:raise ValueError('audit summary differs')
        for c in read(audit/'cases.json')['cases']:
            if sha(audit/'sources'/(c['name']+'.cpp'))!=c['generated_source_sha256']:raise ValueError('public generated source identity changed')
            for name,h in c['public_VUL_source_sha256'].items():
                if sha(audit/'public-source'/c['name']/name)!=h:raise ValueError('public VUL source identity changed')
    if external:
        for name,h in read(folder/'provenance.json')['original_artifacts'].items():
            if sha(name)!=h:raise ValueError('external audit artifact differs: '+name)
    result={'status':'passed','external':external,'source_files':ns,'audit_files':na,'receipt_files':nr,
        'candidates':summary['candidate_count'],'views':summary['view_count'],'PPA_calls':0,
        'physical_admission_allowed':False,'full_D_ready':False}
    print(json.dumps(result),flush=True);return result


def isolated(folder):
    with tempfile.TemporaryDirectory(prefix='D-requirements-isolated-') as tmp:
        tmp=Path(tmp);local=tmp/'evidence';shutil.copytree(folder,local);source=tmp/'source';unpack(local/'source-pool.json.gz',source)
        script=source/'experiments/arithmetic_dse/model_d_requirements_evidence.py'
        code="""import builtins,io,os,runpy,subprocess,sys
from pathlib import Path
script,folder=sys.argv[1:]
def guarded(original):
 def checked(path,*a,**kw):
  if isinstance(path,(str,bytes,os.PathLike)) and str(Path(path).resolve()).startswith('/home/zyrv/vulsim'):
   raise RuntimeError('original repository read forbidden')
  return original(path,*a,**kw)
 return checked
builtins.open=guarded(builtins.open);io.open=guarded(io.open)
def forbidden(*a,**kw):raise RuntimeError('subprocess forbidden in static replay')
subprocess.Popen=forbidden
sys.argv=[script,'verify','--folder',folder];runpy.run_path(script,run_name='__main__')
"""
        env=os.environ.copy();env.update(PATH='',PYTHONDONTWRITEBYTECODE='1');env.pop('PYTHONPATH',None)
        result=subprocess.run([sys.executable,'-B','-c',code,str(script),str(local)],cwd=tmp,env=env,capture_output=True,text=True)
        if result.returncode:raise ValueError('isolated requirements replay failed: '+result.stderr[-1800:])
        path=local/'audit-pool.json.gz';raw=bytearray(path.read_bytes());raw[len(raw)//2]^=1;path.write_bytes(raw)
        result=subprocess.run([sys.executable,'-B',str(script),'verify','--folder',str(local)],cwd=tmp,env=env,capture_output=True,text=True)
        if result.returncode==0 or 'content identity mismatch' not in result.stderr:raise ValueError('tampered static audit accepted')
    print(json.dumps({'status':'passed','original_repository_reads_denied':True,'PATH_empty':True,
        'replay_subprocess_forbidden':True,'audit_tampering_rejected':True,'PPA_calls':0}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('seal','verify','isolated'))
    p.add_argument('--folder',type=Path,required=True);p.add_argument('--audit',type=Path);p.add_argument('--review',type=Path);p.add_argument('--external',action='store_true');a=p.parse_args()
    if a.action=='seal':seal(a.audit.resolve(),a.review.resolve(),a.folder.resolve())
    elif a.action=='isolated':isolated(a.folder.resolve())
    else:verify(a.folder.resolve(),a.external)
