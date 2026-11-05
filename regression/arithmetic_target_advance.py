"""Check acquisition boundaries and frozen-decision forwarding without EDA calls."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.arithmetic_dse import model_target_advance as advance


class AcquisitionBoundaries(unittest.TestCase):
    def exercise(self,mode,count,*,gate_error=False):
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary)
            split='test' if mode=='test' else 'train'
            role='absolute-2250' if mode=='initial' else 'relative-0.8'
            tasks=[{'id':f'{split}-{i:03d}','split':split,'target_roles':[role]} for i in range(count)]
            plan={'id':'TEST_ONLY_phase_driver','tasks':tasks}
            proof=folder/'frozen.json';proof.write_text('{}')
            commands=[]
            def call(command,**kwargs):
                commands.append(command)
                if 'admit' in command:
                    remaining=[t for t in tasks if not (folder/'runs'/t['id']).exists()]
                    limit=int(command[command.index('--limit')+1])
                    wave=Path(command[command.index('--out')+1]);wave.parent.mkdir(exist_ok=True)
                    wave.write_text(json.dumps({'task_ids':[t['id'] for t in remaining[:limit]]}))
                else:
                    wave=Path(command[command.index('--wave')+1])
                    for tid in json.loads(wave.read_text())['task_ids']:
                        d=folder/'runs'/tid;d.mkdir(parents=True)
                        (d/'manifest.json').write_text('{"status":"completed"}')
            argv=['advance','--folder',str(folder),'--mode',mode]
            if mode!='initial':argv+=['--selection' if mode=='test' else '--screening',str(proof)]
            with patch.object(advance,'verify_plan',return_value=plan),patch('sys.argv',argv),\
                    patch.object(advance.subprocess,'run',side_effect=call),\
                    patch('experiments.arithmetic_dse.model_target_fit.verify_selection',side_effect=ValueError('bad frozen selection') if gate_error else None) as selection,\
                    patch('experiments.arithmetic_dse.model_target_fit.verify_screening',side_effect=ValueError('bad baseline screening') if gate_error else None) as screening:
                if gate_error:
                    with self.assertRaises(ValueError):advance.main()
                    self.assertEqual(commands,[])
                    self.assertEqual(json.loads((folder/'advance-progress.json').read_text())['phase'],'stopped_on_error')
                    return
                advance.main()
                if mode=='test':selection.assert_called_once_with(proof,folder/'plan.json');screening.assert_not_called()
                if mode=='conditional':screening.assert_called_once_with(proof,folder/'plan.json');selection.assert_not_called()
            admissions=[c for c in commands if 'admit' in c]
            if mode!='initial':
                key='--selection' if mode=='test' else '--screening'
                self.assertTrue(all(c[c.index(key)+1]==str(proof) for c in admissions))
                self.assertTrue(all(c[c.index('--mode')+1]==mode for c in admissions))
            expected='initial_collection_complete' if mode=='initial' else mode+'_collection_complete'
            self.assertEqual(json.loads((folder/'advance-progress.json').read_text())['phase'],expected)
            self.assertEqual(len(list((folder/'runs').glob('*/manifest.json'))),count)
            self.assertTrue(all('fit' not in c and 'publish' not in c for c in commands))
            if count==29:self.assertEqual([int(c[c.index('--limit')+1]) for c in admissions],[4,24,24])

    def test_independent_acquisition_only_after_selection_and_stops_for_evaluation(self):self.exercise('test',29)
    def test_conditional_acquisition_requires_screening_and_stops_for_refit(self):self.exercise('conditional',7)
    def test_bad_selection_launches_no_tasks(self):self.exercise('test',1,gate_error=True)
    def test_bad_baseline_screening_launches_no_tasks(self):self.exercise('conditional',1,gate_error=True)
    def test_initial_mode_never_collects_deferred_training(self):self.exercise('initial',5)


if __name__=='__main__':unittest.main()
