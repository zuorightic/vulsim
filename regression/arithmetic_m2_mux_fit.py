"""Mux selection observes complete fitting groups, margins and no test labels."""
import copy
import unittest
from unittest.mock import patch

from experiments.arithmetic_dse.model_m2_mux_fit import choose_component,choose
from experiments.arithmetic_dse.model_m2_fit_v4 import predict


def row(source,split='train',period=1500,delay=100):
    return {'source_sha256':source,'split':split,'features':{},'delay_ps':delay,'comb_area_um2':10,
        'period_ps':period,'observed_H_ps':10,'spec':{'lhs_width':8,'rhs_width':0,'result_width':8}}


def predictor(value):return {'kind':'linear','features':[],'coefficients':[],'intercept':value}


class MuxFitter(unittest.TestCase):
    def data(self):return [row('A',period=t) for t in (750,1500)]+[row('B',period=t) for t in (750,1500)]+[row('V','validation',t) for t in (750,1500)]

    def algorithms(self,rows,field,floor):
        self.assertTrue(all(r['split']=='train' for r in rows))
        for source in {r['source_sha256'] for r in rows}:
            self.assertEqual({r['period_ps'] for r in rows if r['source_sha256']==source},{750,1500})
        return [('constant',predictor(90 if field=='delay_ps' else 10))]

    def test_whole_source_crossfit_and_validation_reserve(self):
        with patch('experiments.arithmetic_dse.model_m2_mux_fit.algorithms',self.algorithms):model,report=choose_component(self.data(),'delay_ps')
        self.assertEqual(report['training_sources'],2);self.assertEqual(report['validation_sources'],1)
        self.assertAlmostEqual(predict(model,row('V','validation'),'delay'),101.5)
        self.assertEqual(report['quality']['status'],'passed')

    def test_independent_row_rejected_before_any_coefficient_fit(self):
        with patch('experiments.arithmetic_dse.model_m2_mux_fit.algorithms') as fit:
            with self.assertRaisesRegex(ValueError,'independent row'):choose_component(self.data()+[row('T','test')],'delay_ps')
            fit.assert_not_called()

    def test_extra_diagnostic_arc_numbers_are_not_fitted_features(self):
        original=self.data();modified=copy.deepcopy(original)
        for r in modified:r['diagnostic_post_backend_buffer_count']=999999
        with patch('experiments.arithmetic_dse.model_m2_mux_fit.algorithms',self.algorithms):
            a,ar=choose_component(original,'delay_ps');b,br=choose_component(modified,'delay_ps')
        self.assertEqual(a,b);self.assertEqual(ar,br)

    def test_training_coefficients_do_not_depend_on_validation(self):
        original=self.data();modified=copy.deepcopy(original)
        for r in modified:
            if r['split']=='validation':r['delay_ps']=120
        with patch('experiments.arithmetic_dse.model_m2_mux_fit.algorithms',self.algorithms):
            a,_=choose_component(original,'delay_ps');b,_=choose_component(modified,'delay_ps')
        self.assertEqual(a['predictor'],b['predictor'])
        self.assertGreater(predict(b,row('V','validation'),'delay'),predict(a,row('V','validation'),'delay'))


if __name__=='__main__':unittest.main()
