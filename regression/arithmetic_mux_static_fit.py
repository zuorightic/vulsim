"""Static predictors fit only eligible rows and carry no diagnostic features."""
import copy
import unittest
from unittest.mock import patch

from experiments.arithmetic_dse.model_features import features as basic
from experiments.arithmetic_dse.model_m2_mux_static_features import descriptor,features,predict,EXTRA
from experiments.arithmetic_dse.model_m2_mux_static_fit import component


class StaticFitting(unittest.TestCase):
    def row(self,source,split='train',period=1500,delay=100):
        labels=[{'id':f's{i}','operation':'mux','lhs_width':8,'result_width':8,'fanout':1} for i in range(2)]
        f=basic(8,0,8,1,1500,period)
        return {'source_sha256':source,'split':split,'features':f,'static_features':features(f,descriptor(labels),'s0'),
            'spec':{'lhs_width':8,'rhs_width':0,'result_width':8},'delay_ps':delay,'comb_area_um2':10,'period_ps':period,'observed_H_ps':10}
    def rows(self):return [self.row(g,split,t) for g,split in [('A','train'),('B','train'),('V','validation')] for t in (750,1500)]
    def algorithms(self,rows,key,floor):
        self.assertTrue(all(r['split']=='train' for r in rows))
        self.assertTrue(all(all(k in r['features'] for k in EXTRA) for r in rows))
        for source in {r['source_sha256'] for r in rows}:self.assertEqual({r['period_ps'] for r in rows if r['source_sha256']==source},{750,1500})
        return [('constant',{'kind':'linear','features':[],'coefficients':[],'intercept':90})]
    def test_training_inputs_are_static_and_source_groups_are_whole(self):
        with patch('experiments.arithmetic_dse.model_m2_mux_static_fit.algorithms',self.algorithms):model,report=component(self.rows())
        self.assertEqual(report['training_sources'],2);self.assertEqual(report['quality']['status'],'passed')
        self.assertAlmostEqual(predict(model,self.row('V','validation'),'delay'),101.5)
    def test_independent_rows_rejected_before_coefficient_fit(self):
        with patch('experiments.arithmetic_dse.model_m2_mux_static_fit.algorithms') as algorithm:
            with self.assertRaisesRegex(ValueError,'independent'):component(self.rows()+[self.row('T','test')])
            algorithm.assert_not_called()
    def test_validation_changes_reserve_not_fitted_coefficients(self):
        rows=self.rows();other=copy.deepcopy(rows)
        for r in other:
            if r['split']=='validation':r['delay_ps']=110
        with patch('experiments.arithmetic_dse.model_m2_mux_static_fit.algorithms',self.algorithms):a,_=component(rows);b,_=component(other)
        self.assertEqual(a['predictor'],b['predictor'])
        self.assertGreater(predict(b,self.row('V','validation'),'delay'),predict(a,self.row('V','validation'),'delay'))


if __name__=='__main__':unittest.main()
