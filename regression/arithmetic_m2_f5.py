"""Actual five-bank RTL behavior and prospective F5 admission boundaries."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from experiments.arithmetic_dse.model_m2_source5 import source
from experiments.arithmetic_dse.model_m2_labels5 import label_requests
from experiments.arithmetic_dse.model_m2_f5_tests import prepare
from experiments.arithmetic_dse.model_samples import label_requests as old_requests
from experiments.arithmetic_dse.model_m2_fit_v4 import predict


CFG=Path('experiments/arithmetic_dse/configs/model_asap7_m2_primitives_v1.json')


class FiveBanks(unittest.TestCase):
    def test_all_registered_families_fit_declared_capacity(self):
        cfg=json.loads(CFG.read_text());seen=set()
        for family,entry in cfg['families'].items():
            for width in entry['widths']:
                text,labels=source(family,width,cfg,'module AtomicFp(input [31:0] a,b,output [36:0] value);assign value=0;endmodule')
                self.assertLessEqual(sum(sum(s['input_widths']) for s in labels),640)
                self.assertLessEqual(sum(s['capture_width']*5 for s in labels),2048)
                self.assertEqual(len(label_requests({'labels':labels})),6*len(labels))
                h=hashlib.sha256(text.encode()).hexdigest();self.assertNotIn(h,seen);seen.add(h)
                with self.assertRaises(ValueError):old_requests({'labels':labels})
        self.assertEqual(len(seen),14)

    def test_unready_fit_cannot_create_test(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'unadmitted'
            with patch('experiments.arithmetic_dse.model_m2_f5_tests.verify_fit',return_value={'grt_validation_ready':False}), \
                 patch('experiments.arithmetic_dse.model_m2_collection.verify_plan',return_value={}):
                with self.assertRaisesRegex(ValueError,'validated matching'):prepare(Path('/plan'),Path('/selection'),out)
            self.assertFalse(out.exists())

    def test_conditioned_target_has_no_nearest_point_fallback(self):
        model={'kind':'exact_width_target_slices','slices':{'8/8/8/1500':{'kind':'pooled','predictor':{'kind':'linear','features':[],'coefficients':[],'intercept':100},'delay_scale':1.05,'delay_margin_ps':1.5}}}
        row={'spec':{'lhs_width':8,'rhs_width':8,'result_width':8},'period_ps':1500,'features':{}}
        self.assertEqual(predict(model,row,'delay'),106.5)
        row['period_ps']=1501
        with self.assertRaises(KeyError):predict(model,row,'delay')

    def test_real_fifth_bank_with_continuous_bubbles_and_reset(self):
        cfg=json.loads(CFG.read_text());rtl,labels=source('arithmetic',8,cfg,'')
        ports=['.clk(clk)','.rstn(rstn)','.iv(iv)','.ov(ov)'];declarations=[];checks=[]
        expressions={'add':'sa+sb','add_wide':"{1'b0,sa}+{1'b0,sb}",'addcarry':"{1'b0,sa}+{1'b0,sb}+sc",'mul':'sa*sb','mul_low':'sa*sb'}
        for i,s in enumerate(labels):
            ports += [f'.a{i}(a)',f'.b{i}(b)',f'.c{i}(c)']
            declarations.append(f'wire [{s["result_width"]-1}:0] ex{i}={expressions[s["rtl_operation"]]};')
            for bank in range(5):
                name=f'y{i}_b{bank}';declarations.append(f'wire {name};');ports.append(f'.{name}({name})')
                checks.append(f'if(k>0 && {name} !== ^ex{i}) $fatal(1,"bank mismatch {name}");')
        tb='module tb;reg clk=0,rstn=0,iv=0,c=0,sc=0;reg[7:0]a=0,b=0,sa=0,sb=0;wire ov;integer k;\n'+'\n'.join(declarations)
        tb+='\nModelBundle dut('+','.join(ports)+');\ninitial begin\n'
        tb+='for(k=0;k<64;k=k+1)begin a=(k*37+19);b=(k*13+7);c=k%2;rstn=(k%17!=0);iv=(k%7!=0);#5;clk=1;#1;\n'
        tb+='\n'.join(checks)+'\nif(!rstn)begin sa=0;sb=0;sc=0;end else if(iv)begin sa=a;sb=b;sc=c;end #4;clk=0;end\n$display("F5_RTL_PASS");$finish;end endmodule\n'
        with tempfile.TemporaryDirectory() as td:
            d=Path(td);(d/'design.sv').write_text(rtl);(d/'tb.sv').write_text(tb)
            subprocess.run(['iverilog','-g2012','-s','tb','-o',str(d/'sim'),str(d/'design.sv'),str(d/'tb.sv')],check=True,capture_output=True,text=True)
            p=subprocess.run(['vvp',str(d/'sim')],check=True,capture_output=True,text=True)
            self.assertIn('F5_RTL_PASS',p.stdout)


if __name__=='__main__':unittest.main()
