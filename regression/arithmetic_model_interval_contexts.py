"""Real native interval capture banks, legacy bytes, and mapped-load rejection."""
import argparse
import hashlib
import json
import random
import subprocess
import tempfile
import unittest
from pathlib import Path
from experiments.arithmetic_dse.model_mul_intervals import interval,source
from experiments.arithmetic_dse.model_samples import label_requests,render_label_requests,verify_capture_banks
from regression.arithmetic_model_intervals import expected


class CaptureBankAudit(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.contract=self.root/'contract.json';self.prefix=self.root/'actual'
        self.row={'id':'s000','source_cells':'s000/src*','target_cells':['s000/dst0*','s000/dst1*'],
                  'input_widths':[2],'capture_width':2,'fanout':2,
                  'capture_banks':[{'id':'s000_bank0','target_cells':['s000/dst0*'],'static_bit_capacity':2},
                                   {'id':'s000_bank1','target_cells':['s000/dst1*'],'static_bit_capacity':2}]}
        self.cells={'DFF':{'sequential':True},'AND':{'sequential':False}}
        self.save()
        self.instances=['s000/src0','s000/src1','s000/dst0_0','s000/dst0_1','s000/dst1_0','s000/dst1_1']
        self.write_instances()
    def save(self):self.contract.write_text(json.dumps({'version':'arithmetic-model-labels-v1','labels':[self.row]}))
    def write_instances(self):Path(str(self.prefix)+'_instances.tsv').write_text(''.join(name+'\tDFF\n' for name in self.instances))
    def test_every_bank_has_an_explicit_path_and_distinct_mapped_load(self):
        requests=label_requests(json.loads(self.contract.read_text()));self.assertEqual(len(requests),3)
        self.assertEqual(requests[1]['parent_sample_id'],'s000')
        self.assertIn('s000_bank1',render_label_requests(self.contract))
        result=verify_capture_banks(self.prefix,self.contract,self.cells)['s000']
        self.assertEqual(result['capture_DFFs'],4);self.assertEqual(result['capture_bank_counts'],{'s000_bank0':2,'s000_bank1':2})
        self.assertFalse(result['mapped_counts_are_prediction_inputs'])
    def test_merged_missing_unequal_and_oversized_banks_are_rejected(self):
        original=list(self.instances)
        for values in (original[:4],original[:-1],original+['s000/dst1_2']):
            self.instances=values;self.write_instances()
            with self.assertRaises(ValueError):verify_capture_banks(self.prefix,self.contract,self.cells)
        self.instances=original;self.write_instances();self.row['capture_banks'][1]['target_cells']=['s000/dst0*'];self.save()
        with self.assertRaises(ValueError):verify_capture_banks(self.prefix,self.contract,self.cells)
    def test_no_bank_counts_are_added_to_legacy_contract(self):
        del self.row['capture_banks'];self.row['fanout']=1;self.save()
        self.assertEqual(len(label_requests(json.loads(self.contract.read_text()))),1)
        self.assertEqual(verify_capture_banks(self.prefix,self.contract,self.cells),{})
    def test_invalid_fanout_and_nonstatic_bank_selection_are_rejected(self):
        for bad in (0,5,True,2.0):
            with self.assertRaises(ValueError):source([],capture_fanout=bad)
        self.row['capture_banks'][0]['target_cells']=['[exec bad]'];self.save()
        with self.assertRaises(ValueError):render_label_requests(self.contract)


def check_legacy(graphs,batch):
    reports={json.loads(p.read_text())['graph_sha256']:json.loads(p.read_text()) for p in graphs.glob('*.json')}
    admission=json.loads((batch/'admission.json').read_text());checked=0
    for task in admission['tasks']:
        contract=json.loads(Path(task['sample_contract']).read_text())
        items=[(reports[s['graph_sha256']],interval(reports[s['graph_sha256']],s['first'],s['last'])) for s in contract['labels']]
        text,labels=source(items)
        if hashlib.sha256(text.encode()).hexdigest()!=task['rtl_sha256'] or labels!=contract['labels']:
            raise ValueError('default single-bank generator changed frozen RTL or contract')
        checked+=1
    return checked


def functional(graphs,out,batch):
    out.mkdir(parents=True,exist_ok=False);rng=random.Random(20261103);observations=[];designs=[];checks=0
    legacy=check_legacy(graphs,batch)
    for path in sorted(graphs.glob('*.json')):
        report=json.loads(path.read_text());region=report['graph']['regions'][0]
        if region['parameters']['lhs_width'] not in (8,12,16,20,24,28,32):continue
        groups=region['legal_groups'];items=[(report,interval(report,a,b)) for a in range(len(groups)) for b in range(a,len(groups))]
        for fanout in (2,3,4):
            text,labels=source(items,capture_fanout=fanout);name=path.stem+f'-F{fanout}'
            design=out/(name+'.sv');design.write_text(text)
            contract={'version':'arithmetic-model-labels-v1','labels':labels};(out/(name+'.contract.json')).write_text(json.dumps(contract,indent=2)+'\n')
            benches=['module Bench; reg clk=0,rstn=0,iv=0; wire ov;'];connections=['.clk(clk)','.rstn(rstn)','.iv(iv)','.ov(ov)']
            for i,(_,spec) in enumerate(items):
                for k,w in enumerate(spec['input_widths']):
                    benches.append(f'reg [{w-1}:0] x{i}_{k}=0;');connections.append(f'.x{i}_{k}(x{i}_{k})')
                for bank in range(fanout):
                    benches.append(f'wire y{i}_b{bank};');connections.append(f'.y{i}_b{bank}(y{i}_b{bank})')
            benches.append('ModelBundle dut('+','.join(connections)+'); initial begin')
            state=None;wants={};stimulus=[]
            for cycle in range(20):
                reset=cycle in (0,1,10);enable=cycle not in (5,6,15)
                vectors=[[rng.getrandbits(w) for w in spec['input_widths']] for _,spec in items]
                stimulus.append({'cycle':cycle,'reset':reset,'enable':enable,'inputs_hex':[[format(v,'x') for v in values] for values in vectors]})
                benches.append(f'rstn={int(not reset)};iv={int(enable)};')
                for i,((_,spec),values) in enumerate(zip(items,vectors)):
                    for k,(w,value) in enumerate(zip(spec['input_widths'],values)):benches.append(f'x{i}_{k}={w}\'h{value:x};')
                benches.append('#5;clk=1;#1;')
                if state is not None:
                    for i,((graph,spec),values) in enumerate(zip(items,state)):
                        want=expected(graph,spec,values);wants[cycle,i]=want
                        for bank in range(fanout):
                            benches.append(f'if(dut.s{i:03d}.dst{bank} !== {spec["capture_width"]}\'h{want:x})$fatal(1,"capture-bank mismatch {name}/{cycle}/{i}/{bank}");')
                            benches.append(f'$display("BANK_VALUE {cycle} {i} {bank} %h",dut.s{i:03d}.dst{bank});');checks+=1
                if reset:state=[[0]*len(spec['input_widths']) for _,spec in items]
                elif enable:state=vectors
                benches.append('#4;clk=0;')
            benches.append('$display("CONTEXT_BANKS_PASS");$finish;end endmodule')
            with tempfile.TemporaryDirectory() as tmp:
                directory=Path(tmp);bench=directory/'bench.sv';bench.write_text('\n'.join(benches))
                subprocess.run(['iverilog','-g2012','-s','Bench','-o',str(directory/'sim'),str(design),str(bench)],check=True,capture_output=True)
                result=subprocess.run(['vvp',str(directory/'sim')],check=True,capture_output=True,text=True)
            if 'CONTEXT_BANKS_PASS' not in result.stdout:raise ValueError('missing real capture-bank functional marker')
            seen=set()
            for line in result.stdout.splitlines():
                fields=line.split()
                if not fields or fields[0]!='BANK_VALUE':continue
                cycle,i,bank=map(int,fields[1:4]);identity=(cycle,i,bank)
                if identity in seen or int(fields[4],16)!=wants[cycle,i]:raise ValueError('invalid actual capture-bank observation')
                seen.add(identity);observations.append({'design':name,'cycle':cycle,'interval':i,'bank':bank,'observed_hex':fields[4],'expected_hex':format(wants[cycle,i],'x')})
            if len(seen)!=len(wants)*fanout:raise ValueError('incomplete actual capture-bank observations')
            designs.append({'id':name,'graph_sha256':report['graph_sha256'],'rtl_sha256':hashlib.sha256(text.encode()).hexdigest(),'fanout':fanout,
                            'intervals':[{'first':s['first'],'last':s['last']} for _,s in items],'stimulus':stimulus})
    receipt={'version':'native-interval-capture-context-functional-v1','legacy_bundles_byte_identical':legacy,
             'seed':20261103,'designs':designs,'checks':checks,'observations':observations,
             'semantics':'unconditional capture of previous launch state; reset and enable affect launch only; every bank checked'}
    (out/'functional.json').write_text(json.dumps(receipt,separators=(',',':'))+'\n')
    print(json.dumps({k:receipt[k] for k in ('version','legacy_bundles_byte_identical','checks')}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--graphs',type=Path);parser.add_argument('--out',type=Path);parser.add_argument('--legacy-batch',type=Path)
    args=parser.parse_args()
    if not all((args.graphs,args.out,args.legacy_batch)):parser.error('--graphs, --out and --legacy-batch required')
    functional(args.graphs,args.out,args.legacy_batch)
