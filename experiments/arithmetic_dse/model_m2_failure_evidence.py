"""Portable frozen numeric replay of the sealed first F4 primitive failure."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from .model_collection import sha,write
from .model_m2_evaluate import report,verify_result
from .model_m2_fit_v2 import quality


ROOT=Path(__file__).resolve().parents[2]


def read(path):return json.loads(Path(path).read_text())


def package(result_path,out):
    r=verify_result(result_path);selection=Path(r['selection_path']);f=read(selection);prior=Path(f['parent_fit_path']).parent
    if r['quality_status']!='failed':raise ValueError('failure archive requires actual failed independent result')
    out.mkdir(parents=True,exist_ok=False);objects={};docs={}
    def add(path):
        text=Path(path).read_text();h=hashlib.sha256(text.encode()).hexdigest();objects[h]=text;return h
    files={'selection':selection,'candidate':selection.parent/'candidate.json','validation':selection.parent/'fit-report.json',
        'fit-freeze':selection.parent/'fit-freeze.json','fitting-data':f['dataset_path'],'prior-candidate':prior/'candidate.json',
        'prior-validation':prior/'fit-report.json','prior-fit-freeze':prior/'fit-freeze.json','test-result':result_path,
        'test-data':r['dataset_path'],'test-consumption':selection.parent/'independent-evaluation-consumption.json',
        'publication':result_path.parent.parent/'primitive-publication-v1/publication.json',
        'fit-reproduction':selection.parent.parent/'primitive-refit-v2/reproduction.json',
        'fit-protocol':ROOT/'experiments/arithmetic_dse/configs/model_asap7_m2_fit_v2.json',
        'base-protocol':ROOT/'experiments/arithmetic_dse/configs/model_asap7_m2_fit_v1.json'}
    for name,path in files.items():docs[name]=add(path)
    for container,folder in ((f,selection.parent/'source'),(r,result_path.parent/'source')):
        for name,h in container['sources'].items():
            if add(folder/name)!=h:raise ValueError('changed archived numerical producer')
    data=read(r['dataset_path']);admissions={}
    for name,binding in data['admission_ancestry'].items():
        if add(binding['path'])!=binding['sha256']:raise ValueError('changed archived test admission')
        admissions[name]=binding['sha256'];a=read(binding['path'])
        for path,h in a['sources'].items():
            if add(Path(binding['path']).parent/'source'/path)!=h:raise ValueError('changed archived test source')
    manifests={}
    for run in data['runs']:
        d=Path(run['directory']);h=add(d/'manifest.json')
        if h!=run['manifest_sha256']:raise ValueError('changed audited test manifest')
        manifests[run['task_id']]=h
    pool=out/'numeric-and-provenance.json.gz'
    pool.write_bytes(gzip.compress(json.dumps(objects,ensure_ascii=False,separators=(',',':')).encode(),mtime=0))
    index={'version':'asap7-m2-primitives-failure-evidence-v1','quality_status':'failed','published':[],
        'documents':docs,'test_admissions':admissions,'test_manifests':manifests,'pool_sha256':sha(pool),
        'portable_scope':'frozen training/validation/test numeric labels, predictions, original gates and failed publication; source and manifest provenance',
        'external_scope':'full raw stage/SDC/QD/bank/area/LEC replay uses preserved original paths and the audited dataset producer',
        'test_labels_permanently_excluded_from_revision_fitting':True,'full_step7_complete':False,'verifier_sha256':sha(__file__)}
    write(out/'index.json',index)
    (out/'README.md').write_text('''# ASAP7 M2基础算子首轮独立失败封存

本包保存完整56项F4测试、488行阶段标签及冻结模型的数值评价，不是可发布模型。
grt／synth均8／12操作通过；失败来自逐操作错误可行预测门槛，发布清单为空。
F4及更早测试永久排除后继拟合、验证、算法／裕量选择。原门槛与冻结参数不追改。

便携数值核验：
`python3 -m experiments.arithmetic_dse.model_m2_failure_evidence verify --folder experiments/arithmetic/evidence/step7_m2_primitives_failure_v1`

本机完整外部回放：给上述命令增加`--external`。该模式重新读取全部56项原始报告／SDC／Q-D／银行／core面积／LEC和费用父链，不启动EDA。
便携包不含ODB、AIG二进制或完整物理日志，不将数值回放冒称重新执行SAT证明。
''')
    print(json.dumps({'status':'packaged','bytes':pool.stat().st_size,'documents':len(objects),'test_tasks':len(manifests)}))


def verify(folder,external=False):
    index=read(folder/'index.json');pool=folder/'numeric-and-provenance.json.gz'
    if sha(pool)!=index['pool_sha256']:raise ValueError('changed failure evidence pool')
    objects=json.loads(gzip.decompress(pool.read_bytes()))
    for h,text in objects.items():
        if hashlib.sha256(text.encode()).hexdigest()!=h:raise ValueError('changed pooled document')
    docs=index['documents'];obj=lambda name:json.loads(objects[docs[name]])
    f=obj('selection');r=obj('test-result');candidate=obj('candidate');fit=obj('fitting-data');test=obj('test-data')
    for name,key in (('candidate','candidate_sha256'),('validation','fit_report_sha256'),('fitting-data','dataset_sha256')):
        if docs[name]!=f[key]:raise ValueError('changed frozen fitting identity')
    if docs['selection']!=r['selection_sha256'] or docs['test-data']!=r['dataset_sha256']:raise ValueError('changed independent inputs')
    if len(test['runs'])!=56 or len(test['rows'])!=488 or len({v['id'] for v in test['rows']})!=488:raise ValueError('incomplete independent cohort')
    if any(x['split'] not in ('train','validation') for x in fit['rows']) or any(x['split']!='test' for x in test['rows']):raise ValueError('data role contamination')
    if {v['source_sha256'] for v in fit['rows']}&{v['source_sha256'] for v in test['rows']}:raise ValueError('source crossed independent boundary')
    for stage,value in candidate['stages'].items():
        for op,model in value['operations'].items():
            rows=[v for v in fit['rows'] if v['stage']==stage and v['operation']==op and v['split']=='validation']
            for quantity in ('delay','area'):
                if quality(rows,model[quantity],quantity)!=obj('validation')['stages'][stage]['operations'][op][quantity]['quality']:
                    raise ValueError('validation does not recompute')
    actual=report(test['rows'],candidate)
    if actual!=r['stages'] or actual['grt']['status']!='failed' or obj('publication')['published'] or index['published']:
        raise ValueError('failed independent verdict does not recompute')
    for container in (f,r):
        if any(h not in objects for h in container['sources'].values()):raise ValueError('missing executed numerical sources')
    for run in test['runs']:
        if index['test_manifests'][run['task_id']]!=run['manifest_sha256']:raise ValueError('changed audited test manifest')
    if external:
        import tempfile
        from .model_m2_evaluate import extract
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'replayed.json';extract(Path(test['admission_path']).parent,path)
            if read(path)!=test:raise ValueError('external raw test replay differs')
    print(json.dumps({'status':'verified','quality_status':'failed','test_tasks':56,'test_rows':488,'external':external}))
    return index


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['package','verify'])
    ap.add_argument('--result',type=Path);ap.add_argument('--folder',type=Path,required=True);ap.add_argument('--external',action='store_true');a=ap.parse_args()
    if a.action=='package':package(a.result.resolve(),a.folder.resolve())
    else:verify(a.folder.resolve(),a.external)


if __name__=='__main__':main()
