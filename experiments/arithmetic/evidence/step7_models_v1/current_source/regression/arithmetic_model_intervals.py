"""Native-template interval arithmetic checked with Python integer semantics."""
import argparse,copy,hashlib,json,random,subprocess,tempfile
from pathlib import Path
from experiments.arithmetic_dse.model_mul_intervals import interval,source
from experiments.arithmetic_dse.model_analysis import literal


def expected(report,spec,packed):
    nodes={n['id']:n for n in report['graph']['nodes']};values={}
    for node,value in zip(spec['input_nodes'],packed):
        z,o,w=spec['facts'][node];n=o
        for i,bit in enumerate(spec['input_bit_positions'][node]):n|=((value>>i)&1)<<bit
        values[node]=n
    def operand(v):return literal(v) if v['kind']==1 else value(v['node'])
    def value(node):
        if node in values:return values[node]
        if node not in spec['members']:return spec['facts'][node][1]
        n=nodes[node];a=[operand(v) for v in n['operands']];kind=n['kind']
        if kind in (0,8,11,13):v=a[0]
        elif kind==14:v=a[0]>>n['lo']
        elif kind==18:
            v=0
            for x,op in zip(a,n['operands']):v=(v<<op['width'])|x
        elif kind==4 and n['opcode']==3:v=a[0]*a[1]
        elif kind==2:v=sum(a)
        else:raise ValueError('unsupported independent evaluator operation')
        values[node]=v&((1<<n['width'])-1);return values[node]
    result=at=0
    for node in spec['output_nodes']:
        v=value(node)
        for bit in spec['output_bit_positions'][node]:result|=((v>>bit)&1)<<at;at+=1
    return result


def check_trimmed(report,spec,rng):
    """Vary every unknown external bit before dependency-based pruning."""
    nodes={n['id']:n for n in report['graph']['nodes']};inside=set(spec['members'])
    external={v['node'] for node in inside for v in nodes[node]['operands'] if v['kind']==0 and v['node'] not in inside}
    full=copy.deepcopy(spec);full['input_nodes']=[];full['input_bit_positions']={}
    for node in sorted(external,key=int):
        z,o,w=spec['facts'][node];positions=[b for b in range(w) if not ((z|o)>>b)&1]
        if positions:full['input_nodes'].append(node);full['input_bit_positions'][node]=positions
    for trial in range(16):
        raw={node:rng.getrandbits(len(full['input_bit_positions'][node])) for node in full['input_nodes']};small=[]
        for node in spec['input_nodes']:
            at={bit:j for j,bit in enumerate(full['input_bit_positions'][node])}
            small.append(sum(((raw[node]>>at[bit])&1)<<j for j,bit in enumerate(spec['input_bit_positions'][node])))
        if expected(report,full,[raw[node] for node in full['input_nodes']])!=expected(report,spec,small):
            raise ValueError('consumed-bit pruning changes native interval semantics')
    return 16


def run(graphs,evidence=None):
    rng=random.Random(20261103);trim_rng=random.Random(20261103);checks=0;intervals=0;trim_checks=0
    receipt={'version':'arithmetic-native-interval-functional-v1','seed':20261103,'graphs':[],'observations':[]}
    for path in sorted(Path(graphs).glob('*.json')):
        report=json.loads(path.read_text());groups=report['graph']['regions'][0]['legal_groups'];items=[]
        receipt['graphs'].append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'graph_sha256':report['graph_sha256']})
        for first in range(len(groups)):
            for last in range(first,len(groups)):items.append((report,interval(report,first,last)))
        for _,spec in items:trim_checks+=check_trimmed(report,spec,trim_rng)
        text,_=source(items);bench='module Bench;\n';cases={}
        for idx,(report,spec) in enumerate(items):
            args=[]
            for k,w in enumerate(spec['input_widths']):bench+=f'reg [{w-1}:0] x{idx}_{k}=0;\n';args.append(f'.x{k}(x{idx}_{k})')
            bench+=f'wire [{spec["capture_width"]-1}:0] y{idx};Core_s{idx:03d} c{idx}('+','.join(args)+f',.value(y{idx}));\n'
        bench+='initial begin\n'
        for trial in range(8):
            wants=[]
            for idx,(report,spec) in enumerate(items):
                data=[rng.getrandbits(w) if trial>1 else (0 if trial==0 else (1<<w)-1) for w in spec['input_widths']]
                for k,(v,w) in enumerate(zip(data,spec['input_widths'])):bench+=f'x{idx}_{k}={w}\'d{v};\n'
                wants.append(expected(report,spec,data))
                cases[trial,idx]={'graph_sha256':report['graph_sha256'],'first':spec['first'],'last':spec['last'],'trial':trial,
                    'inputs_hex':[format(v,'x') for v in data],'expected_hex':format(wants[-1],'x')}
            bench+='#1;\n'
            for idx,((_,spec),want) in enumerate(zip(items,wants)):
                bench+=f'if(y{idx} !== {spec["capture_width"]}\'d{want})$fatal(1,"interval {path.name}/{idx}/{trial}");\n'
                bench+=f'$display("INTERVAL_VALUE {trial} {idx} %h",y{idx});\n';checks+=1
        bench+='$display("INTERVALS_PASS");$finish;end endmodule\n'
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'design.sv').write_text(text);(p/'bench.sv').write_text(bench)
            subprocess.run(['iverilog','-g2012','-s','Bench','-o',str(p/'sim'),str(p/'design.sv'),str(p/'bench.sv')],check=True,capture_output=True)
            output=subprocess.run(['vvp',str(p/'sim')],check=True,capture_output=True,text=True)
            if 'INTERVALS_PASS' not in output.stdout:raise AssertionError('no interval marker')
            seen=set()
            for line in output.stdout.splitlines():
                fields=line.split()
                if not fields or fields[0]!='INTERVAL_VALUE':continue
                trial,idx=int(fields[1]),int(fields[2]);identity=(trial,idx)
                if identity in seen:raise AssertionError('duplicate RTL observation')
                seen.add(identity);value=int(fields[3],16);item=dict(cases[identity],observed_hex=format(value,'x'))
                if value!=int(item['expected_hex'],16):raise AssertionError('RTL observation mismatch')
                receipt['observations'].append(item)
            if seen!=set(cases):raise AssertionError('incomplete RTL observations')
        intervals+=len(items)
    receipt.update(native_graphs=len(receipt['graphs']),intervals=intervals,RTL_integer_checks=checks,untrimmed_integer_checks=trim_checks)
    if evidence is not None:Path(evidence).write_text(json.dumps(receipt,indent=2)+'\n')
    print({k:receipt[k] for k in ('native_graphs','intervals','RTL_integer_checks','untrimmed_integer_checks')});return checks

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('graphs',type=Path);p.add_argument('--evidence',type=Path);a=p.parse_args()
    run(a.graphs,a.evidence)
