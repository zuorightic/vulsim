"""Deferred-test release gates and semantic mutations of actual interval evidence."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from experiments.arithmetic_dse import model_collection as collection
from experiments.arithmetic_dse.model_mul_interval_fit import extract
from experiments.arithmetic_dse.model_mul_intervals import CONFIG
from experiments.arithmetic_dse.model_evidence import pool,same,replay_runs
from experiments.arithmetic_dse.model_interval_evidence import verify_intervals

ROOT=Path(__file__).resolve().parents[1]


class TestRelease(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.admission=self.root/'admission.json';self.data=self.root/'fitting.json';self.freeze=self.root/'selection-freeze.json';self.candidate=self.root/'asap7.candidate.json'
        self.a={'version':'arithmetic-model-collection-admission-v1','id':'TEST_ONLY_release_gate','purpose':'arithmetic_model_collection',
            'test_read_after_fit_only':True,'policy_sha256':collection.sha(collection.POLICY),'protocol_sha256':collection.sha(collection.PROTOCOL),'automatic_retries':0,
            'supplemental_protocol':{'path':str(CONFIG),'sha256':collection.sha(CONFIG)},
            'tasks':[{'id':s,'split':s,'platform':'asap7','rtl_sha256':s} for s in ('train','validation','test')]}
        self.save(self.admission,self.a)
        d={'admission_sha256':collection.sha(self.admission),'protocol_sha256':collection.sha(CONFIG),'failures':[],
            'rows':[{'split':s,'platform':'asap7','source_sha256':s} for s in ('train','validation')]}
        self.save(self.data,d)
        b={'target_platform':'asap7','quality_status':'awaiting_independent_test','interval_fit_dataset_sha256':collection.sha(self.data),
            'interval_fit_protocol_sha256':collection.sha(CONFIG),'stages':{'grt':{'mul_interval_model':{'intervals':{'TEST_ONLY':{'validation_ready':True}}}}}}
        self.save(self.candidate,b)
        self.f={'version':'arithmetic-mul-interval-selection-freeze-v1','admission_sha256':collection.sha(self.admission),'protocol_sha256':collection.sha(CONFIG),
            'fitting_dataset_path':str(self.data),'dataset_sha256':collection.sha(self.data),'test_consumed':False,
            'models':[{'platform':'asap7','candidate_sha256':collection.sha(self.candidate)}]}
        self.save(self.freeze,self.f)

    def save(self,path,data):path.write_text(json.dumps(data))
    def check(self):return collection.verify_test_release(self.admission,self.freeze,['asap7'])

    def test_complete_release(self):self.assertEqual(self.check(),collection.sha(self.freeze))

    def test_missing_freeze_blocks_runner_and_extraction_before_any_work(self):
        with patch.object(collection.subprocess,'call') as backend:
            with self.assertRaisesRegex(ValueError,'selection-freeze'):collection.run(self.root,['test'])
            backend.assert_not_called()
        with self.assertRaisesRegex(ValueError,'selection-freeze'):extract(self.root,['test'])

    def test_direct_backend_admission_also_blocks(self):
        args=SimpleNamespace(admission=self.admission,admission_id=self.a['id'],task_id='test',selection_freeze=None)
        with self.assertRaisesRegex(ValueError,'selection-freeze'):collection.verify_admission(args,{},None,None)

    def test_default_runner_skips_tests(self):
        for split in ('train','validation'):
            d=self.root/'runs'/split;d.mkdir(parents=True);self.save(d/'manifest.json',{'status':'completed'})
        with patch.object(collection.subprocess,'call') as backend:
            collection.run(self.root);backend.assert_not_called()
        self.assertFalse((self.root/'runs/test').exists())

    def test_runner_forwards_release_to_backend(self):
        def backend(cmd,**kwargs):
            self.assertEqual(cmd[cmd.index('--selection-freeze')+1],str(self.freeze))
            d=self.root/'runs/test';d.mkdir();self.save(d/'manifest.json',{'status':'completed'});return 0
        # The remaining launch fields are irrelevant to identity checks but
        # required to assemble the backend command; update the frozen binding.
        t=self.a['tasks'][-1];t.update(rtl='fixture.sv',top='Fixture',period_ps=1500,abc_target_ps=1500,stage='grt',sample_contract='contract.json')
        self.save(self.admission,self.a)
        d=json.loads(self.data.read_text());d['admission_sha256']=collection.sha(self.admission);self.save(self.data,d)
        b=json.loads(self.candidate.read_text());b['interval_fit_dataset_sha256']=collection.sha(self.data);self.save(self.candidate,b)
        self.f.update(admission_sha256=collection.sha(self.admission),dataset_sha256=collection.sha(self.data));self.f['models'][0]['candidate_sha256']=collection.sha(self.candidate);self.save(self.freeze,self.f)
        (self.root/'runs').mkdir()
        with patch.object(collection.subprocess,'call',side_effect=backend):collection.run(self.root,['test'],selection_freeze=self.freeze)

    def test_changed_freeze_bindings_and_candidate_rejected(self):
        for key in ('admission_sha256','protocol_sha256','dataset_sha256'):
            with self.subTest(key=key):
                bad=copy.deepcopy(self.f);bad[key]='changed';self.save(self.freeze,bad)
                with self.assertRaises(ValueError):self.check()
        self.save(self.freeze,self.f);b=json.loads(self.candidate.read_text());b['stages']['grt']['mul_interval_model']['intervals']['TEST_ONLY']['validation_ready']=False;self.save(self.candidate,b)
        with self.assertRaises(ValueError):self.check()
        self.f['models'][0]['candidate_sha256']=collection.sha(self.candidate);self.save(self.freeze,self.f)
        with self.assertRaisesRegex(ValueError,'validation-ready'):self.check()

    def test_test_rows_cannot_qualify_as_fitting_data(self):
        d=json.loads(self.data.read_text());d['rows'][0]['split']='test';self.save(self.data,d);self.f['dataset_sha256']=collection.sha(self.data);self.save(self.freeze,self.f)
        with self.assertRaisesRegex(ValueError,'train/validation'):self.check()


class IntervalEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        directory=ROOT/'experiments/arithmetic/evidence/step7_models_v1';cls.index=json.loads((directory/'index.json').read_text());cls.objects=pool(directory,cls.index)
        cls.documents={k:json.loads(cls.objects[v]) for k,v in cls.index['documents'].items()}
        note=cls.documents['interval-run-summary.json'];archive=ROOT/note['full_archive'];i=json.loads((archive/'index.prepared.json').read_text());o=pool(archive,i)
        cls.replay,_=replay_runs(json.loads(o[i['run_catalog']]),o)

    def check(self,documents=None,replay=None,index=None):
        return verify_intervals(index or self.index,self.objects,documents or self.documents,self.replay if replay is None else replay,same)

    def test_actual_portable_and_external_interval_replay(self):
        portable=self.check(replay={});actual=self.check()
        self.assertEqual(portable['interval_raw_rows_recomputed'],0)
        self.assertEqual(actual['interval_raw_rows_recomputed'],24)
        self.assertEqual(actual['interval_RTL_observations_recomputed'],3216)
        self.assertEqual(actual['interval_untrimmed_checks_recomputed'],6432)
        self.assertEqual(actual['interval_mechanism_platforms_recomputed'],4)

    def test_wrong_functional_artifact_and_forged_RTL_observation_rejected(self):
        name=self.index['interval_evidence']['functional']
        bad=dict(self.documents);bad[name]=[]
        with self.assertRaises((ValueError,TypeError,KeyError)):self.check(bad)
        bad=copy.deepcopy(self.documents);obs=bad[name]['observations'][-1];obs['observed_hex']=format(int(obs['observed_hex'],16)^1,'x')
        with self.assertRaisesRegex(ValueError,'RTL interval observation'):self.check(bad)

    def test_missing_observation_and_features_rejected(self):
        name=self.index['interval_evidence']['functional'];bad=copy.deepcopy(self.documents);bad[name]['observations'].pop()
        with self.assertRaises(ValueError):self.check(bad)
        bad=copy.deepcopy(self.documents);bad[self.index['interval_evidence']['dataset']]['rows'][0]['features']['input_bits']+=1
        with self.assertRaisesRegex(ValueError,'interval features'):self.check(bad)

    def test_boundary_counts_require_JSON_integers(self):
        for field in ('capture_DFFs','launch_DFFs'):
            bad=copy.deepcopy(self.documents);row=bad[self.index['interval_evidence']['dataset']]['rows'][0];row[field]=float(row[field])
            with self.assertRaisesRegex(ValueError,'JSON integer'):self.check(bad)

    def test_actual_QD_area_counts_and_hashes_rejected(self):
        for field in ('delay_ps','comb_area_um2','capture_DFFs','launch_DFFs','instances_sha256','points_sha256'):
            with self.subTest(field=field):
                bad=copy.deepcopy(self.documents);row=bad[self.index['interval_evidence']['dataset']]['rows'][0]
                row[field]=row[field]+1 if isinstance(row[field],(int,float)) else 'changed'
                with self.assertRaises(ValueError):self.check(bad)

    def test_mechanism_must_be_in_native_recomputation(self):
        bad=copy.deepcopy(self.index);name=bad['interval_evidence']['mechanism_pairs'][0]['D'];bad['native_reports']=[r for r in bad['native_reports'] if r['report']!=name]
        with self.assertRaisesRegex(ValueError,'missing native'):self.check(index=bad)


if __name__=='__main__':unittest.main()
