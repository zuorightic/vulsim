"""Portable raw-label and frozen numerical replay for the sealed F5 verdict."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import tempfile

from .budget import Ledger,usage
from .model_collection import sha,write
from .model_features import features
from .model_m2_f5_evaluate import report,verify_result,extract as external_extract
from .model_m2_fit_v4 import quality

ROOT=Path(__file__).resolve().parents[2]
SUFFIX=Path('asap7/arithmetic_probe/base')


def read(path):return json.loads(Path(path).read_text())


class Pool:
    def __init__(self,out):self.out=out;self.seen=set();self.objects={};self.size=0;self.parts=[]
    def add(self,path):
        text=Path(path).read_text();h=hashlib.sha256(text.encode()).hexdigest()
        if h not in self.seen:
            self.seen.add(h);self.objects[h]=text;self.size+=len(text.encode())
            if self.size>=32*1024**2:self.flush()
        return h
    def flush(self):
        if not self.objects:return
        path=self.out/f'text-{len(self.parts):03d}.json.gz'
        path.write_bytes(gzip.compress(json.dumps(self.objects,ensure_ascii=False,separators=(',',':')).encode(),mtime=0))
        self.parts.append({'file':path.name,'sha256':sha(path),'bytes':path.stat().st_size});self.objects={};self.size=0


def package(result_path,publication,out):
    from .model_m2_collection import run_directory
    r=verify_result(result_path);selection=Path(r['selection_path']);f=read(selection);data=read(r['dataset_path']);fit=read(f['dataset_path'])
    out.mkdir(parents=True,exist_ok=False);pool=Pool(out);docs={}
    paths={'selection':selection,'candidate':selection.parent/'candidate.json','validation':selection.parent/'fit-report.json',
        'fitting-data':f['dataset_path'],'test-data':r['dataset_path'],'test-result':result_path,'publication':publication/'publication.json',
        'test-consumption':selection.parent/'independent-F5-evaluation-consumption.json',
        'test-admission':data['admission_path'],'fit-reproduction':selection.parent.parent/'primitive-refit-v4/reproduction.json',
        'parent-F4-evidence-index':ROOT/'experiments/arithmetic/evidence/step7_m2_primitives_failure_v1/index.json'}
    for name,path in paths.items():docs[name]=pool.add(path)
    for item in read(publication/'publication.json')['published']:docs['released-model']=pool.add(publication/item['file'])
    fit_freezes=[];path=selection
    while path:
        frozen=read(path);fit_freezes.append(pool.add(path))
        for name,h in frozen['sources'].items():
            if pool.add(path.parent/'source'/name)!=h:raise ValueError('changed archived fit source')
        for name in ('candidate.json','fit-report.json'):pool.add(path.parent/name)
        if path.parent.name=='primitive-fit-v4':
            refit=path.parent.parent/'primitive-refit-v4'
            for name in ('candidate.json','fit-report.json'):
                if (refit/name).read_bytes()!=(path.parent/name).read_bytes():raise ValueError('actual v4 reproduction changed')
                pool.add(refit/name)
        path=Path(frozen['parent_fit_path']) if frozen.get('parent_fit_path') else None
    for name,h in r['sources'].items():
        if pool.add(result_path.parent/'source'/name)!=h:raise ValueError('changed archived evaluation source')
    admissions={}
    for name,v in data['admission_ancestry'].items():
        if pool.add(v['path'])!=v['sha256']:raise ValueError('changed F5 admission')
        admissions[name]=v['sha256'];a=read(v['path'])
        for source,h in a['sources'].items():
            if pool.add(Path(v['path']).parent/'source'/source)!=h:raise ValueError('changed archived F5 source')
    plan=read(f['plan_path']);docs['plan']=pool.add(f['plan_path'])
    recovered=read(fit['recovery_admission_path']);docs['fit-recovery-admission']=pool.add(fit['recovery_admission_path'])
    overrides={i['task']['id']:Path(fit['recovery_admission_path']).parent/'runs'/i['task']['id'] for i in recovered['tasks']}
    tasks=[(t,overrides.get(t['id'],run_directory(Path(f['plan_path']).parent,t))) for t in plan['tasks'] if t['split'] in ('train','validation')]
    test_tasks={t['id']:t for t in read(data['admission_path'])['tasks']}
    tasks.extend((test_tasks[v['task_id']],Path(v['directory'])) for v in data['runs'])
    catalog=[];charged=set();external={}
    for t,d in tasks:
        m=read(d/'manifest.json');files={};charged.update(c['budget_reservation_id'] for c in m['commands'])
        selected=[d/name for name in ('manifest.json','input.sv','sample-contract.json','liberty_cells.json')]
        for stage in m['metrics']:
            prefix=d/'reports'/SUFFIX/('vulsim_'+stage['stage'])
            selected+=sorted(p for p in prefix.parent.glob(prefix.name+'*') if p.is_file())
            selected.append(d/'results'/SUFFIX/({'synth':'1_synth','grt':'5_1_grt'}[stage['stage']]+'.sdc'))
        if t['split']=='test':
            proof=d/'logs'/SUFFIX/'structural_cec'
            selected += [p for p in proof.iterdir() if p.is_file() and (p.name in ('proof.json','state-correspondence.json','complete-boundary.json') or p.suffix=='.log')]
        for path in selected:
            name=str(path.relative_to(d));h=pool.add(path);files[name]=h
            if name in m['evidence_sha256'] and m['evidence_sha256'][name]!=h:raise ValueError('changed raw stage evidence')
        catalog.append({'task':t,'files':files,'external_directory':str(d),'external_artifacts':m['evidence_sha256']})
        external[str(d/'manifest.json')]=sha(d/'manifest.json')
    # Include paid recovery ancestors, without pretending their incomplete
    # physical stages supply usable independent labels.
    for directory in data['physical_ancestry']:
        path=Path(directory)/'manifest.json';m=read(path);pool.add(path)
        charged.update(c['budget_reservation_id'] for c in m['commands']);external[str(path)]=sha(path)
    ledger=read(Ledger().path);entries=[e for e in ledger['entries'] if e['id'] in charged]
    if len(entries)!=len(charged) or any(e['status']=='reserved' for e in entries):raise ValueError('unsettled consumed evidence charges')
    cost=out/'consumed-run-ledger.json';write(cost,{'entries':entries,'usage':usage(entries),'scope':'consumed224 measurements and F5 mapped/checkpoint ancestors; includes charged failures, no walltime stitching or concurrency discount'})
    docs['consumed-run-ledger']=pool.add(cost)
    # The replay implementation is distinct from the archived executed producer.
    replay={}
    for path in sorted(Path(__file__).parent.glob('*.py')):replay[str(path.relative_to(ROOT))]=pool.add(path)
    for path in sorted((Path(__file__).parent/'configs').rglob('*.json')):replay[str(path.relative_to(ROOT))]=pool.add(path)
    pool.flush()
    index={'version':'asap7-m2-F5-evidence-v1','quality_status':r['quality_status'],'full_D_ready':False,'full_step7_complete':False,
        'documents':docs,'fit_freezes':fit_freezes,'test_admissions':admissions,'runs':catalog,'text_pool_parts':pool.parts,
        'external_manifest_sha256':external,'replay_code':replay,'verifier_sha256':sha(__file__),
        'portable_scope':'all224 fitted/test measurements,448 raw stages and1952 rows; frozen validation and one-shot F5 numerical verdict; original proof logs and provenance',
        'external_scope':'all original raw artifacts and complete stored CEC inputs/proofs by hash; never a new SAT/EDA run',
        'parent_F4_evidence_sha256':docs['parent-F4-evidence-index'],'independent_labels_excluded_from_revision_fitting':True}
    write(out/'index.json',index)
    write(out/'summary.json',{'quality_status':r['quality_status'],'published':read(publication/'publication.json')['published'],
        'stages':{s:{k:v for k,v in val.items() if k not in ('operations','ranking')} for s,val in r['stages'].items()},
        'failed_operations':{s:{op:{'delay':v['delay'],'area':v['area']} for op,v in val['operations'].items() if v['status']=='failed'} for s,val in r['stages'].items()}})
    (out/'README.md').write_text('''# ASAP7 M2 F5独立评价封存

本包记录冻结v4模型在新F5五银行／源上下文的原门槛评价。发布范围以publication和summary为准；不表示完整D或步骤七完成。

便携核验：`python3 -m experiments.arithmetic_dse.model_m2_f5_evidence verify --folder experiments/arithmetic/evidence/step7_m2_F5_v1`

本机原始产物核验：上述命令增加`--external`。两种模式均不启动EDA；便携模式回放224份测量的原始文本阶段／SDC／Q-D／银行／core面积及冻结质量，external另核对原始大产物及已存完整CEC。便携模式不重新执行SAT，也不要求安装原工具／库。

F4和F5独立标签均封存，不能回填后续拟合、验证、算法或裕量选择。模型、质量门槛、目标和数据划分不追改。
''')
    print(json.dumps({'status':'packaged','runs':len(catalog),'parts':len(pool.parts),'bytes':sum(v['bytes'] for v in pool.parts),'quality_status':r['quality_status']}),flush=True)


def load_pool(folder,index):
    objects={}
    for part in index['text_pool_parts']:
        path=folder/part['file']
        if sha(path)!=part['sha256']:raise ValueError('changed F5 evidence pool')
        for h,text in json.loads(gzip.decompress(path.read_bytes())).items():
            if h in objects or hashlib.sha256(text.encode()).hexdigest()!=h:raise ValueError('changed pooled F5 text')
            objects[h]=text
    return objects


def verify(folder,external=False):
    from .backend import stage_metrics
    from .model_samples import read_labels as labels4,verify_capture_banks as banks4
    from .model_m2_labels5 import read_labels as labels5,verify_capture_banks as banks5
    from .sdc import verify_sdc,rtl_ports
    index=read(folder/'index.json');objects=load_pool(folder,index);docs=index['documents'];obj=lambda name:json.loads(objects[docs[name]])
    frozen=obj('selection');candidate=obj('candidate');validation=obj('validation');fit=obj('fitting-data');test=obj('test-data');result=obj('test-result')
    for name,key in (('candidate','candidate_sha256'),('validation','fit_report_sha256'),('fitting-data','dataset_sha256')):
        if docs[name]!=frozen[key]:raise ValueError('changed portable fit identity')
    if result['selection_sha256']!=docs['selection'] or result['dataset_sha256']!=docs['test-data']:raise ValueError('changed portable independent inputs')
    for h in index['fit_freezes']:
        f=json.loads(objects[h])
        if f['candidate_sha256'] not in objects or f['fit_report_sha256'] not in objects or any(v not in objects for v in f['sources'].values()):raise ValueError('incomplete executed fit sources')
        if f.get('parent_fit_sha256') and f['parent_fit_sha256'] not in objects:raise ValueError('broken fit parent chain')
    rows=fit['rows']+test['rows'];by_manifest={}
    for row in rows:by_manifest.setdefault(row['manifest_sha256'],[]).append(row)
    if len(index['runs'])!=224 or len(rows)!=1952 or len({r['id'] for r in rows})!=1952:raise ValueError('incomplete224 measurement scope')
    if any(r['split'] not in ('train','validation') for r in fit['rows']) or any(r['split']!='test' for r in test['rows']):raise ValueError('data role contamination')
    if {r['source_sha256'] for r in fit['rows']}&{r['source_sha256'] for r in test['rows']}:raise ValueError('F5 crossed fitting source partition')
    for run in index['runs']:
        files=run['files'];m=json.loads(objects[files['manifest.json']]);t=run['task'];contract=json.loads(objects[files['sample-contract.json']]);cells=json.loads(objects[files['liberty_cells.json']])['cells']
        if m['status']!='completed' or m['task_id']!=t['id'] or files['input.sv']!=t['rtl_sha256'] or files['sample-contract.json']!=t['sample_contract_sha256']:
            raise ValueError('changed portable measurement source')
        consumed=by_manifest[files['manifest.json']];specs={s['id']:s for s in contract['labels']}
        labels_reader,banks_reader=(labels5,banks5) if t['split']=='test' else (labels4,banks4)
        with tempfile.TemporaryDirectory() as td:
            d=Path(td)
            for name,h in files.items():
                if name in m['evidence_sha256'] and m['evidence_sha256'][name]!=h:raise ValueError('portable raw hash differs from manifest')
                path=d/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(objects[h])
            for stored in m['metrics']:
                stage=stored['stage'];reports=d/'reports'/SUFFIX;prefix=reports/('vulsim_'+stage);parsed=stage_metrics(reports,stage,cells,m['period_ps'],selected=m['platform_profile'])
                if any(v!=stored[k] for k,v in parsed.items() if k!='raw_reports_prefix'):raise ValueError('portable raw stage replay differs')
                labels=labels_reader(prefix,d/'sample-contract.json',parsed['raw_report_units']['time']['to_ps']);banks=banks_reader(prefix,d/'sample-contract.json',cells)
                if labels!=stored['model_labels'] or banks!=stored.get('model_capture_banks',{}):raise ValueError('portable QD or bank replay differs')
                sdc=d/'results'/SUFFIX/({'synth':'1_synth','grt':'5_1_grt'}[stage]+'.sdc')
                verify_sdc(sdc.read_text(),m['platform_profile'],t['period_ps'],rtl_ports((d/'input.sv').read_text(),t['top']))
                instances=[line.split('\t')[:2] for line in Path(str(prefix)+'_instances.tsv').read_text().splitlines()];label_by_id={v['id']:v for v in labels}
                for r in (v for v in consumed if v['stage']==stage):
                    s=specs[r['spec']['id']];label=label_by_id[s['id']]
                    expected_f=features(s['lhs_width'],s['rhs_width'],s['result_width'],s['fanout'],1500,t['period_ps'])
                    area=sum(cells[master]['area_um2'] for name,master in instances if master in cells and not cells[master]['sequential'] and name.startswith(s['arithmetic_scope']))
                    if (r['spec']!=s or r['features']!=expected_f or r['delay_ps']!=label['data_delay_ps'] or r['comb_area_um2']!=area
                        or r['bank_counts']!=banks.get(s['id']) or r['source_sha256']!=files['input.sv'] or r['split']!=t['split']
                        or r['observed_H_ps']!=t['period_ps']-label['data_delay_ps']-label['slack_ps'] or r['path_slack_ps']!=label['slack_ps']
                        or r['whole_setup_slack_ps']!=stored['setup_worst_slack_ps']):raise ValueError('portable raw label/feature differs')
        if external:
            d=Path(run['external_directory'])
            if sha(d/'manifest.json')!=files['manifest.json']:raise ValueError('changed external F5 evidence manifest')
            for name,h in run['external_artifacts'].items():
                if sha(d/name)!=h:raise ValueError('changed external raw artifact')
    for stage,value in candidate['stages'].items():
        for op,model in value['operations'].items():
            selected=[r for r in fit['rows'] if r['stage']==stage and r['operation']==op and r['split']=='validation']
            for q in ('delay','area'):
                if quality(selected,model[q],q)!=validation['stages'][stage]['operations'][op][q]['quality']:raise ValueError('frozen validation does not recompute')
    actual=report(test['rows'],candidate)
    if actual!=result['stages'] or actual['grt']['status']!=index['quality_status']:raise ValueError('F5 independent verdict does not recompute')
    publication=obj('publication')
    if publication['quality_status']!=result['quality_status'] or (bool(publication['published'])!=(result['quality_status']=='passed')):raise ValueError('publication not consistent with mandatory gates')
    if result['quality_status']=='passed':
        published=json.loads(objects[docs['released-model']]);original=json.loads(objects[docs['candidate']])
        for op,value in original['stages']['grt']['operations'].items():
            deployed=published['stages']['grt']['operations'][op]
            if any(value[k]!=deployed[k] for k in ('delay','area','joint_domain')):raise ValueError('publication changed frozen numbers/domain')
    entries=obj('consumed-run-ledger')['entries'];charges={e['id']:e for e in entries}
    if usage(entries)!=obj('consumed-run-ledger')['usage'] or any(e['status']=='reserved' for e in entries):raise ValueError('invalid settled resource evidence')
    for run in index['runs']:
        m=json.loads(objects[run['files']['manifest.json']])
        for c in m['commands']:
            e=charges[c['budget_reservation_id']]
            if e['command']!=c['command'] or e['status']!='completed' or c['exit_code'] or c['cleanup']['remaining_live_pids']:raise ValueError('missing paid successful stage')
    if external:
        for path,h in index['external_manifest_sha256'].items():
            if sha(path)!=h:raise ValueError('changed external ancestor')
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'test-replayed.json';external_extract(Path(test['admission_path']).parent,path)
            if read(path)!=test:raise ValueError('full external F5 replay differs')
    print(json.dumps({'status':'verified','quality_status':result['quality_status'],'runs':224,'stages':448,'rows':1952,'external':external}),flush=True)
    return index


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['package','verify'])
    ap.add_argument('--result',type=Path);ap.add_argument('--publication',type=Path);ap.add_argument('--folder',type=Path,required=True);ap.add_argument('--external',action='store_true');a=ap.parse_args()
    if a.action=='package':package(a.result.resolve(),a.publication.resolve(),a.folder.resolve())
    else:verify(a.folder.resolve(),a.external)


if __name__=='__main__':main()
