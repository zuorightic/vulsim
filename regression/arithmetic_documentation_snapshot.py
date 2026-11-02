"""Editable planning prose must not weaken implementation identity checks."""
from pathlib import Path
import hashlib,json,tempfile,unittest
from experiments.arithmetic_dse.freeze_history import source_location

class DocumentationSnapshots(unittest.TestCase):
    def test_editable_plan_reads_immutable_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);relative='mission/lxy-plan-fix.md';active=root/relative;active.parent.mkdir();active.write_text('## 步骤六\n')
            saved=root/'evidence/old-plan.md';saved.parent.mkdir();saved.write_text('## 6. 步骤六\n')
            h=hashlib.sha256(saved.read_bytes()).hexdigest();f=root/'freeze.json';f.write_text(json.dumps({'source_snapshots':{relative:'evidence/old-plan.md'}}))
            self.assertEqual(source_location(root,'freeze.json',relative,h),saved)
            saved.write_text('tampered')
            with self.assertRaises(ValueError):source_location(root,'freeze.json',relative,h)

    def test_source_and_cost_config_remain_strict(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for relative in ('rtlzz/src/backend/arithmetic_core.cpp','experiments/arithmetic_dse/configs/fixed_op_width_v1.json'):
                active=root/relative;active.parent.mkdir(parents=True,exist_ok=True);active.write_text('changed')
                saved=root/'saved.txt';saved.write_text('original');h=hashlib.sha256(saved.read_bytes()).hexdigest()
                (root/'freeze.json').write_text(json.dumps({'source_snapshots':{relative:'saved.txt'}}))
                with self.subTest(relative=relative),self.assertRaises(ValueError):source_location(root,'freeze.json',relative,h)

if __name__=='__main__':unittest.main()
