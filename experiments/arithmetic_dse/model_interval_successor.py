"""Prepare and seal an additive interval-learning evidence checkpoint.

Parent payloads and freezes stay byte-identical. Large raw reports remain in an
explicit local archive; the portable package references parent byte pools.
"""
import argparse
import copy
import gzip
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from .model_collection import sha, write
from .model_evidence import pool
from .model_mul_intervals import CONFIG
from .budget import usage
from .freeze_history import MUTABLE_DOCUMENTATION

ROOT = Path(__file__).resolve().parents[2]


def compressed(path, value):
    path.write_bytes(gzip.compress((json.dumps(value,separators=(',',':'))+'\n').encode(),mtime=0))


def parts(directory, prefix, objects):
    result=[];group={};size=0
    def flush():
        if not group:return
        name=prefix+str(len(result)).zfill(3)+'.json.gz';path=directory/name
        compressed(path,group)
        if path.stat().st_size>1024*1024:raise ValueError('evidence part exceeds single-file ceiling')
        result.append({'file':name,'sha256':sha(path),'objects':len(group)})
    for digest,text in sorted(objects.items()):
        if group and size+len(text.encode())>650000:flush();group={};size=0
        group[digest]=text;size+=len(text.encode())
    flush();return result


def prepare(args):
    if (args.release or args.native) and not args.test_data:
        raise ValueError('release/native interval evidence requires independent test data and result')
    evidence=args.evidence.resolve();archive=args.raw_archive.resolve()
    evidence.mkdir(parents=True,exist_ok=False);archive.mkdir(parents=True,exist_ok=False)
    parent=json.loads(args.parent_freeze.read_text());parent_dir=ROOT/parent['evidence_directory']
    index=json.loads((parent_dir/'index.json').read_text());known=pool(parent_dir,index)
    old_index=copy.deepcopy(index);objects={};raw={}
    for part in index['text_pool_parts']:
        part['file']=os.path.relpath(parent_dir/part['file'],evidence)
    # Evidence directories normally share a parent. Refuse an accidental path
    # interpretation instead of constructing a nonportable absolute reference.
    if evidence.parent!=parent_dir.parent:raise ValueError('successor evidence must share parent evidence directory')
    def blob(path,target=objects):
        text=Path(path).read_bytes().decode('utf-8');digest=hashlib.sha256(text.encode()).hexdigest();target[digest]=text;return digest
    def document(name,path):
        index['documents'][name]=blob(path);return name
    def object_document(name,value):
        text=json.dumps(value,ensure_ascii=False,indent=2)+'\n';digest=hashlib.sha256(text.encode()).hexdigest();objects[digest]=text;index['documents'][name]=digest;return name
    parent_path=evidence/'parent-candidate.json';shutil.copyfile(args.parent_freeze,parent_path)
    note_name='interval-learning-'+args.batch.name
    fitting=json.loads(args.fitting_data.read_text());datasets=[fitting]
    record={'fitting_data':document(note_name+'/fitting-data.json',args.fitting_data),
            'selection':document(note_name+'/selection-freeze.json',args.fit_dir/'selection-freeze.json'),
            'admission':document(note_name+'/admission.json',args.batch/'admission.json'),
            'protocol_blob':blob(CONFIG),'training_source_blobs':{},'candidates':{},'fit_reports':{},'base_models':{},'released':{}}
    selection=json.loads((args.fit_dir/'selection-freeze.json').read_text())
    for name,digest in selection['training_sources'].items():
        actual=blob(args.fit_dir/'training-source'/name)
        if actual!=digest:raise ValueError('changed executed interval training source')
        record['training_source_blobs'][name]=actual
    for item in selection['models']:
        p=item['platform']
        if sha(args.base/(p+'.json'))!=parent['models'][p]:raise ValueError('interval base is not the parent qualified local model')
        record['candidates'][p]=document(note_name+'/'+p+'.candidate.json',args.fit_dir/(p+'.candidate.json'))
        record['fit_reports'][p]=document(note_name+'/'+p+'.fit.json',args.fit_dir/(p+'.fit.json'))
        record['base_models'][p]=document(note_name+'/'+p+'.base.json',args.base/(p+'.json'))
    if args.test_data:
        if not args.test_result:raise ValueError('test data requires evaluated independent result')
        datasets.append(json.loads(args.test_data.read_text()))
        record['test_data']=document(note_name+'/test-data.json',args.test_data)
        record['test_result']=document(note_name+'/independent-test.json',args.test_result)
        record['consumption']=document(note_name+'/test-consumption.json',args.fit_dir/'independent-test-consumption.json')
    if args.release:
        released=json.loads((args.release/'release.json').read_text())
        document(note_name+'/release.json',args.release/'release.json')
        for item in released['published']:
            p=item['platform'];record['released'][p]=document(note_name+'/'+p+'.released.json',args.release/(p+'.json'))
    index.setdefault('interval_training_evidence',[]).append(record)
    combined=copy.deepcopy(fitting);combined['rows']=[r for d in datasets for r in d['rows']]
    combined['failures']=[r for d in datasets for r in d['failures']]
    interval_metadata=copy.deepcopy(index['interval_evidence'])
    interval_metadata['dataset']=object_document(note_name+'/all-data.json',combined)
    interval_metadata['admission']=record['admission'];interval_metadata['bundles']={}
    included={r['id'].split('/')[0] for r in combined['rows']}
    # Retain the old checkpoint's sources through references; current intervals
    # replace only the active semantic coverage metadata, not old payload bytes.
    for task in sorted(included):
        directory=args.batch/'runs'/task
        interval_metadata['bundles'][task]={'contract':blob(directory/'sample-contract.json'),'rtl':blob(directory/'input.sv')}
    index['interval_evidence']=interval_metadata
    previous=set()
    for name in ['run-summary.json','interval-run-summary.json']+old_index.get('additional_raw_archives',[]):
        summary=json.loads(known[old_index['documents'][name]]);directory=ROOT/summary['full_archive']
        original=json.loads((directory/'index.prepared.json').read_text());content=pool(directory,original)
        previous.update(x['files']['manifest.json'] for x in json.loads(content[original['run_catalog']]))
    catalog=[];large=[]
    for manifest_path in sorted((args.batch/'runs').glob('*/manifest.json')):
        if sha(manifest_path) in previous:continue
        directory=manifest_path.parent;files={'manifest.json':blob(manifest_path,raw)}
        for name in ('input.sv','sample-contract.json','liberty_cells.json','effective-environment.txt','abc_constraints.txt','abc_speed_target.script','config.mk'):
            if (directory/name).is_file():files[name]=blob(directory/name,raw)
        for subdir in ('source','reports'):
            for path in sorted((directory/subdir).rglob('*')):
                if path.is_file() and (subdir!='reports' or path.name.startswith('vulsim_')):files[str(path.relative_to(directory))]=blob(path,raw)
        for path in sorted((directory/'results').rglob('*.sdc')):files[str(path.relative_to(directory))]=blob(path,raw)
        for path in sorted(directory.rglob('*')):
            if path.is_file() and 'flow-scripts' not in path.relative_to(directory).parts and path.suffix in ('.odb','.spef','.v','.log'):
                large.append({'path':str(path.resolve().relative_to(ROOT)),'size':path.stat().st_size,'sha256':sha(path)})
        catalog.append({'original_directory':str(directory.resolve().relative_to(ROOT)),'files':files})
    text=json.dumps(catalog,separators=(',',':'));catalog_hash=hashlib.sha256(text.encode()).hexdigest();raw[catalog_hash]=text
    write(archive/'index.prepared.json',{'text_pool_parts':parts(archive,'text-',raw),'run_catalog':catalog_hash})
    compressed(archive/'local_artifacts.json.gz',large)
    raw_note=object_document(note_name+'/raw-archive.json',{'full_archive':str(archive.relative_to(ROOT)),
        'full_archive_sha256':hashlib.sha256(b''.join(sorted(p.read_bytes() for p in archive.rglob('*') if p.is_file()))).hexdigest(),
        'additional_runs':len(catalog),'parent_runs_referenced_without_duplication':len(previous),
        'data_role':'actual interval training/validation and explicitly frozen independent test if present'})
    index.setdefault('additional_raw_archives',[]).append(raw_note)
    if args.native:
        for p,model_name in record['released'].items():
            report_name=document(note_name+'/'+p+'.native-report.json',args.native/(p+'.report.json'))
            document(note_name+'/'+p+'.C-native-report.json',args.native/(p+'.C.report.json'))
            index['native_reports'].append({'report':report_name,'model':model_name,'rtl':blob(args.native/(p+'.sv')),'evidence_role':'actual qualified interval model public source entry'})
    if args.cycle_receipt:document(note_name+'/actual-RTL-cycles.json',args.cycle_receipt)
    # Preserve actual software receipts with their execution-time source map.
    # Source maps describe their own runs, not every later edit of the files.
    ledger=json.loads((ROOT/'experiments/arithmetic/backend_usage.json').read_text())
    start=next(i for i,e in enumerate(ledger['entries']) if e.get('task_id')=='interval-resume-preflight-v1')
    index.setdefault('interval_support_records',[])
    for entry in ledger['entries'][start:]:
        if entry.get('admission_id')!='step7-model-development-v1' or entry['status']=='reserved':continue
        command_path=Path(entry['command_record']);command=json.loads(command_path.read_text())
        source_path=command_path.with_name(command_path.name.replace('.command.json','.sources.json'))
        log=Path(command['log'])
        receipt={'ledger_entry_id':entry['id'],'execution':command,'stdout':log.read_text(),
                 'source_sha256_at_execution':json.loads(source_path.read_text()) if source_path.exists() else None}
        index['interval_support_records'].append(object_document(note_name+'/support/'+entry['task_id']+'.json',receipt))
    for name in ('advance_asap7.py','continue_test_after_budget_fix.py','reconcile_test_preflight.py','summarize_independent_failure.py'):
        driver=args.fit_dir.parent/name
        if driver.is_file():
            target=evidence/'workflow_source'/name;target.parent.mkdir(exist_ok=True);shutil.copyfile(driver,target)
    for name in ('resume-preflight.json','continue-fitting.json','fitting-runtime-reestimate-v2.json','test-preflight-correction-v1.json','asap7-independent-failure-analysis-v1.json'):
        path=args.fit_dir.parent/name
        if path.is_file():document(note_name+'/execution/'+name,path)
    index['text_pool_parts']+=parts(evidence,'text-learning-',{h:t for h,t in objects.items() if h not in known})
    write(evidence/'index.prepared.json',index)
    # Preserve old code that has been superseded. Its digest must match the
    # parent; HEAD is only a candidate source, never a substitute for checking.
    snapshots=evidence/'parent-source'
    for name,digest in parent['files_sha256'].items():
        active=ROOT/name
        if name in MUTABLE_DOCUMENTATION or not active.is_file() or sha(active)==digest:continue
        sources=[ROOT/path/name for path in parent['historical_source_roots']]
        if name in parent.get('source_snapshots',{}):sources.append(ROOT/parent['source_snapshots'][name])
        content=next((p.read_bytes() for p in sources if p.is_file() and sha(p)==digest),None)
        if content is None:
            repo=ROOT/'rtlzz' if name.startswith('rtlzz/') else ROOT
            relative=name.removeprefix('rtlzz/') if name.startswith('rtlzz/') else name
            content=subprocess.check_output(['git','-C',str(repo),'show','HEAD:'+relative])
        if hashlib.sha256(content).hexdigest()!=digest:raise ValueError('cannot recover exact parent source: '+name)
        destination=snapshots/name;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(content)
    write(evidence/'preparation.json',{'version':'interval-model-checkpoint-preparation-v1','parent_freeze_sha256':sha(args.parent_freeze),
        'parent_evidence':parent['evidence_directory'],'parent_source_root':str(snapshots.relative_to(ROOT)),
        'added_runs':len(catalog),'platforms':list(record['candidates']),'independent_test_present':bool(args.test_data),
        'released_platforms':list(record['released']),'main_matrix_authorized':False,'full_step7_complete':False})
    print(json.dumps({'phase':'prepared; seal only after support settlement','added_runs':len(catalog),'rows':len(combined['rows'])}))


def seal(args):
    evidence=args.evidence.resolve();parent=json.loads((evidence/'parent-candidate.json').read_text())
    parent_dir=ROOT/parent['evidence_directory'];index=json.loads((evidence/'index.prepared.json').read_text())
    ledger=json.loads((ROOT/'experiments/arithmetic/backend_usage.json').read_text())
    if usage(ledger['entries'])['pending']:raise ValueError('cannot seal unsettled resource ledger')
    before=json.loads(gzip.decompress((parent_dir/'usage_before.json.gz').read_bytes()))
    receipts=json.loads(gzip.decompress((parent_dir/'receipts.json.gz').read_bytes()));known={r['id'] for r in receipts}
    for entry in ledger['entries'][len(before['entries']):]:
        if entry['id'] in known:continue
        record=json.loads(Path(entry['command_record']).read_text())
        receipts.append({'id':entry['id'],'record':record,'GNU_time':Path(record['gnu_time']).read_text()})
    compressed(evidence/'ledger.json.gz',ledger);compressed(evidence/'receipts.json.gz',receipts)
    shutil.copyfile(parent_dir/'usage_before.json.gz',evidence/'usage_before.json.gz')
    resources=json.loads((parent_dir/'resources.json').read_text())
    resources['cumulative_usage']=usage(ledger['entries']);resources['new_usage']=usage(ledger['entries'][len(before['entries']):])
    resources['checkpoint_note']='settled immutable prefix at interval successor seal; subsequent verification remains in live ledger'
    write(evidence/'resources.json',resources)
    current=set(parent['files_sha256'])
    current.update(str(p.relative_to(ROOT)) for p in (ROOT/'experiments/arithmetic_dse').glob('model_*interval*.py'))
    current.update({'experiments/arithmetic_dse/model_interval_successor.py','regression/arithmetic_model_interval_evaluation.py',
                    'regression/arithmetic_model_interval_native.py','regression/arithmetic_model_cycles.py',
                    'regression/arithmetic_backend.py',
                    'rtlzz/testv2/arithmetic_model_joint_test.cpp'})
    snapshots={}
    for name in current & MUTABLE_DOCUMENTATION:
        destination=evidence/'documentation-source'/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,destination)
        snapshots[name]=str(destination.relative_to(ROOT))
    index['files_sha256']={str(p.relative_to(evidence)):sha(p) for p in evidence.rglob('*') if p.is_file() and p.name not in ('index.json','index.prepared.json')}
    write(evidence/'index.json',index)
    preparation=json.loads((evidence/'preparation.json').read_text())
    frozen=copy.deepcopy(parent);frozen.update(completion_status='local_interval_learning_checkpoint_full_step7_incomplete',
        scope='qualified base models plus actual native template interval fitting/test status explicitly recorded; incomplete wide and other arithmetic domains retained',
        evidence_directory=str(evidence.relative_to(ROOT)),evidence_index_sha256=sha(evidence/'index.json'),
        files_sha256={name:sha(ROOT/name) for name in sorted(current)},source_snapshots=snapshots,
        full_step7_complete=False,main_matrix_authorized=False)
    frozen['interval_learning']={'platforms':preparation['platforms'],'independent_test_present':preparation['independent_test_present'],
                                'released_platforms':preparation['released_platforms'],'evidence_records':index['interval_training_evidence']}
    frozen['historical_freezes'][str((evidence/'parent-candidate.json').relative_to(ROOT))]=sha(evidence/'parent-candidate.json')
    frozen['historical_source_roots'].append(preparation['parent_source_root'])
    size=sum(p.stat().st_size for p in evidence.rglob('*') if p.is_file())
    if size>5*1024*1024 or max(p.stat().st_size for p in evidence.rglob('*') if p.is_file())>1024*1024:
        raise ValueError('successor package exceeds portable size ceilings; deduplicate before sealing')
    if args.freeze.exists():raise ValueError('never overwrite an existing freeze')
    write(args.freeze,frozen);print(json.dumps({'phase':'sealed','freeze':str(args.freeze),'package_bytes':size,'resources':resources['cumulative_usage']}))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['prepare','seal'])
    for name in ('evidence','parent-freeze','raw-archive','batch','fitting-data','fit-dir','base','test-data','test-result','release','native','cycle-receipt','freeze'):
        parser.add_argument('--'+name,type=Path,required=name=='evidence')
    args=parser.parse_args()
    required=('parent_freeze','raw_archive','batch','fitting_data','fit_dir','base') if args.action=='prepare' else ('freeze',)
    if any(getattr(args,name) is None for name in required):parser.error('missing required arguments: '+', '.join(required))
    if args.action=='prepare':prepare(args)
    else:seal(args)


if __name__=='__main__':main()
