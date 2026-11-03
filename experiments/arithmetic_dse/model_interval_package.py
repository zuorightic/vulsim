"""Extend an unpublished step-seven candidate with replayable interval bytes.

Keep the prior raw archive immutable. This command only copies existing runs,
graphs, mechanism fixtures and a fresh functional receipt; it launches no EDA.
The administrative candidate seal follows this preparation separately.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from .model_collection import sha,write

ROOT=Path(__file__).resolve().parents[2]


def prepare(build,evidence,raw_archive,functional):
    if (ROOT/'experiments/arithmetic/offline_model_freeze_v1.json').exists():raise ValueError('published evidence needs a new revision')
    raw_archive.mkdir(parents=True,exist_ok=False);index=json.loads((evidence/'index.json').read_text());known={}
    for part in index['text_pool_parts']:known.update(json.loads(gzip.decompress((evidence/part['file']).read_bytes())))
    objects={};raw={}
    def blob(path,pool):
        text=Path(path).read_bytes().decode('utf-8');h=hashlib.sha256(text.encode()).hexdigest();pool[h]=text;return h
    def document(name,path):
        h=blob(path,objects);index['documents'][name]=h;return h
    catalog=[];large=[]
    for folder in ('native-interval-asap7-v3','native-interval-asap7-v4'):
        for manifest in sorted((build/folder/'runs').glob('*/manifest.json')):
            directory=manifest.parent;files={'manifest.json':blob(manifest,raw)}
            for name in ('input.sv','sample-contract.json','liberty_cells.json','effective-environment.txt','abc_constraints.txt','abc_speed_target.script','config.mk'):
                p=directory/name
                if p.is_file():files[name]=blob(p,raw)
            for subdir in ('source','reports'):
                for p in sorted((directory/subdir).rglob('*')):
                    if p.is_file() and (subdir!='reports' or p.name.startswith('vulsim_')):files[str(p.relative_to(directory))]=blob(p,raw)
            for p in sorted((directory/'results').rglob('*.sdc')):files[str(p.relative_to(directory))]=blob(p,raw)
            for p in sorted(directory.rglob('*')):
                if p.is_file() and 'flow-scripts' not in p.relative_to(directory).parts and p.suffix in ('.odb','.spef','.v','.log'):
                    large.append({'path':str(p.relative_to(ROOT)),'size':p.stat().st_size,'sha256':sha(p)})
            catalog.append({'original_directory':str(directory.relative_to(ROOT)),'files':files})
    encoded=json.dumps(catalog,separators=(',',':'));catalog_hash=hashlib.sha256(encoded.encode()).hexdigest();raw[catalog_hash]=encoded
    def parts(directory,prefix,pool):
        result=[];group={};size=0
        def flush():
            if not group:return
            name=prefix+str(len(result)).zfill(3)+'.json.gz';p=directory/name
            p.write_bytes(gzip.compress((json.dumps(group,separators=(',',':'))+'\n').encode(),mtime=0))
            if p.stat().st_size>1024*1024:raise ValueError('interval evidence part exceeds file ceiling')
            result.append({'file':name,'sha256':sha(p),'objects':len(group)})
        for h,text in sorted(pool.items()):
            if group and size+len(text.encode())>700000:flush();group={};size=0
            group[h]=text;size+=len(text.encode())
        flush();return result
    write(raw_archive/'index.prepared.json',{'text_pool_parts':parts(raw_archive,'text-',raw),'run_catalog':catalog_hash})
    (raw_archive/'local_artifacts.json.gz').write_bytes(gzip.compress((json.dumps(large)+'\n').encode(),mtime=0))
    note={'version':'model-interval-run-summary-v1','full_archive':str(raw_archive.relative_to(ROOT)),
        'full_archive_sha256':hashlib.sha256(b''.join(sorted(p.read_bytes() for p in raw_archive.rglob('*') if p.is_file()))).hexdigest(),
        'excluded_from_fitting':'all five initial v1 pilots; retained only for failure/measurement history',
        'current_training_runs':2,'no_independent_test_run_or_label_added':True}
    note_path=raw_archive.parent/(raw_archive.name+'-summary.json');write(note_path,note);document('interval-run-summary.json',note_path)
    graphs={}
    for p in sorted((build/'interval-native-graphs-v3').glob('*.json')):
        name='native-interval-graphs/'+p.name;document(name,p);graphs[p.name]=name
    document('interval-native-functional-regression.json',functional)
    admission=build/'native-interval-asap7-v4/admission.json';document('native-interval-admission-v2.json',admission)
    document('native-interval-pilot-labels-v2.json',build/'native-interval-pilot-labels-v2.json')
    bundles={}
    for p in sorted((build/'native-interval-asap7-v4/runs').glob('*/manifest.json')):
        bundles[p.parent.name]={'contract':blob(p.parent/'sample-contract.json',objects),'rtl':blob(p.parent/'input.sv',objects)}
    pairs=[]
    for platform in ('asap7','nangate45','sky130hd','gf180'):
        folder=build/'interval-joint-native-v2';d='interval-joint-native-v2/'+platform+'.report.json';c='interval-joint-native-v2/'+platform+'.C.report.json'
        document(d,folder/(platform+'.report.json'));document(c,folder/(platform+'.C.report.json'))
        model='interval-mechanism-fixtures-v3/'+platform+'.json';document(model,build/model)
        rtl=blob(folder/(platform+'.sv'),objects)
        if any(r['report']==d for r in index['native_reports']):raise ValueError('mechanism report already registered; use a fresh evidence revision')
        index['native_reports'].append({'report':d,'model':model,'rtl':rtl,'evidence_role':'TEST_ONLY_mechanism; not fitted quality or physical benefit'})
        pairs.append({'D':d,'C':c})
    for name,relative in [('model_mul_intervals.py','model_mul_intervals.py'),('model_mul_interval_fit.py','model_mul_interval_fit.py'),
        ('model_mul_interval_protocol.json','configs/model_mul_intervals_v2.json'),('model_mul_interval_labels.json','configs/model_mul_interval_labels_v1.json')]:
        index['text_files'][name]=blob(ROOT/'experiments/arithmetic_dse'/relative,objects)
    index['interval_evidence']={'graphs':graphs,'functional':'interval-native-functional-regression.json',
        'admission':'native-interval-admission-v2.json','dataset':'native-interval-pilot-labels-v2.json','bundles':bundles,'mechanism_pairs':pairs}
    index['text_pool_parts']+=parts(evidence,'text-interval-integrity-v1-',{h:t for h,t in objects.items() if h not in known})
    index['files_sha256']={str(p.relative_to(evidence)):sha(p) for p in evidence.rglob('*') if p.is_file() and p.name!='index.json'}
    write(evidence/'index.json',index)
    print({'additional_raw_runs':len(catalog),'mechanism_platforms':len(pairs),'native_graphs':len(graphs),'new_portable_objects':len(set(objects)-set(known)),
        'package_bytes':sum(p.stat().st_size for p in evidence.rglob('*') if p.is_file()),'phase':'prepared; candidate not sealed or published'})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--raw-archive',type=Path,required=True);p.add_argument('--functional',type=Path,required=True);a=p.parse_args()
    prepare(a.build.resolve(),a.evidence.resolve(),a.raw_archive.resolve(),a.functional.resolve())
