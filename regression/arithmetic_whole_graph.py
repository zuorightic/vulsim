"""Step6 actual RTL scoreboard for fixed-L graphs, wide reset and safe ops."""
from pathlib import Path
import json,random,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.arithmetic_dse.whole_graph import expected,port_name
FIELDS=['a','b','c','d','e','bias','bypass','mask','s','select']
def prepare(fixtures,generated,out,exhaustive=False):
 out=Path(out);out.mkdir(parents=True,exist_ok=False);items=json.loads((Path(fixtures)/'items.json').read_text());N=len(items)
 if exhaustive:
  items=[x for x in items if (x['case']['id']=='UDR_8' or x['case']['width']==8 and x['case'].get('diagnostic') in ('shared_divrem','single_div','single_mod'))];N=len(items)
 text=f'''`timescale 1ns/1ps
module WholeGraph(input logic clk,rstn,iv,input logic [255:0] values[0:9],output logic [256:0] results[0:{N-1}][0:2],output logic valids[0:{N-1}]);
'''
 for i,item in enumerate(items):
  case=item['case'];connections=['.clk(clk)' if item['L']>1 else '', '.rstn(rstn)' if item['L']>1 else '', '.iv(iv)',f'.ov(v{i})'];text+=f'wire v{i};\n'
  for name,w in case['inputs'].items():connections.append(f'.{port_name(name)}(values[{FIELDS.index(name)}][{w-1}:0])')
  for k,(name,w) in enumerate(case['outputs'].items()):text+=f'wire [{w-1}:0] o{i}_{k};\n';connections.append(f'.{name}(o{i}_{k})')
  text+=item['name']+f' inst{i}('+','.join(x for x in connections if x)+');\n'
  text+=f'always_ff @(posedge clk) begin if(!rstn) begin valids[{i}]<=0;'
  for k,(name,w) in enumerate(case['outputs'].items()):text+=f'results[{i}][{k}]<=257\'d{item["reset_outputs"][name]};'
  for k in range(len(case['outputs']),3):text+=f'results[{i}][{k}]<=0;'
  text+=f'end else begin valids[{i}]<=v{i};if(v{i})begin '
  for k in range(len(case['outputs'])):text+=f'results[{i}][{k}]<=257\'(o{i}_{k});'
  text+='end end end\n'
 text+='endmodule\n';(out/'wrapper.sv').write_text(text)
 driver='''#include "VWholeGraph.h"
#include "verilated.h"
#include <fstream>
#include <iomanip>
#include <iostream>
int main(int argc,char**argv){if(argc!=2)return 2;Verilated::commandArgs(argc,argv);VWholeGraph top;std::ifstream input(argv[1]);unsigned iv,rst;unsigned words[10][8];
auto wide=[](const auto& value){int k=8;while(k>0&&!value[k])--k;std::cout<<std::hex<<value[k];for(--k;k>=0;--k)std::cout<<std::setw(8)<<std::setfill('0')<<value[k];};
while(true){for(auto&field:words)for(auto&word:field)if(!(input>>std::hex>>word))return 0;if(!(input>>std::hex>>iv>>rst))return 3;
top.clk=0;top.iv=iv;top.rstn=rst;for(int i=0;i<10;++i)for(int k=0;k<8;++k)top.values[i][k]=words[i][k];top.eval();top.clk=1;top.eval();
'''+f'''for(int i=0;i<{N};++i){{if(i)std::cout<<' ';std::cout<<std::hex<<unsigned(top.valids[i]);for(int k=0;k<3;++k){{std::cout<<' ';wide(top.results[i][k]);}}}}std::cout<<'\\n';}}}}
'''
 (out/'driver.cpp').write_text(driver);rng=random.Random(20261031);base={p:rng.getrandbits(256) for p in FIELDS};rows=[]
 def add(**values):rows.append({**base,**values})
 add(**{p:0 for p in FIELDS});add(**{p:(1<<256)-1 for p in FIELDS})
 for w in (8,16,32,64,128,12,24,48,96):
  mask=(1<<w)-1
  for a in (0,1,mask,1<<(w-1),mask-1):
   for d in (0,1,2,3,1<<(w//2),mask):add(a=a,b=mask,c=(1<<(min(2*w,256)))-1,d=d,e=0 if d%2 else 3)
  for s in (0,1,w-1,w,w+1,2*w,(1<<(w.bit_length()+1))-1):add(a=mask,b=1,d=3,s=s)
  for k in sorted({0,7,15,31,32,63,64,65,w-1}&set(range(w))):add(a=1<<k,d=0,b=mask)
 edges=[0,0x80000000,1,3,0x007fffff,0x00800000,0x3f000000,0x3f7fffff,0x3f800000,0x3f800001,0x40000000,0x7f7fffff,0xff7fffff,0x7f800000,0xff800000,0x7fc12345,0x7f812345,0xff812345]
 for a in edges:
  for b in edges:add(a=a,b=b,c=edges[(a^b)%len(edges)],select=(a^b)&1,bypass=0x7f812345)
 for k in range(512):add(**{p:rng.getrandbits(256) for p in FIELDS})
 controls=[]
 if exhaustive:rows=[{**base,'a':a,'d':d} for a in range(256) for d in range(256)]
 for k,row in enumerate(rows):
  iv=1 if exhaustive else int(k<128 or k%7 not in (1,2));rst=1 if exhaustive else int(k not in (0,1,127,128,511,700));controls.append((row,iv,rst))
 if exhaustive:controls=[({p:0 for p in FIELDS},0,0),*controls]
 controls += [({p:0 for p in FIELDS},0,1)]*5
 limbs=lambda n:' '.join(f'{(n>>(32*k))&0xffffffff:x}' for k in range(8))
 (out/'vectors.txt').write_text(''.join(' '.join(limbs(row[p]) for p in FIELDS)+f' {iv:x} {rst:x}\n' for row,iv,rst in controls));(out/'items.json').write_text(json.dumps(items,indent=2)+'\n');(out/'mode.json').write_text(json.dumps({'exhaustive_udiv8':exhaustive}))
 command=['verilator','--cc','--exe','--build','-j','2','-Wno-fatal','--top-module','WholeGraph','--Mdir',str(out.resolve()/'obj'),str(out.resolve()/'wrapper.sv'),*[str(Path(generated).resolve()/(item['name']+'.sv')) for item in items],str(out.resolve()/'driver.cpp')]
 (out/'build_command.json').write_text(json.dumps(command));print({'implementations':N,'cycles':len(controls)})

def verify(out):
 out=Path(out);items=json.loads((out/'items.json').read_text());source=(out/'vectors.txt').read_text().splitlines();actual=(out/'rtl-run.log').read_text().splitlines();assert len(source)==len(actual)
 history=[];held=[list(x['reset_outputs'].values())+[0]*(3-len(x['reset_outputs'])) for x in items];counts=[{'valid':0,'data':0,'reset':0,'bubble_hold':0} for x in items]
 for cycle,(raw,line) in enumerate(zip(source,actual)):
  words=[int(v,16) for v in raw.split()];row={name:sum(words[i*8+k]<<(32*k) for k in range(8)) for i,name in enumerate(FIELDS)};iv,rst=words[-2:];data=[int(v,16) for v in line.split()];assert len(data)==4*len(items)
  if not rst:history=[];held=[list(x['reset_outputs'].values())+[0]*(3-len(x['reset_outputs'])) for x in items]
  else:history.append((row,iv))
  for i,item in enumerate(items):
   L=item['L'];valid=bool(rst and len(history)>=L and history[-L][1]);counts[i]['valid']+=1
   if not rst:counts[i]['reset']+=len(item['case']['outputs'])
   elif valid:
    tx=history[-L][0];inputs={n:tx[n]&((1<<w)-1) for n,w in item['case']['inputs'].items()};value=expected(item['case'],inputs);held[i]=list(value.values())+[0]*(3-len(value));counts[i]['data']+=len(value)
   else:counts[i]['bubble_hold']+=len(item['case']['outputs'])
   assert data[i*4:i*4+4]==[int(valid),*held[i]],(cycle,item['name'],data[i*4:i*4+4],[int(valid),*held[i]])
 exhaustive=json.loads((out/'mode.json').read_text())['exhaustive_udiv8'] if (out/'mode.json').exists() else False
 formal_count=sum(not item['case'].get('diagnostic') for item in items)
 result={'version':'step6-whole-graph-cycle-v1','status':'passed','seed':20261031,'cycles':len(source),'implementations':len(items),'formal_cases':len({item['case']['id'] for item in items if not item['case'].get('diagnostic')}),'A_B_C_formal_implementations':formal_count,'diagnostic_implementations':len(items)-formal_count,'exhaustive_8bit_pairs':65536 if exhaustive else 0,'counts':{key:sum(c[key] for c in counts) for key in counts[0]},'per_implementation':{item['name']:c for item,c in zip(items,counts)},'scope':'actual RTL; external output capture counts toward L; continuous inputs, bubbles, in-flight reset, flush; shared diagnostic is quotient-reuse DAG, not a fused primitive'}
 (out/'functional.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='per_implementation'},indent=2))
if __name__=='__main__':
 if sys.argv[1]=='prepare':prepare(*map(Path,sys.argv[2:5]))
 elif sys.argv[1]=='prepare-exhaustive':prepare(*map(Path,sys.argv[2:5]),exhaustive=True)
 elif sys.argv[1]=='verify':verify(Path(sys.argv[2]))
