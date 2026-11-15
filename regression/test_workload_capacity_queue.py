"""Slot contention may wait; an attempted job or body failure never retries."""
from contextlib import contextmanager
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from experiments.arithmetic_dse.budget import BudgetExceeded
from experiments.arithmetic_dse.workload_capacity_queue import wait_for_job


class CapacityQueue(unittest.TestCase):
    def fixture(self, folder, entries=None, jobs=None):
        path = Path(folder)/'ledger.json'
        path.write_text(json.dumps(dict(entries=entries or [], jobs=jobs or [])))
        return SimpleNamespace(path=path, job_id=None)

    def test_contention_waits_without_restarting_the_task_body(self):
        with tempfile.TemporaryDirectory() as folder:
            ledger = self.fixture(folder);calls = [];released = [];pauses = []
            @contextmanager
            def acquire(context):
                calls.append(context)
                if len(calls) < 3:raise BudgetExceeded('all backend job slots occupied')
                try:yield 'one-job'
                finally:released.append(True)
            body = []
            with wait_for_job(ledger, dict(admission_id='a', task_id='t'), acquire, pauses.append) as job:
                body.append(job)
            self.assertEqual(body, ['one-job']);self.assertEqual(pauses, [2, 2])
            self.assertEqual(released, [True]);self.assertEqual(len(calls), 3)

    def test_a_recorded_leaf_or_job_prevents_waiting(self):
        identity = dict(admission_id='a', task_id='t')
        for field in ('entries', 'jobs'):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as folder:
                ledger = self.fixture(folder, **{field: [identity]})
                @contextmanager
                def acquire(context):
                    raise BudgetExceeded('all backend job slots occupied')
                    yield
                with self.assertRaisesRegex(ValueError, 'attempted capacity'):
                    with wait_for_job(ledger, identity, acquire, lambda _: self.fail('waited')):
                        self.fail('task body entered')

    def test_body_budget_failure_is_propagated_and_releases_the_job(self):
        with tempfile.TemporaryDirectory() as folder:
            ledger = self.fixture(folder);calls = [];released = []
            @contextmanager
            def acquire(context):
                calls.append(context)
                try:yield 'job'
                finally:released.append(True)
            with self.assertRaisesRegex(BudgetExceeded, 'all backend job slots occupied'):
                with wait_for_job(ledger, dict(admission_id='a', task_id='t'), acquire,
                                  lambda _: self.fail('retried task body')):
                    raise BudgetExceeded('all backend job slots occupied')
            self.assertEqual(len(calls), 1);self.assertEqual(released, [True])

    def test_other_budget_rejection_is_immediate(self):
        with tempfile.TemporaryDirectory() as folder:
            ledger = self.fixture(folder)
            @contextmanager
            def acquire(context):
                raise BudgetExceeded('unfinished backend reservation requires evidence reconciliation')
                yield
            with self.assertRaisesRegex(BudgetExceeded, 'reconciliation'):
                with wait_for_job(ledger, dict(admission_id='a', task_id='t'), acquire,
                                  lambda _: self.fail('waited on unresolved accounting')):
                    self.fail('task body entered')


if __name__ == '__main__':unittest.main()
