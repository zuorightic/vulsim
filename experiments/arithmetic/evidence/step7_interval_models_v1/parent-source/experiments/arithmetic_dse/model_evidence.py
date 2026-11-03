"""Portable replay of fitted-model evidence; no EDA or ML imports required.

The content-addressed text pool preserves the original file bytes. Large
databases/netlists/logs stay in the separately enumerated local artifact set.
"""
import argparse
import gzip
import hashlib
import json
import math
import tempfile
from pathlib import Path
from .model_features import infer,features
from .model_training import metric
from .model_calibration_fit import quality as calibration_quality
from .model_analysis import verify_report,verify_selection
from .sdc import verify_sdc,rtl_ports
from .model_samples import read_labels
from .backend import stage_metrics
from .platforms import verify_wire_readback
from .budget import usage,cpu_seconds

ROOT=Path(__file__).resolve().parents[2]
FREEZE='experiments/arithmetic/offline_model_freeze_v1.json'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    data=Path(path).read_bytes()
    return json.loads(gzip.decompress(data) if str(path).endswith('.gz') else data)


def same(a,b,label):
    if type(a) in (int,float) and type(b) in (int,float):okay=math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-7)
    elif type(a) is dict and type(b) is dict:
        if a.keys()!=b.keys():raise ValueError('model evidence key mismatch: '+label)
        for k in a:same(a[k],b[k],label+'.'+k)
        return
    elif type(a) is list and type(b) is list:
        if len(a)!=len(b):raise ValueError('model evidence list length: '+label)
        for i,(x,y) in enumerate(zip(a,b)):same(x,y,label+f'[{i}]')
        return
    else:okay=type(a) is type(b) and a==b
    if not okay:raise ValueError('model evidence mismatch: '+label)


def pool(directory,manifest):
    result={}
    for item in manifest['text_pool_parts']:
        path=directory/item['file'];same(sha(path),item['sha256'],'text-pool part')
        objects=read(path)
        for key,text in objects.items():
            if type(text) is not str or hashlib.sha256(text.encode()).hexdigest()!=key:raise ValueError('changed content-addressed text')
            if key in result:raise ValueError('duplicate content-addressed text entry')
            result[key]=text
    return result


def replay_runs(catalog,objects):
    replay={};stage_count=sdc_count=labels=0
    for run in catalog:
        m=json.loads(objects[run['files']['manifest.json']]);files=run['files']
        if m['status']!='completed':continue
        p=m['platform_profile'];platform=m['target_platform'];input_rtl=objects[files['input.sv']]
        contract=objects[files['sample-contract.json']];specs={x['id']:x for x in json.loads(contract)['labels']}
        cells=json.loads(objects[files['liberty_cells.json']])['cells'];stages={}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'contract.json').write_text(contract)
            for name,ref in files.items():
                if name.startswith('reports/') or name.endswith('.sdc'):
                    path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(objects[ref])
            for archived in m['metrics']:
                stage=archived['stage'];reports=root/f'reports/{platform}/arithmetic_probe/base'
                parsed=stage_metrics(reports,stage,cells,m['period_ps'],selected=p)
                for key,value in parsed.items():
                    if key!='raw_reports_prefix':same(value,archived[key],'actual stage report '+key)
                if 'wire_RC_readback' in archived:
                    # The runtime helper returns coordinate tuples; manifests
                    # serialize these as JSON arrays. Compare the serialized
                    # meaning while retaining strict JSON scalar types.
                    actual=json.loads(json.dumps(verify_wire_readback(reports/('vulsim_'+stage+'_layer_rc.tsv'),p)))
                    same(actual,archived['wire_RC_readback'],'actual stage wire RC readback')
                raw=read_labels(reports/('vulsim_'+stage),root/'contract.json',parsed['raw_report_units']['time']['to_ps'])
                same(raw,archived['model_labels'],'actual Q-D point/clock-path labels');labels+=len(raw)
                sdc={'synth':'1_synth','grt':'5_1_grt'}[stage]
                text=objects[files[f'results/{platform}/arithmetic_probe/base/{sdc}.sdc']]
                verify_sdc(text,p,m['period_ps'],rtl_ports(input_rtl,m['rtl_interface']['design']));sdc_count+=1
                instances=[line.split('\t')[:2] for line in objects[files[f'reports/{platform}/arithmetic_probe/base/vulsim_{stage}_instances.tsv']].splitlines()]
                stages[stage]={'labels':{x['id']:x for x in raw},'instances':instances,'metrics':archived};stage_count+=1
        replay[run['files']['manifest.json']]={'manifest':m,'specs':specs,'cells':cells,'stages':stages,
            'rtl_sha256':files['input.sv'],'contract_sha256':files['sample-contract.json'],'files':files}
    return replay,{'completed_runs':len(replay),'stages_reparsed':stage_count,'actual_SDC_checked':sdc_count,'actual_QD_labels_recomputed':labels,
                   'failed_runs_preserved':sum(json.loads(objects[r['files']['manifest.json']])['status']!='completed' for r in catalog)}


def replay_rows(data,replay):
    groups={};checked=0
    for row in data['rows']:
        run=replay[row['manifest_sha256']];sample=row['id'].split('/')[-2];stage=run['stages'][row['stage']];spec=run['specs'][sample]
        same(row['source_sha256'],run['rtl_sha256'],'dataset source identity');same(row['profile_sha256'],run['manifest']['platform_profile']['profile_sha256'],'dataset profile')
        label=stage['labels'][sample];same(row['delay_ps'],label['data_delay_ps'],'dataset measured Q-D delay')
        area=sequential=functional=0.;capture=launch=0;masters={}
        for name,master in stage['instances']:
            if not name.startswith(spec['instance_scope']) or master not in run['cells']:continue
            cell=run['cells'][master];functional+=cell['area_um2'];masters[master]=masters.get(master,0)+1
            if cell['sequential']:
                sequential+=cell['area_um2'];capture+=name.startswith(spec['instance_scope']+'y') or name.startswith(spec['instance_scope']+'dst');launch+=name.startswith(spec['instance_scope']+'src')
            elif name.startswith(spec['arithmetic_scope']):area+=cell['area_um2']
        same(area,row['comb_area_um2'],'actual unique scoped core area');same(capture,spec['fanout']*spec['result_width'],'actual capture DFF count')
        if 'features' in row:
            f=features(spec['lhs_width'],spec['rhs_width'],spec['result_width'],spec['fanout'],row['features']['abc_target_ps'],row['features']['sdc_period_ps'])
            for key,value in row['features'].items():same(value,f[key],'pre-mapping feature '+key)
            same(row['scope_masters'],masters,'scope master counts');same(row['actual_capture_DFFs'],capture,'sample capture count')
            same(row['sequential_boundary_area_um2'],sequential,'sample boundary sequential area')
        else:
            same(row['spec'],spec,'calibration actual operand graph');same(row['state_bits'],capture+launch,'actual state bits')
            same(row['scoped_functional_area_um2'],functional,'scoped actual functional area')
            same(row['scoped_sequential_area_um2'],sequential,'scoped sequential area')
            same(row['boundary_overhead_ps'],row['period_ps']-label['data_delay_ps']-label['slack_ps'],'boundary overhead no double uncertainty')
        key=(row['platform'],row['source_sha256'])
        if key in groups and groups[key]!=row['split']:raise ValueError('same source graph crosses dataset partitions')
        groups[key]=row['split'];checked+=1
    return checked


def isolated_test(dataset,models,report):
    count=0
    for row in report['reports']:
        platform,stage,operation=row['platform'],row['stage'],row['operation'];b=models[platform];model=b['stages'][stage]['operations'][operation]
        group=[r for r in dataset['rows'] if r['platform']==platform and r['stage']==stage and r['operation']==operation and r['split']=='test']
        for key,label,unit in [('delay_ps','delay','ps'),('comb_area_um2','area','um2')]:
            values=[infer(model[label],r['features']) for r in group];floor=max(1,b['mapping_abc_target_ps']*.001) if key=='delay_ps' else 1e-4
            actual=metric([r[key] for r in group],values,floor);actual['unit']=unit;same(actual,row['metrics'][label],'independent isolated test '+platform+'/'+stage+'/'+operation+'/'+label)
        count+=1
    return count


def verify(root=ROOT,external=False,parents=True,freeze=FREEZE):
    from .freeze_history import model_revision
    with model_revision(freeze):return _verify(root,external,parents,freeze)


def _verify(root,external,parents,freeze):
    root=Path(root);f=read(root/freeze);directory=root/f['evidence_directory'];index=read(directory/'index.json');same(sha(directory/'index.json'),f['evidence_index_sha256'],'model evidence index')
    from .freeze_history import source_location,MUTABLE_DOCUMENTATION
    for relative,h in f['files_sha256'].items():same(sha(source_location(root,freeze,relative,h)),h,'frozen model source '+relative)
    for path,h in f['historical_freezes'].items():same(sha(root/path),h,'preserved parent freeze')
    for path,h in index['files_sha256'].items():same(sha(directory/path),h,'model evidence payload')
    objects=pool(directory,index);compact=index.get('portable_scope','').startswith('compact_');full_directories=[]
    if compact:
        summary={'completed_runs':None,'stages_reparsed':0,'actual_SDC_checked':0,'actual_QD_labels_recomputed':0,
                 'raw_stage_replay':'requires explicit --verify-external and retained local full archive'}
        replay={}
        if external:
            notes=['run-summary.json']+(['interval-run-summary.json'] if 'interval_evidence' in index else [])
            for name in notes:
                note=json.loads(objects[index['documents'][name]]);full_directory=root/note['full_archive']
                if not full_directory.is_dir():raise ValueError('artifact_unavailable: '+note['full_archive'])
                full_directories.append(full_directory);members=[p for p in full_directory.rglob('*') if p.is_file()]
                same(hashlib.sha256(b''.join(sorted(p.read_bytes() for p in members))).hexdigest(),note['full_archive_sha256'],'complete retained raw text archive')
                full_index=read(full_directory/'index.prepared.json');raw_objects=pool(full_directory,full_index)
                catalog=json.loads(raw_objects[full_index['run_catalog']]);extra,counts=replay_runs(catalog,raw_objects)
                if replay.keys() & extra.keys():raise ValueError('same raw run appears in multiple archives')
                replay.update(extra)
                for key,value in counts.items():summary[key]=(summary.get(key) or 0)+value
            summary['raw_stage_replay']='actual retained original bytes; expanded reports/intermediate path points/instance lists all read'
    else:
        catalog=json.loads(objects[index['run_catalog']]);replay,summary=replay_runs(catalog,objects)
    documents={name:json.loads(objects[ref]) for name,ref in index['documents'].items()}
    replayed_rows=0
    if replay:
        for name in ('isolated-fitting-dataset-v2.json','isolated-independent-dataset-v2.json','state-stage-fitting-dataset-v5.json','state-stage-test-dataset-v5.json','context-qualification-dataset-v1.json'):
            if name in documents:replayed_rows+=replay_rows(documents[name],replay)
    interval_summary={}
    if 'native-interval-pilot-labels-v2.json' in documents or 'interval_evidence' in index:
        from .model_interval_evidence import verify_intervals
        interval_summary=verify_intervals(index,objects,documents,replay,same)
        replayed_rows+=interval_summary['interval_raw_rows_recomputed']
    isolated={p:documents['isolated-models-v2/'+p+'.tested.json'] for p in ('asap7','nangate45','sky130hd','gf180')}
    scopes=isolated_test(documents['isolated-independent-dataset-v2.json'],isolated,documents['isolated-models-v2/independent-test.json'])
    calibration_scopes=0
    test_key='calibrated-models-v6/calibration-independent-test.json'
    if test_key in documents:
        data=documents['state-stage-test-dataset-v5.json'];fitting_key='state-stage-fitting-dataset-v5.json'
        frozen=documents['calibrated-models-v6/calibration-selection-freeze.json']
        same(data['fitting_dataset_sha256'],index['documents'][fitting_key],'deferred test binds fitting rows')
        same(frozen['dataset_sha256'],index['documents'][fitting_key],'fitted data frozen before test')
        same(data['admission_sha256'],frozen['admission_sha256'],'same predeclared test task list')
        fitting_sources={r['source_sha256'] for r in documents[fitting_key]['rows']}
        if fitting_sources & {r['source_sha256'] for r in data['rows']}:raise ValueError('calibration fitting/test source overlap')
        for report in documents[test_key]['reports']:
            platform=report['platform'];bundle=documents['calibrated-models-v6/'+platform+'.json'];candidate_key='calibrated-models-v6/'+platform+'.candidate.json'
            item=next(x for x in frozen['models'] if x['platform']==platform);same(item['candidate_sha256'],index['documents'][candidate_key],'candidate frozen before test')
            same(bundle['stages'],documents[candidate_key]['stages'],'test did not change fitted parameters')
            ready=True
            for stage,result in report['stages'].items():
                if result['status']=='not_evaluated':ready=False;continue
                rows=[r for r in data['rows'] if r['platform']==platform and r['stage']==stage and r['split']=='test']
                actual=calibration_quality(bundle,stage,rows);same(actual,result,'independent stage/state/feasibility test')
                ready &= result['status']=='passed';calibration_scopes+=1
            same(bundle['quality_status'],'passed' if ready else 'failed','unready model never published passed')
    qualification_scopes=0
    qualification_key='qualified-models-v1/qualification-test.json'
    if qualification_key in documents:
        q=documents[qualification_key];rows=documents['context-qualification-dataset-v1.json']['rows']
        same(documents['context-qualification-dataset-v1.json']['not_training'],True,'qualification never fitting data')
        for result in q['reports']:
            platform=result['platform'];source_key='calibrated-models-v6/'+platform+'.json';source=documents[source_key]
            same(index['documents'][source_key],result['frozen_source_model_sha256'],'context check uses frozen numerical model')
            ready=True
            for context in result['contexts']:
                for stage,archived in context['stages'].items():
                    group=[r for r in rows if r['platform']==platform and r['stage']==stage and r['period_ps']==context['period_ps']]
                    actual=calibration_quality(source,stage,group);boundary=archived['boundary_qualification']
                    same(actual,{k:v for k,v in archived.items() if k!='boundary_qualification'},'frozen model additional context quality')
                    h=max(r['boundary_overhead_ps'] for r in group);control=max(r['delay_ps'] for r in group if r['spec']['role']=='state');b=source['stages'][stage]['boundary_model']
                    expected={'maximum_measured_H_ps':h,'measured_capture_control_path_ps':control,'required_without_extra_reserve_ps':h+control,
                        'frozen_register_overhead_ps':b['register_overhead_ps'],'frozen_input_overhead_ps':b['input_overhead_ps'],
                        'covered':min(b['register_overhead_ps'],b['input_overhead_ps'])+1e-6>=h+control}
                    same(expected,boundary,'measured boundary coverage')
                    if stage=='grt':ready &= actual['status']=='passed' and expected['covered'];qualification_scopes+=1
            same(result['grt_domain_status'],'passed' if ready else 'failed','qualified grt domain outcome')
            release_key='qualified-models-v1/'+platform+'.json'
            if ready:
                released=documents[release_key];same(set(released['stages']),{'grt'},'only qualified stage released')
                expected=json.loads(json.dumps(source['stages']['grt']))
                for operation in expected['operations'].values():
                    for condition in operation['domain']['conditions']:
                        condition['sdc_min_ps']=source['mapping_abc_target_ps'];condition['sdc_max_ps']=source['mapping_abc_target_ps']*1.5
                same(released['stages']['grt'],expected,'qualification changes no numerical coefficients or other shape domains')
                same(released['qualified_source_model_sha256'],index['documents'][source_key],'release inherited source model')
            elif release_key in documents:raise ValueError('failed qualification has a published model')
    native=0
    for row in index.get('native_reports',[]):
        report=documents[row['report']];bundle=documents[row['model']];same(report['request']['model_bundle_sha256'],index['documents'][row['model']],'actual requested model byte identity');verify_report(report,bundle,objects[row['rtl']]);verify_selection(report,bundle);native+=1
    resources=read(directory/'resources.json');entries=read(directory/'ledger.json.gz')['entries'];same(usage(entries),resources['cumulative_usage'],'settled ledger snapshot at seal');same(resources['cumulative_usage']['pending'],0,'no pending reservation at seal')
    before=read(directory/'usage_before.json.gz')['entries'];same(entries[:len(before)],before,'immutable pre-step7 charges');same(usage(entries[len(before):]),resources['new_usage'],'step7 actual charges')
    receipts=read(directory/'receipts.json.gz');same({r['id'] for r in receipts},{e['id'] for e in entries[len(before):]},'all step7 leaf receipts')
    for r in receipts:
        e=next(e for e in entries[len(before):] if e['id']==r['id']);same(r['record']['walltime_s'],e['walltime_s'],'leaf walltime');same(r['record']['exit_code'],e['exit_code'],'leaf outcome')
        same(r['record']['cleanup']['remaining_live_pids'],[],'actual leaf cleanup')
        if e.get('CPU_accounting')=='full_reservation_missing_CPU_evidence':same(e['CPU_time_s'],r['record']['CPU_limit_s'],'conservative CPU settlement')
        else:
            with tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp)/'time';path.write_text(r['GNU_time']);same(cpu_seconds(path),e['CPU_time_s'],'actual GNU CPU settlement')
    local=0
    if external:
        for archive in full_directories or [directory]:
            for item in read(archive/'local_artifacts.json.gz'):
                path=root/item['path']
                if not path.is_file():raise ValueError('artifact_unavailable: '+item['path'])
                same(path.stat().st_size,item['size'],'local actual artifact size');same(sha(path),item['sha256'],'local actual artifact');local+=1
    parent=None
    if parents:
        from .whole_graph_evidence import verify as parent_verify
        parent=parent_verify(root,external,True)['status']
    return {'status':'passed','completion_status':f['completion_status'],'scope':f['scope'],**summary,**interval_summary,'isolated_test_scopes_recomputed':scopes,
            'native_reports_recomputed':native,'actual_raw_dataset_rows_recomputed':replayed_rows,'calibration_test_scopes_recomputed':calibration_scopes,'qualified_grt_contexts_recomputed':qualification_scopes,'parent_status':parent,'resources':resources,'local_artifacts_read':local,
            'remote_retention':'not confirmed','full_step7_complete':False,
            'documentation_drift':[p for p in f['files_sha256'] if p in MUTABLE_DOCUMENTATION and (not (root/p).is_file() or sha(root/p)!=f['files_sha256'][p])]}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--freeze',type=Path,default=Path(FREEZE),help='explicit candidate or published freeze; identical checks apply');p.add_argument('--verify-external',action='store_true');p.add_argument('--no-parents',action='store_true');a=p.parse_args()
    print(json.dumps(verify(a.root,a.verify_external,not a.no_parents,a.freeze),ensure_ascii=False,indent=2))
