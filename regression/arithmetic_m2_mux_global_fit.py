"""Global selection changes candidate assignment, not coefficients or gates."""
import copy
import unittest
from experiments.arithmetic_dse.model_m2_mux_fit_v2 import select,score


def component(value):return {'kind':'pooled','predictor':{'kind':'linear','features':[],'coefficients':[],'intercept':value},'delay_scale':1.,'delay_margin_ps':0.}


def row(width):return {'split':'validation','features':{},'spec':{'lhs_width':width,'rhs_width':0,'result_width':width},
    'period_ps':750.,'delay_ps':100.,'observed_H_ps':10.}


class GlobalSelection(unittest.TestCase):
    def test_operation_gate_selects_an_existing_component(self):
        start={'kind':'exact_width_target_slices','slices':{'8/0/8/750':component(200),'16/0/16/750':component(100)}}
        before=copy.deepcopy(start);pools={'8/0/8/750':{'original':component(200),'better':component(110)},'16/0/16/750':{'original':component(100)}}
        model,q,trace=select([row(8),row(16)],start,pools)
        self.assertEqual(q['status'],'passed');self.assertEqual(model['slices']['8/0/8/750'],pools['8/0/8/750']['better'])
        self.assertEqual(start,before);self.assertEqual(len(trace),1)

    def test_qualification_precedes_lower_average_error(self):
        good={'status':'passed','median_relative_error':.2,'p95_relative_error':.7,'MAE':20,'false_feasible':0,'denominator':100,'actual_target_false_feasible':0,'actual_target_denominator':10}
        bad={**good,'status':'failed','MAE':1,'p95_relative_error':.8}
        self.assertLess(score(good),score(bad))

    def test_independent_rows_rejected_before_selection(self):
        with self.assertRaisesRegex(ValueError,'independent'):select([{**row(8),'split':'test'}],{}, {})


if __name__=='__main__':unittest.main()
