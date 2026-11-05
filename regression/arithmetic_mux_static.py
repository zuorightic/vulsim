"""Static semantic context and native BEIR extraction, without EDA prices."""
import copy
import json
import os
from pathlib import Path
import subprocess
import unittest

from experiments.arithmetic_dse.model_features import features as base_features
from experiments.arithmetic_dse.model_m2_collection import CONFIG as LEGACY
from experiments.arithmetic_dse.model_m2_samples import source
from experiments.arithmetic_dse.model_m2_mux_static_features import descriptor,context_features,features,predict


class MuxStaticFeatures(unittest.TestCase):
    def labels(self,width=32,fanout=1,replicas=2,mixed=False):
        cfg=json.loads(LEGACY.read_text())
        if not mixed:cfg['families']['control']['operations']=['mux']*replicas
        return source('control',width,fanout,cfg,'')[1]

    def test_semantic_bits_exclude_unused_sampler_ports(self):
        labels=self.labels(64,3,mixed=True);f=context_features(descriptor(labels),'s000')
        self.assertEqual(f,{'context_operation_count':6,'context_dynamic_mux_count':1,'context_constant_mux_count':3,'context_boolean_count':2,
            'context_launch_bits':516,'context_capture_bits':963,'context_result_bits':321,'selector_fanout_bits':64})
        self.assertNotEqual(f['context_launch_bits'],sum(sum(s['input_widths']) for s in labels))

    def test_operation_names_and_order_do_not_price_a_sample_id(self):
        cut=descriptor(self.labels());before=context_features(cut,'s000');renamed=copy.deepcopy(cut)
        for index,o in enumerate(renamed['operations']):
            o['id']='renamed'+str(index)
            for i,v in enumerate(o['operands']):v['id']=o['id']+'wire'+str(i)
        renamed['operations'].reverse()
        self.assertEqual(context_features(renamed,'renamed0'),before)

    def test_shared_select_and_connected_inputs_rejected(self):
        cut=descriptor(self.labels())
        cut['operations'][1]['operands'][-1]['id']=cut['operations'][0]['operands'][-1]['id']
        with self.assertRaisesRegex(ValueError,'shared'):context_features(cut,'s000')
        cut=descriptor(self.labels());cut['operations'][1]['operands'][0]['id']='s000'
        with self.assertRaisesRegex(ValueError,'connected'):context_features(cut,'s000')

    def test_post_backend_fields_are_not_features(self):
        cut=descriptor(self.labels());before=context_features(cut,'s000');cut['measured_buffer_count']=999999;cut['measured_delay_ps']=1
        self.assertEqual(context_features(cut,'s000'),before)

    def test_missing_context_is_not_zero_or_legacy_fallback(self):
        with self.assertRaises(ValueError):features(base_features(32,0,32,1,1500,1500),None,'s000')
        model={'kind':'pooled','predictor':{'kind':'linear','features':[],'coefficients':[],'intercept':100},'delay_scale':1,'delay_margin_ps':1.5}
        with self.assertRaisesRegex(ValueError,'lacks explicit'):predict(model,{'features':{}},'delay')

    def test_native_actual_BEIR_context_matches_independent_python(self):
        executable=os.environ.get('MUX_STATIC_NATIVE')
        if not executable:self.skipTest('native probe path not provided')
        for width in (1,5,8,16,32,64):
            for banks in (1,2,3):
                for shape in ('2','3','4','mixed'):
                    labels=self.labels(width,banks,replicas=2 if shape=='mixed' else int(shape),mixed=shape=='mixed')
                    expected=context_features(descriptor(labels),'s000')
                    for mutation in ('','rename','reorder'):
                        cmd=[executable,str(width),str(banks),shape]+([mutation] if mutation else [])
                        actual=json.loads(subprocess.run(cmd,check=True,capture_output=True,text=True).stdout)
                        self.assertTrue(actual['covered']);self.assertEqual(actual['features'],expected)
        for mutation in ('shared','connected','missing','unknown'):
            actual=json.loads(subprocess.run([executable,'32','1','3',mutation],check=True,capture_output=True,text=True).stdout)
            self.assertFalse(actual['covered'])


if __name__=='__main__':unittest.main()
