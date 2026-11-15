"""The user-approved memory exception cannot spread to another method or size."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.arithmetic_dse import workload_memory as memory
from experiments.arithmetic_dse.workload_abcd import write,sha


class MemoryPilotScope(unittest.TestCase):
    def test_only_one_confirmed_task_and_resource_envelope(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);folder=root/'capacity/pilot';folder.mkdir(parents=True)
            write(root/'admission.json',dict(id='frozen-parent'))
            a=dict(version=memory.VERSION,parent_admission_sha256=sha(root/'admission.json'),
                   memory_limit_MiB=16384,threads=4,grt_timeout_s=7200,
                   tasks=[dict(id='montgomery256-T1500-D')],sources={})
            with patch.object(memory,'verify_parent'):
                write(folder/'admission.json',a)
                self.assertEqual(memory.verify(root,folder)['memory_limit_MiB'],16384)
                for key,value in (('memory_limit_MiB',32768),('threads',8),('grt_timeout_s',14400),
                                  ('tasks',[dict(id='montgomery256-T1500-A')]),
                                  ('tasks',[dict(id='montgomery256-T3000-D')])):
                    changed=deepcopy(a);changed[key]=value;write(folder/'admission.json',changed)
                    with self.subTest(key=key,value=value),self.assertRaisesRegex(ValueError,'unregistered'):
                        memory.verify(root,folder)


if __name__=='__main__':unittest.main()
