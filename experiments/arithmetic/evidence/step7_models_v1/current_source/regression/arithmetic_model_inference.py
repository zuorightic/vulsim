"""Inference protocol negatives and deterministic fixtures, never training data."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from experiments.arithmetic_dse.model_features import VERSION,features,infer,validate_query
from experiments.arithmetic_dse.platforms import profile


def fixture(platform):
    p=profile(platform);ref=p['trial_period_ps']
    predictor={'kind':'linear','features':['lhs_width','width_product'],'intercept':0.125,'coefficients':[.25,.0625]}
    tree={'kind':'tree','features':['lhs_width'],'nodes':[{'feature':0,'threshold':8,'left':1,'right':2},{'value':2.25},{'value':5.75}]}
    operations={}
    for op,shapes in [('mul',['full_mul','low_mul']),('add',['same_width','carry']),('addcarry',['carry'])]:
        conditions=[{'lhs_min':1,'lhs_max':128,'rhs_min':1,'rhs_max':128,'result_shape':shape,
                     'fanout_max':16,'abc_target_ps':ref,'sdc_min_ps':ref*.5,'sdc_max_ps':ref*2} for shape in shapes]
        operations[op]={'quality_status':'passed','delay':tree,'delay_margin_ps':.25,'area':predictor,'domain':{'conditions':conditions}}
    stage={'operations':operations,'state_model':{'bit_area_um2':.3,'clock_area_per_bit_um2':.01,'signal_area_um2':.02,
           'protocol_id':'sync_zero_reset_valid_enable_v1','domain':{'max_bits':4096,'max_signals':1024,'max_data_word_width':512,'min_variable_data_word_bits':1}},
           'boundary_model':{'io_delay_fraction':.2,'input_overhead_ps':25.,'register_overhead_ps':35.},
           'stage_correction':{'delay_base_scale':1.,'area_base_scale':1.,'intercept_ps':.1,'per_operation_ps':.01,'per_result_bit_ps':.001,'intercept_um2':0.,'per_operation_um2':0.,'per_result_bit_um2':0.,'max_operations':256,'max_live_result_bits':65536,
                               'graph_domain':{'version':'independent-single-output-arithmetic-tree-v1','max_multiplications':4,'max_output_roots':1}}}
    return {'version':'arithmetic-backend-model-v1','id':'TEST_ONLY_'+platform,'target_platform':platform,'platform_profile_sha256':p['profile_sha256'],
            'feature_schema':VERSION,'quality_status':'passed','mapping_abc_target_ps':ref,'stages':{'synth':stage,'grt':stage},'data_role':'unit-test artificial coefficients; never trained or published'}


def write_fixtures(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    for name in ('asap7','nangate45','sky130hd','gf180'):(out/(name+'.json')).write_text(json.dumps(fixture(name),indent=2)+'\n')


def check_parity(models,report):
    rows=json.loads(Path(report).read_text())
    for row in rows:
        b=json.loads((Path(models)/(row['platform']+'.json')).read_text());w=row['width'];f=features(w,w,2*w,1,b['mapping_abc_target_ps'],b['mapping_abc_target_ps'])
        estimate=validate_query(b,'mul',f,platform=b['target_platform'],profile_sha256=b['platform_profile_sha256'],stage='grt')
        if estimate['status']!='predicted_in_domain':raise ValueError('native test outside model support')
        for field in ('delay_ps','comb_area_um2'):
            if abs(estimate[field]-row[field])>max(1e-9,abs(estimate[field])*1e-10):raise ValueError('C++/Python physical inference mismatch')
    print(json.dumps({'native_python_inference_parity':'passed','queries':len(rows),'tolerance':'max(1e-9 absolute,1e-10 relative)'}))


class Inference(unittest.TestCase):
    def test_linear_and_tree_known_values(self):
        b=fixture('asap7');f=features(8,8,16,1,1500,1500)
        self.assertEqual(infer(b['stages']['grt']['operations']['mul']['delay'],f),2.25)
        self.assertEqual(infer(b['stages']['grt']['operations']['mul']['area'],f),6.125)
        f['lhs_width']=16;self.assertEqual(infer(b['stages']['grt']['operations']['mul']['delay'],f),5.75)
    def test_unknown_shape_target_platform_and_quality_rejected(self):
        b=fixture('asap7');f=features(8,8,16,1,1500,1500)
        call=lambda v:validate_query(b,'mul',v,platform='asap7',profile_sha256=b['platform_profile_sha256'],stage='grt')['status']
        self.assertEqual(call(f),'predicted_in_domain')
        self.assertEqual(call(features(8,16,24,1,1500,1500)),'uncovered')
        for key,value in [('lhs_width',129),('result_width',15),('fanout',17),('abc_target_ps',1600),('sdc_period_ps',1)]:
            v=dict(f);v[key]=value;self.assertEqual(call(v),'uncovered')
        b['quality_status']='failed';self.assertEqual(call(f),'uncovered')
    def test_nonfinite_and_boolean_features_rejected(self):
        for bad in (float('nan'),float('inf'),True):
            with self.assertRaises(ValueError):features(bad,8,16,1,1500,1500)
        with self.assertRaises(ValueError):features(8.0,8,16,1,1500,1500)

    def test_constant_ones_and_known_zero_patterns_do_not_inherit_coverage(self):
        b=fixture('asap7')
        for f in (features(8,8,16,1,1500,1500,literal_operands=True),features(8,8,16,1,1500,1500,lhs_zero_bits=1),
                  features(8,8,16,1,1500,1500,constant_carry=True),features(8,8,16,1,1500,1500,correlated_operands=True)):
            result=validate_query(b,'mul',f,platform='asap7',profile_sha256=b['platform_profile_sha256'],stage='grt')
            self.assertEqual(result['status'],'uncovered')
        b['stages']['grt']['operations']['mul']['domain']['known_zero_policy']='unregistered'
        self.assertEqual(validate_query(b,'mul',features(8,8,16,1,1500,1500),platform='asap7',profile_sha256=b['platform_profile_sha256'],stage='grt')['status'],'uncovered')
    def test_bad_predictors_rejected(self):
        f=features(8,8,16,1,1500,1500)
        for predictor in [ {'kind':'unknown','features':[]},
            {'kind':'linear','features':['lhs_width'],'coefficients':[],'intercept':0},
            {'kind':'tree','features':['lhs_width'],'nodes':[{'feature':0,'threshold':10,'left':0,'right':0}]}]:
            with self.assertRaises(ValueError):infer(predictor,f)


if __name__=='__main__':
    import sys
    if len(sys.argv)>1 and sys.argv[1]=='fixtures':write_fixtures(sys.argv[2])
    elif len(sys.argv)>1 and sys.argv[1]=='parity':check_parity(sys.argv[2],sys.argv[3])
    else:unittest.main()
