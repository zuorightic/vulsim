"""Portable raw-label and frozen-decision replay for target/load interval models."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
import math
from pathlib import Path
import tempfile
import os
import subprocess
import sys

from .backend import stage_metrics
from .model_samples import read_labels,verify_capture_banks
from .sdc import verify_sdc,rtl_ports
from .model_target_features import features,infer
from .model_mul_intervals import interval,key
from .model_target_fit import quality,test_report
from .model_target_collection import CONFIG,read
from .model_target_collection import selected_tasks,run_directory,measurement_context
from .budget import Ledger,usage,cpu_seconds
from .model_collection import sha,write


def digest(text):return hashlib.sha256(text.encode()).hexdigest()


class PoolWriter:
    def __init__(self,out):
        self.out=out;self.seen=set();self.objects={};self.size=0;self.parts=[]
    def add(self,path):
        text=Path(path).read_text();h=digest(text)
        if h not in self.seen:
            self.seen.add(h);self.objects[h]=text;self.size+=len(text.encode())
            if self.size>=32*1024**2:self.flush()
        return h
    def flush(self):
        if not self.objects:return
        name=f'text-{len(self.parts):03d}.json.gz';path=self.out/name
        path.write_bytes(gzip.compress(json.dumps(self.objects,ensure_ascii=False,separators=(',',':')).encode(),mtime=0))
        self.parts.append({'file':name,'sha256':sha(path),'bytes':path.stat().st_size})
        self.objects={};self.size=0


def package(selection,result,release,out,native=None):
    from .model_target_fit import verify_test
    verified=verify_test(result);f=read(selection);plan=read(f['plan_path']);ref=read(plan['reference_path'])
    out.mkdir(parents=True,exist_ok=False);pool=PoolWriter(out)
    docs={}
    for name,path in [('protocol',CONFIG),('plan',f['plan_path']),('reference',plan['reference_path']),('selection',selection),
                      ('fit-data',f['dataset_path']),('candidate',selection.parent/'candidate.json'),('fit-report',selection.parent/'fit-report.json'),
                      ('test-data',verified['dataset_path']),('test-result',result),('test-consumption',selection.parent/'independent-test-consumption.json'),
                      ('release',release/'release.json')]:docs[name]=pool.add(path)
    released=read(release/'release.json')['published']
    for item in released:docs['released-model']=pool.add(release/item['file'])
    for a,folder,key in [(plan,Path(plan['source_snapshot']),'sources'),(f,selection.parent/'training-source','training_sources')]:
        for name,h in a[key].items():
            if pool.add(folder/name)!=h:raise ValueError('changed frozen source snapshot')
    if plan.get('predecessor'):
        docs['predecessor-plan']=pool.add(plan['predecessor']['plan_path'])
        if docs['predecessor-plan']!=plan['predecessor']['plan_sha256']:raise ValueError('changed predecessor plan')
    # Reference generation is bound to actual old TRAIN measurements only.
    old=read(ref['admission_path']);docs['reference-admission']=pool.add(ref['admission_path'])
    docs['reference-fitting-data']=pool.add(ref['dataset_path'])
    tasks=[];folder=Path(f['plan_path']).parent
    used={r['task_id'] for name in ('fit-data','test-data') for r in read(f['dataset_path'] if name=='fit-data' else verified['dataset_path'])['rows']}
    for t in plan['tasks']:
        if t['id'] in used:tasks.append((run_directory(folder,t),t,'target_load'))
    for t in old['tasks']:
        if t['split']=='train':tasks.append((Path(ref['admission_path']).parent/'runs'/t['id'],t,'reference_train'))
    catalog=[]
    charged_ids=set()
    for directory,t,role in tasks:
        m=read(directory/'manifest.json');files={}
        charged_ids.update(c['budget_reservation_id'] for c in m['commands'])
        paths=[directory/name for name in ('manifest.json','input.sv','sample-contract.json','liberty_cells.json')]
        for stage in m['metrics']:
            prefix=directory/f'reports/{t["platform"]}/arithmetic_probe/base'/('vulsim_'+stage['stage'])
            paths+=sorted(prefix.parent.glob(prefix.name+'*'))
            paths.append(directory/f'results/{t["platform"]}/arithmetic_probe/base'/({'synth':'1_synth','grt':'5_1_grt'}[stage['stage']]+'.sdc'))
        # Full stage Verilog/ODB and physical logs remain in the external catalog.
        for path in paths:
            if path.suffix=='.v':continue
            name=str(path.relative_to(directory));files[name]=pool.add(path)
            if name in m['evidence_sha256'] and files[name]!=m['evidence_sha256'][name]:raise ValueError('changed raw artifact: '+name)
        catalog.append({'task':t,'role':role,'files':files,'external_directory':str(directory.resolve()),
                        'external_artifacts':m['evidence_sha256']})
    wave_hashes={}
    for path in sorted((folder/'waves').glob('*.json')):
        if path.name.endswith('.outcome.json'):continue
        wave=read(path)
        if isinstance(wave,dict) and wave.get('version')=='arithmetic-target-load-wave-v1':wave_hashes[wave['id']]=pool.add(path)
    for t in plan['tasks']:
        if t.get('inherited_run'):
            origin=t['inherited_run'];path=Path(origin['wave_path']);wave=read(path)
            h=pool.add(path)
            if h!=origin['wave_sha256']:raise ValueError('changed inherited wave')
            wave_hashes[wave['id']]=h
    ledger_entries=[e for e in read(Ledger().path)['entries'] if e['id'] in charged_ids]
    if len(ledger_entries)!=len(charged_ids) or any(e['status']!='completed' for e in ledger_entries):
        raise ValueError('missing/unsettled actual run charges')
    ledger_file=out/'measured-run-ledger.json'
    write(ledger_file,{'entries':ledger_entries,'usage':usage(ledger_entries),
                       'scope':'consumed target/load runs plus explicitly reused historical reference runs; historical charges are not new work'})
    docs['measured-run-ledger']=pool.add(ledger_file)
    # Actual deterministic refit outputs are compared, not just a success label.
    reproduced=selection.parent.with_name(selection.parent.name+'-reproduced')
    reproduction={}
    for name in ('candidate.json','fit-report.json'):
        if (reproduced/name).read_bytes()!=(selection.parent/name).read_bytes():raise ValueError('actual refit bytes differ')
        reproduction[name]={'selected_sha256':pool.add(selection.parent/name),'reproduced_sha256':pool.add(reproduced/name)}
    native_graphs={}
    if native is not None:
        for path in sorted(native.iterdir()):
            if path.is_file() and path.suffix in ('.json','.sv'):docs['native/'+path.name]=pool.add(path)
        parity=native/'parity.json'
        if parity.exists():
            proof=read(parity)
            for name,h in proof['graph_sha256'].items():
                actual=pool.add(Path(proof['graphs_directory'])/name)
                if actual!=h:raise ValueError('changed native query graph')
                native_graphs[name]=actual
        docs['qualified-base']=pool.add(Path('experiments/arithmetic/evidence/step7_models_v1/models/asap7.json'))
    # Replay code is a separate capsule, not a claim that every module below
    # executed during fitting. Executed producer hashes remain independently bound.
    module_root=Path(__file__).parent;repo=module_root.parents[1]
    capsule={str(path.relative_to(repo)):pool.add(path) for path in module_root.glob('*.py')}
    capsule.update({str(path.relative_to(repo)):pool.add(path) for path in (module_root/'configs').rglob('*.json')})
    native_sources={}
    for name in ('rtlzz/src/backend/arithmetic_model.cpp','rtlzz/src/backend/arithmetic_model.hpp',
                 'rtlzz/testv2/arithmetic_target_interval_test.cpp','regression/arithmetic_target_native.py'):
        native_sources[name]=pool.add(repo/name)
    parent=Path('experiments/arithmetic/interval_model_checkpoint_v1.json')
    docs['parent-checkpoint']=pool.add(parent)
    pool.flush()
    index={'version':'arithmetic-target-load-evidence-v1','scope':'local interval model; full step7 remains incomplete',
           'quality_status':verified['quality_status'],'full_step7_complete':False,'documents':docs,'runs':catalog,
           'text_pool_parts':pool.parts,'reproduction':reproduction,
           'wave_admissions':wave_hashes,
           'replay_code_capsule':capsule,'native_sources':native_sources,
           'native_graphs':native_graphs,
           'parent_checkpoint':{'path':str(parent),'sha256':sha(parent)},
           'portable_scope':'original numeric SDC, QD, banks, core area, static features and frozen validation/test/release',
           'external_scope':'full original stage artifacts by hash; no EDA rerun',
           'verifier_sha256':sha(Path(__file__))}
    write(out/'index.json',index)
    print(json.dumps({'runs':len(catalog),'parts':len(pool.parts),'compressed_bytes':sum(p['bytes'] for p in pool.parts),'quality_status':index['quality_status']}))


def same(a,b,label):
    if isinstance(a,(int,float)) and not isinstance(a,bool) and isinstance(b,(int,float)):
        okay=math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-7)
    else:okay=a==b
    if not okay:raise ValueError('target/load evidence mismatch: '+label)


def load_pool(folder,index):
    objects={}
    for part in index['text_pool_parts']:
        path=folder/part['file'];same(sha(path),part['sha256'],'text pool hash')
        for h,text in json.loads(gzip.decompress(path.read_bytes())).items():
            same(digest(text),h,'content-addressed text')
            if h in objects:raise ValueError('duplicate pooled text')
            objects[h]=text
    return objects


def replay_runs(index,objects,external):
    replay={};stages=bank_paths=external_files=0
    for run in index['runs']:
        files=run['files'];m=json.loads(objects[files['manifest.json']]);t=run['task'];platform=t['platform']
        same(m['status'],'completed','actual completed status');same(m['task_id'],t['id'],'task identity')
        same(m['period_ps'],t['period_ps'],'actual requested SDC');same(m['abc_target_ps'],t['abc_target_ps'],'actual ABC')
        same(files['input.sv'],t['rtl_sha256'],'actual RTL');same(files['sample-contract.json'],t['sample_contract_sha256'],'actual boundary')
        if external:
            root=Path(run['external_directory']);same(sha(root/'manifest.json'),files['manifest.json'],'external manifest')
            for name,h in run['external_artifacts'].items():same(sha(root/name),h,'external artifact '+name);external_files+=1
        cells=json.loads(objects[files['liberty_cells.json']])['cells'];contract=json.loads(objects[files['sample-contract.json']])
        specs={s['id']:s for s in contract['labels']};actual={}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for name,h in files.items():
                if name in m['evidence_sha256']:same(h,m['evidence_sha256'][name],'original report hash')
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(objects[h])
            for stored in m['metrics']:
                stage=stored['stage'];reports=root/f'reports/{platform}/arithmetic_probe/base';prefix=reports/('vulsim_'+stage)
                parsed=stage_metrics(reports,stage,cells,m['period_ps'],selected=m['platform_profile'])
                for name,value in parsed.items():
                    if name!='raw_reports_prefix':same(value,stored[name],'actual stage '+name)
                labels=read_labels(prefix,root/'sample-contract.json',parsed['raw_report_units']['time']['to_ps'])
                same(labels,stored['model_labels'],'actual QD and path points');bank_paths+=len(labels)
                banks=verify_capture_banks(prefix,root/'sample-contract.json',cells)
                same(banks,stored.get('model_capture_banks',{}),'actual mapped capture banks')
                sdc=root/f'results/{platform}/arithmetic_probe/base'/({'synth':'1_synth','grt':'5_1_grt'}[stage]+'.sdc')
                result=verify_sdc(sdc.read_text(),m['platform_profile'],m['period_ps'],rtl_ports(objects[files['input.sv']],t['top']))
                same(result,m['sdc_contracts'][stage],'actual SDC semantics')
                instances=[line.split('\t')[:2] for line in Path(str(prefix)+'_instances.tsv').read_text().splitlines()]
                actual[stage]={'metrics':stored,'labels':{l['id']:l for l in labels},'banks':banks,'instances':instances};stages+=1
        replay[files['manifest.json']]={'manifest':m,'task':t,'role':run['role'],'stages':actual,'specs':specs,'cells':cells,'files':files}
    return replay,{'runs':len(replay),'stages_and_SDCs':stages,'raw_QD_bank_paths':bank_paths,'external_artifacts_checked':external_files}


def verify(folder,external=False):
    index=read(folder/'index.json');objects=load_pool(folder,index);docs=index['documents']
    obj=lambda name:json.loads(objects[docs[name]])
    protocol=obj('protocol');same(docs['protocol'],sha(CONFIG),'active registered protocol')
    same(docs['parent-checkpoint'],index['parent_checkpoint']['sha256'],'preserved parent checkpoint')
    plan=obj('plan');reference=obj('reference');frozen=obj('selection');candidate=obj('candidate');fit_report=obj('fit-report')
    same(docs['plan'],frozen['plan_sha256'],'selected plan');same(docs['fit-data'],frozen['dataset_sha256'],'selected fitting data')
    same(docs['candidate'],frozen['candidate_sha256'],'selected candidate');same(docs['fit-report'],frozen['fit_report_sha256'],'selected validation')
    same(docs['reference'],plan['reference_sha256'],'sampling reference')
    for container,key in ((plan,'sources'),(frozen,'training_sources')):
        for name,h in container[key].items():
            if h not in objects:raise ValueError('missing frozen producer source: '+name)
    replay,counts=replay_runs(index,objects,external)
    same(set(candidate['stages']['grt']['intervals']),set(reference['intervals']),'all registered interval classes')
    same(len(reference['intervals']),42,'registered class count')
    old_rows={r['id']:r for r in obj('reference-fitting-data')['rows'] if r['split']=='train' and r['stage']=='grt'}
    for name,entry in reference['intervals'].items():
        overheads=[]
        for anchor,row_id in zip(entry['delay_anchors'],entry['source_rows'],strict=True):
            row=old_rows[row_id];actual=replay[row['manifest_sha256']]
            same(actual['role'],'reference_train','reference data role');same(row['interval_key'],name,'reference interval')
            label=actual['stages']['grt']['labels'][row_id.split('/')[-2]]
            same(anchor[0],row['features']['width'],'reference width');same(anchor[1],label['data_delay_ps'],'reference actual QD')
            overheads.append(actual['manifest']['period_ps']-label['data_delay_ps']-label['slack_ps'])
        same(entry['overhead_ps'],max([0.]+overheads),'reference actual boundary overhead')
    planned={t['id']:t for t in plan['tasks']};by_task={r['task']['id']:r for r in replay.values() if r['role']=='target_load'}
    charges={e['id']:e for e in obj('measured-run-ledger')['entries']};static_identities=set()
    for tid,run in by_task.items():
        same(run['task'],planned[tid],'actual task from frozen plan')
        m=run['manifest'];wave_hash=index['wave_admissions'][m['admission_id']];wave=json.loads(objects[wave_hash])
        origin=planned[tid].get('inherited_run')
        same(wave['plan_sha256'],docs['predecessor-plan'] if origin else docs['plan'],'wave plan identity')
        if origin:
            same(digest(json.dumps(m)),digest(json.dumps(json.loads(objects[origin['manifest_sha256']]))),'inherited manifest')
            same(wave_hash,origin['wave_sha256'],'inherited wave')
        if tid not in wave['task_ids']:raise ValueError('run not admitted by wave')
        for command in m['commands']:
            charge=charges[command['budget_reservation_id']]
            same(charge['admission_sha256'],wave_hash,'paid wave identity');same(charge['task_id'],tid,'paid task')
            same(charge['status'],'completed','paid completion')
        identity=measurement_context(m,planned[tid])
        static_identities.add(digest(json.dumps(identity,sort_keys=True,separators=(',',':'))))
        if m.get('checkpoint_reuse'):
            reused=m['checkpoint_reuse'];original=replay[reused['source_manifest_sha256']]
            name='results/asap7/arithmetic_probe/base/1_2_yosys.v'
            same(reused['source_netlist_sha256'],m['evidence_sha256'][name],'consumed mapped checkpoint')
            same(reused['source_netlist_sha256'],original['manifest']['evidence_sha256'][name],'original mapped checkpoint')
            same(reused['old_ODB_or_SDC_copied'],False,'fresh physical target implementation')
    same(static_identities,{candidate['measurement_static_identity_sha256']},'single qualified static measurement context')
    for name in ('fit-data','test-data'):
        data=obj(name);same(data['failures'],[],'complete data');same(data['plan_sha256'],docs['plan'],'data plan')
        expected=set()
        for t in selected_tasks(plan,data['mode']):
            for sid in by_task[t['id']]['specs']:
                for stage in ('synth','grt'):expected.add(t['id']+'/'+sid+'/'+stage)
        same({r['id'] for r in data['rows']},expected,'complete declared samples/stages')
        same(len(data['rows']),len(expected),'no duplicate sample rows')
        for row in data['rows']:
            actual=replay[row['manifest_sha256']];stage=actual['stages'][row['stage']];spec=actual['specs'][row['id'].split('/')[-2]]
            label=stage['labels'][spec['id']]
            same(row['features'],features(spec,row['period_ps'],reference),'pre-backend static features')
            same(row['spec'],spec,'sample specification');same(row['source_sha256'],actual['files']['input.sv'],'row source')
            same(row['delay_ps'],label['data_delay_ps'],'actual row QD');same(row['path_slack_ps'],label['slack_ps'],'actual local slack')
            area=0.;launch=capture=0
            for instance,master in stage['instances']:
                if master not in actual['cells'] or not instance.startswith(spec['instance_scope']):continue
                cell=actual['cells'][master]
                if cell['sequential']:
                    launch+=int(instance.startswith(spec['instance_scope']+'src'))
                    capture+=int(instance.startswith(spec['instance_scope']+'dst') or instance.startswith(spec['instance_scope']+'y'))
                elif instance.startswith(spec['arithmetic_scope']):area+=cell['area_um2']
            same(row['comb_area_um2'],area,'actual scoped area');same(row['launch_DFFs'],launch,'actual launch count')
            same(row['capture_DFFs'],capture,'actual capture count')
            same(row['bank_counts'],stage['banks'].get(spec['id'],{}),'actual bank count evidence')
            same(row['observed_H_ps'],row['period_ps']-label['data_delay_ps']-label['slack_ps'],'actual evaluation-only H')
            same(row['whole_setup_slack_ps'],stage['metrics']['setup_worst_slack_ps'],'whole setup')
    fitting=obj('fit-data');test=obj('test-data');result=obj('test-result')
    if any(r['split'] not in ('train','validation') for r in fitting['rows']) or any(r['split']!='test' for r in test['rows']):
        raise ValueError('fitting/test role contamination')
    for stage in ('synth','grt'):
        for name,entry in candidate['stages'][stage]['intervals'].items():
            rows=[r for r in fitting['rows'] if r['stage']==stage and r['interval_key']==name and r['split']=='validation']
            same(quality(entry,rows),fit_report['stages'][stage]['intervals'][name]['quality'],'frozen validation recomputation')
    actual_test=test_report(test,candidate);same(actual_test,result['stages'],'independent test recomputation')
    same(result['quality_status'],actual_test['grt']['status'],'independent quality status')
    same(result['selection_sha256'],docs['selection'],'consumed selection');same(result['dataset_sha256'],docs['test-data'],'consumed test')
    same(obj('test-consumption')['result_sha256'],docs['test-result'],'once-only test receipt')
    same(obj('test-consumption')['selection_sha256'],docs['selection'],'once-only selection')
    same(obj('test-consumption')['data_sha256'],docs['test-data'],'once-only data')
    same(obj('test-consumption')['status'],'completed','once-only completion')
    release=obj('release');same(release['independent_test_sha256'],docs['test-result'],'release basis')
    if bool(release['published'])!=(result['quality_status']=='passed'):raise ValueError('incorrect model publication')
    if release['published']:
        same(docs['released-model'],release['published'][0]['sha256'],'published model hash')
        expected=json.loads(json.dumps(candidate));expected['quality_status']='passed';expected['stages']={'grt':expected['stages']['grt']}
        expected['stages']['grt']['quality_status']='passed'
        for entry in expected['stages']['grt']['intervals'].values():entry['quality_status']='passed'
        published=obj('released-model')
        for name in ('version','reference','stages','abc_target_ps','io_policy','measurement_static_identity_sha256'):
            same(published[name],expected[name],'unchanged published numbers/domain '+name)
    for name,proof in index['reproduction'].items():
        same(proof['selected_sha256'],docs[{'candidate.json':'candidate','fit-report.json':'fit-report'}[name]],'selected refit artifact')
        same(proof['selected_sha256'],proof['reproduced_sha256'],'actual refit '+name)
    native_queries=0
    if index.get('native_graphs'):
        graft=obj('native/asap7.json');queries=obj('native/queries.json');parity=obj('native/parity.json');base=obj('qualified-base')
        same(parity['model_sha256'],docs['native/asap7.json'],'native consumed model')
        same(parity['query_report_sha256'],docs['native/queries.json'],'native query receipt')
        same(parity['numeric_model_claim'],True,'real trained model native evidence')
        same(queries['candidate_PPA_calls'],0,'native no-PPA inference')
        local=graft['stages']['grt']['mul_interval_model'];published=obj('released-model')
        same(local['intervals'],published['stages']['grt']['intervals'],'native interval coefficients/domain')
        same(local['reference'],published['reference'],'native static reference')
        same(graft['joint_model_context']['base_sha256'],docs['qualified-base'],'native qualified base')
        same(graft['joint_model_context']['interval_sha256'],docs['released-model'],'native qualified interval')
        for name,value in base['stages']['grt'].items():
            if name!='mul_interval_model':same(graft['stages']['grt'][name],value,'unchanged native base '+name)
        graphs={name:json.loads(objects[h]) for name,h in index['native_graphs'].items()};expected=set()
        required={f'w{w}_{shape}_{configuration}.json' for w in (8,12,16,20,24,28,32) for shape in ('full','low') for configuration in ('half','quarter')}
        if not required<=set(graphs):raise ValueError('missing required native interval graph')
        for name,g in graphs.items():
            n=len(g['graph']['regions'][0]['legal_groups'])
            for first in range(n):
                for last in range(first,n):
                    for period in (1500.,1875.,2250.,1.,2251.):expected.add((name,first,last,period))
        same({(r['graph'],r['first'],r['last'],r['period_ps']) for r in queries['rows']},expected,'native query coverage')
        same(len(queries['rows']),len(expected),'native duplicate query rejection')
        for row in queries['rows']:
            width=row['width'];joint=graft['joint_model_context'];period=row['period_ps']
            covered=joint['sdc_min_ps']<=period<=joint['sdc_max_ps'] and 8<=width<=32 and width%4==0
            if covered:
                spec=interval(graphs[row['graph']],row['first'],row['last']);spec['fanout']=1
                values=features(spec,period,local['reference']);entry=local['intervals'][key(spec)]
                covered=values['pressure']>=entry['domain']['reference_pressure_min'] and period<=entry['domain']['period_max_ps']
            same(row['covered'],covered,'native joint target/geometry coverage')
            if covered:
                same(row['delay_ps'],infer(entry['delay'],values)*entry['validation_delay_scale'],'native delay')
                same(row['comb_area_um2'],infer(entry['area'],values),'native area')
            native_queries+=1
    return {'status':'passed','quality_status':result['quality_status'],**counts,'fit_rows':len(fitting['rows']),
            'independent_rows':len(test['rows']),'published_models':len(release['published']),'native_queries':native_queries,'full_step7_complete':False}


def seal(folder,checkpoint):
    """Administrative settled-prefix seal; run after the packaging leaf settles."""
    if checkpoint.exists() or (folder/'resource-prefix.json.gz').exists():raise ValueError('preserve existing seal')
    ledger=read(Ledger().path);entries=ledger['entries']
    if usage(entries)['pending']:raise ValueError('cannot seal an unsettled shared ledger')
    starts=[i for i,e in enumerate(entries) if e.get('task_id')=='target-load-fitting-reference-summary-v1']
    if len(starts)!=1:raise ValueError('unbound target/load task accounting start')
    start=starts[0];receipts=[]
    for entry in entries[start:]:
        record=read(entry['command_record'])
        if record['cleanup']['remaining_live_pids']:raise ValueError('unreconciled live descendants')
        timing=Path(record['gnu_time'])
        receipts.append({'id':entry['id'],'record':record,'GNU_time':timing.read_text() if timing.exists() else ''})
    resource={'baseline_usage':usage(entries[:start]),'new_usage':usage(entries[start:]),'cumulative_usage':usage(entries),
              'starting_entry_id':entries[start]['id'],'new_failed_leaves':sum(e.get('exit_code',0)!=0 for e in entries[start:]),
              'scope':'one complete settled shared ledger prefix; later audits remain charged in the same live ledger',
              'full_step7_complete':False}
    for name,value in [('resource-prefix.json.gz',ledger),('resource-receipts.json.gz',receipts),('resources.json.gz',resource)]:
        (folder/name).write_bytes(gzip.compress(json.dumps(value,ensure_ascii=False,separators=(',',':')).encode(),mtime=0))
    index=read(folder/'index.json');repo=Path(__file__).resolve().parents[2]
    write(checkpoint,{'version':'arithmetic-target-load-checkpoint-v1','evidence_directory':str(folder.resolve().relative_to(repo)),
                      'parent_checkpoint':index['parent_checkpoint'],'quality_status':index['quality_status'],'full_step7_complete':False,
                      'files':{str(path.relative_to(folder)):sha(path) for path in sorted(folder.iterdir()) if path.is_file()},
                      'resources':resource,'scope':'ASAP7 local native interval target/load model only; full required step-seven domains remain outstanding'})
    print(json.dumps(resource,indent=2))


def verify_seal(folder):
    if not (folder/'resource-prefix.json.gz').exists():return {'status':'not_sealed'}
    ledger=json.loads(gzip.decompress((folder/'resource-prefix.json.gz').read_bytes()))
    resource=json.loads(gzip.decompress((folder/'resources.json.gz').read_bytes()))
    entries=ledger['entries'];start=next(i for i,e in enumerate(entries) if e['id']==resource['starting_entry_id'])
    same(usage(entries),resource['cumulative_usage'],'settled cumulative resource prefix')
    same(usage(entries[start:]),resource['new_usage'],'actual task increment')
    same(usage(entries)['pending'],0,'no pending reservation at seal')
    receipts=json.loads(gzip.decompress((folder/'resource-receipts.json.gz').read_bytes()))
    same({r['id'] for r in receipts},{e['id'] for e in entries[start:]},'complete new leaf receipts')
    by_id={e['id']:e for e in entries[start:]}
    for receipt in receipts:
        entry=by_id[receipt['id']];record=receipt['record']
        same(record['walltime_s'],entry['walltime_s'],'leaf walltime');same(record['exit_code'],entry['exit_code'],'leaf result')
        same(record['cleanup']['remaining_live_pids'],[],'leaf descendant cleanup')
        if entry.get('CPU_accounting')=='full_reservation_missing_CPU_evidence':
            same(record['CPU_limit_s'],entry['CPU_time_s'],'retained conservative CPU reservation')
        else:
            with tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp)/'time.txt';path.write_text(receipt['GNU_time'])
                same(cpu_seconds(path),entry['CPU_time_s'],'actual GNU CPU charge')
    return {'status':'passed',**resource}


def archived_verify(folder,external):
    index=read(folder/'index.json');objects=load_pool(folder,index)
    with tempfile.TemporaryDirectory(prefix='target-model-archived-code-') as tmp:
        root=Path(tmp)
        for name,h in index['replay_code_capsule'].items():
            relative=Path(name)
            if relative.is_absolute() or '..' in relative.parts:raise ValueError('unsafe capsule path')
            path=root/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(objects[h])
        env=dict(os.environ,PATH='',PYTHONDONTWRITEBYTECODE='1');env.pop('PYTHONPATH',None)
        command=[sys.executable,'-B','-m','experiments.arithmetic_dse.model_target_evidence','verify','--out',str(folder.resolve())]
        if external:command.append('--external')
        subprocess.run(command,cwd=root,env=env,check=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['package','verify','seal']);p.add_argument('--out',type=Path,required=True)
    for name in ('selection','result','release','native'):p.add_argument('--'+name,type=Path)
    p.add_argument('--external',action='store_true');p.add_argument('--archived-code',action='store_true');p.add_argument('--checkpoint',type=Path);a=p.parse_args()
    if a.action=='package':package(a.selection,a.result,a.release,a.out,a.native)
    elif a.action=='seal':seal(a.out,a.checkpoint)
    elif a.archived_code:archived_verify(a.out,a.external)
    else:print(json.dumps({**verify(a.out,a.external),'resources':verify_seal(a.out)},indent=2))


if __name__=='__main__':main()
