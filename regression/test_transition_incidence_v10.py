import math
import unittest
from experiments.arithmetic_dse import transition_incidence_features_v10 as f
from experiments.arithmetic_dse.prospective_logic import Circuit


class TransitionIncidenceTests(unittest.TestCase):
    def test_root_reset_second_moment(self):
        roots=[[0,1]]; words=[dict(reset_bits=[0,1],invert_bits=[0,1])]
        result=f.signed_incidence(roots,words,[[0],[0,1]])
        self.assertAlmostEqual(result['reset_one_degree_second_fraction'],.2)
        self.assertAlmostEqual(result['reset_degree_second_imbalance'],.6)
        self.assertAlmostEqual(result['phase_split_fraction'],.4)
        self.assertAlmostEqual(result['reset_cross_fraction'],1/3)

    def test_root_renaming_invariance(self):
        words=[dict(reset_bits=[0,1,1],invert_bits=[0,1,1])]
        a=f.signed_incidence([[0,1,0]],words,[[0,1],[0,2],[2]])
        b=f.signed_incidence([[0,0,1]],words,[[1,2],[1,0],[0]])
        self.assertEqual(a,b)

    def test_operand_exchange_invariance(self):
        words=[dict(reset_bits=[1,0],invert_bits=[0,1])]
        self.assertEqual(f.signed_incidence([[0,1]],words,[[0,1],[1,0]]),
                         f.signed_incidence([[0,1]],words,[[1,0],[0,1]]))

    def test_polarity_concentration_is_joint(self):
        words=[dict(reset_bits=[0,0,0,0],invert_bits=[0,0,1,1])]
        a=f.signed_incidence([[0,0]],words,[[0],[0],[1],[1]])
        b=f.signed_incidence([[0,0]],words,[[0],[1],[0],[1]])
        self.assertNotEqual(a['phase_split_fraction'],b['phase_split_fraction'])

    def test_empty_incidence_is_finite(self):
        self.assertTrue(all(math.isfinite(v) for v in f.signed_incidence([[0]],[],[]).values()))

    def test_dead_logic_does_not_add_work(self):
        c=Circuit();a,b=c.leaf(('a',0)),c.leaf(('b',0));out=c.gate('and',a,b)
        before=f.path_load_work(c,[out]);c.gate('or',a,b)
        self.assertEqual(before,f.path_load_work(c,[out]))

    def test_output_observation_increases_path_load(self):
        c=Circuit();a,b=c.leaf(('a',0)),c.leaf(('b',0));out=c.gate('and',a,b)
        self.assertGreater(f.path_load_work(c,[out,out])['log2_path_load_work'],f.path_load_work(c,[out])['log2_path_load_work'])

    def test_constant_output_has_zero_path_work(self):
        c=Circuit();self.assertEqual(f.path_load_work(c,[0,1])['log2_path_load_work'],0.)


if __name__=='__main__':unittest.main()
