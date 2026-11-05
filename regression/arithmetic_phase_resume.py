"""Checkpoint identity, complete proof coverage and rolling fitting admission."""
from pathlib import Path
import json
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from experiments.arithmetic_dse import model_m2_collection as collection
from experiments.arithmetic_dse import model_m2_phase_resume as resume


class PhaseResume(unittest.TestCase):
    def test_complete_source_preservation_and_rolling_training_validation_without_test(self):
        parent=Path('build/step7-m2-models-20261104/primitives-v5/plan.json').resolve()
        if not parent.exists():self.skipTest('preserved physical fixture unavailable')
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/'continuation';collection.prepare(folder,parent.parent/'AtomicFp.sv',parent,phase_continuation=True)
            p=collection.verify_plan(folder/'plan.json');prior=collection.read(parent)
            self.assertEqual(sum(bool(t.get('inherited_run')) for t in p['tasks']),98)
            for t,old in zip(p['tasks'],prior['tasks']):
                for name in ('id','split','period_ps','abc_target_ps','rtl_sha256','sample_contract_sha256','mapping_source_task'):
                    self.assertEqual(t[name],old[name])
            target=next(t for t in p['tasks'] if t.get('phase_resume'))
            self.assertEqual(target['id'],'train-F1-divrem-w32-t2')
            self.assertIn('3_place.odb',target['phase_resume']['checkpoint_sha256'])
            collection.write(folder/'capacity-proof.json',{'status':'passed','plan_sha256':collection.sha(folder/'plan.json')})
            with patch.object(collection,'funding',return_value={}):
                wave=folder/'waves/fitting.json';collection.admit(folder,'fitting',wave,70)
            ids=collection.read(wave)['task_ids'];chosen=[t for t in p['tasks'] if t['id'] in ids]
            self.assertEqual(len(ids),70);self.assertEqual(sum(t['split']=='validation' for t in chosen),56)
            self.assertFalse(any(t['split']=='test' for t in chosen))
            self.assertEqual(ids[0],target['id'])
            with self.assertRaisesRegex(ValueError,'locked'):collection.admit(folder,'test',folder/'waves/test.json')

    def test_observational_checkpoint_keeps_original_CTS_and_LEC_operations(self):
        original=Path('/home/zyrv/OpenROAD-flow-scripts/flow/scripts/cts.tcl').read_text()
        rendered=resume.render_observational_cts(original)
        added='    orfs_write_db $::env(RESULTS_DIR)/4_1_post_repair_pre_lec.odb\n    orfs_write_sdc $::env(RESULTS_DIR)/4_1_post_repair_pre_lec.sdc\n'
        self.assertEqual(rendered.replace(added,''),original)
        self.assertLess(rendered.index('4_1_post_repair_pre_lec.odb'),rendered.index('    run_lec_test 4_rsz'))

    def test_actual_solver_equivalence_and_counterexample_are_distinguished(self):
        executable=Path(resume.read(resume.CONFIG)['lec_executable'])
        if not executable.exists():self.skipTest('Kepler unavailable')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);a=root/'a.v';b=root/'b.v'
            a.write_text('module top(input a,b,output y);assign y=a;endmodule\n')
            for equivalent,expression in ((True,'a'),(False,'b')):
                b.write_text('module top(input a,b,output y);assign y='+expression+';endmodule\n')
                log=root/('pass.log' if equivalent else 'fail.log');cfg=root/'config.yml'
                cfg.write_text(json.dumps({'format':'verilog','verification':'lec','input_paths':[str(a),str(b)],'solver':'glucose','log_file':str(log)}))
                result=subprocess.run([str(executable),'--config',str(cfg)],capture_output=True,timeout=30)
                self.assertTrue(log.exists(),f'Kepler exit {result.returncode}: '+result.stdout.decode(errors='replace')+result.stderr.decode(errors='replace'))
                if equivalent:
                    resume.validate_lec(log.read_text(),2,1)
                    proof=root/'proof.json';proof.write_text(json.dumps({'status':'passed','command_exit_code':result.returncode,
                        'log_path':str(log),'log_sha256':collection.sha(log),'before_sha256':collection.sha(a),'after_sha256':collection.sha(b),
                        'boundary':{'primary_inputs':2,'primary_outputs':1},'executable':str(executable),
                        'executable_sha256':collection.sha(executable),'libraries':[]}))
                    resume.validate_replayed_pair(proof,a,b)
                    b.write_text('module top(input a,b,output y);assign y=b;endmodule\n')
                    with self.assertRaisesRegex(ValueError,'replayed CTS circuit'):resume.validate_replayed_pair(proof,a,b)
                else:
                    with self.assertRaises(ValueError):resume.validate_lec(log.read_text(),2,1)

    def test_incomplete_solver_log_or_boundary_mismatch_never_passes(self):
        log='SAT solver finished: UNSAT\nCircuits are IDENTICAL\n'
        for d in (0,1):log+=f'size of PIs in circuit {d}: 326\nsize of POs in circuit {d}: 389\nsize of diff{d} inputs: 0\nsize of diff{d} outputs: 0\n'
        resume.validate_lec(log,326,389)
        for bad in (log.replace('UNSAT','UNKNOWN'),log.replace('circuit 1: 389','circuit 1: 388'),log.replace('diff0 inputs: 0','diff0 inputs: 1'),'Starting solver'):
            with self.assertRaises(ValueError):resume.validate_lec(bad,326,389)


if __name__=='__main__':unittest.main()
