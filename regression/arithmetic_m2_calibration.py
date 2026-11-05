"""Prospective group calibration uses train/validation only and all targets."""
import copy
import unittest
from unittest.mock import patch

from experiments.arithmetic_dse.model_m2_fit_v3 import calibrate,predict


def row(split,fanout,delay,period):
    return {'id':f'{split}-{fanout}-{period}','split':split,'spec':{'lhs_width':8,'rhs_width':8,'result_width':8,'fanout':fanout},
            'features':{},'delay_ps':delay,'period_ps':period,'observed_H_ps':10}


class ContextCalibration(unittest.TestCase):
    def data(self):
        return [row('train',f,d,t) for f,d in ((1,100),(3,120)) for t in (2250,1500,750,375)]+[row('validation',2,110,t) for t in (2250,1500,750,375)]

    def fit(self,train,field,floor):
        self.assertTrue(all(r['split']=='train' for r in train))
        for fanout in {r['spec']['fanout'] for r in train}:
            self.assertEqual({r['period_ps'] for r in train if r['spec']['fanout']==fanout},{2250,1500,750,375})
        return [('constant',{'kind':'linear','features':[],'coefficients':[],'intercept':sum(r[field] for r in train)/len(train)})]

    def test_whole_context_crossfit_controls_reserve(self):
        with patch('experiments.arithmetic_dse.model_m2_fit_v3.algorithms',self.fit):model,report=calibrate(self.data())
        self.assertAlmostEqual(model['delay_scale'],1.2*1.05)
        self.assertAlmostEqual(predict(model,row('validation',2,110,1500),'delay'),110*1.2*1.05+1.5)
        self.assertEqual(report['quality']['status'],'passed')

    def test_test_rows_rejected_before_fitting(self):
        with self.assertRaisesRegex(ValueError,'train/validation only'):calibrate(self.data()+[row('test',5,999999,1500)])

    def test_wrong_grouping_rejected(self):
        rows=self.data()
        for r in rows:
            if r['split']=='train' and r['spec']['fanout']==3:r['spec']['fanout']=4
        with self.assertRaisesRegex(ValueError,'crossfit contexts'):calibrate(rows)

    def test_validation_is_not_used_to_fit_coefficients(self):
        rows=self.data();changed=copy.deepcopy(rows)
        for r in changed:
            if r['split']=='validation':r['delay_ps']=140
        with patch('experiments.arithmetic_dse.model_m2_fit_v3.algorithms',self.fit):
            before,_=calibrate(rows);after,_=calibrate(changed)
        self.assertEqual(before['predictor'],after['predictor'])
        self.assertGreater(after['delay_scale'],before['delay_scale'])


if __name__=='__main__':unittest.main()
