"""A-clock reuse and dispatch changes; all fixtures run without EDA."""
import csv
import signal
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.arithmetic_dse.workload_abcd import read,write
from experiments.arithmetic_dse import workload_reference_A as revised

write=revised.write


class ReferenceA(unittest.TestCase):
    def test_known_default_controller_entry_matches_only_its_default_root_and_code_directory(self):
        module='experiments.arithmetic_dse.workload_two_depths_run'
        info=dict(argv=['python3','-u','-m',module,'run'],cwd=str(revised.ROOT.resolve()))
        self.assertTrue(revised.matches(info,module,'run',revised.old.DEFAULT))
        self.assertFalse(revised.matches(info,module,'run',Path('/tmp/another-experiment')))
        self.assertFalse(revised.matches(dict(info,cwd='/tmp'),module,'run',revised.old.DEFAULT))
        explicit=dict(info,argv=info['argv']+['--root','/tmp/another-experiment'])
        self.assertTrue(revised.matches(explicit,module,'run',Path('/tmp/another-experiment')))

    def test_failed_handoff_validation_restores_old_dispatch_before_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);parent=dict(pid=42,start='100',argv=['old-controller'])
            with patch.object(revised,'signal_exact') as send,\
                 patch.object(revised,'process_info',return_value=dict(parent,state='T')),\
                 patch.object(revised.time,'sleep'):
                with self.assertRaisesRegex(ValueError,'ambiguous worker'):
                    with revised.paused_parents([parent],folder):
                        raise ValueError('ambiguous worker')
            self.assertEqual([c.args[1] for c in send.call_args_list],[signal.SIGSTOP,signal.SIGCONT])
            receipt=read(folder/'handoff-failure.json')
            self.assertFalse(receipt['committed']);self.assertEqual(receipt['resumed_predecessor_pids'],[42])

    def test_A_finishing_during_inspection_is_not_treated_as_missing_active_worker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);ledger=root/'ledger.json';batch=root/'backend/matrix-case'
            job=dict(id='job',status='active',admission_id='matrix-case',task_id='A-task')
            write(ledger,dict(jobs=[job],entries=[]))
            def finished(*args):
                write(ledger,dict(jobs=[dict(job,status='released')],entries=[]))
                return []
            with patch.object(revised.runtime.budget,'LEDGER',ledger),\
                 patch.object(revised,'aliases',return_value={str(batch/'runs/A-task'):{'A'}}),\
                 patch.object(revised.runtime,'verify',return_value=dict(tasks=[dict(id='A-task')])),\
                 patch.object(revised.monitor,'wrappers',side_effect=finished):
                _,planned=revised.active_A_cancellations(root)
            self.assertEqual(planned,[])

    def test_original_request_is_used_for_readout_and_failed_A_has_no_invented_Tmin(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);parent=root/'predecessor';tasks=[]
            for index,cid in enumerate(revised.matrix.DEPTHS):
                if cid=='mac32':continue
                request=1100+index*100;tid=cid+'-A-reference'
                tasks.append(dict(id=tid,case=cid,period_ps=request,rtl_sha256=cid+'-hash'))
                run=parent/'A-reference/runs'/tid
                write(run/'manifest.json',dict(status='failed' if cid=='montgomery256' else 'completed',threads_per_tool=4))
                if cid!='montgomery256':self.readout(run,request,request*.9)
            write(parent/'A-reference/admission.json',dict(tasks=tasks))
            write(parent/'final-mac32-methods.json',dict(records=[
                dict(target=dict(T_ps=500),methods=dict(A=dict(task_id='mac500',rtl_sha256='mac-hash'))),
                dict(target=dict(T_ps=1000),methods=dict(A=dict(task_id='mac1000',rtl_sha256='mac-hash')))]))
            mac=parent/'final-mac32/runs/mac1000'
            write(mac/'manifest.json',dict(status='completed',threads_per_tool=4));self.readout(mac,1000,1444.7)
            with patch.object(revised.old,'PARENT',parent):refs=revised.references(root)
            mac=next(r for r in refs if r['case']=='mac32')
            self.assertEqual((mac['reference_request_ps'],mac['Tmin_ps']),(1000,1444.7))
            self.assertFalse(mac['setup_met_at_own_request'])
            failed=next(r for r in refs if r['case']=='montgomery256')
            self.assertEqual(failed['status'],'failed');self.assertNotIn('Tmin_ps',failed)
            for row in refs:
                self.assertFalse(row['BCD_target_applied_to_A'])
                self.assertIsNone(row['comparison_setup_met'])

    def readout(self,run,request,Tmin):
        write(run/'clock-readout/result.json',dict(target_ps=request,full_setup_minimum_period_ps=Tmin,
            area_um2=2000,hold_WNS_ps=-.2,classes={'threshold_check_-0.1':dict(slack_ps=-.1),
                'threshold_check_0.1':dict(slack_ps=.1)}))

    def test_shared_physical_task_is_never_cancelled_just_because_it_has_A_alias(self):
        batch=Path('/tmp/fixture-batch');task=dict(id='task')
        key=str((batch/'runs/task').resolve())
        self.assertEqual(revised.classification(batch,task,{key:{'A'}}),'excluded_repeated_A')
        for names in ({'A','B'},{'C','D'},{'same_policy_static'}):
            self.assertEqual(revised.classification(batch,task,{key:names}),'pipeline_or_ablation')
        with self.assertRaisesRegex(ValueError,'ownership'):
            revised.classification(batch,task,{})

    def test_future_variant_never_admits_A_and_still_deduplicates_C_D(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);sel=root/'selection.json';methods={}
            for name,h in [('A','a'*64),('B','b'*64),('C','c'*64),('D','c'*64)]:
                folder=root/name;folder.mkdir();rtl=folder/'workload.sv';rtl.write_text('module Workload;endmodule\n')
                methods[name]=dict(L=1 if name=='A' else 2,grammar=[0,0],rtl_sha256=h,rtl=str(rtl),
                    prediction={},simulation_status='passed',simulation_receipt=str(folder/'receipt.json'))
            write(sel,dict(records=[dict(target=dict(T_ps=T),methods=methods) for T in (950,1100)]))
            with patch.object(revised.matrix,'ready_selection',return_value=sel),\
                 patch.object(revised.old,'collect',return_value=[]),\
                 patch.object(revised.old,'settled_old_measurement',return_value=None),\
                 patch.object(revised.old,'old_memory_failure',return_value=None),\
                 patch.object(revised.runtime,'admit') as admit:
                result=revised.register_variant(root,'mac32',2)
            tasks=admit.call_args.args[1]
            self.assertEqual(len(tasks),4)
            self.assertEqual({t['period_ps'] for t in tasks},{950,1100})
            self.assertTrue(all('/A/' not in t['rtl'] for t in tasks))
            self.assertEqual(result['A_per_target_physical_tasks'],0)
            for group in result['records']:
                self.assertNotIn('A',group['methods'])
                self.assertEqual(group['methods']['C']['measurement'],group['methods']['D']['measurement'])

    def test_published_ABCD_table_uses_own_A_clock_not_legacy_tight_A_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);evidence=root/'evidence';rows=[]
            for cid,depths in revised.matrix.DEPTHS.items():
                for L in depths:
                    targets=[500,750,1000] if (cid,L)==('mac32',3) else [350,400]
                    rows.append(dict(case=cid,L=L,targets_ps=targets))
            write(root/'target-matrix.json',dict(rows=rows));write(root/'ledger.json',dict(jobs=[]))
            refs=[dict(case=cid,method='A',L=1,reference_request_ps=1100,status='measured_grt',
                Tmin_ps=1059.684803,area_um2=2133.38934,frequency_MHz=943.6,hold_WNS_ps=.2,
                setup_met_at_own_request=True,measured_threads=4,run='/original-A',origin='initial')
                for cid in revised.matrix.DEPTHS]
            legacy=dict(case='add512',comparison_L=4,T_ps=350,method='A',Tmin_ps=841.8,status='measured_grt')
            with patch.object(revised,'references',return_value=refs),\
                 patch.object(revised.old,'collect',return_value=[legacy]),\
                 patch.object(revised.runtime.budget,'LEDGER',root/'ledger.json'),\
                 patch.object(revised,'EVIDENCE',evidence):
                doc=revised.publish(root)
            self.assertEqual(doc['BCD_measured'],0);self.assertEqual(doc['A_reference_measured'],9)
            self.assertEqual(len(doc['comparison_groups']),37)
            with (evidence/'comparison.csv').open() as f:
                table=list(csv.DictReader(f))
            self.assertEqual(len(table),148)
            a_rows=[r for r in table if r['method']=='A']
            self.assertEqual(len(a_rows),37)
            self.assertTrue(all(float(r['measurement_request_ps'])==1100 for r in a_rows))
            self.assertTrue(all(float(r['Tmin_ps'])==1059.684803 for r in a_rows))
            self.assertEqual(doc['legacy_per_target_A_records'],[legacy])
            self.assertFalse(doc['physical_comparison_complete'])


if __name__=='__main__':unittest.main()
