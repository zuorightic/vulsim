"""Independent Mux verdict applies reserve, stage and error gates unchanged."""
import copy
import unittest
from experiments.arithmetic_dse.model_features import features as base_features
from experiments.arithmetic_dse.model_m2_mux_static_features import descriptor,features
from experiments.arithmetic_dse.model_m2_mux_static_evaluate import report


def row(index=0,stage='grt'):
    base=base_features(8,0,8,1,1500,1500);labels=[{'id':f's{i}','operation':'mux','lhs_width':8,'result_width':8,'fanout':1} for i in range(2)]
    return {'id':str(index),'task_id':str(index),'source_sha256':'source','stage':stage,'spec':{'id':'s0','lhs_width':8,'rhs_width':0,'result_width':8,'fanout':1},
        'features':base,'static_features':features(base,descriptor(labels),'s0'),'period_ps':1500,'delay_ps':100,'comb_area_um2':10,'observed_H_ps':10}


def model(value=100,scale=1,margin=1.5):
    def constant(v):return {'kind':'linear','features':[],'coefficients':[],'intercept':v}
    return {'delay':{'kind':'pooled','predictor':constant(value),'delay_scale':scale,'delay_margin_ps':margin},
        'area':{'kind':'pooled','predictor':constant(10),'delay_margin_ps':0}}


class StaticIndependentVerdict(unittest.TestCase):
    def test_applied_reserve_is_in_precision_gate(self):
        c={'stages':{'grt':{'operations':{'mux':model(scale=2)}}}};r=report([row()],c)['grt']
        self.assertEqual(r['status'],'failed');self.assertEqual(r['delay']['false_feasible'],0)
    def test_false_feasible_not_hidden_by_loose_target(self):
        c={'stages':{'grt':{'operations':{'mux':model(80,margin=0)}}}};r=report([row()],c)['grt']
        self.assertEqual(r['status'],'failed');self.assertEqual(r['delay']['actual_target_false_feasible'],0);self.assertGreater(r['delay']['false_feasible'],0)
    def test_stage_outcomes_separate_and_no_tuning(self):
        c={'stages':{'grt':{'operations':{'mux':model()}},'synth':{'operations':{'mux':model(200,margin=0)}}}};before=copy.deepcopy(c)
        r=report([row(),row(1,'synth')],c)
        self.assertEqual(r['grt']['status'],'passed');self.assertEqual(r['synth']['status'],'failed');self.assertEqual(c,before)


if __name__=='__main__':unittest.main()
