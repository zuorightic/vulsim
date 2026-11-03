"""Characterization labels must exclude boundary delay and bind raw points."""
import json,tempfile,unittest
from pathlib import Path
from experiments.arithmetic_dse.model_samples import render_label_requests,read_labels
from experiments.arithmetic_dse.platforms import verify_wire_readback
from experiments.arithmetic_dse.backend import render_repair_script

class ModelLabels(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.contract=self.root/'contract.json';self.data={'version':'arithmetic-model-labels-v1','labels':[{'id':'mul8','source_cells':'op_mul8/src_*','target_cells':'op_mul8/dst_*'}]};self.contract.write_text(json.dumps(self.data));self.prefix=self.root/'vulsim_synth'
        self.table=Path(str(self.prefix)+'_model_paths.tsv');self.points=Path(str(self.prefix)+'_model_mul8_points.tsv')
        self.table.write_text('sample_id\tstart_pin\tend_pin\tstart_arrival_native\tend_arrival_native\tdata_delay_native\tpoint_count\nmul8\top_mul8/src_0/Q\top_mul8/dst_0/D\t0.25\t0.75\t0.5\t3\n')
        self.points.write_text('op_mul8/src_0/Q\t0.25\nu/A\t0.5\nop_mul8/dst_0/D\t0.75\n')
    def test_Q_D_difference_and_units(self):
        self.assertEqual(read_labels(self.prefix,self.contract,1000)[0]['data_delay_ps'],500)
        self.assertIn('op_mul8/src_*',render_label_requests(self.contract))
    def test_dynamic_boundary_commands_rejected(self):
        for value in ['[all_registers]','x;exit','${HOME}','x} {exit','x\\y']:
            self.data['labels'][0]['source_cells']=value;self.contract.write_text(json.dumps(self.data))
            with self.subTest(value=value),self.assertRaises(ValueError):render_label_requests(self.contract)
    def test_wrong_data_difference_and_nonfinite_rejected(self):
        raw=self.table.read_text()
        for bad in ['0.75','nan','-0.5']:
            self.table.write_text(raw.replace('\t0.5\t3','\t'+bad+'\t3'))
            with self.subTest(bad=bad),self.assertRaises(ValueError):read_labels(self.prefix,self.contract,1000)
    def test_raw_point_or_coverage_mismatch_rejected(self):
        for text in ['op_mul8/src_0/Q\t0.0\nu/A\t0.5\nop_mul8/dst_0/D\t0.75\n','op_mul8/src_0/Q\t0.25\nu/A\t0.5\nop_mul8/dst_0/D\t0.8\n','op_mul8/src_0/Q\t0.25\nop_mul8/dst_0/D\t0.75\n']:
            self.points.write_text(text)
            with self.subTest(text=text),self.assertRaises(ValueError):read_labels(self.prefix,self.contract,1000)

    def test_wire_readback_roundtrip_and_large_errors(self):
        p={'rc_adapter':{'wire_calibration':{'version':'test','resistance_ohm_per_um':{'Metal2':.32502850540936595},'capacitance_fF_per_um':{'Metal2':.135357}}}}
        path=self.root/'wire.tsv';header='layer\tresistance_ohm_per_um\tcapacitance_fF_per_um\n'
        valid='Metal2\t0.32502850622998408\t0.1353569998008837\n'
        path.write_text(header+valid);self.assertEqual(verify_wire_readback(path,p)['status'],'passed')
        for bad in ['Metal2\t.0003250285\t.135357\n','Metal2\t.3250285\t.000135357\n','Metal2\tnan\t.135357\n',valid+valid,'']:
            path.write_text(header+bad)
            with self.subTest(bad=bad),self.assertRaises(ValueError):verify_wire_readback(path,p)

    def test_bounded_repair_script_renderer(self):
        original='proc repair_timing_helper { args } {\n  set additional_args {}\n  lappend additional_args {*}$args -verbose\n  log_cmd repair_timing {*}$additional_args\n}\n'
        rendered=render_repair_script(original)
        self.assertIn('-max_buffer_percent $::env(VULSIM_REPAIR_MAX_BUFFER_PERCENT)',rendered)
        self.assertIn('log_cmd repair_timing {*}$additional_args',rendered)
        for bad in ('',original+original):
            with self.assertRaises(ValueError):render_repair_script(bad)

if __name__=='__main__':unittest.main()
