"""Only proven constant sources may reconcile a complete CEC PI census."""
from copy import deepcopy
import unittest

from experiments.arithmetic_dse.workload_cec import reconcile_inputs,pi_census


def circuit():
    return dict(modules=dict(Workload=dict(ports=dict(a=dict(direction='input',bits=[2])),
                 cells=dict(ff=dict(type='FF'),tie=dict(type='ZERO'))),
        FF=dict(ports=dict(D=dict(direction='input',bits=[2]),Q=dict(direction='output',bits=[3])),
                cells=dict(ff=dict(type='$_DFF_P_'))),
        ZERO=dict(ports=dict(L=dict(direction='output',bits=['0'])),cells={})))


class CompleteCutCensus(unittest.TestCase):
    def test_constant_is_proved_and_named(self):
        c=reconcile_inputs(circuit(),'Workload',{'Workload/a':1,'FF/Q':1,'ZERO/L':1})
        self.assertEqual(c,[dict(instance='tie',master='ZERO',pin='L',literal_bits=['0'])])

    def test_unmodelled_state_or_input_cannot_be_deleted(self):
        with self.assertRaisesRegex(ValueError,'census'):
            reconcile_inputs(circuit(),'Workload',{'Workload/a':1,'ZERO/L':1})

    def test_undriven_output_cannot_be_called_constant(self):
        d=circuit();d['modules']['ZERO']['ports']['L']['bits']=[4]
        with self.assertRaisesRegex(ValueError,'census'):
            reconcile_inputs(d,'Workload',{'Workload/a':1,'FF/Q':1,'ZERO/L':1})

    def test_extra_logic_inside_constant_model_is_rejected(self):
        d=circuit();d['modules']['ZERO']['cells']={'mystery':dict(type='logic')}
        with self.assertRaisesRegex(ValueError,'census'):
            reconcile_inputs(d,'Workload',{'Workload/a':1,'FF/Q':1,'ZERO/L':1})


if __name__=='__main__':unittest.main()
