"""Target features, numeric representation and independent acquisition boundaries."""
import math
from pathlib import Path
import tempfile
import unittest
from experiments.arithmetic_dse.model_target_features import clock_request,sta_roundtrip_ps,reference_values,features,infer
from experiments.arithmetic_dse.model_target_collection import selected_tasks


class TargetLoadContracts(unittest.TestCase):
    def reference(self):
        return {'intervals':{'half/full/0/0':{'delay_anchors':[[8,300],[16,500],[32,800]],'overhead_ps':100}}}

    def test_interpolation_uses_only_registered_train_anchors(self):
        self.assertEqual(reference_values(self.reference(),'half/full/0/0',20),(575.,100))
        with self.assertRaises(ValueError):reference_values(self.reference(),'half/full/0/0',64)

    def test_period_grid_preserves_absolute_io_policy_and_serialized_precision(self):
        for raw in [200,225,1021,1500,2250,2388.3]+list(range(201,2300,37)):
            c=clock_request(raw);p=c['requested_period_ps']
            self.assertGreaterEqual(c['nominal_grid_ps'],raw)
            for wanted in (p,.2*p):
                value=wanted
                for _ in range(10):
                    value=float(format(sta_roundtrip_ps(value),'.4f'))
                    self.assertLessEqual(abs(value-wanted),.500001e-4)
        for raw in (0,-1,float('inf'),float('nan')):
            with self.assertRaises(ValueError):clock_request(raw)

    def test_features_respond_to_clock_and_fanout_without_measured_cell_counts(self):
        s={'configuration':'half','result_shape':'full','first':0,'last':0,'width':16,'capture_width':64,
           'input_widths':[16,16],'block_width':8,'fanout':1}
        loose=features(s,1500,self.reference());tight=features(s,500,self.reference())
        self.assertEqual(loose['tightness'],0)
        self.assertGreater(tight['tightness'],0)
        self.assertEqual(tight['reference_delay_ps'],loose['reference_delay_ps'])
        s['fanout']=3;loaded=features(s,500,self.reference())
        self.assertEqual(loaded['load_tightness'],3*tight['load_tightness'])
        self.assertNotIn('mapped_DFFs',loaded)
        prediction={'kind':'linear','features':['width','load_tightness'],'intercept':1,'coefficients':[2,3]}
        self.assertAlmostEqual(infer(prediction,loaded),33+3*loaded['load_tightness'])

    def test_baseline_fit_never_implicitly_includes_test_or_deferred_training(self):
        plan={'tasks':[{'id':'a','split':'train','target_roles':['absolute-2250']},
                       {'id':'b','split':'train','target_roles':['relative-0.8']},
                       {'id':'c','split':'validation','target_roles':['absolute-2250']},
                       {'id':'d','split':'test','target_roles':['absolute-2250']}]}
        self.assertEqual([t['id'] for t in selected_tasks(plan,'fitting-baseline')],['a','c'])
        self.assertEqual([t['id'] for t in selected_tasks(plan,'fitting-full')],['a','b','c'])
        self.assertEqual([t['id'] for t in selected_tasks(plan,'conditional')],['b'])


class TargetFittingContracts(unittest.TestCase):
    def rows(self,widths,response):
        reference={'intervals':{'half/full/0/0':{'delay_anchors':[[8,80],[16,160],[32,320]],'overhead_ps':100}}}
        result=[]
        for width in widths:
            for fanout in (1,2,3):
                for target in ('tight','near','loose-edge','absolute'):
                    pressure={'tight':.8,'near':1.,'loose-edge':1.5}.get(target)
                    period=2250 if pressure is None else 100+10*width*pressure
                    spec={'configuration':'half','result_shape':'full','first':0,'last':0,'width':width,
                          'capture_width':4*width,'input_widths':[width,width],'block_width':width//2,'fanout':fanout}
                    values=features(spec,period,reference)
                    result.append({'id':f'{width}/{fanout}/{target}','features':values,
                                   'target_roles':['absolute-2250'] if target=='absolute' else [target],
                                   'delay_ps':10*width+3*fanout+response*values['width_tightness']})
        return result

    def test_simple_eligible_baseline_is_preferred_over_extra_target_terms(self):
        from experiments.arithmetic_dse.model_target_fit import choose
        selected,_=choose(self.rows((8,16,32),.1),self.rows((12,24),.1),'delay_ps','delay',True)
        self.assertEqual(selected['family'],'baseline')
        self.assertEqual(selected['validation']['status'],'passed')
        self.assertGreaterEqual(selected['reserve'],1.05)

    def test_large_real_response_requires_conditional_model_after_calibration(self):
        from experiments.arithmetic_dse.model_target_fit import choose
        selected,_=choose(self.rows((8,16,32),50),self.rows((12,24),50),'delay_ps','delay',True)
        self.assertEqual(selected['family'],'conditional')
        self.assertEqual(selected['validation']['status'],'passed')

    def test_false_feasible_and_actual_target_checks_keep_distinct_denominators(self):
        from experiments.arithmetic_dse.model_target_fit import quality
        row={'id':'synthetic','features':{},'delay_ps':100,'comb_area_um2':10,'period_ps':100,'observed_H_ps':10,
             'path_slack_ps':-10,'whole_setup_slack_ps':-10}
        entry={'delay':{'kind':'linear','features':[],'intercept':80,'coefficients':[]},
               'area':{'kind':'linear','features':[],'intercept':10,'coefficients':[]},'validation_delay_scale':1}
        q=quality(entry,[row]);self.assertEqual(q['status'],'failed')
        self.assertEqual(q['delay']['denominator'],11);self.assertEqual(q['actual_target_denominator'],1)
        self.assertEqual(q['actual_target_false_feasible'],1)


if __name__=='__main__':unittest.main()
