from copy import deepcopy
import unittest
from experiments.arithmetic_dse import nested_control_contexts as contexts


class NestedControlContextTests(unittest.TestCase):
    def setUp(self):
        self.rows = [dict(source=s, fold=g, role='train', target_ps=t, stage=stage,
                          actual=float(10+i+t/100+stage), f=dict(load=float(i+1)))
                     for i, (s,g) in enumerate([('a','A'), ('a-reset','A'), ('b','B'), ('c','C'), ('d','D')])
                     for t in (500,1500) for stage in (0,1)]

    @staticmethod
    def fit(rows):
        return dict(mean=sum(r['actual'] for r in rows)/len(rows))

    def make(self, rows):
        inherited = {}
        for fold in ['A','B','C','D','all_train']:
            training = [r for r in rows if fold == 'all_train' or r['fold'] != fold]
            inherited[fold] = dict(function=self.fit(training),
                training_sources=sorted({r['source'] for r in training}),
                excluded_sources=sorted({r['source'] for r in rows if fold != 'all_train' and r['fold'] == fold}),
                uses_held_out_labels=False)
        return contexts.build(rows, inherited, ['load'], self.fit)

    def test_outer_labels_cannot_change_its_upstream_contexts(self):
        a = self.make(self.rows)
        changed = deepcopy(self.rows)
        for row in changed:
            if row['fold'] == 'A':
                row['actual'] *= 1000
        b = self.make(changed)
        for row in self.rows:
            self.assertEqual(contexts.route('A', row['fold'], a)['function'],
                             contexts.route('A', row['fold'], b)['function'])

    def test_training_row_group_is_also_excluded(self):
        a = self.make(self.rows)
        changed = deepcopy(self.rows)
        for row in changed:
            if row['fold'] == 'B':
                row['actual'] *= 1000
        b = self.make(changed)
        self.assertEqual(contexts.route('A','B',a)['function'], contexts.route('A','B',b)['function'])
        self.assertNotEqual(contexts.route('A','C',a)['function'], contexts.route('A','C',b)['function'])

    def test_reset_family_and_all_targets_stay_together(self):
        a = self.make(self.rows)
        record = contexts.route('B','A',a)
        self.assertEqual(record['excluded_sources'], ['a','a-reset','b'])
        self.assertEqual(record['training_rows'], 8)
        self.assertEqual(contexts.verify(self.rows,a)['routing_checks'],100)

    def test_symmetric_pairs_share_one_fit(self):
        a = self.make(self.rows)
        self.assertIs(contexts.route('A','B',a), contexts.route('B','A',a))
        self.assertEqual(a['new_pair_context_fits'],6)
        self.assertEqual(a['inherited_contexts'],5)

    def test_final_training_uses_row_holdout_and_runtime_uses_all(self):
        a = self.make(self.rows)
        self.assertEqual(contexts.route('all_train','A',a)['excluded_folds'], ['A'])
        self.assertEqual(a['contexts'][a['final_context_key']]['excluded_folds'], [])

    def test_tampered_exclusion_or_training_label_is_rejected(self):
        a = self.make(self.rows)
        b = deepcopy(a)
        contexts.route('A','B',b)['training_sources'].append('a')
        with self.assertRaisesRegex(ValueError,'lineage'):
            contexts.verify(self.rows,b)
        changed = deepcopy(self.rows)
        changed[-1]['actual'] += 1
        with self.assertRaisesRegex(ValueError,'lineage'):
            contexts.verify(changed,a)

    def test_nontrain_and_split_source_are_rejected(self):
        changed = deepcopy(self.rows); changed[0]['role'] = 'validation'
        with self.assertRaisesRegex(ValueError,'train rows'):
            self.make(changed)
        changed = deepcopy(self.rows); changed[0]['fold'] = 'D'
        with self.assertRaisesRegex(ValueError,'one group'):
            self.make(changed)


if __name__ == '__main__':
    unittest.main()
