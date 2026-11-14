"""Semantic reset preservation, renaming and crossfit leakage contracts."""
from copy import deepcopy
import math
from pathlib import Path
import unittest
from unittest.mock import patch
from experiments.arithmetic_dse import semantic_reset_features_v9 as features,semantic_reset_model_v9 as model
from experiments.arithmetic_dse.common_centered_replay_v1 import load,close
from experiments.arithmetic_dse.prospective_logic import Circuit
from experiments.arithmetic_dse.semantic_reset_replay_v9 import verify_context_lineage

ROOT=Path(__file__).resolve().parents[1]/'experiments/arithmetic/evidence/common_semantic_reset_v9'


class SemanticResetTests(unittest.TestCase):
    def setUp(self):
        self.bundle=load(ROOT/'runtime-bundle.json.gz')
        self.train=load(ROOT/'train-data.json.gz')
        self.query=deepcopy(self.train['data']['S'][0]['structure'])

    def test_explicit_masks_are_required(self):
        self.query.pop('reset_semantics')
        self.assertEqual(model.predict_state(self.bundle,self.query,diagnostic=True)['status'],'cost_uncovered')

    def test_reset_and_birth_inversion_must_agree(self):
        bit=self.query['reset_semantics']['words'][0]['invert_bits']
        bit[0]^=1
        with self.assertRaisesRegex(ValueError,'birth polarity disagree'):
            features.base_state_controls(self.query)

    def test_stage_projection_cannot_disagree_with_word_lifetimes(self):
        self.query['reset_semantics']['words'][0]['end']=1
        with self.assertRaisesRegex(ValueError,'stage projection|lifetime'):
            features.base_state_controls(self.query)

    def test_root_group_renaming_preserves_features(self):
        q=deepcopy(self.query);widths=q['input_widths'];order=list(reversed(range(len(widths))))
        offsets=[sum(widths[:i]) for i in range(len(widths))];mapping={}
        for rank,i in enumerate(order):
            for bit in range(widths[i]):mapping[offsets[i]+bit]=sum(widths[j] for j in order[:rank])+bit
        q['input_widths']=[widths[i] for i in order]
        q['reset_semantics']['input_bits']=[q['reset_semantics']['input_bits'][i] for i in order]
        q['input_sink_inputs']=[[mapping[n] for n in sink] for sink in q['input_sink_inputs']]
        close(features.state_controls(q,self.bundle['context_function']),features.state_controls(self.query,self.bundle['context_function']))

    def test_previous_query_alias_is_distinguished(self):
        pairs=[p for p in self.train['paired_folds'] if p.get('origin')=='v8_identical_query_train_contrast']
        for pair in pairs:
            before,after=[next(r for r in self.train['data']['S'] if r['source']==pair[side] and r['target_ps']==1500)['structure'] for side in ('old','new')]
            self.assertNotEqual(before,after)
            a,b=[features.state_controls(q,self.bundle['context_function']) for q in (before,after)]
            self.assertNotEqual(a,b)

    def test_cone_spans_exclude_dead_and_control_nodes(self):
        c=Circuit();a=c.leaf(('lhs',0));b=c.leaf(('rhs',4));control=c.leaf(('cin',0))
        out=c.gate('and',c.gate('xor',a,b),control)
        c.gate('xor',a,c.leaf(('lhs',30)))
        values=features.cone_spans(c,[out])
        self.assertAlmostEqual(values['log2_total_span'],math.log2(9))
        self.assertAlmostEqual(values['log2_peak_cut'],math.log2(3))
        self.assertEqual(values['local_fraction'],0.)

    def test_entire_parent_fold_is_excluded_from_context(self):
        cross=load(ROOT/'context-crossfit.json.gz');pair=next(p for p in self.train['paired_folds'] if p.get('origin'))
        cross['contexts'][pair['group']]['training_sources'].append(pair['new'])
        with self.assertRaisesRegex(ValueError,'held-out context training leaked'):
            verify_context_lineage(self.train,cross,load(ROOT/'train-predictions.json.gz'),self.bundle)

    def test_state_inference_uses_no_io_or_process(self):
        with patch('subprocess.Popen',side_effect=AssertionError('online process')):
            with patch('builtins.open',side_effect=AssertionError('online file')):
                with patch('pathlib.Path.open',side_effect=AssertionError('online path')):
                    result=model.predict_state(self.bundle,self.query,diagnostic=True)
        self.assertEqual(result['status'],'diagnostic_estimate')


if __name__=='__main__':unittest.main()
