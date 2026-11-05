"""Bounded state-bank publication and portable raw/frozen-verdict replay."""
import argparse
from contextlib import redirect_stdout
import copy
import io
import json
from pathlib import Path
import shutil
import tempfile

from .model_collection import sha, write
from .model_m2_f5_evidence import Pool, load_pool
from .model_m2_state_collection import ROOT, CONFIG, SUFFIX
from .model_m2_state_fit import quality


def read(path):
    return json.loads(Path(path).read_text())


def report(candidate, rows, cfg):
    result = {}
    for stage in ('synth','grt'):
        group = [r for r in rows if r['stage']==stage]
        model = candidate['stages'][stage]
        b, coverage = model['boundary_model'], {}
        for period in cfg['SDC_ps']:
            paths = [x for r in group if r['period_ps']==period for x in r['paths']]
            required = max(0.,max(x['H_ps'] for x in paths))+max(0.,max(x['QD_ps'] for x in paths))
            margin = min(b['input_overhead_ps'],b['register_overhead_ps'])-required
            coverage[str(period)] = {'status':'passed' if margin>=0 else 'failed',
                'required_H_plus_control_ps':required,'frozen_overhead_ps':b['register_overhead_ps'],'margin_ps':margin}
        area = quality(model['area_model'],group,cfg)
        passed = area['status']=='passed' and all(x['status']=='passed' for x in coverage.values())
        result[stage] = {'status':'passed' if passed else 'failed','state_area':area,
            'state_area_by_exact_SDC':{str(t):quality(model['area_model'],[r for r in group if r['period_ps']==t],cfg) for t in cfg['SDC_ps']},
            'boundary_coverage':coverage,'whole_setup_failed':sum(r['whole_setup_slack_ps']<0 for r in group),
            'whole_hold_negative':sum(r['whole_hold_slack_ps']<0 for r in group)}
    return result


def package(collection, evaluation, out):
    from .model_m2_state_test import verify as verify_admission
    from .model_m2_state_replay import RawAudit
    from .budget import Ledger, usage
    admission = verify_admission(collection)
    selection = Path(admission['selection_path'])
    frozen = read(selection)
    fit = read(frozen['dataset_path'])
    test, verdict = read(evaluation/'test-dataset.json'), read(evaluation/'verdict.json')
    candidate = read(selection.parent/'candidate.json')
    cfg = read(CONFIG)
    if (verdict['status']!='passed' or verdict['selection_sha256']!=sha(selection)
        or verdict['candidate_sha256']!=sha(selection.parent/'candidate.json')
        or verdict['test_dataset_sha256']!=sha(evaluation/'test-dataset.json')
        or verdict['parameters_or_margins_changed'] or verdict['PPA_calls_during_evaluation']
        or report(candidate,test['rows'],cfg)!=verdict['stages']):
        raise ValueError('frozen state independent verdict differs')
    out.mkdir(parents=True,exist_ok=False)
    pool, documents = Pool(out), {}
    paths = {'selection':selection,'candidate':selection.parent/'candidate.json',
        'validation':selection.parent/'validation.json','fitting-data':frozen['dataset_path'],
        'test-data':evaluation/'test-dataset.json','verdict':evaluation/'verdict.json',
        'evaluation-started':evaluation/'evaluation-started.json','evaluation-claim':collection/'evaluation-claim.json',
        'test-admission':collection/'admission.json','test-progress':collection/'progress.json',
        'state-protocol':CONFIG,'primitive-parent':ROOT/cfg['parent_primitives']}
    for name,path in paths.items():
        documents[name] = pool.add(path)
    reproduced = selection.parent.parent/'reproduce'
    for name in ('candidate.json','validation.json','selection-freeze.json'):
        if (selection.parent/name).read_bytes() != (reproduced/name).read_bytes():
            raise ValueError('state byte reproduction changed')
    # Archive every admitted producer, including failed parser/support parents.
    admissions, pending = {}, [Path(fit['admission_path']),collection/'admission.json']
    while pending:
        path = pending.pop()
        if str(path) in admissions:
            continue
        a = read(path);admissions[str(path)] = pool.add(path)
        for name,h in a['sources'].items():
            if pool.add(path.parent/'source'/name) != h:
                raise ValueError('state archived producer changed')
        for key in ('predecessor','support_predecessor'):
            if a.get(key):
                parent = a[key]
                if pool.add(parent['admission_path']) != parent['admission_sha256']:
                    raise ValueError('state failed admission ancestry changed')
                pending.append(Path(parent['admission_path']))
        if a.get('fitting_admission_path'):
            pending.append(Path(a['fitting_admission_path']))
    ledger = read(Ledger().path)
    audit = RawAudit(ledger['entries'])
    fitting_admission = read(fit['admission_path'])
    fitting_tasks = {t['id']:t for t in fitting_admission['tasks']}
    tasks = [(fitting_tasks[r['task_id']],Path(fit['admission_path']).parent/'runs'/r['task_id']) for r in fit['runs']]
    tasks += [(t,collection/'runs'/t['id']) for t in admission['tasks']]
    catalog = []
    for task,directory in tasks:
        audit.ancestry(directory)
        m = read(directory/'manifest.json')
        selected = [directory/name for name in ('manifest.json','input.sv','sample-contract.json','liberty_cells.json')]
        for stage in ('synth','grt'):
            prefix = directory/'reports'/SUFFIX/('vulsim_'+stage)
            selected += sorted(p for p in prefix.parent.glob(prefix.name+'*') if p.is_file() and p.suffix!='.v')
            stem = {'synth':'1_synth','grt':'5_1_grt'}[stage]
            selected += [directory/'results'/SUFFIX/(stem+'.sdc'),directory/'logs'/SUFFIX/(stem+'.json')]
        proof = directory/'logs'/SUFFIX/'structural_cec'
        selected += [p for p in proof.iterdir() if p.is_file() and (p.name=='proof.json' or p.suffix=='.log')]
        files = {str(p.relative_to(directory)):pool.add(p) for p in selected}
        for name,h in files.items():
            if name in m['evidence_sha256'] and m['evidence_sha256'][name]!=h:
                raise ValueError('state raw report changed during packaging')
        catalog.append({'task':task,'files':files,'external_directory':str(directory)})
    external = {}
    for directory,h in audit.directories.items():
        m = read(directory/'manifest.json')
        pool.add(directory/'manifest.json')
        external[str(directory/'manifest.json')] = h
        for name,digest in m.get('evidence_sha256',{}).items():
            external[str(directory/name)] = digest
    entries = [e for e in ledger['entries'] if e['id'] in audit.commands]
    if len(entries)!=len(audit.commands) or any(e['status']=='reserved' for e in entries):
        raise ValueError('state consumed charges incomplete')
    write(out/'consumed-run-ledger.json',{'entries':entries,'usage':usage(entries),
        'scope':'144 successful measured tasks plus required paid mapping/replay ancestors; all global failures remain in shared ledger'})
    documents['consumed-ledger'] = pool.add(out/'consumed-run-ledger.json')
    # Include the damaged support sidecars and their original successful and
    # failed command/log/resource context without relabeling their bytes.
    for item in fit['support_sidecar_reconciliations']:
        for key in ('observed_sidecar_path','original_manifest_path'):
            pool.add(item[key])
        for command in (item['original_command'],):
            pool.add(command['log']);pool.add(command['gnu_time'])
        failure = item['paid_failed_v3_entry']
        pool.add(Path(failure['output']).with_suffix('.log'))
        pool.add(Path(failure['output']).with_suffix('.resources.txt'))
    # Released parameters are copied, never fitted or adjusted after test.
    released = copy.deepcopy(candidate)
    released.update(version='arithmetic-state-boundary-qualified-v1',id='asap7-m2-state-bank-grt-qualified-v1',
        quality_status='passed',qualification_scope='bounded synthetic valid-chain state-bank component',
        independent_verdict_sha256=sha(evaluation/'verdict.json'),selection_sha256=sha(selection),
        independent_labels_consumed=True,test_labels_read=True,
        independent_labels_excluded_from_future_fitting=True,
        native_state_binding_qualified=False,full_D_ready=False)
    released['stages'] = {'grt':released['stages']['grt']}
    released['stages']['grt']['quality_status'] = 'passed'
    released['stages']['grt']['independent_quality'] = verdict['stages']['grt']
    write(out/'asap7-state-boundary.json',released)
    write(out/'publication.json',{'version':'asap7-m2-state-bank-publication-v1','quality_status':'passed',
        'published':[{'file':'asap7-state-boundary.json','sha256':sha(out/'asap7-state-boundary.json'),'stage':'grt'}],
        'parent_primitives_sha256':cfg['parent_primitives_sha256'],'candidate_sha256':verdict['candidate_sha256'],
        'selection_sha256':sha(selection),'verdict_sha256':sha(evaluation/'verdict.json'),
        'parameter_boundary_or_domain_changes_after_test':False,'native_state_binding_qualified':False,'full_D_ready':False})
    write(out/'capabilities.json',{'qualified_state_bank_grt':True,'state_bank_boundary_grt':True,
        'control_family':'valid_chain','exact_ABC_ps':1500,'exact_SDC_ps':cfg['SDC_ps'],'IO':'0.2T',
        'synth_test_passed_diagnostic_only':verdict['stages']['synth']['status']=='passed',
        'native_state_binding_qualified':False,'whole_stage_composition_qualified':False,
        'joint_arithmetic_or_formal_boundary_qualified':False,'full_D_ready':False,'nine_case_36_complete':False,
        'independent_labels_consumed_and_permanently_excluded_from_revision_fitting':True})
    for name in ('asap7-state-boundary.json','publication.json','capabilities.json'):
        documents[name] = pool.add(out/name)
    # Portable verifier imports only repo Python code and uses report text.
    # Archives preserve the executed sources independently of this replay code.
    replay = {}
    for path in sorted(Path(__file__).parent.glob('*.py'))+sorted(Path(__file__).with_name('configs').rglob('*.json')):
        replay[str(path.relative_to(ROOT))] = pool.add(path)
    pool.flush()
    write(out/'index.json',{'version':'asap7-m2-state-bank-evidence-v1','documents':documents,
        'admissions':admissions,'runs':catalog,'text_pool_parts':pool.parts,'replay_code':replay,
        'external_artifacts':external,'verifier_sha256':sha(__file__),'quality_status':'passed',
        'portable_scope':'144 raw measured banks, 288 stages, 864 paths; state/physical areas, SDC/RC, saved CEC logs, fixed validation and once-only independent verdict',
        'external_scope':'all original artifacts plus complete saved CTS CEC/state correspondence and paid ancestors; no new SAT/EDA',
        'native_state_binding_qualified':False,'full_D_ready':False})
    (out/'README.md').write_text('''# ASAP7状态银行／边界独立资格

72 train／36 validation／36新独立test，全部原始采集和冻结参数评价通过。
grt状态总面积独立误差中位6.401676%、P95 8.624627%；synth诊断为2.454918%／6.146589%。
原面积门槛20%／50%及边界冻结规则保持；grt三个精确SDC的边界覆盖全部通过，最小裕量105.182022ps。

发布asap7-state-boundary.json只含grt，控制家族valid_chain、受限合成状态银行、ABC1500ps／精确SDC40500、1500、375ps／IO0.2T。
面积包含状态／控制和时钟／物理／未归属repair，排除独立post-capture observer；不能再计为算术面积。
375ps可能没有正的数据预算，质量通过不表示任意该目标阶段可行。
原生state绑定、算术阶段／正式I/O边界、整阶段模型和完整D尚未取得资格。

便携核验：`python3 -B -m experiments.arithmetic_dse.model_m2_state_evidence verify --folder experiments/arithmetic/evidence/step7_m2_state_boundary_v1`

加`--external`核对本机原始大产物、Liberty、完整已存CTS状态图／CEC与费用。
便携模式重提取144份银行的原始文本数值并重算既有结论，不执行SAT、训练或EDA，不依赖build或外部工具。
两种模式都不重新消费独立测试或重选模型。独立标签已消费，永久排除后继拟合／验证／算法、裕量或域选择。

v1–v3失败及费用保持；v3日志别名覆盖两份v2支持命令副本的实际字节、原成功manifest／日志／资源／账本及另付费失败链均明确保留，见fitting-data中的support_sidecar_reconciliations。
旧发布组件和原冻结字节不覆盖。Git由用户提交。
''')
    print(json.dumps({'status':'packaged','runs':len(catalog),'stages':288,'path_labels':864,
        'pool_bytes':sum(p['bytes'] for p in pool.parts),'model_sha256':sha(out/'asap7-state-boundary.json')}),flush=True)


def verify(folder, external=False):
    from .backend import stage_metrics, verify_orfs_area
    from .model_samples import read_labels
    from .model_m2_state_collection_v2 import state_witness
    from .model_m2_state_collection_v3 import rtl_ports
    from .model_m2_state_samples import specifications, source, features
    from .platforms import profile, verify_wire_readback
    from .sdc import verify_sdc
    index = read(folder/'index.json')
    if sha(__file__) != index['verifier_sha256']:
        raise ValueError('state replay implementation changed')
    objects = load_pool(folder,index)
    for name,h in index['replay_code'].items():
        if sha(ROOT/name)!=h:
            raise ValueError('state replay source changed: '+name)
    docs = {name:json.loads(objects[h]) for name,h in index['documents'].items()}
    f,candidate,fit,test,verdict,cfg = [docs[n] for n in ('selection','candidate','fitting-data','test-data','verdict','state-protocol')]
    if (index['documents']['candidate']!=f['candidate_sha256']
        or index['documents']['validation']!=f['validation_sha256']
        or index['documents']['fitting-data']!=f['dataset_sha256']
        or index['documents']['test-data']!=verdict['test_dataset_sha256']
        or index['documents']['selection']!=verdict['selection_sha256']
        or index['documents']['state-protocol']!=f['protocol_sha256']):
        raise ValueError('state evidence frozen inputs differ')
    for name in ('asap7-state-boundary.json','publication.json','capabilities.json'):
        if sha(folder/name)!=index['documents'][name]:
            raise ValueError('published state file changed')
    published = docs['asap7-state-boundary.json']
    expected_grt = copy.deepcopy(candidate['stages']['grt'])
    expected_grt.update(quality_status='passed',independent_quality=verdict['stages']['grt'])
    if (published['stages']!={'grt':expected_grt} or published['domain']!=candidate['domain']
        or published['selection_sha256']!=index['documents']['selection']
        or published['native_state_binding_qualified'] or published['full_D_ready']):
        raise ValueError('state release parameters/domain/scope changed')
    specs = {s['id']:s for s in specifications(cfg)}
    fitting_rows = {r['id']:r for r in fit['rows']}
    test_rows = {r['id']:r for r in test['rows']}
    seen, sources = set(), {}
    p = profile('asap7')
    for run in index['runs']:
        task = run['task'];spec = specs[task['source_group']]
        with tempfile.TemporaryDirectory() as td:
            directory=Path(td)
            for name,h in run['files'].items():
                dst=directory/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_text(objects[h])
            m = read(directory/'manifest.json');contract=read(directory/'sample-contract.json')
            rtl,labels=source(spec)
            if ((directory/'input.sv').read_text()!=rtl or sha(directory/'input.sv')!=task['rtl_sha256']
                or sha(directory/'sample-contract.json')!=task['sample_contract_sha256']
                or contract['state_geometry']!=spec or contract['labels']!=labels
                or task['features']!=features(spec,task['period_ps']) or contract['split']!=task['split']):
                raise ValueError('portable state geometry/features/partition differ')
            previous=sources.setdefault(task['rtl_sha256'],task['split'])
            if previous!=task['split']:
                raise ValueError('state source crosses partitions')
            cells=read(directory/'liberty_cells.json')['cells']
            for stage in ('synth','grt'):
                reports=directory/'reports'/SUFFIX
                g=stage_metrics(reports,stage,cells,task['period_ps'],selected=p)
                witness=state_witness(directory,stage,cells)
                paths=read_labels(reports/('vulsim_'+stage),directory/'sample-contract.json',g['raw_report_units']['time']['to_ps'])
                old=next(v for v in m['metrics'] if v['stage']==stage)
                for key,value in g.items():
                    if key!='raw_reports_prefix' and old.get(key)!=value:
                        raise ValueError('portable state raw metric differs: '+key)
                if witness!=old['state_witness'] or paths!=old['model_labels']:
                    raise ValueError('portable state FF/area/path differs')
                wire=verify_wire_readback(reports/('vulsim_'+stage+'_layer_rc.tsv'),p)
                if wire is not None and wire!=old.get('wire_RC_readback'):
                    raise ValueError('portable state RC differs')
                stem={'synth':'1_synth','grt':'5_1_grt'}[stage]
                numeric=verify_sdc((directory/'results'/SUFFIX/(stem+'.sdc')).read_text(),p,task['period_ps'],rtl_ports(rtl,'ModelBundle'))
                if numeric!=m['sdc_contracts'][stage]:
                    raise ValueError('portable state SDC differs')
                native=read(directory/'logs'/SUFFIX/(stem+'.json'))[('synth' if stage=='synth' else 'globalroute')+'__design__instance__area__stdcell']
                if verify_orfs_area(g['cell_area_um2'],native)!=old['orfs_area_crosscheck']:
                    raise ValueError('portable state area crosscheck differs')
                identifier=task['id']+'/'+stage
                row=(test_rows if task['split']=='test' else fitting_rows)[identifier]
                actual_area=g['cell_area_um2']-witness['excluded_observer_area_um2']
                if (row['state_area_um2']!=actual_area or row['features']!=task['features']
                    or row['whole_setup_slack_ps']!=g['setup_worst_slack_ps']
                    or row['whole_hold_slack_ps']!=g['hold_worst_slack_ps']):
                    raise ValueError('portable state fitted/tested row differs')
                actual_paths=[{'H_ps':task['period_ps']-v['data_delay_ps']-v['slack_ps'],'QD_ps':v['data_delay_ps']} for v in paths]
                expected_paths=row['paths'] if task['split']=='test' else [{'H_ps':v['H_ps'],'QD_ps':v['QD_ps']} for v in row['boundary_paths']]
                if actual_paths!=expected_paths:
                    raise ValueError('portable state boundary labels differ')
                seen.add(identifier)
            proof=read(directory/'logs'/SUFFIX/'structural_cec/proof.json')
            from .model_m2_live_cec_v3 import check_result
            check_result((directory/'logs'/SUFFIX/'structural_cec/cec.log').read_text(),True)
            for name in proof['negative_controls']:
                check_result((directory/'logs'/SUFFIX/('structural_cec/negative-'+name+'.log')).read_text(),False)
    if seen!=set(fitting_rows)|set(test_rows) or len(seen)!=288:
        raise ValueError('portable state coverage incomplete')
    for stage in ('synth','grt'):
        validation=[r for r in fit['rows'] if r['stage']==stage and r['split']=='validation']
        if quality(candidate['stages'][stage]['area_model'],validation,cfg)!=docs['validation'][stage]['selected_validation']:
            raise ValueError('fixed state validation differs')
    if report(candidate,test['rows'],cfg)!=verdict['stages']:
        raise ValueError('frozen state independent verdict differs')
    if external:
        from .budget import Ledger
        from .model_m2_state_replay import RawAudit, reparse
        audit=RawAudit(read(Ledger().path)['entries'])
        for name,h in index['external_artifacts'].items():
            if audit.digest(name)!=h:
                raise ValueError('external state artifact changed: '+name)
        for run in index['runs']:
            directory=Path(run['external_directory']);audit.ancestry(directory)
            reparse(directory,run['task'])
    print(json.dumps({'status':'verified','external':external,'measured_banks':144,'stage_rows':288,
        'path_labels':864,'independent_status':verdict['status'],'PPA_calls':0,
        'native_state_binding_qualified':False,'full_D_ready':False}),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('package','verify'))
    parser.add_argument('--folder',type=Path,required=True)
    parser.add_argument('--collection',type=Path)
    parser.add_argument('--evaluation',type=Path)
    parser.add_argument('--external',action='store_true')
    args=parser.parse_args()
    if args.action=='package':
        if args.collection is None or args.evaluation is None:
            parser.error('package requires collection/evaluation')
        package(args.collection.resolve(),args.evaluation.resolve(),args.folder.resolve())
    else:
        verify(args.folder.resolve(),args.external)


if __name__=='__main__':
    main()
