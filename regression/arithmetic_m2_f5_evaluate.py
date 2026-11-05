"""Frozen target-scale inference, mandatory class gates and F5 source lock."""
import copy
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from experiments.arithmetic_dse.model_m2_f5_evaluate import report,validate_cohort,initial_observation_owner
from experiments.arithmetic_dse.model_collection import write,sha


def row(index=0,op='add',period=150):
    return {'id':str(index),'task_id':str(index),'operation':op,'rtl_operation':op,'stage':'grt',
        'features':{},'spec':{'lhs_width':8,'rhs_width':8,'result_width':8},'delay_ps':100,'comb_area_um2':10,
        'period_ps':period,'observed_H_ps':10,'path_slack_ps':period-110,'whole_setup_slack_ps':period-110}


def model(value=100,scale=1,margin=1.5):
    def constant(v):return {'kind':'linear','features':[],'coefficients':[],'intercept':v}
    return {'delay':{'kind':'pooled','predictor':constant(value),'delay_scale':scale,'delay_margin_ps':margin},
        'area':{'kind':'pooled','predictor':constant(10),'delay_margin_ps':0}}


class F5Verdict(unittest.TestCase):
    def test_t0_optional_observation_annotation_follows_exact_ancestor(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);source=root/'t0';source.mkdir();(source/'snapshot').write_text('original')
            old={'initial_synth_observation_sha256':{'snapshot':sha(source/'snapshot')},'initial_unlabeled_synth_metrics':[{'stage':'synth'}]}
            write(source/'manifest.json',old)
            new={**old,'checkpoint_reuse':{'mode':'exact_t0_mapping_fresh_SDC_ODB','source_run':str(source),'source_manifest_sha256':sha(source/'manifest.json')}}
            self.assertEqual(initial_observation_owner(root/'t1',new),source)
            changed=copy.deepcopy(new);changed['initial_synth_observation_sha256']['snapshot']='changed'
            with self.assertRaisesRegex(ValueError,'inherited initial'):initial_observation_owner(root/'t1',changed)

    def test_missing_observation_cannot_be_ignored_without_inheritance(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,'missing initial'):initial_observation_owner(Path(td),{'initial_synth_observation_sha256':{'missing':'x'}})
    def test_scaled_margin_is_evaluated_without_tuning(self):
        candidate={'stages':{'grt':{'operations':{'add':model(scale=1.1)}}}};before=copy.deepcopy(candidate)
        result=report([row()],candidate)['grt']
        self.assertAlmostEqual(result['operations']['add']['predictions'][0]['delay_ps'],111.5)
        self.assertAlmostEqual(result['delay']['median_relative_error'],.115)
        self.assertEqual(candidate,before)

    def test_exact_target_partition_cannot_fall_back(self):
        m=model();m['delay']={'kind':'exact_width_target_slices','slices':{'8/8/8/150':m['delay']}}
        candidate={'stages':{'grt':{'operations':{'add':m}}}}
        self.assertEqual(report([row()],candidate)['grt']['status'],'passed')
        with self.assertRaises(KeyError):report([row(period=151)],candidate)

    def test_failed_class_cannot_be_rescued_by_overall_average(self):
        rows=[row(i) for i in range(30)]+[row(30,'mux')]
        candidate={'stages':{'grt':{'operations':{'add':model(),'mux':model(40,margin=0)}}}}
        result=report(rows,candidate)['grt']
        self.assertEqual(result['passing_operations'],1);self.assertEqual(result['status'],'failed')

    def test_conservative_estimate_still_must_pass_error_gate(self):
        candidate={'stages':{'grt':{'operations':{'add':model(scale=2)}}}}
        result=report([row()],candidate)['grt']
        self.assertEqual(result['false_feasible'],0);self.assertEqual(result['status'],'failed')

    def test_wrong_task_count_rejected(self):
        with self.assertRaisesRegex(ValueError,'all56'):validate_cohort({'tasks':[]},{'tasks':[]})

    def test_old_F4_cohort_rejected(self):
        tasks=[{'id':f'test-F4-{i}','split':'test'} for i in range(56)]
        with self.assertRaisesRegex(ValueError,'source/target cohort'):validate_cohort({'tasks':tasks},{'tasks':tasks})

    def test_local_false_feasible_cannot_hide_behind_large_actual_period(self):
        candidate={'stages':{'grt':{'operations':{'add':model(80,margin=0)}}}}
        result=report([row(period=1000)],candidate)['grt']
        self.assertEqual(result['actual_target_false_feasible'],0)
        self.assertGreater(result['false_feasible'],0);self.assertEqual(result['status'],'failed')


if __name__=='__main__':unittest.main()
