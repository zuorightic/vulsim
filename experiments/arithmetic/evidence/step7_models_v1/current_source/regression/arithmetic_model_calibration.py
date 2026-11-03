"""Independent RTL checks for synthetic stage and reset/enable fixtures."""
import random
import subprocess
import tempfile
import unittest
from pathlib import Path
from experiments.arithmetic_dse.model_calibration import source


class Calibration(unittest.TestCase):
    def test_actual_RTL_state_and_synthetic_contexts(self):
        rng=random.Random(20261102);checks=0
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for split,fan_override in (('train',None),('validation',None),('test',None),('test',1)):
                if fan_override:
                    from experiments.arithmetic_dse.model_stage_samples import source as mixed_source
                    text,labels=mixed_source(split,fan_override)
                else:text,labels=source(split)
                bench='module Bench;reg clk=0,rstn=0,iv=1;wire ov;\n';connections=['.clk(clk)','.rstn(rstn)','.iv(iv)','.ov(ov)']
                widths=[]
                for i,r in enumerate(labels):
                    w=r['lhs_width'];out=r['result_width'];fan=r['fanout']
                    ins=r.get('input_widths') or ([w] if r['role']=='state' else [w]*6 if r['topology']=='tree' else [w,w]+[out]*(len(r['graph_nodes'])-1))
                    widths.append(ins)
                    for k,v in enumerate(ins):bench+=f'reg [{v-1}:0] x{i}_{k};\n';connections.append(f'.x{i}_{k}(x{i}_{k})')
                    bench+=(f'wire y{i};\n' if r.get('observer') else f'wire [{out*fan-1}:0] y{i};\n');connections.append(f'.y{i}(y{i})')
                bench+='ModelBundle dut('+','.join(connections)+');\ninitial begin\n'
                for iteration in range(32):
                    expected=[]
                    for i,(r,ins) in enumerate(zip(labels,widths)):
                        values=[]
                        for k,w in enumerate(ins):
                            v=rng.getrandbits(w) if iteration>1 else (0 if iteration==0 else (1<<w)-1)
                            values.append(v);bench+=f'x{i}_{k}={w}\'h{v:x};\n'
                        if r['role']=='state':v=values[0]
                        elif r['graph_nodes'] and 'operand_sources' in r['graph_nodes'][0]:
                            computed=[]
                            for node in r['graph_nodes']:
                                args=[computed[s['node']] if 'node' in s else values[s['input']] for s in node['operand_sources']]
                                v=args[0]*args[1] if node['operation']=='mul' else sum(args)
                                computed.append(v&((1<<node['result_width'])-1))
                            v=computed[-1]
                        else:v=sum(values[k]*values[k+1] for k in (0,2,4)) if r['topology']=='tree' else values[0]*values[1]+sum(values[2:])
                        v&=(1<<r['result_width'])-1;expected.append(sum(v<<(r['result_width']*b) for b in range(r['fanout'])))
                    bench+='rstn=1;iv=1;#5;clk=1;#5;clk=0;#5;clk=1;#5;clk=0;#1;\n'
                    for i,(r,v) in enumerate(zip(labels,expected)):
                        observed=f'dut.captured_{i}' if r.get('observer') else f'y{i}'
                        checks+=1;bench+=f'if({observed} !== {r["result_width"]*r["fanout"]}\'h{v:x})$fatal(1,"calibration {split}/{i}/{iteration}");\n'
                    bench+='iv=0;#5;clk=1;#5;clk=0;#1;\n'
                    for i,(r,v) in enumerate(zip(labels,expected)):
                        observed=f'dut.captured_{i}' if r.get('observer') else f'y{i}'
                        if r['role']=='state':checks+=1;bench+=f'if({observed} !== {r["result_width"]*r["fanout"]}\'h{v:x})$fatal(1,"state enable");\n'
                    bench+='rstn=0;#5;clk=1;#5;clk=0;#1;\n'
                    for i,r in enumerate(labels):
                        observed=f'dut.captured_{i}' if r.get('observer') else f'y{i}'
                        if r['role']=='state':checks+=1;bench+=f'if({observed} !== 0)$fatal(1,"state reset");\n'
                bench+='$display("CALIBRATION_FUNCTIONAL_PASS");$finish;end endmodule\n'
                (root/'fixtures.sv').write_text(text+bench)
                subprocess.run(['iverilog','-g2012','-s','Bench','-o',str(root/'sim'),str(root/'fixtures.sv')],check=True,capture_output=True)
                run=subprocess.run(['vvp',str(root/'sim')],check=True,capture_output=True,text=True);self.assertIn('CALIBRATION_FUNCTIONAL_PASS',run.stdout)
        print({'calibration_RTL_checks':checks,'source_families':4,'seed':20261102})


if __name__=='__main__':unittest.main()
