import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.arithmetic_dse.workload_storage import pack, restore


class SettledStorage(unittest.TestCase):
    def setup_batch(self,root,status='batch_settled'):
        root=Path(root);(root/'progress.json').write_text(json.dumps(dict(status=status)))
        p=root/'runs/sample/results/asap7/probe/base/3_place.odb';p.parent.mkdir(parents=True)
        p.write_bytes(b'ODB test bytes\x00'*2048);return p

    def test_exact_restore_and_repeat_pack(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.setup_batch(d);data=p.read_bytes();r=pack(d)
            self.assertEqual(r['files'],1);self.assertFalse(p.exists())
            self.assertLess(r['stored_bytes'],r['original_bytes'])
            restore(d);self.assertEqual(p.read_bytes(),data)
            self.assertEqual(pack(d)['index_sha256'],r['index_sha256'])
            restore(d);self.assertEqual(p.read_bytes(),data)

    def test_running_batch_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.setup_batch(d,'running')
            with self.assertRaises(ValueError):pack(d)
            self.assertTrue(p.exists())

    def test_corrupt_archive_cannot_restore(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.setup_batch(d);pack(d);p.with_suffix('.odb.gz').write_bytes(b'bad archive')
            with self.assertRaisesRegex(ValueError,'archive byte identity'):restore(d)
            self.assertFalse(p.exists())

    def test_changed_destination_never_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.setup_batch(d);pack(d);p.write_bytes(b'different')
            with self.assertRaisesRegex(ValueError,'different bytes'):restore(d)
            self.assertEqual(p.read_bytes(),b'different')

    def test_old_dispatcher_settled_but_transferred_job_active_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=self.setup_batch(root)
            (root/'admission.json').write_text(json.dumps(dict(id='a-transferred-batch')))
            ledger=root/'ledger.json';ledger.write_text(json.dumps(dict(jobs=[
                dict(admission_id='a-transferred-batch',status='active')])))
            with patch('experiments.arithmetic_dse.budget.LEDGER',ledger):
                with self.assertRaisesRegex(ValueError,'active or unsettled'):pack(root)
            self.assertTrue(p.exists())


if __name__=='__main__':unittest.main()
