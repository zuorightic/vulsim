"""Actual RTL and admission boundaries for M2 primitive collection."""
from argparse import Namespace
import json
import os
from pathlib import Path
import random
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from experiments.arithmetic_dse import model_m2_collection as collection
from experiments.arithmetic_dse.model_m2_samples import source,sample_expression
from experiments.arithmetic_dse.model_samples import label_requests
from experiments.arithmetic_dse.reference import f32_mul


class M2Sampling(unittest.TestCase):
    def test_original_grid_resumption_preserves_75_successes_and_only_relaunches_cancellation(self):
        parent=Path('build/step7-m2-models-20261104/primitives-v4/plan.json').resolve()
        if not parent.exists():self.skipTest('original-grid resumption fixture unavailable')
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/'resumption';collection.prepare(folder,parent.parent/'AtomicFp.sv',parent,resume_original=True)
            p=collection.verify_plan(folder/'plan.json');old=collection.read(parent)
            self.assertEqual(sum(bool(t.get('inherited_run')) for t in p['tasks']),75)
            for t,prior in zip(p['tasks'],old['tasks']):
                for key in ('id','split','period_ps','abc_target_ps','rtl_sha256','sample_contract_sha256','mapping_source_task'):
                    self.assertEqual(t[key],prior[key])
            self.assertEqual(p['timeout_recovery']['priority_task_ids'],['train-F1-divrem-w32-t2'])
            completed=next(t for t in p['tasks'] if t['id']=='train-F1-divrem-w32-t3')
            self.assertIn('primitives-v4/runs/',completed['inherited_run']['directory'])
            self.assertEqual(completed['route_timeout_s'],3600)
            collection.write(folder/'capacity-proof.json',{'status':'passed','plan_sha256':collection.sha(folder/'plan.json')})
            with patch.object(collection,'funding',return_value={}):
                wave=folder/'waves/resume.json';collection.admit(folder,'train',wave,24)
            ids=collection.read(wave)['task_ids'];self.assertEqual(ids[0],'train-F1-divrem-w32-t2')
            self.assertNotIn('train-F1-divrem-w32-t3',ids)
            self.assertEqual(len(ids),24)
            with self.assertRaisesRegex(ValueError,'locked'):collection.admit(folder,'test',folder/'waves/test.json')
            saved=p['timeout_recovery']['failed_attempts'][0]
            self.assertEqual(saved['previous_route_timeout_s'],3600)
            self.assertTrue(saved['cancellation_audit']['sha256'])

    def make_recovery_fixture(self,folder):
        parent=Path('build/step7-m2-models-20261104/primitives-v3/plan.json').resolve()
        if not parent.exists():self.skipTest('preserved M2 timeout fixture unavailable')
        collection.prepare(folder,parent.parent/'AtomicFp.sv',parent,timeout_recovery=True)
        p=collection.verify_plan(folder/'plan.json')
        return p

    def test_timeout_successor_inherits_all_74_measurements_including_three_ancestor_pilots(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/'recovery';p=self.make_recovery_fixture(folder)
            inherited=[t for t in p['tasks'] if t.get('inherited_run')]
            self.assertEqual(len(inherited),74)
            self.assertEqual(sum('primitives-v1/runs/' in t['inherited_run']['directory'] for t in inherited),3)
            for t in inherited:
                self.assertEqual(collection.sha(Path(t['inherited_run']['directory'])/'manifest.json'),t['inherited_run']['manifest_sha256'])
            self.assertEqual({t['id'] for t in p['tasks'] if t.get('route_timeout_s')==3600},set(collection.read(collection.RECOVERY)['extended_task_ids']))
            self.assertFalse(any(t.get('route_timeout_s') for t in p['tasks'] if t['split']=='test'))
            with patch.object(collection,'funding',return_value={}):
                collection.write(folder/'capacity-proof.json',{'status':'passed','plan_sha256':collection.sha(folder/'plan.json')})
                wave=folder/'waves/recovery.json';collection.admit(folder,'train',wave,2)
            self.assertEqual(collection.read(wave)['task_ids'],collection.read(collection.RECOVERY)['failed_task_ids'])

    def test_timeout_exception_rejects_unregistered_resources_and_preserves_test_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/'recovery';p=self.make_recovery_fixture(folder)
            collection.write(folder/'capacity-proof.json',{'status':'passed','plan_sha256':collection.sha(folder/'plan.json')})
            with patch.object(collection,'funding',return_value={}):
                wave=folder/'waves/recovery.json';collection.admit(folder,'train',wave,2)
            a=collection.read(wave);t=next(t for t in p['tasks'] if t['id']==a['task_ids'][0])
            mapping=next(t2 for t2 in p['tasks'] if t2['id']==t['mapping_source_task'])
            args=Namespace(admission=wave,admission_id=a['id'],task_id=t['id'],platform='asap7',top='ModelBundle',stage='grt',
                           period_ps=t['period_ps'],abc_target_ps=1500,threads=4,memory_limit_mib=8192,synth_timeout_s=300,
                           route_timeout_s=3600,budget_purpose='characterization',period_role='resource_trial',io_delay_max_ps=None,
                           rtl=Path(t['rtl']),sample_contract=Path(t['sample_contract']),
                           resume_synth_from=collection.run_directory(folder,mapping),out=folder/'runs'/t['id'])
            self.assertEqual(collection.task(args)[2]['route_timeout_s'],3600)
            for timeout in (1200,3601):
                with self.assertRaises(ValueError):collection.task(Namespace(**{**vars(args),'route_timeout_s':timeout}))
            with self.assertRaisesRegex(ValueError,'locked'):collection.admit(folder,'test',folder/'waves/test.json')
            changed=collection.read(folder/'plan.json');changed['tasks'][0]['route_timeout_s']=3600
            collection.write(folder/'plan.json',changed)
            with self.assertRaisesRegex(ValueError,'resource exception'):collection.verify_plan(folder/'plan.json')

    def test_preregistered_topologies_fit_capacity_and_have_distinct_split_sources(self):
        cfg=collection.read(collection.CONFIG);seen={}
        for split,banks in cfg['split_capture_banks'].items():
            for fan in banks:
                for family,f in cfg['families'].items():
                    for width in f['widths']:
                        text,labels=source(family,width,fan,cfg,'module AtomicFp(input [31:0] a,b,output [36:0] value);assign value=0;endmodule')
                        self.assertLessEqual(sum(sum(l['input_widths']) for l in labels),640)
                        self.assertLessEqual(sum(l['capture_width']*fan for l in labels),2048)
                        import hashlib
                        h=hashlib.sha256(text.encode()).hexdigest();self.assertNotIn(h,seen);seen[h]=split
                        self.assertEqual(len(label_requests({'labels':labels})),len(labels)*(1+fan if fan>1 else 1))
        self.assertEqual(len(seen),56)

    def test_test_acquisition_rejected_before_any_measurement(self):
        with patch.object(collection,'verify_plan',return_value={}),self.assertRaisesRegex(ValueError,'locked'):
            collection.admit(Path('/tmp'),'test',Path('/tmp/not-created'))

    def test_native_semantic_shapes_and_mux_feature_signature(self):
        cfg=collection.read(collection.CONFIG);_,labels=source('control',32,2,cfg,'')
        self.assertTrue(all(x['rhs_width']==0 for x in labels if x['operation'].startswith('mux')))
        _,labels=source('arithmetic',32,1,cfg,'')
        self.assertEqual(next(x for x in labels if x['rtl_operation']=='add_wide')['result_width'],33)
        self.assertEqual(sample_expression('fp32',32)[2:],(37,'fp37'))

    def test_one_bit_top_ports_are_scalar_for_exact_sdc_serialization(self):
        from experiments.arithmetic_dse.sdc import rtl_ports
        cfg=collection.read(collection.CONFIG)
        for width in (1,5,64):
            text,_=source('control',width,3,cfg,'');ports=rtl_ports(text,'ModelBundle')
            self.assertIn('b1',ports['inputs']);self.assertNotIn('b1[0]',ports['inputs'])
            if width==1:self.assertIn('a0',ports['inputs']);self.assertNotIn('a0[0]',ports['inputs'])

    def test_boolean_capture_bank_aliases_replay_actual_mapped_flops(self):
        from experiments.arithmetic_dse.model_samples import verify_capture_banks
        root=Path('build/step7-m2-models-20261104/primitives-v2/runs/train-F3-control-w64-t0')
        if not root.exists():self.skipTest('actual diagnostic fixture unavailable')
        cfg=collection.read(collection.CONFIG);_,labels=source('control',64,3,cfg,'')
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'contract.json';path.write_text(json.dumps({'version':'arithmetic-model-labels-v1','labels':labels}))
            cells=collection.read(root/'liberty_cells.json')['cells']
            banks=verify_capture_banks(root/'reports/asap7/arithmetic_probe/base/vulsim_synth',path,cells)
            self.assertEqual(banks['s004']['capture_bank_counts'],{'s004_bank0':1,'s004_bank1':1,'s004_bank2':1})

    def test_frozen_wave_binds_actual_threads_targets_sources_and_test_lock(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);atom=root/'atom.sv';atom.write_text('module AtomicFp(input [31:0] a,b,output [36:0] value);assign value=0;endmodule')
            folder=root/'collection';collection.prepare(folder,atom)
            with patch.object(collection,'funding',return_value={}):
                wave=folder/'waves/pilots.json';collection.admit(folder,'pilots',wave,4)
            a=collection.read(wave);p=collection.read(folder/'plan.json');t=next(x for x in p['tasks'] if x['id']==a['task_ids'][0])
            args=Namespace(admission=wave,admission_id=a['id'],task_id=t['id'],platform='asap7',top='ModelBundle',stage='grt',
                           period_ps=t['period_ps'],abc_target_ps=1500,threads=4,memory_limit_mib=8192,synth_timeout_s=300,
                           route_timeout_s=1200,budget_purpose='characterization',period_role='resource_trial',io_delay_max_ps=None,
                           rtl=Path(t['rtl']),sample_contract=Path(t['sample_contract']),resume_synth_from=None,out=folder/'runs'/t['id'])
            self.assertEqual(collection.task(args)[2]['id'],t['id'])
            for name,value in [('threads',3),('period_ps',t['period_ps']+25),('abc_target_ps',1000),('io_delay_max_ps',300),('out',folder/'wrong')]:
                with self.subTest(name=name),self.assertRaises(ValueError):collection.task(Namespace(**{**vars(args),name:value}))
            Path(t['sample_contract']).write_text('{}')
            with self.assertRaises(ValueError):collection.task(args)

    def test_actual_generated_rtl_primitive_and_safe_divisor_semantics(self):
        cfg=collection.read(collection.CONFIG);rng=random.Random(20261104);checks=0
        with tempfile.TemporaryDirectory() as temporary:
            d=Path(temporary)
            for family,width in [('arithmetic',8),('arithmetic',32),('arithmetic',64),('control',1),('control',5),('control',32),('divrem',8),('divrem',32)]:
                text,labels=source(family,width,3,cfg,'');ports=['.clk(clk)','.rstn(rstn)','.iv(iv)'];decl=[]
                for i,l in enumerate(labels):
                    decl.append(f'reg [{width-1}:0] a{i}=0;reg [{max(1,l["input_widths"][1])-1}:0] b{i}=0;reg c{i}=0;')
                    ports += [f'.a{i}(a{i})',f'.b{i}(b{i})',f'.c{i}(c{i})']
                    ports += [f'.y{i}_b{k}()' for k in range(3)]
                bench='module Bench;reg clk=0,rstn=0,iv=1;'+''.join(decl)+'ModelBundle dut('+','.join(ports)+');initial begin #5;clk=1;#5;clk=0;rstn=1;'
                mask=(1<<width)-1
                for trial in range(24):
                    a=[0,mask,1,1<<(width-1)][trial] if trial<4 else rng.getrandbits(width)
                    b=[0,1,2,mask][trial] & mask if trial<4 else rng.getrandbits(width);c=trial&1
                    bench+=''.join(f'a{i}={width}\'h{a:x};b{i}={labels[i]["input_widths"][1]}\'h{b&((1<<labels[i]["input_widths"][1])-1):x};c{i}={c};' for i in range(len(labels)))
                    bench+='#5;clk=1;#1;'
                    for i,l in enumerate(labels):
                        op=l['rtl_operation'];safe=b or 1
                        values={'add':a+b,'add_wide':a+b,'addcarry':a+b+c,'mul':a*b,'mul_low':a*b,'or':a|b,
                                'eq_zero':int(a==0),'mux':a if c else b,'mux_zero':a if c else 0,
                                'mux_one':a if c else 1,'mux_ones':a if c else mask,'div':a//safe,'mod':a%safe}
                        expected=values[op]&((1<<l['result_width'])-1)
                        bench+=f'if(dut.s{i:03d}.value!=={l["result_width"]}\'h{expected:x})$fatal(1,"M2 primitive {family}/{width}/{op}/{trial}");';checks+=1
                    bench+='#4;clk=0;'
                bench+='$finish;end endmodule'
                (d/'input.sv').write_text(text);(d/'bench.sv').write_text(bench)
                subprocess.run(['iverilog','-g2012','-s','Bench','-o',str(d/'sim'),str(d/'input.sv'),str(d/'bench.sv')],check=True,capture_output=True)
                subprocess.run(['vvp',str(d/'sim')],check=True,capture_output=True)
        self.assertGreater(checks,800)

    def test_native_complete_binary32_atom_against_independent_integer_reference(self):
        atom=Path(os.environ.get('M2_NATIVE_FP_ATOM','build/step7-m2-models-20261104/atomic-fp/AtomicFp.sv'))
        self.assertTrue(atom.exists());rng=random.Random(20261104)
        edges=[0,0x80000000,1,0x007fffff,0x00800000,0x3f800000,0x3f800001,0x7f7fffff,0x7f800000,0xff800000,0x7fc12345,0x7f812345]
        cases=[(a,b) for a in edges for b in edges]+[(rng.getrandbits(32),rng.getrandbits(32)) for _ in range(256)]
        bench='module Bench;reg [31:0] a,b;wire [36:0] value;AtomicFp dut(.a(a),.b(b),.value(value));initial begin\n'
        for i,(a,b) in enumerate(cases):
            ref=f32_mul(a,b);packed=(ref.flags<<32)|ref.bits
            bench+=f'a=32\'h{a:x};b=32\'h{b:x};#1;if(value!==37\'h{packed:x})$fatal(1,"M2 FP {i}");\n'
        bench+='$finish;end endmodule'
        with tempfile.TemporaryDirectory() as temporary:
            d=Path(temporary);(d/'bench.sv').write_text(bench)
            subprocess.run(['iverilog','-g2012','-s','Bench','-o',str(d/'sim'),str(atom),str(d/'bench.sv')],check=True,capture_output=True)
            subprocess.run(['vvp',str(d/'sim')],check=True,capture_output=True)


if __name__=='__main__':unittest.main()
