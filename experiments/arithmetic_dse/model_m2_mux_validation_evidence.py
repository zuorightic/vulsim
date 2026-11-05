"""Small numerical checkpoint for Mux fitting failure before independent tests."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import tempfile

from .model_collection import sha,write
from .model_m2_fit_v4 import predict,quality,target_key


def read(path):return json.loads(Path(path).read_text())


def package(root,out):
    out.mkdir(parents=True,exist_ok=False);objects={};docs={}
    def add(path):
        text=Path(path).read_text();h=hashlib.sha256(text.encode()).hexdigest();objects[h]=text;return h
    files={'data':root/'mux-fitting-data-v1.json','admission':root/'mux-context-v1/admission.json','inherited11':root/'mux-context-v1/inherited11.json',
        'protocol':Path(__file__).with_name('configs')/'model_asap7_m2_mux_context_v1.json',
        'selector-protocol':Path(__file__).with_name('configs')/'model_asap7_m2_mux_fit_selection_v2.json',
        'finite-pool':root/'mux-candidate-feasibility-v1/pool.json','other-levels':root/'mux-candidate-feasibility-v1/other-levels-summary.json'}
    for v in (1,2):
        folder=root/f'mux-fit-v{v}';f=read(folder/'fit-freeze.json')
        for name in ('candidate.json','fit-report.json','fit-freeze.json'):files[f'v{v}/'+name]=folder/name
        files[f'v{v}/reproduction.json']=root/f'mux-refit-v{v}/reproduction.json'
        for name,h in f['sources'].items():
            if add(folder/'source'/name)!=h:raise ValueError('changed frozen Mux fitting source')
        for name in ('candidate.json','fit-report.json'):
            if (root/f'mux-refit-v{v}'/name).read_bytes()!=(folder/name).read_bytes():raise ValueError('Mux reproduction bytes differ')
    for name,path in files.items():docs[name]=add(path)
    pool=out/'numerical-checkpoint.json.gz';pool.write_bytes(gzip.compress(json.dumps(objects,ensure_ascii=False,separators=(',',':')).encode(),mtime=0))
    write(out/'index.json',{'version':'asap7-m2-mux-validation-failure-v1','documents':docs,'pool_sha256':sha(pool),'quality_status':'failed_validation',
        'independent_tasks_consumed':0,'independent_tasks_locked':48,'unchanged_qualified_components':11,'verifier_sha256':sha(__file__),
        'scope':'eligible fitting numbers, frozen candidate/validation/reproduction and finite-pool diagnosis; original raw audit remains hash-bound in local dataset, no portable SAT claim'})
    (out/'README.md').write_text('''# Mux训练／验证未通过检查点

120个新train／validation任务全部完成，768行合法拟合标签已回放；48个新独立任务仍锁定，没有消费。
首版grt P95为79.0365%，原候选池整类选择后为79.0148%，都超过原75%门槛；synth和面积通过，11类固定资格保持。
本包只回放冻结数值与有限候选池诊断，不冒称独立测试完成、原始大产物便携回放或完整D就绪。

`python3 -m experiments.arithmetic_dse.model_m2_mux_validation_evidence verify --folder experiments/arithmetic/evidence/step7_m2_mux_validation_v1`

增加`--external`从本机原始产物重新提取全部合法train／validation与分路径观测，不启动EDA，不读取旧独立Mux标签。
''')
    print(json.dumps({'status':'packaged','bytes':pool.stat().st_size,'documents':len(objects),'independent_tasks_consumed':0}),flush=True)


def verify(folder,external=False):
    index=read(folder/'index.json');path=folder/'numerical-checkpoint.json.gz'
    if sha(path)!=index['pool_sha256']:raise ValueError('changed Mux validation checkpoint')
    objects=json.loads(gzip.decompress(path.read_bytes()))
    for h,text in objects.items():
        if hashlib.sha256(text.encode()).hexdigest()!=h:raise ValueError('changed pooled fitting text')
    docs=index['documents'];obj=lambda n:json.loads(objects[docs[n]]);d=obj('data');inherit=obj('inherited11')
    if (len(d['rows'])!=768 or any(r['split'] not in ('train','validation') for r in d['rows']) or d['old_independent_mux_labels_read']
        or d['new_independent_labels_read'] or 'mux' in inherit['operations'] or len(inherit['operations'])!=11):raise ValueError('Mux fitting/test role violation')
    for v in (1,2):
        f=obj(f'v{v}/fit-freeze.json');c=obj(f'v{v}/candidate.json');r=obj(f'v{v}/fit-report.json')
        if f['dataset_sha256']!=docs['data'] or f['candidate_sha256']!=docs[f'v{v}/candidate.json'] or f['fit_report_sha256']!=docs[f'v{v}/fit-report.json']:
            raise ValueError('changed frozen fitting inputs')
        if any(h not in objects for h in f['sources'].values()):raise ValueError('missing executed fitter source')
        for op,value in inherit['operations'].items():
            if c['stages']['grt']['operations'][op]!=value['model']:raise ValueError('inherited11 altered')
        for stage,entry in c['stages'].items():
            rows=[row for row in d['rows'] if row['stage']==stage and row['split']=='validation'];model=entry['operations']['mux']
            for q in ('delay','area'):
                if quality(rows,model[q],q)!=r['stages'][stage]['mux'][q]['quality']:raise ValueError('frozen Mux quality does not recompute')
        if f['grt_validation_ready'] or obj(f'v{v}/reproduction.json')['status']!='passed':raise ValueError('wrong validation or reproduction verdict')
    val=[r for r in d['rows'] if r['stage']=='grt' and r['split']=='validation'];minimum=0
    for component,options in obj('finite-pool')['pools'].items():
        rows=[r for r in val if target_key(r)==component];counts=[]
        for option in options:
            errors=[abs(predict(option['model'],r,'delay')-r['delay_ps'])/max(1.5,r['delay_ps']) for r in rows]
            if errors!=option['relative_errors'] or sum(e>.75 for e in errors)!=option['bad75']:raise ValueError('finite candidate count differs')
            counts.append(option['bad75'])
        minimum+=min(counts)
    if minimum!=obj('finite-pool')['minimum_total_bad75'] or minimum!=13:raise ValueError('finite registered candidate lower bound differs')
    if external:
        from .model_m2_mux_fit import extract
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'replayed.json';extract(Path(d['admission_path']).parent,out)
            if read(out)!=d:raise ValueError('external fitting replay differs')
    print(json.dumps({'status':'verified','quality_status':'failed_validation','rows':768,'new_fitting_tasks':120,
        'independent_tasks_consumed':0,'registered_width_target_minimum_bad75':minimum,'external':external}),flush=True)
    return index


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['package','verify']);ap.add_argument('--root',type=Path)
    ap.add_argument('--folder',type=Path,required=True);ap.add_argument('--external',action='store_true');a=ap.parse_args()
    if a.action=='package':package(a.root.resolve(),a.folder.resolve())
    else:verify(a.folder.resolve(),a.external)


if __name__=='__main__':main()
