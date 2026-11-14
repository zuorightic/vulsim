import copy
import math
import unittest
from unittest.mock import patch

from experiments.arithmetic_dse import local_bank_features_v12 as local
from experiments.arithmetic_dse import factorized_area_v12 as area


def query(entries, depth=2):
    roots = [0,1,0]
    words, sinks = [], []
    for inputs, inversions, start, end in entries:
        reset = [(sum(roots[n] for n in ns)+inv)%2 for ns,inv in zip(inputs,inversions)]
        words.append(dict(reset_bits=reset,invert_bits=inversions,start=start,end=end,external=False))
        sinks.extend(inputs)
    return dict(input_widths=[3],stage_words=[[len(w['reset_bits']) for w in words
        if w['start']<=stage<=w['end']] for stage in range(1,depth+1)],external_bits=0,
        stage_reset_one_bits=[sum(sum(w['reset_bits']) for w in words
        if w['start']<=stage<=w['end']) for stage in range(1,depth+1)],
        input_reset_one_bits=1,input_sink_inputs=sinks,
        reset_semantics=dict(version=local.previous.SEMANTICS,input_bits=[roots],words=words))


class CaptureLocalTests(unittest.TestCase):
    def test_polarity_normalization_preserves_raw_difference(self):
        q = query([([[0],[0]],[0,1],1,1)])
        f = local.bank_profiles(q)[0]
        self.assertEqual(f['local_raw_alias_fraction'],0)
        self.assertEqual(f['local_normalized_alias_fraction'],.5)
        self.assertEqual(f['local_phase_split_fraction'],.5)

    def test_kept_hold_registers_are_distinct(self):
        q = query([([[0],[0]],[0,0],1,2)])
        first,second = local.bank_profiles(q)
        self.assertEqual(first['local_raw_alias_fraction'],.5)
        self.assertEqual(second['local_raw_alias_fraction'],0)
        self.assertEqual(second['local_birth_fraction'],0)

    def test_later_birth_does_not_change_earlier_bank(self):
        q = query([([[0]],[0],1,1),([[0],[2]],[0,0],2,2)])
        changed = query([([[0]],[0],1,1),([[0],[0]],[0,0],2,2)])
        a,b = local.bank_profiles(q),local.bank_profiles(changed)
        self.assertEqual(a[0],b[0])
        self.assertNotEqual(a[1],b[1])

    def test_root_renaming_and_word_order_invariant(self):
        q = query([([[0,1],[2]],[0,1],1,2),([[1],[0]],[0,1],2,2)])
        changed = copy.deepcopy(q)
        permutation = [2,0,1]
        original = q['reset_semantics']['input_bits'][0]
        changed['reset_semantics']['input_bits'][0] = [original[permutation.index(i)] for i in range(3)]
        changed['input_sink_inputs'] = [[permutation[n] for n in ns] for ns in q['input_sink_inputs']]
        self.assertEqual(local.bank_profiles(q),local.bank_profiles(changed))
        reversed_q = query([([[1],[0]],[0,1],2,2),([[0,1],[2]],[0,1],1,2)])
        self.assertEqual(local.bank_profiles(q),local.bank_profiles(reversed_q))

    def test_contradictory_semantics_rejected(self):
        q = query([([[0]],[0],1,1)])
        q['reset_semantics']['words'][0]['reset_bits'][0] = 1
        with self.assertRaises(ValueError):
            local.bank_profiles(q)

    def test_factorized_prediction_needs_no_measurements_or_io(self):
        def constant(value):
            return dict(version='centered-numerical-response-v1',features=[],centers=[],scales=[],
                        coefficients=[],intercept=math.log(value),link='positive_log_linear')
        model = dict(version=area.VERSION,price_status='train_diagnostic_only',
            mapping=constant(2),physical_ratio=constant(.75),mapping_reference='work_area')
        with patch('builtins.open',side_effect=AssertionError('file')):
            with patch('subprocess.Popen',side_effect=AssertionError('process')):
                result = area.predict(model,dict(work_area=8))
                self.assertEqual(result,area.predict(model,dict(work_area=8,measured_area=-1000)))
        self.assertAlmostEqual(result['predicted_grt_area_um2'],12)
        self.assertFalse(result['qualified_for_public_D'])


if __name__=='__main__':
    unittest.main()
