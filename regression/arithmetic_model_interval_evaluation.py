"""Quality/release failures and nonconstant interval inference without EDA."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from experiments.arithmetic_dse import model_mul_interval_evaluation as evaluation
from experiments.arithmetic_dse.model_collection import sha, write
from experiments.arithmetic_dse.model_features import infer as ordinary_infer
from experiments.arithmetic_dse.model_mul_intervals import CONFIG, infer, features
from experiments.arithmetic_dse.model_interval_training_evidence import verify_training
from experiments.arithmetic_dse.model_mul_interval_fit import quality
from experiments.arithmetic_dse.model_mul_interval_fit import fit as fit_intervals
from experiments.arithmetic_dse.model_training import metric
from experiments.arithmetic_dse.model_evidence import same


def predictor(scale):
    return {'kind':'linear','features':['width'],'intercept':0.,'coefficients':[scale]}


def fixture():
    entries = {name: {'quality_status':'awaiting_independent_test','validation_ready':True,
                     'delay':predictor(2.),'area':predictor(3.),'validation_delay_scale':1.05}
               for name in ('half/full/0/2','quarter/full/0/4')}
    rows = []
    for stage in ('synth','grt'):
        for name in entries:
            configuration = name.split('/')[0]
            for width in (20,28):
                rows.append({'id':stage+'/'+name+'/'+str(width), 'platform':'asap7','stage':stage,'split':'test',
                             'interval_key':name,'features':{'width':width},'delay_ps':2.*width,'comb_area_um2':3.*width,
                             'spec':{'width':width,'configuration':configuration,'result_shape':'full','first':0,
                                     'last':2 if configuration=='half' else 4,'groups':3 if configuration=='half' else 5}})
    return entries, rows


class IntervalInference(unittest.TestCase):
    def test_linear_and_tree_use_declared_interval_features(self):
        self.assertEqual(infer(predictor(2.),{'width':20}),40.)
        tree={'kind':'tree','features':['capture_bits'],'nodes':[{'feature':0,'threshold':16.,'left':1,'right':2},{'value':3.},{'value':7.}]}
        self.assertEqual(infer(tree,{'capture_bits':16}),3.)
        self.assertEqual(infer(tree,{'capture_bits':32}),7.)
        with self.assertRaisesRegex(ValueError,'feature names'):ordinary_infer(predictor(2.),{'width':20})
        tree['features']=['mapped_cell_count']
        with self.assertRaisesRegex(ValueError,'feature names'):infer(tree,{'mapped_cell_count':16})

    def test_quality_counts_and_equivalent_ranking(self):
        entries,rows=fixture()
        models={'asap7':{'mapping_abc_target_ps':1500,'stages':{'grt':{}}}}
        fits={'asap7':{s:{'model':{'intervals':copy.deepcopy(entries)}} for s in ('synth','grt')}}
        report=evaluation.compute_report(rows,models,fits)['asap7']
        self.assertEqual(report['quality_status'],'passed')
        grt=report['stages']['grt'];self.assertEqual(grt['samples'],4)
        self.assertEqual(grt['ranking']['denominator'],4)
        self.assertEqual(grt['ranking']['matching_pairs'],4)
        for item in grt['intervals'].values():
            self.assertEqual(item['false_feasible'],0)
            self.assertEqual(item['denominator'],22)
            self.assertGreater(item['conservative_rejections'],0)
        fits['asap7']['grt']['model']['intervals']['half/full/0/2']['delay']=predictor(1.)
        failed=evaluation.compute_report(rows,models,fits)['asap7']
        self.assertEqual(failed['quality_status'],'failed')
        self.assertGreater(failed['stages']['grt']['intervals']['half/full/0/2']['false_feasible'],0)

    def test_missing_interval_width_cannot_shrink_denominator(self):
        entries,rows=fixture();models={'asap7':{'mapping_abc_target_ps':1500,'stages':{'grt':{}}}}
        fits={'asap7':{s:{'model':{'intervals':entries}} for s in ('synth','grt')}}
        with self.assertRaisesRegex(ValueError,'widths'):evaluation.compute_report(rows[:-1],models,fits)
        with self.assertRaisesRegex(ValueError,'coverage'):evaluation.compute_report([r for r in rows if r['interval_key']!='half/full/0/2'],models,fits)


class DatasetCoverage(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);self.root=Path(tmp.name)
        self.path=self.root/'data.json';self.admission=self.root/'admission.json'
        self.spec={'id':'s000','width':8,'capture_width':16,'input_widths':[8,8],
                   'block_width':4,'configuration':'half','result_shape':'full','first':0,'last':2}
        source=self.root/'input.sv';source.write_text('// TEST_ONLY dataset validation fixture\n')
        contract=self.root/'contract.json';write(contract,{'labels':[self.spec]})
        task={'id':'TEST_ONLY_train','platform':'asap7','split':'train','stage':'grt',
              'sample_contract':str(contract),'sample_contract_sha256':sha(contract),
              'rtl':str(source),'rtl_sha256':sha(source),'profile_sha256':'TEST_ONLY_profile','period_ps':1500,'abc_target_ps':1500}
        write(self.admission,{'supplemental_protocol':{'sha256':sha(CONFIG)},'tasks':[task]})
        self.rows=[{'id':'TEST_ONLY_train/s000/'+s,'platform':'asap7','stage':s,'split':'train','spec':self.spec,
                    'source_sha256':sha(source),'contract_sha256':sha(contract),'profile_sha256':'TEST_ONLY_profile',
                    'period_ps':1500,'abc_target_ps':1500,'features':features(self.spec),'interval_key':'half/full/0/2',
                    'delay_ps':20.,'comb_area_um2':30.,'launch_DFFs':16,'capture_DFFs':16} for s in ('synth','grt')]
        self.data={'version':'arithmetic-mul-interval-dataset-v1','admission_path':str(self.admission),
                   'admission_sha256':sha(self.admission),'protocol_sha256':sha(CONFIG),'rows':self.rows,'failures':[]}
        write(self.path,self.data)

    def test_complete_data_and_actual_measurement_replay(self):
        with patch.object(evaluation,'extract',return_value=copy.deepcopy(self.data)):
            data,_=evaluation.validate_dataset(self.path,['train']);self.assertEqual(len(data['rows']),2)
        changed=copy.deepcopy(self.data);changed['rows'][0]['delay_ps']+=1
        with patch.object(evaluation,'extract',return_value=changed):
            with self.assertRaisesRegex(ValueError,'measurement replay'):evaluation.validate_dataset(self.path,['train'])

    def test_missing_duplicate_or_wrong_split_is_rejected(self):
        for rows in (self.rows[:-1],self.rows+[self.rows[0]]):
            bad=copy.deepcopy(self.data);bad['rows']=rows;write(self.path,bad)
            with self.assertRaisesRegex(ValueError,'coverage'):evaluation.validate_dataset(self.path,['train'])
        bad=copy.deepcopy(self.data);bad['rows'][0]['split']='test';write(self.path,bad)
        with self.assertRaisesRegex(ValueError,'frozen task'):evaluation.validate_dataset(self.path,['train'])

    def test_postmapping_features_and_boolean_counts_are_rejected(self):
        for change in ('features','boundary','negative'):
            bad=copy.deepcopy(self.data);r=bad['rows'][0]
            if change=='features':r['features']['first']=False
            elif change=='boundary':r['capture_DFFs']=True
            else:r['delay_ps']=-1.
            write(self.path,bad)
            with self.assertRaises(ValueError):evaluation.validate_dataset(self.path,['train'])


class IndependentRelease(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);self.root=Path(tmp.name)
        self.selection=self.root/'selection-freeze.json';self.admission=self.root/'admission.json'
        self.fitting=self.root/'fitting.json';self.test=self.root/'test.json';self.candidate=self.root/'asap7.candidate.json'
        self.result=self.root/'evaluation'/'independent-test.json'
        entries,rows=fixture();self.rows=rows
        write(self.admission,{'test_read_after_fit_only':True,'supplemental_protocol':{'path':str(CONFIG),'sha256':sha(CONFIG)},
                             'tasks':[{'platform':'asap7','split':s,'rtl_sha256':s} for s in ('train','validation','test')]})
        write(self.fitting,{'admission_path':str(self.admission),'admission_sha256':sha(self.admission),'protocol_sha256':sha(CONFIG),'failures':[],
                           'rows':[{'platform':'asap7','split':s,'source_sha256':s} for s in ('train','validation')]})
        write(self.test,{'admission_sha256':sha(self.admission),'rows':rows})
        self.bundle={'target_platform':'asap7','quality_status':'awaiting_independent_test','mapping_abc_target_ps':1500,
                     'interval_fit_dataset_sha256':sha(self.fitting),'interval_fit_protocol_sha256':sha(CONFIG),
                     'interval_base_model_sha256':'TEST_ONLY_base',
                     'stages':{'grt':{'mul_interval_model':{'quality_status':'awaiting_independent_test','intervals':entries},
                                      'TEST_ONLY_unchanged_base':{'numeric_parameters':[1.234,5.678]}}}}
        self.fits={s:{'model':{'quality_status':'awaiting_independent_test','intervals':copy.deepcopy(entries)}} for s in ('synth','grt')}
        source='experiments/arithmetic_dse/model_mul_interval_evaluation.py'
        dest=self.root/'training-source'/source;dest.parent.mkdir(parents=True);dest.write_bytes((evaluation.ROOT/source).read_bytes())
        self.sources={source:sha(dest)}
        self.freeze()
        # Physical extraction is deliberately mocked in these software tests;
        # the real runner validates every test task and actual measurement.
        self.mock=patch.object(evaluation,'validate_dataset',side_effect=lambda path,splits,selection:(json.loads(Path(path).read_text()),{})).start()
        self.addCleanup(patch.stopall)

    def freeze(self):
        write(self.candidate,self.bundle);write(self.root/'asap7.fit.json',self.fits)
        write(self.selection,{'version':'arithmetic-mul-interval-selection-freeze-v1','admission_sha256':sha(self.admission),
                              'protocol_sha256':sha(CONFIG),'dataset_sha256':sha(self.fitting),'fitting_dataset_path':str(self.fitting),
                              'models':[{'platform':'asap7','candidate_sha256':sha(self.candidate),'fit_report_sha256':sha(self.root/'asap7.fit.json'),
                                         'base_model_sha256':'TEST_ONLY_base'}],'test_consumed':False,'training_sources':self.sources})

    def run_test(self):return evaluation.evaluate(self.test,self.selection,self.result.parent)

    def test_pass_replay_release_preserves_coefficients_and_base(self):
        before=self.selection.read_bytes();self.run_test()
        evaluation.verify(self.selection,self.result)
        result=evaluation.publish(self.selection,self.result,self.root/'released')
        self.assertEqual(len(result['published']),1)
        released=json.loads((self.root/'released/asap7.json').read_text())
        self.assertEqual(released['stages']['grt']['TEST_ONLY_unchanged_base'],self.bundle['stages']['grt']['TEST_ONLY_unchanged_base'])
        original=self.bundle['stages']['grt']['mul_interval_model']['intervals']
        for name,entry in released['stages']['grt']['mul_interval_model']['intervals'].items():
            for field in ('delay','area','validation_delay_scale'):self.assertEqual(entry[field],original[name][field])
        self.assertEqual(self.selection.read_bytes(),before)
        self.assertFalse(result['full_step7_complete'])

    def test_new_output_directory_does_not_permit_retesting(self):
        self.run_test()
        with self.assertRaisesRegex(ValueError,'already consumed'):evaluation.evaluate(self.test,self.selection,self.root/'second')

    def test_grt_quality_failure_never_publishes(self):
        for entry in self.fits['grt']['model']['intervals'].values():entry['delay']=predictor(1.)
        self.bundle['stages']['grt']['mul_interval_model']['intervals']=copy.deepcopy(self.fits['grt']['model']['intervals']);self.freeze()
        report=self.run_test();self.assertEqual(report['platforms']['asap7']['quality_status'],'failed')
        release=evaluation.publish(self.selection,self.result,self.root/'released')
        self.assertEqual(release['published'],[]);self.assertEqual(release['failed_platforms'],['asap7'])
        self.assertFalse((self.root/'released/asap7.json').exists())

    def test_synth_failure_is_retained_without_blocking_qualified_grt(self):
        for entry in self.fits['synth']['model']['intervals'].values():entry['area']=predictor(20.)
        self.freeze();report=self.run_test()
        self.assertEqual(report['platforms']['asap7']['stages']['synth']['status'],'failed')
        self.assertEqual(report['platforms']['asap7']['quality_status'],'passed')
        evaluation.publish(self.selection,self.result,self.root/'released')
        released=json.loads((self.root/'released/asap7.json').read_text());self.assertEqual(set(released['stages']),{'grt'})

    def test_tampered_candidate_and_snapshot_rejected_before_test_read(self):
        self.bundle['mapping_abc_target_ps']=2000;write(self.candidate,self.bundle)
        with self.assertRaisesRegex(ValueError,'candidate'):self.run_test()
        self.mock.assert_not_called();self.freeze()
        snapshot=self.root/'training-source'/next(iter(self.sources));snapshot.write_text('changed')
        with self.assertRaisesRegex(ValueError,'source'):self.run_test()
        self.mock.assert_not_called()

    def test_tampered_report_or_test_data_blocks_publication(self):
        self.run_test();raw=self.result.read_bytes();r=json.loads(raw);r['platforms']['asap7']['quality_status']='forged';write(self.result,r)
        with self.assertRaisesRegex(ValueError,'identity'):evaluation.publish(self.selection,self.result,self.root/'released')
        self.result.write_bytes(raw);self.rows[0]['delay_ps']=999;write(self.test,{'admission_sha256':sha(self.admission),'rows':self.rows})
        with self.assertRaisesRegex(ValueError,'dataset'):evaluation.publish(self.selection,self.result,self.root/'released')
        self.assertFalse((self.root/'released').exists())


class PortableTraining(unittest.TestCase):
    def setUp(self):
        self.index={'documents':{},'interval_training_evidence':[]};self.objects={};self.documents={}
        def blob(text):
            digest=hashlib.sha256(text.encode()).hexdigest();self.objects[digest]=text;return digest
        def document(name,value):
            self.documents[name]=value;self.index['documents'][name]=blob(json.dumps(value));return name
        protocol=json.loads(CONFIG.read_text());protocol_digest=blob(CONFIG.read_bytes().decode())
        entries,test_rows=fixture();fit_rows=[]
        for stage in ('synth','grt'):
            for name in entries:
                for split in ('train','validation'):
                    for width in protocol['splits'][split]:
                        fit_rows.append({'id':f'{stage}/{name}/{width}','platform':'asap7','stage':stage,'split':split,
                                         'interval_key':name,'features':{'width':width},'delay_ps':2.*width,
                                         'comb_area_um2':3.*width,'source_sha256':split+str(width)})
        for row in test_rows:row['source_sha256']='test'+str(row['features']['width'])
        admission_name=document('admission',{'TEST_ONLY':'portable numerical fixture'})
        admission_digest=self.index['documents'][admission_name]
        fitting_name=document('fitting',{'rows':fit_rows,'failures':[],'admission_sha256':admission_digest,'protocol_sha256':protocol_digest})
        base={'quality_status':'passed','mapping_abc_target_ps':1500,'stages':{'grt':{'state_model':{'TEST_ONLY_coefficient':1.5}}}}
        base_name=document('base',base)
        document('qualified-models-v1/asap7.json',base)
        candidate={'target_platform':'asap7','quality_status':'awaiting_independent_test','mapping_abc_target_ps':1500,
                   'interval_fit_dataset_sha256':self.index['documents'][fitting_name],
                   'interval_fit_protocol_sha256':protocol_digest,'interval_base_model_sha256':self.index['documents'][base_name],
                   'stages':copy.deepcopy(base['stages'])}
        fit={}
        for stage in ('synth','grt'):
            fit[stage]={'model':{'quality_status':'awaiting_independent_test','intervals':copy.deepcopy(entries)},'intervals':{}}
            for name,entry in entries.items():
                val=[r for r in fit_rows if r['stage']==stage and r['split']=='validation' and r['interval_key']==name]
                selected={}
                for label,field,floor in [('delay','delay_ps',1.5),('area','comb_area_um2',1e-4)]:
                    selected[label]={'validation_before_margin':metric([r[field] for r in val],[infer(entry[label],r['features']) for r in val],floor)}
                fit[stage]['intervals'][name]={'quality_after_margin':quality(entry,val,1500),'selection':selected}
        candidate['stages']['grt']['mul_interval_model']=copy.deepcopy(fit['grt']['model'])
        fit_name=document('fit',fit);candidate_name=document('candidate',candidate)
        trainer_digest=blob('# TEST_ONLY numerical fixture, no training claim\n')
        selection={'dataset_sha256':self.index['documents'][fitting_name],'admission_sha256':admission_digest,
                   'protocol_sha256':protocol_digest,'test_consumed':False,'training_sources':{'TEST_ONLY_trainer.py':trainer_digest},
                   'models':[{'platform':'asap7','candidate_sha256':self.index['documents'][candidate_name],
                              'fit_report_sha256':self.index['documents'][fit_name],'base_model_sha256':self.index['documents'][base_name]}]}
        selection_name=document('selection',selection)
        test_name=document('test',{'rows':test_rows,'failures':[],'admission_sha256':admission_digest})
        result={'selection_freeze_sha256':self.index['documents'][selection_name],'test_dataset_sha256':self.index['documents'][test_name],
                'platforms':evaluation.compute_report(test_rows,{'asap7':candidate},{'asap7':fit}),
                'numeric_parameters_changed':False,'test_used_for_fitting':False}
        result_name=document('result',result)
        consumption_name=document('consumption',{'status':'completed','report_sha256':self.index['documents'][result_name],
                                                'selection_sha256':self.index['documents'][selection_name],
                                                'test_dataset_sha256':self.index['documents'][test_name]})
        self.record={'fitting_data':fitting_name,'selection':selection_name,'admission':admission_name,'protocol_blob':protocol_digest,
                     'training_source_blobs':{'TEST_ONLY_trainer.py':trainer_digest},'candidates':{'asap7':candidate_name},
                     'fit_reports':{'asap7':fit_name},'base_models':{'asap7':base_name},'test_data':test_name,
                     'test_result':result_name,'consumption':consumption_name,'released':{}}
        self.index['interval_training_evidence']=[self.record]

    def check(self,documents=None):return verify_training(self.index,self.objects,documents or self.documents,same)

    def test_frozen_margin_and_independent_metrics_replay(self):
        report=self.check();self.assertEqual(report['interval_validation_scopes_recomputed'],4)
        self.assertEqual(report['interval_independent_test_stages_recomputed'],2)
        self.assertEqual(report['interval_training_test_rows_recomputed'],28)

    def test_test_leakage_margin_and_quality_mutations_rejected(self):
        for change in ('leak','margin','quality','base'):
            bad=copy.deepcopy(self.documents)
            if change=='leak':bad['fitting']['rows'][0]['split']='test'
            elif change=='margin':bad['fit']['synth']['model']['intervals']['half/full/0/2']['validation_delay_scale']=1.2
            elif change=='quality':bad['result']['platforms']['asap7']['quality_status']='failed'
            else:bad['candidate']['stages']['grt']['state_model']['TEST_ONLY_coefficient']=2.
            with self.subTest(change=change):
                with self.assertRaises(ValueError):self.check(bad)

    def test_actual_test_measurement_requires_selection_binding(self):
        documents=copy.deepcopy(self.documents);replay={}
        for row in documents['test']['rows']:
            row['manifest_sha256']='TEST_ONLY_'+str(row['features']['width'])
            replay[row['manifest_sha256']]={'manifest':{'selection_freeze_sha256':self.index['documents']['selection']}}
        result=verify_training(self.index,self.objects,documents,same,replay)
        self.assertEqual(result['interval_test_run_selection_bindings_checked'],2)
        replay['TEST_ONLY_20']['manifest']['selection_freeze_sha256']='wrong_selection'
        with self.assertRaises(ValueError):verify_training(self.index,self.objects,documents,same,replay)


class FittingABI(unittest.TestCase):
    def test_actual_nonconstant_fit_and_deterministic_reproduction_without_test(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);base=root/'base';base.mkdir();admission=root/'admission.json';data_path=root/'fitting.json'
            cfg=json.loads(CONFIG.read_text());rows=[];tasks=[]
            for split in ('train','validation'):
                for width in cfg['splits'][split]:
                    source=split+str(width);tasks.append({'platform':'asap7','split':split,'rtl_sha256':source})
                    for stage in ('synth','grt'):
                        for configuration,last in [('half',2),('quarter',4)]:
                            spec={'width':width,'capture_width':2*width,'input_widths':[width,width],'block_width':width//(2 if configuration=='half' else 4),'first':0,'last':last}
                            rows.append({'platform':'asap7','stage':stage,'split':split,'source_sha256':source,
                                         'profile_sha256':'TEST_ONLY_profile','abc_target_ps':1500,'period_ps':1500,
                                         'interval_key':configuration+'/full/0/'+str(last),'features':features(spec),
                                         'delay_ps':5.+2.*width,'comb_area_um2':3.+width*width})
            write(admission,{'test_read_after_fit_only':True,'supplemental_protocol':{'path':str(CONFIG),'sha256':sha(CONFIG)},'tasks':tasks})
            data={'admission_path':str(admission),'admission_sha256':sha(admission),'protocol_sha256':sha(CONFIG),'rows':rows,'failures':[]}
            write(data_path,data);write(base/'asap7.json',{'target_platform':'asap7','platform_profile_sha256':'TEST_ONLY_profile',
                  'quality_status':'passed','mapping_abc_target_ps':1500,'stages':{'grt':{}},'data_role':'TEST_ONLY synthetic fit fixture'})
            with patch.object(evaluation,'validate_dataset',return_value=(data,{})):
                fit_intervals(data_path,base,root/'first')
                result=evaluation.reproduce(root/'first/selection-freeze.json',base,root/'reproduced')
            self.assertEqual(result['status'],'passed');self.assertFalse(result['test_labels_read'])
            candidate=json.loads((root/'first/asap7.candidate.json').read_text())
            entries=candidate['stages']['grt']['mul_interval_model']['intervals']
            self.assertTrue(all(e['validation_ready'] for e in entries.values()))
            self.assertTrue(all(e['delay']['features'] for e in entries.values()))
            self.assertFalse((root/'first/independent-test-consumption.json').exists())


if __name__=='__main__':unittest.main()
