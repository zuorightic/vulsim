import unittest

from experiments.arithmetic_dse.rtl_sensitivity_v13 import reorder_independent_clocked, commute_expression


class StatementCertificates(unittest.TestCase):
    def test_cross_register_old_state_reads_remain_legal(self):
        text = 'module M(input clk);\nalways @(posedge clk) a<=b;\nalways @(posedge clk) b<=a;\nendmodule\n'
        variant, proof = reorder_independent_clocked(text)
        self.assertEqual(reorder_independent_clocked(variant)[0], text)
        self.assertEqual(proof['modules'][0]['unique_targets'], ['a', 'b'])

    def test_duplicate_writer_rejected(self):
        with self.assertRaises(ValueError):
            reorder_independent_clocked('module M;\nalways @(posedge clk) a<=b;\nalways @(posedge clk) a<=c;\nendmodule')

    def test_blocking_or_multi_target_rejected(self):
        for statement in ['always @(posedge clk) a=b;', 'always @(posedge clk)if(x)a<=b;else c<=d;']:
            with self.assertRaises(ValueError):
                reorder_independent_clocked('module M;\n'+statement+'\nendmodule')

    def test_modules_not_mixed(self):
        text = 'module A;\nalways @(posedge clk) x<=y;\nalways @(posedge clk) y<=x;\nendmodule\nmodule B;\nalways @(posedge clk) x<=0;\nendmodule'
        variant, proof = reorder_independent_clocked(text)
        self.assertEqual(len(proof['modules']), 2)
        self.assertIn('module B;\nalways @(posedge clk) x<=0;', variant)

    def test_ambiguous_expression_rejected(self):
        with self.assertRaises(ValueError):
            commute_expression('x=a+b;y=a+b;', 'a+b', 'b+a')

    def test_expression_boundary_preserved(self):
        variant, proof = commute_expression('assign x=(a+b)+c;', 'a+b', 'b+a')
        self.assertEqual(variant, 'assign x=(b+a)+c;')
        self.assertTrue(proof['equivalence_proof_required'])


if __name__ == '__main__':
    unittest.main()
