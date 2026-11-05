"""Real parallel-Mux fixtures and prospective split/observer contracts."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from experiments.arithmetic_dse.model_m2_mux_samples import source
from experiments.arithmetic_dse.model_m2_mux_labels import label_requests,render_label_requests
from experiments.arithmetic_dse.model_m2_mux_collection import run_task
from experiments.arithmetic_dse.model_m2_collection import CONFIG as LEGACY


class MuxContexts(unittest.TestCase):
    def test_real_partition_sources_are_distinct_and_within_capacity(self):
        import hashlib
        cfg=json.loads(LEGACY.read_text());seen=set()
        protocol=json.loads(Path('experiments/arithmetic_dse/configs/model_asap7_m2_mux_context_v1.json').read_text())
        count={}
        for split,c in protocol['splits'].items():
            n=c['independent_muxes_per_source'];count[split]=0
            for fanout in c['capture_fanouts']:
                for width in protocol['widths']:
                    text,labels=source(width,fanout,n,cfg);h=hashlib.sha256(text.encode()).hexdigest()
                    self.assertNotIn(h,seen);seen.add(h);count[split]+=4
                    self.assertLessEqual(sum(sum(s['input_widths']) for s in labels),640)
                    self.assertLessEqual(sum(s['capture_width']*fanout for s in labels),2048)
                    rows=label_requests({'labels':labels})
                    self.assertEqual(len(rows),n*(4+(fanout if fanout>1 else 0)))
                    for sid in [s['id'] for s in labels]:
                        for arc in ('select','data_a','data_b'):self.assertEqual(sum(r['id']==sid+'_'+arc for r in rows),1)
        self.assertEqual(count,protocol['task_counts'])

    def test_old_or_dynamic_label_protocol_rejected(self):
        cfg=json.loads(LEGACY.read_text());_,labels=source(8,1,2,cfg)
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'contract';p.write_text(json.dumps({'version':'arithmetic-model-labels-v1','labels':labels}))
            with self.assertRaises(ValueError):render_label_requests(p)
            p.write_text(json.dumps({'version':'arithmetic-mux-context-labels-v1','labels':labels}));text=render_label_requests(p)
            self.assertIn('s000_select {s000/src_c*}',text);self.assertIn('s001_data_a {s001/src_a*}',text)

    def test_new_independent_task_cannot_run(self):
        with patch('experiments.arithmetic_dse.model_m2_mux_collection.verify',return_value={}):
            with self.assertRaisesRegex(ValueError,'independent test is locked'):run_task(Path('/tmp/not-started'),{'split':'test'})

    def test_parallel_mux_continuous_transactions_bubbles_and_reset(self):
        cfg=json.loads(LEGACY.read_text())
        for width,fanout,n in ((1,1,2),(5,3,3),(64,3,4)):
            with self.subTest(width=width,fanout=fanout,replicas=n):
                rtl,labels=source(width,fanout,n,cfg);ports=['.clk(clk)','.rstn(rstn)','.iv(iv)','.ov(ov)'];decl=[];stim=[];checks=[];update=[]
                for i,s in enumerate(labels):
                    decl.append(f'reg[{width-1}:0]a{i}=0,b{i}=0,sa{i}=0,sb{i}=0;reg c{i}=0,sc{i}=0;wire[{width-1}:0]e{i}=sc{i}?sa{i}:sb{i};')
                    ports += [f'.a{i}(a{i})',f'.b{i}(b{i})',f'.c{i}(c{i})']
                    stim.append(f'a{i}=(k*37+{19+i*13});b{i}=(k*13+{7+i*3});c{i}=(k+{i})%2;')
                    update.append(f'if(!rstn)begin sa{i}=0;sb{i}=0;sc{i}=0;end else if(iv)begin sa{i}=a{i};sb{i}=b{i};sc{i}=c{i};end')
                    for bank in range(fanout):
                        name=f'y{i}_b{bank}';decl.append(f'wire {name};');ports.append(f'.{name}({name})')
                        checks.append(f'if(k>0 && {name} !== ^e{i}) $fatal(1,"Mux bank/transaction mismatch {name}");')
                tb='module tb;reg clk=0,rstn=0,iv=0;wire ov;integer k;\n'+'\n'.join(decl)+'\nModelBundle dut('+','.join(ports)+');\ninitial begin\n'
                tb+='for(k=0;k<96;k=k+1)begin '+''.join(stim)+'rstn=(k%17!=0);iv=(k%7!=0);#5;clk=1;#1;\n'
                tb+='\n'.join(checks)+'\nif(ov !== (rstn && iv))$fatal(1,"valid mismatch");\n'+'\n'.join(update)+'\n#4;clk=0;end\n$display("MUX_CONTEXT_RTL_PASS");$finish;end endmodule'
                with tempfile.TemporaryDirectory() as td:
                    d=Path(td);(d/'design.sv').write_text(rtl);(d/'tb.sv').write_text(tb)
                    subprocess.run(['iverilog','-g2012','-s','tb','-o',str(d/'sim'),str(d/'design.sv'),str(d/'tb.sv')],check=True,capture_output=True,text=True)
                    r=subprocess.run(['vvp',str(d/'sim')],check=True,capture_output=True,text=True);self.assertIn('MUX_CONTEXT_RTL_PASS',r.stdout)


if __name__=='__main__':unittest.main()
