"""Clone restoration preserves accounting, including failed calls and job claims."""
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from experiments.arithmetic_dse.budget import Ledger, digest, usage
from experiments.arithmetic_dse.ledger_snapshot import export_snapshot, load_snapshot, metadata_path


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.policy = self.root/'policy.json'
        self.policy.write_text('{}')
        self.checkpoint = self.root/'checkpoint.json'
        entry = dict(id='paid-failure', stage='synth', status='failed', walltime_s=4., CPU_time_s=8.)
        self.checkpoint.write_text(json.dumps(dict(entries=[entry])))
        self.state = dict(version='physical-budget-ledger-v1', policy_sha256=digest(self.policy),
                          checkpoint_sha256=digest(self.checkpoint), entries=[entry],
                          jobs=[dict(id='claimed',status='released')], migrations=[dict(reason='preserved')],
                          usage=usage([entry]))
        self.live = self.root/'original.json'
        self.live.write_text(json.dumps(self.state))
        self.snapshot = self.root/'backend_usage.snapshot.json.gz'
        export_snapshot(Ledger(self.live,self.policy,self.checkpoint),self.snapshot)

    def test_new_clone_restores_all_entries_migrations_and_job_claims(self):
        self.assertEqual(load_snapshot(self.snapshot,self.policy,self.checkpoint),self.state)
        clone = Ledger(self.root/'clone.json',self.policy,self.checkpoint,snapshot=self.snapshot)
        self.assertTrue(clone.path.is_file())  # Supports existing direct reads of Ledger().path.
        self.assertEqual(clone.summary(),self.state['usage'])
        self.assertEqual(json.loads(clone.path.read_text()),self.state)
        clone.path.unlink()
        with self.assertRaisesRegex(ValueError,'missing after initialization'):
            clone.summary()

    def test_existing_live_history_wins_over_the_published_snapshot(self):
        newer = deepcopy(self.state)
        newer['entries'].append(dict(id='newer',stage='grt',status='completed',walltime_s=2.,CPU_time_s=3.))
        newer['usage'] = usage(newer['entries'])
        self.live.write_text(json.dumps(newer))
        ledger = Ledger(self.live,self.policy,self.checkpoint,snapshot=self.snapshot)
        self.assertEqual(ledger.summary(),newer['usage'])

    def test_missing_tampered_or_wrong_policy_snapshot_is_rejected(self):
        raw = self.snapshot.read_bytes()
        self.snapshot.write_bytes(raw+b'tampered')
        with self.assertRaisesRegex(ValueError,'snapshot identity'):
            load_snapshot(self.snapshot,self.policy,self.checkpoint)
        self.snapshot.write_bytes(raw)
        self.policy.write_text('{"different":true}')
        with self.assertRaisesRegex(ValueError,'policy/checkpoint'):
            load_snapshot(self.snapshot,self.policy,self.checkpoint)
        self.snapshot.unlink()
        with self.assertRaises(FileNotFoundError):
            Ledger(self.root/'new.json',self.policy,self.checkpoint,snapshot=self.snapshot).summary()

    def test_export_rejects_pending_or_live_jobs_and_is_deterministic(self):
        before = self.snapshot.read_bytes()
        export_snapshot(Ledger(self.live,self.policy,self.checkpoint),self.snapshot)
        self.assertEqual(self.snapshot.read_bytes(),before)
        for pending in (True,False):
            changed = deepcopy(self.state)
            if pending:
                changed['entries'].append(dict(id='in-flight',stage='grt',status='reserved',
                                               walltime_s=10.,CPU_time_s=20.))
            else:changed['jobs'][0]['status']='active'
            changed['usage']=usage(changed['entries'])
            self.live.write_text(json.dumps(changed))
            with self.assertRaisesRegex(ValueError,'settled'):
                export_snapshot(Ledger(self.live,self.policy,self.checkpoint),self.snapshot)

    def test_rehashed_snapshot_cannot_drop_the_old_checkpoint_prefix(self):
        changed = deepcopy(self.state)
        changed['entries']=[];changed['usage']=usage([])
        raw=json.dumps(changed).encode();packed=gzip.compress(raw,mtime=0)
        metadata=json.loads(metadata_path(self.snapshot).read_text())
        metadata.update(compressed_sha256=hashlib.sha256(packed).hexdigest(),
                        uncompressed_sha256=hashlib.sha256(raw).hexdigest(),entry_count=0,usage=changed['usage'])
        self.snapshot.write_bytes(packed);metadata_path(self.snapshot).write_text(json.dumps(metadata))
        with self.assertRaisesRegex(ValueError,'lost checkpoint history'):
            load_snapshot(self.snapshot,self.policy,self.checkpoint)


if __name__=='__main__':unittest.main()
