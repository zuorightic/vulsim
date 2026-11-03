"""Portable numerical replay for fitted native-template interval models.

Static graph/label identity is checked by model_interval_evidence; this layer
checks training/test separation, the frozen margin and release decisions.
It does not import an ML library or claim to rerun fitting.
"""
import copy
import json
from .model_mul_intervals import infer
from .model_mul_interval_fit import quality
from .model_mul_interval_evaluation import compute_report
from .model_training import metric


def verify_training(index, objects, documents, same, replay=None):
    scopes = tests = releases = rows_checked = bound_test_runs = 0
    for record in index.get('interval_training_evidence', []):
        fitting = documents[record['fitting_data']]
        selection = documents[record['selection']]
        admission = documents[record['admission']]
        protocol = json.loads(objects[record['protocol_blob']])
        same(selection['dataset_sha256'], index['documents'][record['fitting_data']], 'interval frozen fitting data')
        same(selection['admission_sha256'], index['documents'][record['admission']], 'interval frozen admission')
        same(selection['protocol_sha256'], record['protocol_blob'], 'interval frozen protocol')
        same(fitting['admission_sha256'], selection['admission_sha256'], 'interval fitting admission')
        same(fitting['protocol_sha256'], selection['protocol_sha256'], 'interval fitting protocol')
        same(fitting['failures'], [], 'complete fitting partitions')
        same(selection['test_consumed'], False, 'immutable pre-test selection')
        if any(r['split'] not in ('train','validation') for r in fitting['rows']):
            raise ValueError('interval test data leaked into fitting')
        for name, digest in selection['training_sources'].items():
            same(record['training_source_blobs'][name], digest, 'executed interval training source')
            if digest not in objects:
                raise ValueError('missing executed interval training source bytes')
        models = {}; fits = {}
        for item in selection['models']:
            platform = item['platform']
            candidate_name = record['candidates'][platform]
            fit_name = record['fit_reports'][platform]
            base_name = record['base_models'][platform]
            same(index['documents'][candidate_name], item['candidate_sha256'], 'frozen interval candidate')
            same(index['documents'][fit_name], item['fit_report_sha256'], 'frozen interval fit report')
            same(index['documents'][base_name], item['base_model_sha256'], 'qualified interval base')
            same(index['documents']['qualified-models-v1/'+platform+'.json'],item['base_model_sha256'],'interval base has independent parent qualification evidence')
            model = documents[candidate_name]; fit = documents[fit_name]; base = documents[base_name]
            same(model['interval_fit_dataset_sha256'], selection['dataset_sha256'], 'candidate fitting identity')
            same(model['interval_fit_protocol_sha256'], selection['protocol_sha256'], 'candidate protocol identity')
            same(model['interval_base_model_sha256'], index['documents'][base_name], 'candidate qualified base identity')
            same(model['quality_status'], 'awaiting_independent_test', 'candidate never preapproved')
            same(model['stages']['grt']['mul_interval_model'], fit['grt']['model'], 'consumed fitted interval predictor')
            inherited = copy.deepcopy(model['stages']['grt']);del inherited['mul_interval_model']
            same(inherited, base['stages']['grt'], 'interval fitting preserves qualified base stage')
            for stage in protocol['stages']:
                stage_rows = [r for r in fitting['rows'] if r['platform']==platform and r['stage']==stage]
                entries = fit[stage]['model']['intervals']
                same(set(entries), {r['interval_key'] for r in stage_rows}, 'complete fitted interval classes')
                for name, entry in entries.items():
                    train = [r for r in stage_rows if r['interval_key']==name and r['split']=='train']
                    val = [r for r in stage_rows if r['interval_key']==name and r['split']=='validation']
                    for split, rows in [('train',train),('validation',val)]:
                        same(len(rows),len(protocol['splits'][split]),'one structural interval per fitting width')
                        same({r['features']['width'] for r in rows},set(protocol['splits'][split]),'declared interval fitting widths')
                    scale = max([1.]+[r['delay_ps']/max(1e-9,infer(entry['delay'],r['features'])) for r in val])*1.05
                    same(entry['validation_delay_scale'],scale,'margin determined by validation only')
                    result = quality(entry,val,model['mapping_abc_target_ps'])
                    same(fit[stage]['intervals'][name]['quality_after_margin'],result,'actual interval validation quality')
                    same(entry['validation_ready'],result['status']=='passed','interval validation gate')
                    for label,field,floor in [('delay','delay_ps',max(1,model['mapping_abc_target_ps']*.001)),('area','comb_area_um2',1e-4)]:
                        actual=metric([r[field] for r in val],[infer(entry[label],r['features']) for r in val],floor)
                        same(actual,fit[stage]['intervals'][name]['selection'][label]['validation_before_margin'],'selected predictor validation before reserve')
                    rows_checked += len(train)+len(val);scopes += 1
            models[platform]=model;fits[platform]=fit
        if record.get('test_data'):
            data=documents[record['test_data']];result=documents[record['test_result']]
            same(result['selection_freeze_sha256'],index['documents'][record['selection']],'independent test frozen selection')
            same(result['test_dataset_sha256'],index['documents'][record['test_data']],'independent interval test identity')
            same(data['admission_sha256'],selection['admission_sha256'],'independent interval test admission')
            same(data['failures'],[],'complete independent interval test')
            if any(r['split']!='test' for r in data['rows']):raise ValueError('non-test row in independent interval test')
            if {r['source_sha256'] for r in fitting['rows']} & {r['source_sha256'] for r in data['rows']}:
                raise ValueError('same interval source crosses fitting/test partition')
            same(result['platforms'],compute_report(data['rows'],models,fits),'independent interval quality/ranking recomputation')
            same(result['numeric_parameters_changed'],False,'test cannot change interval parameters')
            same(result['test_used_for_fitting'],False,'test never used for fitting')
            consumption=documents[record['consumption']]
            same(consumption['status'],'completed','single-consumption test completed')
            same(consumption['report_sha256'],index['documents'][record['test_result']],'single-consumption test result')
            same(consumption['selection_sha256'],index['documents'][record['selection']],'single-consumption selection')
            same(consumption['test_dataset_sha256'],index['documents'][record['test_data']],'single-consumption dataset')
            if replay:
                for identity in {r['manifest_sha256'] for r in data['rows']}:
                    same(replay[identity]['manifest']['selection_freeze_sha256'],index['documents'][record['selection']],
                         'actual independent measurement was launched with this frozen selection')
                    bound_test_runs+=1
            rows_checked+=len(data['rows']);tests+=len(result['platforms'])*len(protocol['stages'])
            for platform, name in record.get('released',{}).items():
                same(result['platforms'][platform]['quality_status'],'passed','failed interval model cannot be released')
                released=documents[name];expected=copy.deepcopy(models[platform])
                expected['stages']={'grt':expected['stages']['grt']};expected['quality_status']='passed'
                expected['id']=platform+'-native-mul-interval-qualified-v1'
                interval_model=expected['stages']['grt']['mul_interval_model'];interval_model['quality_status']='passed'
                for entry in interval_model['intervals'].values():entry['quality_status']='passed'
                expected['interval_independent_test_sha256']=index['documents'][record['test_result']]
                expected['interval_selection_freeze_sha256']=index['documents'][record['selection']]
                expected['interval_release_scope']='one qualified template interval per stage at fixed R; base node/state/stage domains unchanged; not full step seven'
                same(released,expected,'released interval model changes no fitted numbers or domain');releases+=1
        elif record.get('released'):
            raise ValueError('interval release without an independent test')
    return {'interval_validation_scopes_recomputed':scopes,'interval_independent_test_stages_recomputed':tests,
            'interval_released_models_recomputed':releases,'interval_training_test_rows_recomputed':rows_checked,
            'interval_test_run_selection_bindings_checked':bound_test_runs}
