"""Bounded native-state publication with raw, ABI and fixed-verdict replay."""
import argparse
import copy
import json
from pathlib import Path
import shutil
import tempfile

from .model_collection import sha,write
from .model_m2_f5_evidence import Pool,load_pool
from .model_native_state_collection import ROOT,CONFIG,SUFFIX
from .model_native_state_test import report,verify as verify_test
from .model_native_state_fit import reparse
from .model_m2_state_fit import quality


def read(path):return json.loads(Path(path).read_text())


def package(collection,evaluation,out):
    from .budget import Ledger,usage
    from .model_m2_state_replay import RawAudit
    a=verify_test(collection);selection=Path(a['selection_path']);f=read(selection);fit=read(f['dataset_path'])
    candidate=read(selection.parent/'candidate.json');test=read(evaluation/'test-dataset.json');verdict=read(evaluation/'verdict.json');cfg=read(CONFIG)
    if (verdict['status']!='passed' or verdict['selection_sha256']!=sha(selection)
        or verdict['candidate_sha256']!=sha(selection.parent/'candidate.json')
        or verdict['test_dataset_sha256']!=sha(evaluation/'test-dataset.json')
        or verdict['parameters_or_reserve_or_domain_changed'] or report(candidate,test['rows'],cfg)!=verdict['stages']):
        raise ValueError('complete immutable native-state pass verdict required')
    out.mkdir(parents=True,exist_ok=False);pool=Pool(out);docs={}
    paths={'selection':selection,'candidate':selection.parent/'candidate.json','validation':selection.parent/'validation.json',
        'fitting-data':f['dataset_path'],'test-data':evaluation/'test-dataset.json','verdict':evaluation/'verdict.json',
        'evaluation-claim':collection/'evaluation-claim.json','test-admission':collection/'admission.json',
        'fitting-admission':a['fitting_admission_path'],'protocol':CONFIG,
        'old-state-parent':ROOT/cfg['parent_model'],'primitive-parent':ROOT/cfg['parent_primitives']}
    for name,path in paths.items():docs[name]=pool.add(path)
    for name in ('candidate.json','validation.json','selection-freeze.json'):
        if (selection.parent/name).read_bytes()!=(selection.parent.parent/'reproduce'/name).read_bytes():
            raise ValueError('native state byte reproduction changed')
    fitting=read(a['fitting_admission_path']);admissions={}
    for path in (Path(a['fitting_admission_path']),collection/'admission.json'):
        adm=read(path);admissions[str(path)]=pool.add(path)
        for name,h in adm['sources'].items():
            if pool.add(path.parent/'source'/name)!=h:raise ValueError('native state archived source changed')
    software=Path(fitting['software_proof_path']);proof=read(software);docs['software-proof']=pool.add(software)
    native_dir=Path(proof['native_audit_path']).parent
    docs['native-audit']=pool.add(proof['native_audit_path']);docs['native-cases']=pool.add(native_dir/'cases.json')
    native_files={str(p.relative_to(native_dir)):pool.add(p) for p in (native_dir/'native').iterdir() if p.suffix in ('.json','.sv')}
    native_sources={}
    for c in read(native_dir/'cases.json')['cases']:
        h=pool.add(c['source']);native_sources[c['name']]=h
    ledger=read(Ledger().path);audit=RawAudit(ledger['entries'])
    tasks_by_id={t['id']:t for t in fitting['tasks']}
    jobs=[(tasks_by_id[r['task_id']],Path(r['directory'])) for r in fit['runs']]
    jobs += [(t,collection/'runs'/t['id']) for t in a['tasks']]
    catalog=[]
    for t,d in jobs:
        audit.ancestry(d);m=read(d/'manifest.json')
        selected=[d/name for name in ('manifest.json','input.sv','native-state-contract.json','sample-contract.json','liberty_cells.json')]
        for stage in ('synth','grt'):
            prefix=d/'reports'/SUFFIX/('vulsim_'+stage)
            selected += [p for p in prefix.parent.glob(prefix.name+'*') if p.is_file() and p.suffix!='.v']
            stem={'synth':'1_synth','grt':'5_1_grt'}[stage]
            selected += [d/'results'/SUFFIX/(stem+'.sdc'),d/'logs'/SUFFIX/(stem+'.json')]
        cec=d/'logs'/SUFFIX/'structural_cec'
        selected += [p for p in cec.iterdir() if p.is_file() and (p.name=='proof.json' or p.suffix=='.log')]
        files={str(p.relative_to(d)):pool.add(p) for p in selected}
        if any(name in m['evidence_sha256'] and h!=m['evidence_sha256'][name] for name,h in files.items()):
            raise ValueError('native state evidence changed while packaging')
        catalog.append({'task':t,'files':files,'external_directory':str(d)})
    external={}
    for d,h in audit.directories.items():
        external[str(d/'manifest.json')]=h;m=read(d/'manifest.json');pool.add(d/'manifest.json')
        external.update({str(d/name):h for name,h in m['evidence_sha256'].items()})
    entries=[e for e in ledger['entries'] if e['id'] in audit.commands]
    if len(entries)!=len(audit.commands) or any(e['status']=='reserved' for e in entries):raise ValueError('native consumed work not settled')
    write(out/'consumed-run-ledger.json',{'entries':entries,'usage':usage(entries),
        'scope':'144 native-state measured banks and their exact mapping ancestors; global history separately retains all failures'})
    docs['consumed-ledger']=pool.add(out/'consumed-run-ledger.json')
    released=copy.deepcopy(candidate);released.update(version='arithmetic-native-state-qualified-v1',id='asap7-native-state-grt-qualified-v1',
        quality_status='passed',selection_sha256=sha(selection),independent_verdict_sha256=sha(evaluation/'verdict.json'),
        test_observed=True,independent_labels_consumed=True,independent_labels_excluded_from_future_fitting=True,
        native_query_extraction_checked=True,production_price_binding_qualified=False,full_D_ready=False)
    released['stages']={'grt':released['stages']['grt']};released['stages']['grt'].update(quality_status='passed',independent_quality=verdict['stages']['grt'])
    write(out/'asap7-native-state.json',released)
    write(out/'publication.json',{'version':'asap7-native-state-publication-v1','status':'passed',
        'published':[{'file':'asap7-native-state.json','sha256':sha(out/'asap7-native-state.json'),'stage':'grt'}],
        'selection_sha256':sha(selection),'candidate_sha256':sha(selection.parent/'candidate.json'),
        'verdict_sha256':sha(evaluation/'verdict.json'),'parent_state_sha256':cfg['parent_model_sha256'],
        'parent_primitives_sha256':cfg['parent_primitives_sha256'],'parameters_or_domain_changed_after_test':False,
        'production_price_binding_qualified':False,'full_D_ready':False})
    write(out/'capabilities.json',{'native_protocol_synthetic_state_bank_grt':True,'input_and_register_control_boundary_grt':True,
        'native_query_extraction_checked':True,'query_coverage':'nine public VUL original cores plus three diagnostics; not every D candidate/move',
        'source_schema':'arithmetic-state-bank-features-v1','ABC_ps':1500,'exact_SDC_ps':cfg['SDC_ps'],'IO':'0.2T',
        'native_enable_policy':cfg['native_protocol'],'known_bits':cfg['known_bits'],
        'production_price_binding_qualified':False,'input_service_wrapper_state_covered':False,
        'joint_arithmetic_or_formal_boundary_qualified':False,'whole_stage_model_qualified':False,
        'full_D_ready':False,'nine_case_36_complete':False,'independent_labels_consumed_and_excluded_from_future_fitting':True})
    for name in ('asap7-native-state.json','publication.json','capabilities.json'):docs[name]=pool.add(out/name)
    replay={}
    for p in sorted(Path(__file__).parent.glob('*.py'))+sorted(Path(__file__).with_name('configs').rglob('*.json'))+[ROOT/'regression/arithmetic_native_state.py']:
        replay[str(p.relative_to(ROOT))]=pool.add(p)
    pool.flush()
    write(out/'index.json',{'version':'asap7-native-state-evidence-v1','documents':docs,'runs':catalog,
        'admissions':admissions,'native_files':native_files,'native_sources':native_sources,
        'text_pool_parts':pool.parts,'external_artifacts':external,'replay_code':replay,'verifier_sha256':sha(__file__),
        'portable_scope':'144 native banks /288 stages/1152 Q-D and PI-D paths; fixed validation and one-shot independent verdict;12 actual native query/RTL audits',
        'external_scope':'all original artifacts, Liberty, complete saved CTS CEC and paid mapping ancestry; no new SAT or EDA',
        'quality_status':'passed','production_price_binding_qualified':False,'full_D_ready':False})
    (out/'README.md').write_text('''# ASAP7原生协议状态／边界组件

72 train／36 validation／36新独立状态测试全部完成。冻结参数一次性评价通过：grt状态总面积误差中位6.034688%、P95 18.922855%；synth诊断3.755745%／17.635903%，原中位20%／P95 50%门槛保持。
输入与注册控制边界在三个精确目标全通过，grt最小余量183.134460ps；冻结input／register均803.206085ps，原50ps reserve未改。

发布asap7-native-state.json仅ASAP7 grt原生协议合成银行，ABC1500ps／精确SDC40500、1500、375ps／IO0.2T。
stage1由内核输入valid使能，其后由前级valid使能，同cut共享；包含非均匀寿命、已知零孔洞／高零填充和预登记复位上下文。
面积包含状态／控制、时钟／tap和未归属repair，排除observer；输入service外壳与联合算术／正式边界尚未覆盖。375ps可能没有正的数据预算。

便携核验：`python3 -B -m experiments.arithmetic_dse.model_native_state_evidence verify --folder experiments/arithmetic/evidence/step7_native_state_v1`

加`--external`核对本机原始大产物、Liberty重建、完整已存CTS状态图／CEC及收费祖先。144银行／288阶段／1152路径及12个真实原生结构的便携数值回放不依赖原build或EDA，不重新训练、SAT或消费测试；external也不启动EDA。

旧12类和旧受限状态银行发布均保持原字节。新独立标签已消费，永久排除后继拟合、验证和算法／裕量／域选择。
新原生查询已做投影／物化／RTL核对，生产价格绑定、全候选／位置、整阶段／真实区间与完整D仍待资格；本包不声称九例36条或步骤七完成。Git由用户提交。
''')
    print(json.dumps({'status':'packaged','banks':144,'stages':288,'path_labels':1152,'native_queries':12,
        'pool_bytes':sum(p['bytes'] for p in pool.parts),'model_sha256':sha(out/'asap7-native-state.json')}),flush=True)


def verify(folder,external=False):
    from .backend import stage_metrics,verify_orfs_area
    from .model_native_state_samples import specifications,source,features
    from .model_native_state_labels import labels,witness
    from .model_m2_live_cec_v3 import check_result
    from .platforms import profile,verify_wire_readback
    from .sdc import verify_sdc,rtl_ports
    index=read(folder/'index.json')
    if sha(__file__)!=index['verifier_sha256']:raise ValueError('native state replay source changed')
    objects=load_pool(folder,index)
    for name,h in index['replay_code'].items():
        if sha(ROOT/name)!=h:raise ValueError('native state replay dependency changed: '+name)
    docs={name:json.loads(objects[h]) for name,h in index['documents'].items()}
    cfg,candidate,fit,test,verdict,f=[docs[n] for n in ('protocol','candidate','fitting-data','test-data','verdict','selection')]
    hashes=index['documents']
    if (hashes['candidate']!=f['candidate_sha256'] or hashes['validation']!=f['validation_sha256']
        or hashes['fitting-data']!=f['dataset_sha256'] or hashes['test-data']!=verdict['test_dataset_sha256']
        or hashes['selection']!=verdict['selection_sha256'] or hashes['protocol']!=f['protocol_sha256']):
        raise ValueError('native state frozen input identities differ')
    for name in ('asap7-native-state.json','publication.json','capabilities.json'):
        if sha(folder/name)!=hashes[name]:raise ValueError('native state published file changed')
    published=docs['asap7-native-state.json'];expected=copy.deepcopy(candidate['stages']['grt'])
    expected.update(quality_status='passed',independent_quality=verdict['stages']['grt'])
    if (published['stages']!={'grt':expected} or published['domain']!=candidate['domain']
        or published['production_price_binding_qualified'] or published['full_D_ready']):
        raise ValueError('native state publication changed coefficients/boundary/domain/scope')
    specs={s['id']:s for s in specifications(cfg)};rows={r['id']:r for r in fit['rows']+test['rows']};seen=set();groups={}
    p=profile('asap7')
    for run in index['runs']:
        t=run['task'];spec=specs[t['source_group']]
        with tempfile.TemporaryDirectory() as td:
            d=Path(td)
            for name,h in run['files'].items():
                dst=d/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_text(objects[h])
            m=read(d/'manifest.json');c=read(d/'native-state-contract.json')
            if (c['spec']!=spec or source(spec)!=(d/'input.sv').read_text() or sha(d/'input.sv')!=t['rtl_sha256']
                or sha(d/'native-state-contract.json')!=t['contract_sha256'] or t['features']!=features(spec,t['period_ps'])
                or groups.setdefault(t['rtl_sha256'],t['split'])!=t['split']):raise ValueError('native portable geometry/role differs')
            cells=read(d/'liberty_cells.json')['cells']
            for stage in ('synth','grt'):
                reports=d/'reports'/SUFFIX;g=stage_metrics(reports,stage,cells,t['period_ps'],selected=p)
                w=witness(d,stage,cells);paths=labels(reports/('vulsim_'+stage),t['period_ps'],g['raw_report_units']['time']['to_ps'])
                old=next(v for v in m['metrics'] if v['stage']==stage)
                for key,value in g.items():
                    if key!='raw_reports_prefix' and value!=old.get(key):raise ValueError('native portable raw stage differs: '+key)
                if w!=old['native_state_witness'] or paths!=old['native_state_paths']:raise ValueError('native portable area/FF/path differs')
                rc=verify_wire_readback(reports/('vulsim_'+stage+'_layer_rc.tsv'),p)
                if rc is not None and rc!=old.get('wire_RC_readback'):raise ValueError('native portable RC differs')
                stem={'synth':'1_synth','grt':'5_1_grt'}[stage]
                sd=verify_sdc((d/'results'/SUFFIX/(stem+'.sdc')).read_text(),p,t['period_ps'],rtl_ports((d/'input.sv').read_text(),'ModelBundle'))
                if sd!=m['sdc_contracts'][stage]:raise ValueError('native portable SDC differs')
                native=read(d/'logs'/SUFFIX/(stem+'.json'))[('synth' if stage=='synth' else 'globalroute')+'__design__instance__area__stdcell']
                if verify_orfs_area(g['cell_area_um2'],native)!=old['orfs_area_crosscheck']:raise ValueError('native portable total area differs')
                key=t['id']+'/'+stage;row=rows[key]
                if (row['state_area_um2']!=g['cell_area_um2']-w['excluded_observer_area_um2'] or row['boundary_paths']!=paths
                    or row['features']!=t['features'] or row['whole_setup_slack_ps']!=g['setup_worst_slack_ps']
                    or row['whole_hold_slack_ps']!=g['hold_worst_slack_ps']):raise ValueError('native portable dataset differs')
                if key in seen:raise ValueError('duplicate native portable measurement')
                seen.add(key)
            proof=read(d/'logs'/SUFFIX/'structural_cec/proof.json')
            check_result((d/'logs'/SUFFIX/'structural_cec/cec.log').read_text(),True)
            for name in proof['negative_controls']:check_result((d/'logs'/SUFFIX/('structural_cec/negative-'+name+'.log')).read_text(),False)
    if len(index['runs'])!=144 or seen!=set(rows) or len(seen)!=288 or len(groups)!=48:
        raise ValueError('native portable coverage incomplete')
    for stage in ('synth','grt'):
        validation=[r for r in fit['rows'] if r['stage']==stage and r['split']=='validation']
        if quality(candidate['stages'][stage]['area_model'],validation,cfg)!=docs['validation'][stage]['selected_validation']:
            raise ValueError('native fixed validation differs')
    if report(candidate,test['rows'],cfg)!=verdict['stages']:raise ValueError('native frozen independent verdict differs')
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)
        (d/'cases.json').write_text(objects[hashes['native-cases']])
        for name,h in index['native_files'].items():
            dst=d/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_text(objects[h])
        from regression.arithmetic_native_state import verify as verify_native
        verify_native(d)
        if read(d/'audit.json')!=docs['native-audit']:raise ValueError('native feature/reset/RTL audit does not reproduce')
        query=read(d/'native/queries.json')
        for row in query['rows']:
            if index['native_sources'][row['case']]!=row['source_sha256']:raise ValueError('native compiled source identity differs')
    if external:
        from .budget import Ledger
        from .model_m2_state_replay import RawAudit
        audit=RawAudit(read(Ledger().path)['entries'])
        for path,h in index['external_artifacts'].items():
            if audit.digest(path)!=h:raise ValueError('native external artifact changed')
        for run in index['runs']:
            d=Path(run['external_directory']);audit.ancestry(d);reparse(d,run['task'])
    print(json.dumps({'status':'verified','external':external,'banks':144,'stages':288,'path_labels':1152,
        'actual_native_queries':12,'independent_status':verdict['status'],'PPA_calls':0,
        'production_price_binding_qualified':False,'full_D_ready':False}),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('package','verify'));p.add_argument('--folder',type=Path,required=True)
    p.add_argument('--collection',type=Path);p.add_argument('--evaluation',type=Path);p.add_argument('--external',action='store_true');a=p.parse_args()
    if a.action=='package':
        if a.collection is None or a.evaluation is None:p.error('package requires collection/evaluation')
        package(a.collection.resolve(),a.evaluation.resolve(),a.folder.resolve())
    else:verify(a.folder.resolve(),a.external)


if __name__=='__main__':main()
