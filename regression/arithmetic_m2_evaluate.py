"""Independent verdict uses every mandatory class and frozen predictions."""
import copy
import unittest

from experiments.arithmetic_dse.model_m2_evaluate import report
from experiments.arithmetic_dse.model_m2_fit_v2 import predict


def model(delay=100,margin=1.5):
    def constant(v):return {'kind':'linear','features':[],'coefficients':[],'intercept':v}
    return {'delay':{'kind':'pooled','predictor':constant(delay),'delay_margin_ps':margin},
            'area':{'kind':'pooled','predictor':constant(10),'delay_margin_ps':0}}


def row(i=0,op='add',period=150):
    return {'id':str(i),'task_id':str(i),'operation':op,'rtl_operation':op,'stage':'grt','features':{},
        'spec':{'lhs_width':8,'rhs_width':8,'result_width':8},'delay_ps':100,'comb_area_um2':10,'period_ps':period,
        'observed_H_ps':10,'path_slack_ps':period-110,'whole_setup_slack_ps':period-110,'whole_hold_slack_ps':1}


class IndependentVerdict(unittest.TestCase):
    def test_no_aggregate_rescue_for_failed_operation(self):
        rows=[row(i) for i in range(30)]+[row(30,'mux')]
        candidate={'stages':{'grt':{'operations':{'add':model(),'mux':model(40,0)}}}}
        result=report(rows,candidate)['grt']
        self.assertEqual(result['passing_operations'],1)
        self.assertEqual(result['status'],'failed')
        self.assertEqual(result['delay']['median_relative_error'],.015)

    def test_applied_margin_controls_error_verdict(self):
        candidate={'stages':{'grt':{'operations':{'add':model(100,50)}}}}
        result=report([row()],candidate)['grt']
        self.assertEqual(result['status'],'failed')
        self.assertEqual(result['operations']['add']['predictions'][0]['delay_ps'],150)

    def test_exact_slice_no_nearest_width_fallback(self):
        m={'kind':'exact_width_slices','slices':{'8/8/8':model()['delay']}}
        r=row();r['spec']['lhs_width']=9
        with self.assertRaises(KeyError):predict(m,r,'delay')

    def test_synth_and_grt_verdicts_separate(self):
        a=row();b={**row(1),'stage':'synth'}
        candidate={'stages':{'grt':{'operations':{'add':model()}},'synth':{'operations':{'add':model(200,0)}}}}
        result=report([a,b],candidate)
        self.assertEqual(result['grt']['status'],'passed');self.assertEqual(result['synth']['status'],'failed')

    def test_actual_target_false_feasible_and_frozen_parameters(self):
        candidate={'stages':{'grt':{'operations':{'add':model(80,0)}}}};before=copy.deepcopy(candidate)
        result=report([row(period=100)],candidate)['grt']
        self.assertEqual(result['actual_target_false_feasible'],1)
        self.assertEqual(result['status'],'failed');self.assertEqual(candidate,before)

    def test_target_response_ranking_is_diagnostic(self):
        candidate={'stages':{'grt':{'operations':{'add':model()}}}}
        a=row(0,period=150);b=row(1,period=200);b['delay_ps']=105
        result=report([a,b],candidate)['grt']
        self.assertEqual(result['status'],'passed')
        self.assertEqual(result['ranking']['denominator'],2)
        self.assertLess(result['ranking']['matching_pairs'],2)


if __name__=='__main__':unittest.main()
