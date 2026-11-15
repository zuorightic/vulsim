"""Clock equations and failure visibility in the final workload report."""
import tempfile
from pathlib import Path
import unittest

from experiments.arithmetic_dse.workload_abcd import write
from experiments.arithmetic_dse.workload_results import physical_result


class FullInterfaceResults(unittest.TestCase):
    def fixture(self, root):
        (root/'runs/example').mkdir(parents=True)
        (root/'clock-readout/example').mkdir(parents=True)
        task=dict(id='example',period_ps=1000)
        metric=dict(stage='grt',cell_area_um2=100,functional_cell_area_um2=95,
                    sequential_area_um2=40,sequential_cells=20,physical_only_area_um2=5,
                    setup_worst_slack_ps=-80,hold_worst_slack_ps=-2,
                    setup_tns_ps=-100,hold_tns_ps=-3,timing_coverage_complete=True,
                    hold_feasible_at_TT=False,hold_review_required=True)
        write(root/'runs/example/manifest.json',dict(status='completed',metrics=[metric]))
        rows=dict(register_to_register=dict(slack_ps=10,required_period_ps=990),
                  input_to_register=dict(slack_ps=-80,required_period_ps=1100),
                  register_to_output=dict(slack_ps=80,required_period_ps=900),
                  full_setup_threshold=dict(slack_ps=-80,required_period_ps=1100))
        rows['threshold_check_-0.1']=dict(slack_ps=-.08,required_period_ps=1099.9)
        rows['threshold_check_0.1']=dict(slack_ps=.08,required_period_ps=1100.1)
        clock=dict(task='example',target_ps=1000,classes=rows,
                   full_setup_minimum_period_ps=1100,maximum_frequency_MHz=1e6/1100)
        write(root/'clock-readout/example/result.json',clock)
        return task,clock

    def test_input_path_uses_proportional_IO_constraint(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);task,_=self.fixture(root);r=physical_result(root,task,{})
            self.assertEqual(r['full_setup_minimum_period_ps'],1100)
            self.assertFalse(r['target_met']);self.assertFalse(r['hold_feasible_at_TT'])

    def test_incorrect_clock_bracket_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);task,c=self.fixture(root)
            c['classes']['threshold_check_0.1']['slack_ps']=-1
            write(root/'clock-readout/example/result.json',c)
            with self.assertRaisesRegex(ValueError,'bracket'):physical_result(root,task,{})

    def test_clock_cannot_belong_to_different_physical_checkpoint(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);task,c=self.fixture(root)
            path=root/'runs/example/manifest.json'
            import json
            m=json.loads(path.read_text())
            name='results/asap7/arithmetic_probe/base/5_1_grt.odb'
            m['evidence_sha256']={name:'actual-checkpoint'}
            c['fixed_inputs']={str(root/'runs/example'/name):'different-checkpoint'}
            write(path,m);write(root/'clock-readout/example/result.json',c)
            with self.assertRaisesRegex(ValueError,'checkpoints'):physical_result(root,task,{})

    def test_clock_frequency_must_match_threshold(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);task,c=self.fixture(root)
            c['maximum_frequency_MHz']=9999
            write(root/'clock-readout/example/result.json',c)
            with self.assertRaisesRegex(ValueError,'bracket'):physical_result(root,task,{})

    def test_failed_tool_does_not_receive_zero_area_or_frequency(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);task=dict(id='failed',period_ps=1000)
            (root/'runs/failed').mkdir(parents=True)
            write(root/'runs/failed/manifest.json',dict(status='failed',metrics=[],
                  active_stage='synth',failure_reason='timeout'))
            r=physical_result(root,task,{'failed':'timeout'})
            self.assertIsNone(r['maximum_frequency_MHz']);self.assertNotIn('cell_area_um2',r)
            self.assertEqual(r['failure_reason'],'timeout')

    def test_completed_grt_is_not_full_clock_completion(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);task,_=self.fixture(root)
            (root/'clock-readout/example/result.json').unlink()
            r=physical_result(root,task,{'example':'readout failed'})
            self.assertEqual(r['status'],'clock_readout_failed')
            self.assertIsNone(r['full_setup_minimum_period_ps'])


if __name__=='__main__':unittest.main()
