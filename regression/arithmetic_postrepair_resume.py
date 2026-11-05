"""Post-repair replay and shared-slot scheduling boundaries."""
from pathlib import Path
import json
import tempfile
import unittest
from experiments.arithmetic_dse import model_m2_postrepair_resume as r
from experiments.arithmetic_dse.model_m2_phase_resume import validate_lec


class PostrepairResume(unittest.TestCase):
    def test_shared_slots_include_other_drivers_and_children_waiting_for_a_lease(self):
        jobs=[{'status':'active','task_id':x} for x in ('F1','validation2','validation3')]
        self.assertEqual(r.available_slots(jobs,set()),1)
        self.assertEqual(r.available_slots(jobs,{'F3'}),0)
        jobs.append({'status':'active','task_id':'F3'})
        self.assertEqual(r.available_slots(jobs,{'F3'}),0)
        jobs[1]['status']='released'
        self.assertEqual(r.available_slots(jobs,{'F3'}),1)

    def test_mapping_dependency_requires_completion_not_just_a_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);task={'id':'t1','mapping_source_task':'t0'};indexed={'t0':{'id':'t0'}}
            self.assertFalse(r.ready(task,indexed,folder))
            d=folder/'runs/t0';d.mkdir(parents=True)
            for status,expected in [('running',False),('failed',False),('completed',True)]:
                (d/'manifest.json').write_text(json.dumps({'status':status}));self.assertEqual(r.ready(task,indexed,folder),expected)

    def test_postrepair_tail_loads_saved_physical_state_and_retains_original_tail(self):
        original=Path('/home/zyrv/OpenROAD-flow-scripts/flow/scripts/cts.tcl').read_text();tail=r.render_tail(original,Path('/tmp/F3-continuation'))
        self.assertIn('load_design 4_1_post_repair_pre_lec.odb 4_1_post_repair_pre_lec.sdc',tail)
        self.assertIn('4_after_resume_load.v',tail);self.assertIn('verify-pair',tail)
        self.assertNotIn('repair_timing_helper',tail);self.assertNotIn('clock_tree_synthesis',tail)
        self.assertIn('report_metrics 4 "cts final"',tail)
        self.assertIn('orfs_write_db $::env(RESULTS_DIR)/4_1_cts.odb',tail)
        marker='    run_lec_test 4_rsz 4_before_rsz_lec.v 4_after_rsz_lec.v'
        start=original.index('\n  set result [catch { log_cmd detailed_placement } msg]',original.index(marker))
        self.assertTrue(tail.endswith(original[start:]))

    def test_F3_proof_requires_its_larger_full_boundary(self):
        text='SAT solver finished: UNSAT\nCircuits are IDENTICAL\n'
        for d in (0,1):text+=f'size of PIs in circuit {d}: 454\nsize of POs in circuit {d}: 649\nsize of diff{d} inputs: 0\nsize of diff{d} outputs: 0\n'
        validate_lec(text,454,649)
        with self.assertRaises(ValueError):validate_lec(text,326,389)


if __name__=='__main__':unittest.main()
