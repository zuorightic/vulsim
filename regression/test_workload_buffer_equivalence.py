from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.arithmetic_dse.workload_buffer_equivalence import prove
from experiments.arithmetic_dse.workload_kepler_proxy import main as proxy

LIB='''library(test) {
 cell(B1) {pin(A) {direction: input;} pin(Y) {direction: output; function: "A";}}
 cell(B2) {pin(A) {direction: input;} pin(Y) {direction: output; function: "A";}}
 cell(N1) {pin(A) {direction: input;} pin(B) {direction: input;} pin(Y) {direction: output; function: "!(A & B)";}}
 cell(N2) {pin(A) {direction: input;} pin(B) {direction: input;} pin(Y) {direction: output; function: "!(A & B)";}}
 cell(O1) {pin(A) {direction: input;} pin(B) {direction: input;} pin(Y) {direction: output; function: "A | B";}}
 cell(FF) {ff(IQ,IQN) {clocked_on:"CK"; next_state:"D"; clear:"!RN";}
   pin(D) {direction: input;} pin(CK) {direction: input;} pin(RN) {direction: input;}
   pin(Q) {direction: output; function:"IQ";}}
 cell(FFOTHER) {ff(IQ,IQN) {clocked_on:"CK"; next_state:"D"; clear:"RN";}
   pin(D) {direction: input;} pin(CK) {direction: input;} pin(RN) {direction: input;}
   pin(Q) {direction: output; function:"IQ";}}
}'''


def net(body):
    return '''module top(a,b,clk,rst,q);
 input a;
 input b;
 input clk;
 input rst;
 output q;
 wire n;
 wire d;
 wire ck;
'''+body+'''
 endmodule
'''


BEFORE=net('N1 gate(.A(a),.B(b),.Y(n));\nFF reg0(.D(n),.CK(clk),.RN(rst),.Q(q));')
AFTER=net('N2 gate(.A(a),.B(b),.Y(n));\nB1 hold(.A(n),.Y(d));\nB2 clock(.A(clk),.Y(ck));\nFF reg0(.D(d),.CK(ck),.RN(rst),.Q(q));')


class ConservativeRepairProof(unittest.TestCase):
    def check(self,a,b):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'cells.lib').write_text(LIB);(p/'a.v').write_text(a);(p/'b.v').write_text(b)
            return prove(p/'a.v',p/'b.v',[p/'cells.lib'])

    def test_buffer_and_size_repair_proven_including_clock(self):
        r=self.check(BEFORE,AFTER)
        self.assertEqual(r['status'],'proven');self.assertEqual(r['nonbuffer_instances'],2)
        self.assertEqual(r['function_equivalent_resized_cells'],1);self.assertEqual(r['after_buffers'],2)

    def test_changed_gate_function_rejected(self):
        with self.assertRaisesRegex(ValueError,'logical cell function'):
            self.check(BEFORE,AFTER.replace('N2 gate','O1 gate'))

    def test_unconnected_clock_load_buffer_is_logically_inert(self):
        r=self.check(BEFORE,AFTER.replace(' endmodule',' B2 dummyload(.A(clk));\n endmodule'))
        self.assertEqual(r['status'],'proven');self.assertEqual(r['after_buffers'],3)

    def test_wrong_arithmetic_input_rejected(self):
        with self.assertRaisesRegex(ValueError,'input driver'):
            self.check(BEFORE,AFTER.replace('.B(b)','.B(a)'))

    def test_wrong_clock_source_rejected(self):
        with self.assertRaisesRegex(ValueError,'input driver'):
            self.check(BEFORE,AFTER.replace('clock(.A(clk)','clock(.A(a)'))

    def test_reset_polarity_change_rejected(self):
        with self.assertRaisesRegex(ValueError,'logical cell function'):
            self.check(BEFORE,AFTER.replace('FF reg0','FFOTHER reg0'))

    def test_output_bypass_rejected(self):
        wrong=AFTER.replace('.Q(q)','.Q(extra)').replace(' endmodule',' B1 wrong(.A(a),.Y(q));\n endmodule')
        with self.assertRaisesRegex(ValueError,'primary output'):
            self.check(BEFORE,wrong)

    def test_added_functional_instance_rejected(self):
        with self.assertRaisesRegex(ValueError,'instance set'):
            self.check(BEFORE,AFTER.replace(' endmodule',' N1 added(.A(a),.B(b),.Y(extra));\n endmodule'))

    def test_duplicate_or_undriven_or_cyclic_buffers_rejected(self):
        for wrong in (AFTER.replace('B2 clock','B2 hold'),AFTER.replace('hold(.A(n)','hold(.A(missing)'),AFTER.replace('hold(.A(n)','hold(.A(d)')):
            with self.subTest(wrong=wrong),self.assertRaises(ValueError):self.check(BEFORE,wrong)

    def test_unsupported_assignment_and_missing_pin_rejected(self):
        for wrong in (AFTER.replace(' endmodule',' assign d = a;\n endmodule'),AFTER.replace(', .B(b)','').replace(', .B(a)','').replace('.B(b),','')):
            with self.subTest(wrong=wrong),self.assertRaises(ValueError):self.check(BEFORE,wrong)

    def test_changed_primary_interface_rejected(self):
        with self.assertRaisesRegex(ValueError,'primary interface'):
            self.check(BEFORE,AFTER.replace('output q;','output [1:0] q;'))

    def test_ORFS_adapter_proves_original_inputs_and_rejects_wrong_clock(self):
        import json
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);lib=p/'cells.lib';a=p/'a.v';b=p/'b.v';log=p/'4_rsz_lec_check.log'
            lib.write_text(LIB);a.write_text(BEFORE);b.write_text(AFTER)
            config=p/'4_rsz_lec_test.yml'
            config.write_text(f'format: verilog\ninput_paths:\n  - {a}\n  - {b}\nliberty_files:\n - {lib}\nlog_file: {log}\n')
            with patch('builtins.print'):
                self.assertEqual(proxy(config),0)
            result=json.loads(log.with_suffix('.proof.json').read_text())
            self.assertEqual(result['status'],'proven')
            self.assertEqual(set(result['inputs_sha256']),set(map(str,[a,b,lib,config])))
            self.assertEqual(a.read_text(),BEFORE);self.assertEqual(b.read_text(),AFTER)
            b.write_text(AFTER.replace('clock(.A(clk)','clock(.A(a)'))
            with patch('builtins.print'):
                self.assertEqual(proxy(config),2)
            self.assertEqual(json.loads(log.read_text())['status'],'not_proven')

    def test_ORFS_adapter_unsupported_config_cannot_succeed(self):
        with tempfile.TemporaryDirectory() as d:
            config=Path(d)/'bad.yml';config.write_text('format: verilog\ninput_paths:\n  - absent.v\n')
            with self.assertRaises(ValueError):proxy(config)


if __name__=='__main__':unittest.main()
