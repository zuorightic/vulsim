"""Candidate-vector parity and production quality/context guards, zero PPA."""
import copy
import json
import math
import os
from pathlib import Path
import subprocess
import unittest

from experiments.arithmetic_dse.model_m2_mux_static_features import FEATURES
from experiments.arithmetic_dse.model_m2_mux_static_query import query
from experiments.arithmetic_dse.model_collection import sha,write


ROOT=Path(__file__).resolve().parents[1]


class StaticQuery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=ROOT/'build/step7-m2-models-20261105'
        cls.model_path=cls.root/'mux-static-fit-v1/candidate.json'
        cls.bundle=json.loads(cls.model_path.read_text());cls.data=json.loads((cls.root/'mux-static-data-v1.json').read_text())
    def example(self):
        row=next(r for r in self.data['rows'] if r['stage']=='grt' and r['spec']['fanout']==1)
        return row,self.data['static_contexts'][row['static_context_sha256']]
    def test_unqualified_model_rejected_by_default(self):
        row,cut=self.example()
        with self.assertRaisesRegex(ValueError,'quality not qualified'):query(self.bundle,row['features'],cut,row['spec']['id'])
    def test_missing_context_and_node_mismatch_rejected(self):
        row,cut=self.example()
        with self.assertRaises(ValueError):query(self.bundle,row['features'],None,row['spec']['id'],candidate_numerical_mode=True)
        changed={**row['features'],'fanout':2}
        with self.assertRaisesRegex(ValueError,'differs from queried'):query(self.bundle,changed,cut,row['spec']['id'],candidate_numerical_mode=True)
    def test_profile_guard_does_not_affect_other11(self):
        row,cut=self.example();fixture=copy.deepcopy(self.bundle);before=copy.deepcopy(self.bundle)
        fixture['quality_status']='passed';fixture['stages']['grt']['operations']['mux']['quality_status']='passed';fixture['platform_profile_sha256']='TEST_ONLY_PROFILE'
        fixture['stages']['grt']['operations']['mux']['context_domain']['independently_qualified_families']=['parallel_dynamic_mux']
        with self.assertRaisesRegex(ValueError,'profile'):query(fixture,row['features'],cut,row['spec']['id'],profile_sha256='wrong')
        actual=query(fixture,row['features'],cut,row['spec']['id'],profile_sha256='TEST_ONLY_PROFILE')
        self.assertEqual(actual['PPA_calls'],0);self.assertEqual(self.bundle,before)
    def test_unqualified_mixed_context_not_inferred_from_pure_test(self):
        row=next(r for r in self.data['rows'] if r['stage']=='grt' and r['source_context']=='legacy_mixed_control' and r['spec']['fanout']==1)
        cut=self.data['static_contexts'][row['static_context_sha256']];fixture=copy.deepcopy(self.bundle)
        fixture['quality_status']='passed';fixture['platform_profile_sha256']='TEST_ONLY_PROFILE'
        fixture['stages']['grt']['operations']['mux']['quality_status']='passed'
        fixture['stages']['grt']['operations']['mux']['context_domain']['independently_qualified_families']=['parallel_dynamic_mux']
        with self.assertRaisesRegex(ValueError,'family has no independent'):query(fixture,row['features'],cut,row['spec']['id'],profile_sha256='TEST_ONLY_PROFILE')
    def test_native_price_and_static_feature_parity_for_all_fitting_rows(self):
        exe=os.environ.get('MUX_STATIC_PREDICT')
        if not exe:self.skipTest('native numerical adapter path not provided')
        by_group={};rows=[]
        for row in self.data['rows']:
            if row['stage']!='grt':continue
            cut=self.data['static_contexts'][row['static_context_sha256']]
            shape='mixed' if row['source_context']=='legacy_mixed_control' else str(len(cut['operations']))
            identity=(row['spec']['lhs_width'],row['spec']['fanout'],shape,int(row['period_ps']))
            if identity not in by_group:
                p=subprocess.run([exe,str(self.model_path),str(identity[0]),str(identity[1]),identity[2],str(identity[3]),'--candidate'],check=True,capture_output=True,text=True)
                by_group[identity]=json.loads(p.stdout)
            native=by_group[identity];self.assertTrue(native['covered']);self.assertEqual(native['PPA_calls'],0)
            expected=query(self.bundle,row['features'],cut,row['spec']['id'],candidate_numerical_mode=True)
            self.assertEqual(native['features'],{k:expected['features'][k] for k in FEATURES})
            for key in ('delay_ps','comb_area_um2'):self.assertTrue(math.isclose(native[key],expected[key],rel_tol=1e-9,abs_tol=1e-7))
            rows.append({'id':row['id'],'native':{k:native[k] for k in ('delay_ps','comb_area_um2')},'python':{k:expected[k] for k in ('delay_ps','comb_area_um2')}})
        self.assertEqual(len(rows),384)
        for args in (('2','1','2','1500'),('8','1','2','751'),('8','4','2','1500'),('8','1','2','1500.5')):
            result=json.loads(subprocess.run([exe,str(self.model_path),*args,'--candidate'],check=True,capture_output=True,text=True).stdout)
            self.assertFalse(result['covered'])
        result=json.loads(subprocess.run([exe,str(self.model_path),'8','1','2','1500'],check=True,capture_output=True,text=True).stdout)
        self.assertFalse(result['covered'])
        out=self.root/'mux-static-query-v1/parity.json'
        write(out,{'status':'passed','model_sha256':sha(self.model_path),'native_executable_sha256':sha(exe),'fitting_rows':384,
            'distinct_context_queries':len(by_group),'rows':rows,'candidate_PPA_calls':0,'candidate_numerical_mode':True,
            'full_native_D_selection_ready':False,'scope':'actual BEIR context and portable numeric queries; no independent quality or whole-stage selection claim'})


if __name__=='__main__':unittest.main()
