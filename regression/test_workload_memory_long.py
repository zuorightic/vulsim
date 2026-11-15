"""An eight-hour exception needs a new exact-point confirmation and source."""
from pathlib import Path
import tempfile
import unittest

from experiments.arithmetic_dse.workload_abcd import sha,write
from experiments.arithmetic_dse.workload_memory_long import authorization,TASK


class LongMemoryAuthorization(unittest.TestCase):
    def fixture(self,root):
        source=root/'retained';source.mkdir()
        write(source/'manifest.json',dict(status='failed'))
        path=root/'authorizations/montgomery-memory16-long-v1.json';path.parent.mkdir()
        auth=dict(status='user_confirmed',user_reply='fixture confirmation',task=TASK,
                  memory_limit_MiB=16384,threads=4,grt_timeout_s=28800,
                  source_manifest_sha256=sha(source/'manifest.json'))
        return source,path,auth

    def test_missing_new_confirmation_does_not_inherit_the_two_hour_permission(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source,_,_=self.fixture(root)
            with self.assertRaisesRegex(ValueError,'new explicit user confirmation'):
                authorization(root,source)

    def test_pending_confirmation_cannot_start(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source,path,auth=self.fixture(root)
            auth['status']='proposed';write(path,auth)
            with self.assertRaisesRegex(ValueError,'scope differs'):authorization(root,source)

    def test_exception_cannot_expand_to_another_point_or_resource_limit(self):
        for key,value in [('task','montgomery256-T3000-D'),('memory_limit_MiB',32768),
                          ('threads',8),('grt_timeout_s',7200)]:
            with self.subTest(key=key),tempfile.TemporaryDirectory() as d:
                root=Path(d);source,path,auth=self.fixture(root)
                auth[key]=value;write(path,auth)
                with self.assertRaisesRegex(ValueError,'scope differs'):authorization(root,source)

    def test_confirmation_binds_the_retained_failed_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source,path,auth=self.fixture(root);write(path,auth)
            self.assertEqual(authorization(root,source)[0],path)
            write(source/'manifest.json',dict(status='changed'))
            with self.assertRaisesRegex(ValueError,'source changed'):authorization(root,source)


if __name__=='__main__':unittest.main()
