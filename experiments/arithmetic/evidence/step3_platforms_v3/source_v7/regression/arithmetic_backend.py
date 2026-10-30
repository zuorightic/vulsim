#!/usr/bin/env python3
"""Check report rejection, feasibility, area accounting and timeout handling.

These checks use synthetic reports and a local child process, without PPA tools.
"""
import os
import json
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.arithmetic_dse.backend import run_command, stage_metrics, render_abc_script, verify_orfs_area
from experiments.arithmetic_dse.characterization import target_coverage
from experiments.arithmetic_dse.characterization import sensitivity_observation, mapped_netlist_hash
from experiments.arithmetic_dse.budget import Ledger, BudgetExceeded, stage_plan, usage_by
from experiments.arithmetic_dse.budget import POLICY
from experiments.arithmetic_dse.physical_control import admission
from experiments.arithmetic_dse.timing_evidence import critical_path
from experiments.arithmetic_dse.platforms import profile,report_scales,library_data,resolve_environment,validate_environment
from experiments.arithmetic_dse.platforms import parameter_provenance
from concurrent.futures import ThreadPoolExecutor


class BackendContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='arithmetic-backend-test-')
        self.directory = Path(self.temp.name)
        self.cells = {'DFF':{'area_um2':2.0,'sequential':True},
                      'AND':{'area_um2':1.0,'sequential':False}}
        self.reports = {'units':' time 1ps\n capacitance 1fF\n distance 1um\n',
                        'setup':'worst slack max 10.000000\n',
                        'hold':'worst slack min 0.500000\n',
                        'setup_tns':'tns max 0.000000\n', 'hold_tns':'tns min 0.000000\n',
                        'period':'core_clk period_min = 1490.00 fmax = 671.14\n',
                        'coverage':'', 'cells':'DFF\t2\t2.0\t0\tCORE\nAND\t3\t1.0\t0\tCORE\n'
                            'TAPCELL_TEST\t1\t0.5\t0\tCORE_WELLTAP\n'
                            'FILLER_TEST\t4\t0.5\t1\tCORE_SPACER\n'}
        self.write_reports()

    def tearDown(self):
        self.temp.cleanup()

    def write_reports(self):
        for key, value in self.reports.items():
            (self.directory/f'vulsim_grt_{key}.{ "tsv" if key == "cells" else "rpt"}').write_text(value)

    def metrics(self):
        return stage_metrics(self.directory, 'grt', self.cells, 1500)

    def test_area_and_feasibility(self):
        result = self.metrics()
        self.assertEqual(result['cell_area_um2'], 7.5)  # includes tap, excludes fillers
        self.assertEqual(result['functional_cell_area_um2'], 7)
        self.assertEqual(result['sequential_area_um2'], 4)
        self.assertEqual(result['excluded_filler_area_um2'], 2)
        self.assertTrue(result['measured_feasibility'])

    def test_orfs_area_rounding_matches_six_significant_digit_serializer(self):
        for area in (572.46912,1622.866,123456.78,0.001234567):
            native=float(format(area,'.6g'))
            verify_orfs_area(area,native)
            with self.assertRaises(ValueError):verify_orfs_area(area*1.0001,native)

    def test_declared_endcap_area_is_physical_and_fillers_remain_excluded(self):
        self.reports['cells']+='gf180mcu_fd_sc_mcu9t5v0__endcap\t3\t1.25\t0\tENDCAP_PRE\n'
        self.write_reports()
        m=self.metrics()
        self.assertEqual(m['cell_area_um2'],11.25)
        self.assertEqual(m['functional_cell_area_um2'],7)
        self.assertEqual(m['physical_only_area_um2'],4.25)
        self.assertEqual(m['excluded_filler_area_um2'],2)
        self.reports['cells']+='macro\t1\t100\t0\tBLOCK\n';self.write_reports()
        with self.assertRaises(ValueError):self.metrics()

    def test_ns_pf_reports_are_converted_without_changing_area(self):
        self.reports['units']='time 1ns\ncapacitance 1pF\ndistance 1um\n'
        self.reports['setup']='worst slack max 0.010000\n'
        self.reports['hold']='worst slack min -0.002000\n'
        self.reports['period']='core_clk period_min = 1.490000\n'
        self.write_reports()
        result=stage_metrics(self.directory,'grt',self.cells,1500,selected=profile('sky130hd'))
        self.assertEqual(result['setup_worst_slack_ps'],10)
        self.assertEqual(result['hold_worst_slack_ps'],-2)
        self.assertEqual(result['minimum_clock_period_ps'],1490)
        self.assertEqual(result['cell_area_um2'],7.5)
        self.assertTrue(result['measured_feasibility'])
        self.assertEqual(result['raw_timing_values']['hold_worst_slack_ps'],-0.002)

    def test_profile_mismatched_report_units_are_rejected(self):
        for platform in ('nangate45','sky130hd','gf180'):
            with self.assertRaises(ValueError):
                report_scales('time 1ps\ncapacitance 1fF\n',profile(platform))
        with self.assertRaises(ValueError):profile('unknown')

    def test_parameter_provenance_preserves_effective_identity_and_detects_mismatch(self):
        from copy import deepcopy
        from experiments.arithmetic_dse.platforms import PARAMETER_SOURCES
        data=json.loads(PARAMETER_SOURCES.read_text())
        for platform in ('asap7','nangate45','sky130hd','gf180'):
            self.assertEqual(parameter_provenance(platform)['profile_sha256'],profile(platform)['profile_sha256'])
            for field in ('profile_sha256','value','unit','basis'):
                altered=deepcopy(data);item=altered['profiles'][platform]
                if field=='profile_sha256':item[field]='0'*64
                else:item['parameters']['setup_uncertainty_ps'][field]={'value':0,'unit':'ns','basis':[]}[field]
                with self.subTest(platform=platform,field=field),self.assertRaises(ValueError):
                    parameter_provenance(platform,document=altered)

    def test_selected_library_checks_name_pvt_and_units_before_physical_launch(self):
        p=profile('nangate45')
        path=self.directory/'NangateOpenCellLibrary_typical.lib'
        text='''library(test) { time_unit : "1ns"; capacitive_load_unit(1,ff);
nom_voltage : 1.1; nom_temperature : 25;
/* cell (example) { area: 999; } */
cell (BUF_X1) { area: 1.0; } }'''
        path.write_text(text)
        libs,cells=library_data([path],p)
        self.assertEqual(libs[0]['time_to_ps'],1000)
        self.assertEqual(list(cells),['BUF_X1'])
        for old,new in [('1.1','1.2'),('25','125'),('1ns','1ps'),('(1,ff)','(1,pf)')]:
            path.write_text(text.replace(old,new))
            with self.assertRaises(ValueError):library_data([path],p)
        path.write_text(text)
        renamed=path.with_name('wrong.lib');renamed.write_text(text)
        with self.assertRaises(ValueError):library_data([renamed],p)

    def environment_fixture(self):
        selected=profile('nangate45')
        d=self.directory/'nangate45';d.mkdir()
        effective={'PLATFORM':'nangate45','PLATFORM_DIR':str(d),'CORNER':'TC',
                   'ABC_DRIVER_CELL':'BUF_X1','ABC_LOAD_IN_FF':'3.898'}
        for key in ('TECH_LEF','SC_LEF','RCX_RULES','PDN_TCL'):
            path=d/key;path.touch();effective[key]=str(path)
        for name in ('setRC.tcl','make_tracks.tcl'):(d/name).touch()
        return effective,selected

    def test_rc_and_tracks_defaults_follow_actual_flow_without_mutating_raw_env(self):
        raw,p=self.environment_fixture()
        effective,origins=resolve_environment(raw)
        validate_environment(effective,p)
        self.assertNotIn('LAYER_PARASITICS_FILE',raw)
        self.assertEqual(Path(effective['LAYER_PARASITICS_FILE']).name,'setRC.tcl')
        self.assertIn('fallback',origins['MAKE_TRACKS'])
        Path(effective['MAKE_TRACKS']).unlink()
        resolved,origins=resolve_environment(raw)
        self.assertEqual(resolved['MAKE_TRACKS'],'')
        self.assertIn('make_tracks command',origins['MAKE_TRACKS'])

    def test_wrong_platform_assets_and_abc_load_are_rejected(self):
        raw,p=self.environment_fixture();effective,_=resolve_environment(raw)
        for key,value in [('CORNER','BC'),('ABC_LOAD_IN_FF','0.003898'),
                          ('ABC_DRIVER_CELL','OTHER'),('RCX_RULES',str(self.directory/'outside'))]:
            if key=='RCX_RULES':Path(value).touch()
            with self.assertRaises(ValueError):validate_environment(dict(effective,**{key:value}),p)
        Path(effective['LAYER_PARASITICS_FILE']).unlink()
        with self.assertRaises(ValueError):validate_environment(effective,p)

    def test_shared_rc_asset_requires_exact_alias_and_content_identity(self):
        import hashlib
        raw,p=self.environment_fixture();effective,_=resolve_environment(raw)
        shared=self.directory/'shared';shared.mkdir()
        rules=shared/'rules';rules.write_text('same interconnect stack')
        alias=Path(raw['PLATFORM_DIR'])/'rcx_alias';alias.symlink_to(rules)
        effective['RCX_RULES']=str(alias)
        with self.assertRaises(ValueError):validate_environment(effective,p)

        p=dict(p,shared_platform_assets={'RCX_RULES':{'logical_relative':'rcx_alias',
               'resolved_relative':'../shared/rules','sha256':hashlib.sha256(rules.read_bytes()).hexdigest()}})
        validate_environment(effective,p)
        rules.write_text('different extraction corner')
        with self.assertRaises(ValueError):validate_environment(effective,p)

    def test_via_adapter_rejects_wrong_resistance_units_and_selected_lef_basis(self):
        raw,p=self.environment_fixture();effective,_=resolve_environment(raw)
        adapter={'via_resistance_ohm':4.5,'via_layers':['Via1']}
        p=dict(p,rc_adapter=adapter)
        # Reject before any adapter file can be accepted: the selected LEF
        # does not establish the declared typical single-cut resistance.
        with self.assertRaisesRegex(ValueError,'technology LEF'):validate_environment(effective,p)
        Path(effective['TECH_LEF']).write_text('VIA Via1_HH DEFAULT\n RESISTANCE 4.500 ;')
        effective['VULSIM_TC_VIA_RESISTANCE_OHM']='4500'
        with self.assertRaisesRegex(ValueError,'resistance override'):validate_environment(effective,p)
        with self.assertRaisesRegex(ValueError,'resistance units'):
            report_scales('time 1ns\ncapacitance 1fF\nresistance 1kohm\n',p)

    def test_grt_hold_is_reported_without_changing_setup_feasibility(self):
        self.reports['hold'] = 'worst slack min -0.000001\n'
        self.write_reports()
        result = self.metrics()
        self.assertTrue(result['measured_feasibility'])
        self.assertFalse(result['sta_feasibility'])
        self.assertTrue(result['hold_review_required'])
        self.assertEqual(result['feasibility_scope'], 'TT_setup_only')

    def test_final_hold_remains_a_gate(self):
        self.reports['hold'] = 'worst slack min -0.000001\n'
        self.write_reports()
        for path in self.directory.glob('vulsim_grt_*'):
            (self.directory/path.name.replace('grt','final')).write_bytes(path.read_bytes())
        self.assertFalse(stage_metrics(self.directory, 'final', self.cells, 1500)['measured_feasibility'])

    def test_hold_review_band_is_not_signoff(self):
        result = self.metrics()
        self.assertTrue(result['hold_review_required'])
        self.assertFalse(result['multi_corner_signoff'])
        self.reports['hold'] = 'worst slack min 5.000000\n'
        self.write_reports()
        self.assertFalse(self.metrics()['hold_review_required'])

    def test_target_axis_rejects_unmeasured_and_outside_points(self):
        self.assertEqual(target_coverage([1000,1500,2000], 1500)['status'],'covered')
        for target in [900,1250,2100]:
            self.assertEqual(target_coverage([1000,1500,2000],target)['status'],'uncovered')
        with self.assertRaises(ValueError):
            target_coverage([1000],float('nan'))

    def test_identical_scalar_metrics_do_not_prove_insensitivity_or_gap_coverage(self):
        point = {'abc_target_ps':500, 'comparison_identity_sha256':'kernel-1',
                 'mapped_netlist_sha256':'netlist-1', 'cell_area_um2':7,
                 'functional_cell_area_um2':6, 'sequential_area_um2':2,
                 'minimum_clock_period_ps':900}
        result = sensitivity_observation([point, dict(point,abc_target_ps=800)])
        self.assertEqual(result['status'],'equal_at_measured_points')
        self.assertFalse(result['early_exit_authorized'])
        self.assertFalse(result['family_target_insensitive'])
        self.assertEqual(target_coverage(result['measured_targets_ps'],1000)['status'],'uncovered')
        different = sensitivity_observation([point,dict(point,abc_target_ps=800,mapped_netlist_sha256='netlist-2')])
        self.assertEqual(different['status'],'differences_observed')

    def test_netlist_hash_ignores_locations_but_preserves_wiring(self):
        a = '/* Generated by Yosys version A */\n(* src = "first.sv:1" *)\nassign y = a;\n'
        b = '/* Generated by Yosys version B */\n(* src = "second.sv:2" *)\nassign y = a;\n'
        self.assertEqual(mapped_netlist_hash(a),mapped_netlist_hash(b))
        self.assertNotEqual(mapped_netlist_hash(a),mapped_netlist_hash(b.replace('y = a','y = b')))

    def test_custom_ABC_script_passes_numeric_target_to_actual_mapping_commands(self):
        for target in [500,800,1000,1250,1500,2000]:
            lines = render_abc_script(target).splitlines()
            commands = [line for line in lines if line.split()[0] in ['&nf','upsize','dnsize']]
            self.assertTrue(commands)
            for line in commands:
                words = line.split()
                self.assertIn('-D',words)
                self.assertEqual(float(words[words.index('-D')+1]),target)
            self.assertNotIn('@TARGET_PS@','\n'.join(lines))

    def budget_ledger(self):
        policy = self.directory/'policy.json'
        policy.write_text(json.dumps({'resources':{'max_synthesis_calls':2,'max_global_route_calls':1,
            'max_detailed_route_calls':1,'max_global_walltime_h':1,'max_tool_CPU_time_h':1}}))
        checkpoint = self.directory/'checkpoint.json'
        checkpoint.write_text(json.dumps({'entries':[{'id':'history','stage':'synth', 'status':'failed',
            'walltime_s':3,'CPU_time_s':2}]}))
        return Ledger(self.directory/'ledger.json',policy,checkpoint)

    def test_budget_reserves_before_launch_and_failure_stays_charged(self):
        ledger = self.budget_ledger()
        reservation = ledger.reserve('synth',10,2,'prototype',['missing-tool'],self.directory)
        self.assertEqual(ledger.summary()['synth'],2)
        self.assertEqual(ledger.summary()['pending'],1)
        ledger.finish(reservation,{'exit_code':1,'walltime_s':1,'timed_out':False,
                                  'log':str(self.directory/'x.log'),'gnu_time':str(self.directory/'missing')})
        self.assertEqual(ledger.summary()['synth'],2)
        self.assertEqual(ledger.summary()['CPU_time_s'],22)  # unknown CPU keeps reservation
        with self.assertRaises(BudgetExceeded):
            Ledger(ledger.path,ledger.policy,ledger.checkpoint).reserve('synth',1,1,'retry',[],self.directory)

    def test_concurrent_admission_cannot_overspend_and_pending_is_not_refunded(self):
        ledger = self.budget_ledger()
        def reserve(_):
            try:
                return ledger.reserve('synth',10,2,'prototype',[],self.directory)
            except BudgetExceeded:
                return None
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(reserve,range(4)))
        self.assertEqual(sum(r is not None for r in results),1)
        self.assertEqual(ledger.summary()['pending'],1)
        with self.assertRaises(BudgetExceeded):
            Ledger(ledger.path,ledger.policy,ledger.checkpoint).reserve('grt',10,2,'prototype',[],self.directory)

    def test_snapshot_time_does_not_double_count_synthesis_and_policy_cannot_reset_usage(self):
        ledger = self.budget_ledger()
        resource = self.directory/'x.resources.txt'
        resource.write_text('User time (seconds): 0.20\nSystem time (seconds): 0.10\n')
        reservation = ledger.reserve(None,10,2,'prototype',['snapshot'],self.directory)
        ledger.finish(reservation,{'exit_code':0,'walltime_s':1,'timed_out':False,
                                  'log':str(self.directory/'x.log'),'gnu_time':str(resource)})
        self.assertEqual(ledger.summary()['synth'],1)
        self.assertEqual(ledger.summary()['walltime_s'],4)
        self.assertAlmostEqual(ledger.summary()['CPU_time_s'],2.3)
        ledger.policy.write_text('{}')
        with self.assertRaises(ValueError):
            ledger.summary()

    def test_explicit_policy_migration_keeps_all_history_and_rejects_replay(self):
        old = self.budget_ledger()
        before = old.summary()
        checkpoint = self.directory/'new-checkpoint.json'
        checkpoint.write_bytes(old.path.read_bytes())
        policy = self.directory/'new-policy.json'
        contents = json.loads(old.policy.read_text())
        contents['resources']['max_synthesis_calls'] = 3
        policy.write_text(json.dumps(contents))
        new = Ledger(old.path,policy,checkpoint)
        with self.assertRaises(ValueError):
            new.summary()
        audit = new.migrate(old.policy,old.checkpoint,'authorized bounded revision')
        self.assertEqual(new.summary(),before)
        state = json.loads(new.path.read_text())
        self.assertEqual(state['entries'],json.loads(checkpoint.read_text())['entries'])
        self.assertEqual(state['migrations'],[audit])
        with self.assertRaises(ValueError):
            new.migrate(old.policy,old.checkpoint,'cannot replay')

    def test_policy_migration_rejects_pending_or_missing_history(self):
        old = self.budget_ledger()
        old.summary()
        checkpoint = self.directory/'new-checkpoint.json'
        checkpoint.write_text(json.dumps({'entries':[]}))
        new = Ledger(old.path,old.policy,checkpoint)
        with self.assertRaisesRegex(ValueError,'every historical entry'):
            new.migrate(old.policy,old.checkpoint,'test')
        old.reserve('grt',10,1,'prototype',[],self.directory)
        checkpoint.write_bytes(old.path.read_bytes())
        with self.assertRaisesRegex(ValueError,'unsettled'):
            new.migrate(old.policy,old.checkpoint,'test')

    def test_platform_stage_list_counts_cold_chains_and_rejects_duplicate_tasks(self):
        resources=json.loads(POLICY.read_text())['resources']
        historical={'synth':33,'grt':11,'final':5,'walltime_s':2500,'CPU_time_s':3700,'pending':0}
        tasks=[{'id':'one','platform':'sky130hd','stage':'grt','period_ps':30000,'abc_target_ps':20000},
               {'id':'two','platform':'gf180','stage':'final','period_ps':30000,'abc_target_ps':30000}]
        plan=stage_plan(tasks,historical,resources,support_walltime_s=600)
        self.assertEqual(plan['new_calls'],{'synth':2,'grt':2,'final':1})
        self.assertEqual(plan['new_calls_by_platform']['gf180'],{'synth':1,'grt':1,'final':1})
        self.assertEqual(plan['status'],'ready')
        self.assertFalse(plan['main_matrix_authorized'])
        for invalid in ([tasks[0],tasks[0]],[dict(tasks[0],abc_target_ps=0)]):
            with self.assertRaises(ValueError):stage_plan(invalid,historical,resources)
        self.assertEqual(stage_plan(tasks,dict(historical,pending=1),resources)['status'],'blocked')
        self.assertEqual(stage_plan(tasks,historical,dict(resources,max_synthesis_calls=33))['status'],'blocked')
        self.assertEqual(stage_plan(tasks,historical,dict(resources,max_global_walltime_h=1))['status'],'blocked')

    def test_accounting_context_is_preserved_without_relabeling_history(self):
        ledger=self.budget_ledger()
        context={'target_platform':'gf180','admission_id':'diagnostic-v1','task_id':'adder',
                 'model_version':'not_applicable'}
        r=ledger.reserve('synth',10,2,'prototype',[],self.directory,context=context)
        with self.assertRaises(ValueError):ledger.reserve(None,1,1,'bad',[],self.directory,context={'unknown':'x'})
        state=json.loads(ledger.path.read_text())
        by_platform=usage_by(state['entries'],'target_platform')
        self.assertEqual(by_platform['gf180']['pending'],1)
        self.assertEqual(by_platform['historical_unattributed']['synth'],1)
        self.assertTrue(all(r[k]==v for k,v in context.items()))

    def test_connection_admission_binds_both_targets_and_requires_small_probe(self):
        from types import SimpleNamespace
        from experiments.arithmetic_dse.platform_probe import verify_admission,digest
        ledger=self.budget_ledger();ledger.summary()
        p=profile('sky130hd');rtl=self.directory/'rtl.sv';rtl.write_text('module test; endmodule')
        task={'id':'product','platform':'sky130hd','kernel':'mul_u32','profile_sha256':p['profile_sha256'],
              'rtl_sha256':digest(rtl),'top':'test','period_ps':30000,'abc_target_ps':20000,
              'stage':'final','purpose':'prototype'}
        frozen={'id':'connection','purpose':'platform_connection_only','policy_sha256':digest(POLICY),
                'tasks':[task,dict(task,id='small',kernel='add_u32')],'call_caps':{'synth':3,'grt':3,'final':2}}
        path=self.directory/'admission.json';path.write_text(json.dumps(frozen))
        args=SimpleNamespace(admission=path,admission_id='connection',task_id='product',top='test',
                             period_ps=30000,abc_target_ps=20000,stage='final',budget_purpose='prototype',
                             period_role='resource_trial',io_delay_max_ps=None,out=self.directory/'runs/product')
        with self.assertRaisesRegex(ValueError,'small add'):verify_admission(args,p,rtl,ledger)
        small=self.directory/'runs/small';small.mkdir(parents=True)
        (small/'manifest.json').write_text(json.dumps({'target_platform':'sky130hd','status':'completed',
             'task_id':'small','platform_profile':p,'sdc_contracts':{'grt':{'status':'passed'}},'metrics':[{'stage':'grt','timing_coverage_complete':True}]}))
        self.assertEqual(verify_admission(args,p,rtl,ledger),digest(path))
        frozen['related_admission_ids']=['unrelated'];path.write_text(json.dumps(frozen))
        with self.assertRaisesRegex(ValueError,'lineage'):verify_admission(args,p,rtl,ledger)
        del frozen['related_admission_ids'];path.write_text(json.dumps(frozen))
        from experiments.arithmetic_dse.sdc import VERSION
        frozen['tasks'][0].update(constraints_sha256='bad-source-hash',sdc_contract_version=VERSION)
        path.write_text(json.dumps(frozen))
        with self.assertRaisesRegex(ValueError,'SDC source'):verify_admission(args,p,rtl,ledger)
        del frozen['tasks'][0]['constraints_sha256'];del frozen['tasks'][0]['sdc_contract_version']
        path.write_text(json.dumps(frozen))
        args.abc_target_ps=30000
        with self.assertRaisesRegex(ValueError,'differs'):verify_admission(args,p,rtl,ledger)
        args.abc_target_ps=20000
        r=ledger.reserve(None,10,1,'test',[],self.directory,context={'admission_id':'connection','task_id':'product'})
        with self.assertRaisesRegex(ValueError,'unsettled'):verify_admission(args,p,rtl,ledger)
        ledger.finish(r,{'exit_code':1,'walltime_s':1,'timed_out':False,'log':str(self.directory/'missing.log'),
                         'gnu_time':str(self.directory/'missing.resources.txt')})
        with self.assertRaisesRegex(ValueError,'already attempted'):verify_admission(args,p,rtl,ledger)

    def test_control_admission_requires_both_grt_slots_and_counts_support_time(self):
        resources = json.loads(POLICY.read_text())['resources']
        used = {'synth':29,'grt':7,'final':5,'walltime_s':1386,'CPU_time_s':2219,'pending':0}
        check = admission(used,resources)
        self.assertEqual(check['planned_new_calls'],{'synth':2,'grt':2,'final':0})
        self.assertFalse(check['caps_increased'])
        with self.assertRaises(ValueError):
            admission(dict(used,grt=resources['max_global_route_calls']-1),resources)
        with self.assertRaises(ValueError):
            admission(dict(used,pending=1),resources)

    def test_path_parser_uses_worst_slack_and_excludes_launch_clock_latency(self):
        text = '''Startpoint: in_reg
Endpoint: out_reg
Path Group: core_clk
10.000000 0.000000 90.000000 ^ in_reg/CLK (DFF)
1 0.5 16.0 47.352940 137.352940 ^ in_reg/QN (DFF)
8.0 0.000000 1084.460388 ^ out_reg/D (DFF)
-20.000000 1480.000000 clock uncertainty
-9.885993 1470.114014 library setup time
475.653625 slack (MET)
Startpoint: port_a
Endpoint: port_y
Path Group: io_clk
100.000000 slack (MET)
'''
        first = critical_path(text.split('Startpoint: port_a')[0])
        self.assertEqual(first['Q_to_D_combinational_ps'],947.107448)
        self.assertEqual(first['data_and_setup_sum_ps'],1024.346381)
        self.assertEqual(first['launch_clock_arrival_ps'],90)
        self.assertEqual(critical_path(text)['path_group'],'io_clk')

    def test_common_SDC_reports_have_separate_tag_from_implementation_reports(self):
        for path in self.directory.glob('vulsim_grt_*'):
            (self.directory/path.name.replace('vulsim_grt_','vulsim_common1500_')).write_bytes(path.read_bytes())
        result = stage_metrics(self.directory,'grt',self.cells,1500,'common1500')
        self.assertEqual(result['target_period_ps'],1500)
        self.assertIn('vulsim_common1500',result['raw_reports_prefix'])

    def test_wall_budget_rejects_before_creating_a_reservation(self):
        ledger = self.budget_ledger()
        with self.assertRaises(BudgetExceeded):
            ledger.reserve('grt',3600,2,'prototype',[],self.directory)
        self.assertEqual(ledger.summary()['grt'],0)

    def test_removing_live_ledger_cannot_restore_checkpoint_budget(self):
        ledger = self.budget_ledger()
        self.assertEqual(ledger.summary()['synth'],1)
        ledger.path.unlink()
        with self.assertRaises(ValueError):
            ledger.summary()

    def test_sampled_CPU_allowance_cancels_busy_tool(self):
        result = run_command([sys.executable,'-c','while True: pass'],self.directory,
                             'cpu-limit',5,os.environ.copy(),cpu_limit_s=0.05)
        self.assertTrue(result['CPU_limit_exceeded'])
        self.assertNotEqual(result['exit_code'],0)
        self.assertEqual(result['cleanup']['remaining_live_pids'],[])

    def test_unconstrained_endpoint_is_not_feasible(self):
        self.reports['coverage'] = 'Warning: There is 1 unconstrained endpoint.\n'
        self.write_reports()
        self.assertFalse(self.metrics()['measured_feasibility'])

    def test_nan_or_missing_report_is_rejected(self):
        self.reports['hold'] = 'worst slack min nan\n'
        self.write_reports()
        with self.assertRaises(ValueError):
            self.metrics()
        (self.directory/'vulsim_grt_hold.rpt').unlink()
        with self.assertRaises(FileNotFoundError):
            self.metrics()

    def test_unit_mismatch_is_rejected(self):
        self.reports['units'] = ' time 1ns\n capacitance 1pF\n'
        self.write_reports()
        with self.assertRaises(ValueError):
            self.metrics()

    def test_unknown_master_or_area_mismatch_is_rejected(self):
        self.reports['cells'] = 'UNKNOWN\t1\t1.0\t0\tCORE\n'
        self.write_reports()
        with self.assertRaises(ValueError):
            self.metrics()
        self.reports['cells'] = 'DFF\t1\t2000000\t0\tCORE\n'
        self.write_reports()
        with self.assertRaises(ValueError):
            self.metrics()

    def test_timeout_retains_failure_record(self):
        result = run_command([sys.executable,'-c','import time; time.sleep(5)'],
                             self.directory, 'timeout', 0.1, os.environ.copy())
        self.assertTrue(result['timed_out'])
        self.assertNotEqual(result['exit_code'], 0)
        self.assertTrue((self.directory/'timeout.command.json').exists())
        self.assertTrue(Path(result['log']).exists())

    def test_memory_cap_retains_failure_record(self):
        result = run_command([sys.executable,'-c','import time; data = bytearray(16*1024*1024); time.sleep(5)'],
                             self.directory, 'memory', 3, os.environ.copy(), memory_limit_mib=8)
        self.assertTrue(result['memory_limit_exceeded'])
        self.assertFalse(result['timed_out'])
        self.assertNotEqual(result['exit_code'], 0)

    def nested_command(self, ignore_term=False, allocate_mib=0):
        pidfile = self.directory/'worker.json'
        worker = ("import os,json,time,signal; from pathlib import Path; "
                  +( "signal.signal(signal.SIGTERM,signal.SIG_IGN); " if ignore_term else '')
                  +f"data=bytearray({allocate_mib}*1024*1024); "
                  +f"Path({str(pidfile)!r}).write_text(json.dumps({{'pid':os.getpid(),'pgid':os.getpgrp()}})); time.sleep(20)")
        inner = ("from experiments.arithmetic_dse.backend import run_command; import os,sys; from pathlib import Path; "
                 +f"run_command([sys.executable,'-c',{worker!r}],Path({str(self.directory)!r}),'inner',15,os.environ.copy())")
        env = os.environ.copy()
        env['PYTHONPATH'] = str(ROOT)
        return [sys.executable,'-c',inner], env, pidfile

    def assert_worker_dead(self, pidfile):
        self.assertTrue(pidfile.exists(), 'nested worker must start before cancellation')
        pid = json.loads(pidfile.read_text())['pid']
        try:
            state = Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[0]
        except FileNotFoundError:
            state = 'gone'
        if state not in ['gone','Z']:
            try:
                os.kill(pid,signal.SIGKILL)
            except ProcessLookupError:
                pass
        self.assertIn(state, ['gone','Z'], f'worker {pid} survived cancellation')

    def test_outer_timeout_kills_nested_session_and_term_ignoring_worker(self):
        command, env, pidfile = self.nested_command(ignore_term=True)
        result = run_command(command,self.directory,'nested-timeout',1,env)
        self.assertTrue(result['timed_out'])
        self.assertGreater(result['cleanup']['kill_sent'],0)
        self.assertEqual(result['cleanup']['remaining_live_pids'],[])
        self.assert_worker_dead(pidfile)

    def test_outer_memory_limit_counts_nested_session(self):
        command, env, pidfile = self.nested_command(allocate_mib=32)
        result = run_command(command,self.directory,'nested-memory',5,env,memory_limit_mib=24)
        self.assertTrue(result['memory_limit_exceeded'])
        self.assert_worker_dead(pidfile)

    def test_external_term_cleans_nested_tool(self):
        command, env, pidfile = self.nested_command()
        wrapper = ("from experiments.arithmetic_dse.backend import run_command; import os; from pathlib import Path; "
                   +f"run_command({command!r},Path({str(self.directory)!r}),'cancelled',10,os.environ.copy())")
        process = subprocess.Popen([sys.executable,'-c',wrapper],env=env)
        try:
            deadline = time.monotonic()+3
            while not pidfile.exists() and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertTrue(pidfile.exists())
            process.send_signal(signal.SIGTERM)
            process.wait(timeout=6)
            result = json.loads((self.directory/'cancelled.command.json').read_text())
            self.assertEqual(result['cancelled_signal'],signal.SIGTERM)
            self.assertNotEqual(result['exit_code'],0)
            self.assert_worker_dead(pidfile)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()

    def test_fast_exiting_parent_cannot_leave_detached_worker(self):
        pidfile = self.directory/'detached.json'
        worker = ("import os,json,time; from pathlib import Path; "
                  +f"Path({str(pidfile)!r}).write_text(json.dumps({{'pid':os.getpid()}})); time.sleep(20)")
        parent = ("import subprocess,sys,time\nfrom pathlib import Path\n"
                  +f"subprocess.Popen([sys.executable,'-c',{worker!r}],start_new_session=True)\n"
                  +f"while not Path({str(pidfile)!r}).exists(): time.sleep(0.01)\n")
        command = [sys.executable,'-c',parent]
        result = run_command(command,self.directory,'orphan',5,os.environ.copy())
        self.assertTrue(result['unexpected_live_descendants'])
        self.assertNotEqual(result['exit_code'],0)
        self.assert_worker_dead(pidfile)


if __name__ == '__main__':
    unittest.main()
