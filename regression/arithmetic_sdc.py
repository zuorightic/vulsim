#!/usr/bin/env python3
"""Execute the actual SDC Tcl generator and check serialized stage semantics."""
import gzip
import json
from pathlib import Path
import os
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.platforms import profile
from experiments.arithmetic_dse.sdc import verify_sdc,rtl_ports


class SdcContracts(unittest.TestCase):
    def actual(self):
        run=ROOT/'experiments/arithmetic/evidence/step3_platforms_v2/runs/nangate45-mul-sdcfix'
        return (gzip.decompress((run/'1_synth.sdc.gz').read_bytes()).decode(),
                profile('nangate45'),rtl_ports((run/'input.sv').read_text()))

    def generate(self,platform,*,period=3001,io_delay=23,load=5):
        p=profile(platform)
        env=os.environ.copy();env.update({
            'VULSIM_TIME_TO_PS':str(1 if platform=='asap7' else 1000),
            'VULSIM_CAP_TO_FF':str(1000 if platform in ('sky130hd','gf180') else 1),
            'VULSIM_CLOCK_PERIOD_PS':str(period),
            'VULSIM_SETUP_UNCERTAINTY_PS':str(p['setup_uncertainty_ps']),
            'VULSIM_HOLD_UNCERTAINTY_PS':str(p['hold_uncertainty_ps']),
            'VULSIM_CLOCK_TRANSITION_PS':str(p['clock_transition_ps']),
            'VULSIM_DRIVER_CELL':p['driver_cell'],'VULSIM_DRIVER_PIN':p['driver_pin'],
            'VULSIM_OUTPUT_LOAD_FF':str(load),'SDC_SOURCE':str(ROOT/'experiments/arithmetic_dse/backend/constraints.sdc')})
        if io_delay is not None:env['VULSIM_IO_DELAY_MAX_PS']=str(io_delay)
        else:env.pop('VULSIM_IO_DELAY_MAX_PS',None)
        script='''
proc get_ports {args} {return port}
proc get_clocks {args} {return core_clk}
proc all_clocks {} {return {core_clk io_clk}}
proc all_inputs {args} {return input_ports}
proc all_outputs {} {return output_ports}
proc capture {command args} {puts [join [linsert $args 0 $command] "\\t"]}
foreach command {create_clock set_clock_uncertainty set_clock_transition set_input_delay set_output_delay set_driving_cell set_load} {
    interp alias {} $command {} capture $command
}
source $::env(SDC_SOURCE)
'''
        result=subprocess.run(['tclsh'],input=script,env=env,text=True,capture_output=True,check=True)
        if result.stderr:raise AssertionError(result.stderr)
        return [line.split('\t') for line in result.stdout.splitlines()]

    def test_actual_tcl_source_uses_fractional_time_and_capacitance_for_integer_env(self):
        for platform in ('asap7','nangate45','sky130hd','gf180'):
            with self.subTest(platform=platform):
                rows=self.generate(platform);p=profile(platform);time=1 if platform=='asap7' else 1000
                cap=1000 if platform in ('sky130hd','gf180') else 1
                clocks=[r for r in rows if r[0]=='create_clock']
                self.assertEqual([float(r[4]) for r in clocks],[3001/time]*2)
                for kind in ('setup','hold'):
                    row=next(r for r in rows if r[0]=='set_clock_uncertainty' and r[1]=='-'+kind)
                    self.assertEqual(float(row[2]),p[kind+'_uncertainty_ps']/time)
                self.assertEqual(float(next(r for r in rows if r[0]=='set_clock_transition')[1]),p['clock_transition_ps']/time)
                self.assertEqual(float(next(r for r in rows if r[0]=='set_load')[1]),5/cap)
                for cmd in ('set_input_delay','set_output_delay'):
                    self.assertEqual(float(next(r for r in rows if r[0]==cmd and r[1]=='-max')[2]),23/time)

    def test_actual_tcl_fractional_default_io_delay(self):
        rows=self.generate('sky130hd',io_delay=None)
        for cmd in ('set_input_delay','set_output_delay'):
            self.assertAlmostEqual(float(next(r for r in rows if r[0]==cmd and r[1]=='-max')[2]),0.6002)

    def test_old_archived_ns_stage_constraints_are_rejected_and_asap7_is_unaffected(self):
        directory=ROOT/'experiments/arithmetic/evidence/step3_platforms_v1/runs'
        for task in ('asap7-mul-finalinterface','nangate45-mul','sky130hd-mul-rcalias','gf180-mul-tcvia'):
            run=directory/task;manifest=json.loads((run/'manifest.json').read_text());ports=rtl_ports((run/'input.sv').read_text())
            for name in ('1_synth.sdc.gz','5_1_grt.sdc.gz','6_final.sdc.gz'):
                with self.subTest(task=task,stage=name):
                    text=gzip.decompress((run/name).read_bytes()).decode()
                    if task.startswith('asap7'):
                        self.assertEqual(verify_sdc(text,manifest['platform_profile'],manifest['period_ps'],ports)['status'],'passed')
                    else:
                        with self.assertRaisesRegex(ValueError,'SDC transition mismatch'):
                            verify_sdc(text,manifest['platform_profile'],manifest['period_ps'],ports)

    def test_sdc_checks_detect_uncertainty_transition_load_period_io_and_missing_port(self):
        run=ROOT/'experiments/arithmetic/evidence/step3_platforms_v1/runs/asap7-mul-finalinterface'
        text=gzip.decompress((run/'1_synth.sdc.gz').read_bytes()).decode()
        p=profile('asap7');ports=rtl_ports((run/'input.sv').read_text())
        replacements=[('set_clock_transition 10.0000','set_clock_transition 0.0000'),
                      ('-setup 20.0000 core_clk','-setup 0.0000 core_clk'),
                      ('-hold 5.0000 io_clk','-hold 0.0000 io_clk'),
                      ('-period 1500.0000','-period 1.5000'),
                      ('-pin_load 3.8980','-pin_load 0.0000'),
                      ('set_input_delay 300.0000','set_input_delay 0.0000'),
                      ('set_output_delay 300.0000','set_output_delay 0.0000')]
        for old,new in replacements:
            self.assertIn(old,text)
            with self.subTest(replaced=old),self.assertRaises(ValueError):verify_sdc(text.replace(old,new),p,1500,ports)
        lines=[l for l in text.splitlines() if not (l.startswith('set_input_delay') and '{rstn}' in l)]
        with self.assertRaisesRegex(ValueError,'coverage'):verify_sdc('\n'.join(lines),p,1500,ports)
        with self.assertRaises(ValueError):verify_sdc(text+'\nset_false_path -from [all_inputs]\n',p,1500,ports)

    def test_all_accepted_archived_sdc_stages_pass_strict_dialect(self):
        directory=ROOT/'experiments/arithmetic/evidence/step3_platforms_v2'
        count=0
        for item in json.loads((directory/'summary.json').read_text())['runs']:
            run=ROOT/item['artifact_directory'] if item.get('artifact_directory') else directory/'runs'/item['task_id']
            m=json.loads((run/'manifest.json').read_text())
            for stage in ('1_synth','5_1_grt','6_final')[:len(m['metrics'])]:
                with self.subTest(task=item['task_id'],stage=stage):
                    result=verify_sdc(gzip.decompress((run/(stage+'.sdc.gz')).read_bytes()).decode(),
                                      m['platform_profile'],m['period_ps'],rtl_ports((run/'input.sv').read_text()))
                    self.assertEqual(result['status'],'passed');count+=1
        self.assertEqual(count,18)

    def test_current_design_has_one_literal_matching_argument_and_one_declaration(self):
        text,p,ports=self.actual();normal='current_design MulProbe_sim_top'
        for declaration in ('current_design','current_design MulProbe_sim_top extra',
                'current_design WrongTop','current_design {}','current_design {MulProbe_sim_top extra}',
                'current_design [get_designs MulProbe_sim_top]','current_design $top',
                'current_design "[set top MulProbe_sim_top]"','current_design {MulProbe_sim_top}[exec true]'):
            with self.subTest(declaration=declaration),self.assertRaises(ValueError):
                verify_sdc(text.replace(normal,declaration),p,3000,ports)
        with self.assertRaises(ValueError):verify_sdc(text+'\n'+normal,p,3000,ports)
        with self.assertRaises(ValueError):verify_sdc(text.replace(normal,''),p,3000,ports)
        for declaration in ('current_design {MulProbe_sim_top}','current_design "MulProbe_sim_top"'):
            self.assertEqual(verify_sdc(text.replace(normal,declaration),p,3000,ports)['status'],'passed')

    def test_command_boundaries_substitutions_and_concatenation_are_rejected(self):
        text,p,ports=self.actual()
        bad_lines=[
            'current_design MulProbe_sim_top; set_false_path -from [get_ports {rstn}]',
            'current_design MulProbe_sim_top ;set_false_path -from [get_ports {rstn}]',
            'set_propagated_clock [get_clocks {core_clk}]; set_false_path -from [get_ports {rstn}]',
            'set_propagated_clock [get_clocks {core_clk}; set_false_path -from [get_ports {rstn}]]',
            'set_propagated_clock [get_clocks "[set clock core_clk]"]',
            'set_propagated_clock [get_clocks {core_clk}][exec true]',
            'set_propagated_clock [get_clocks {core_clk}]junk',
            'set_propagated_clock [get_clocks $clock]',
            'set_propagated_clock [get_clocks {core_clk};]',
            'current_design {MulProbe_sim_top; set_false_path}',
            'current_design MulProbe_sim_top\\\n; set_false_path -from [get_ports {rstn}]',
            '# comment\\\nset_false_path -from [get_ports {rstn}]',
            'current_design MulProbe_sim_top\vset_false_path -from [get_ports {rstn}]',
            'current_design MulProbe_sim_top # trailing-comment dialect is unsupported',
        ]
        for line in bad_lines:
            with self.subTest(line=line),self.assertRaises(ValueError):verify_sdc(text+'\n'+line,p,3000,ports)
        # A continued comment could hide a real constraint from Tcl. Reject
        # rather than treating the following physical line as executable.
        modified=text.replace('set_clock_transition','# hidden by Tcl\\\nset_clock_transition')
        with self.assertRaises(ValueError):verify_sdc(modified,p,3000,ports)
        self.assertEqual(verify_sdc(text+'\n# inert comment; not executed\n',p,3000,ports)['status'],'passed')


if __name__=='__main__':unittest.main()
