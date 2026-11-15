"""A completed CTS checkpoint is reusable only with its complete LEC receipt."""
from pathlib import Path
import tempfile
import unittest

from experiments.arithmetic_dse import workload_checkpoint as checkpoint
from experiments.arithmetic_dse.workload_abcd import sha


class CompletedCheckpoint(unittest.TestCase):
    def fixture(self,root):
        names=checkpoint.GROUPS[0][1]
        m=dict(metrics=[dict(stage='synth')],evidence_sha256={})
        for name in names:
            relative=Path('results')/checkpoint.capacity.SUFFIX/name
            p=root/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(name)
            m['evidence_sha256'][str(relative)]=sha(p)
        log=root/'logs'/checkpoint.capacity.SUFFIX/'4_rsz_lec_check.log'
        log.parent.mkdir(parents=True)
        text='SAT solver finished: UNSAT\nCircuits are IDENTICAL\n'
        for side in (0,1):
            text+=f'size of PIs in circuit {side}: 7\nsize of POs in circuit {side}: 9\n'
            text+=f'size of diff{side} inputs: 0\nsize of diff{side} outputs: 0\n'
        log.write_text(text);m['evidence_sha256'][str(log.relative_to(root))]=sha(log)
        return m,log

    def test_post_CTS_reuse_requires_complete_successful_proof(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);m,log=self.fixture(root)
            phase,hashes,proof=checkpoint.checkpoints(root,m)
            self.assertEqual(phase,'post_CTS');self.assertEqual(len(hashes),7)
            self.assertEqual(proof['boundary'],dict(PIs=7,POs=9))
            log.write_text(log.read_text().replace('diff1 outputs: 0','diff1 outputs: 1'))
            m['evidence_sha256'][str(log.relative_to(root))]=sha(log)
            with self.assertRaisesRegex(ValueError,'boundary mismatch'):
                checkpoint.checkpoints(root,m)

    def test_checkpoint_mutation_cannot_downgrade_to_an_earlier_phase(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);m,_=self.fixture(root)
            (root/'results'/checkpoint.capacity.SUFFIX/'4_cts.odb').write_text('changed')
            with self.assertRaisesRegex(ValueError,'checkpoint changed'):
                checkpoint.checkpoints(root,m)

    def test_incomplete_CTS_uses_complete_synthesis_only(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);m,_=self.fixture(root)
            (root/'results'/checkpoint.capacity.SUFFIX/'4_cts.sdc').unlink()
            phase,_,proof=checkpoint.checkpoints(root,m)
            self.assertEqual(phase,'post_synthesis');self.assertIsNone(proof)


if __name__=='__main__':unittest.main()
