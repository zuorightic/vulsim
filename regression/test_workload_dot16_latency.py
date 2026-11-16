"""Regressions for useful arithmetic stages and isolated Dot16 successors."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.arithmetic_dse.workload_dot16_latency import (
    active_stages, depth_schedule, earlier_wave_settled, frozen)


class ArithmeticStages(unittest.TestCase):
    def tree(self):
        # One product followed by four atomic adds: five serial operations.
        nodes = [dict(id=0,operation='input',operands=[])]
        for i in range(1,6):
            nodes.append(dict(id=i,operation='mul' if i==1 else 'add',operands=[dict(node=i-1)]))
        nodes.append(dict(id=6,operation='wire',operands=[dict(node=5)]))
        units = [dict(members=[i],fixed=i in (0,6),constant=False) for i in range(7)]
        return dict(nodes=nodes),units,{i:1. for i in range(1,6)}

    def test_atomic_operators_fill_L4_and_L5_without_arithmetic_splitting(self):
        raw,units,weights = self.tree()
        for L in (4,5):
            p = depth_schedule(raw,units,L,weights)
            self.assertEqual(active_stages(raw,p,weights),list(range(L)))
            self.assertEqual(p[0],0); self.assertEqual(p[-1],L-1)
            self.assertTrue(all(a<=b for a,b in zip(p,p[1:])))
        with self.assertRaisesRegex(ValueError,'depth'):
            depth_schedule(raw,units,8,weights)

    def test_wires_and_register_padding_cannot_fill_missing_arithmetic(self):
        raw,units,weights = self.tree()
        p = [0,0,1,2,3,3,7]
        self.assertEqual(active_stages(raw,p,weights),[0,1,2,3])

    def test_indivisible_arithmetic_group_stays_together(self):
        raw,units,weights = self.tree()
        units = [units[0],dict(members=[1,2],fixed=False,constant=False),*units[3:]]
        p = depth_schedule(raw,units,4,weights)
        self.assertEqual(p[1],p[2]); self.assertEqual(active_stages(raw,p,weights),[0,1,2,3])


class SuccessorIntegrity(unittest.TestCase):
    def test_input_freeze_rejects_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/'nested/input.json'; frozen(p,dict(L=4))
            frozen(p,dict(L=4))
            with self.assertRaisesRegex(ValueError,'immutable'):
                frozen(p,dict(L=5))

    def test_queued_parent_work_blocks_four_slot_handoff_even_without_live_job(self):
        from experiments.arithmetic_dse.workload_abcd import write
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); batch = root/'final-dot'; batch.mkdir()
            write(batch/'admission.json',{}); write(batch/'progress.json',dict(status='running',active=['queued']))
            with patch('experiments.arithmetic_dse.workload_dot16_latency.PARENT',root):
                self.assertFalse(earlier_wave_settled())


if __name__=='__main__':
    unittest.main()
