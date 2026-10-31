"""Step5 multiplier cycle validation. Leaf build/run commands use shared ledger."""
from pathlib import Path
import json,random,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
def prepare(generated,out):
 out.mkdir(exist_ok=False);items=json.loads((generated/'summary.json').read_text());n=len(items)
 text=f'''`timescale 1ns/1ps
module MulTemplates(input logic clk,rstn,iv,input logic [127:0] a,b,c,output logic [255:0] ys[0:{n-1}],zs[0:{n-1}],output logic vs[0:{n-1}]);
'''
 for i,item in enumerate(items):
  w,R,name=item['W'],item['R'],item['stem'];mask=(1<<R)-1
  text+=f'''wire [{R-1}:0] y{i},z{i};wire v{i};
{name} u{i}(.clk(clk),.rstn(rstn),.iv(iv),.ov(v{i}),.a(a[{w-1}:0]),.b(b[{w-1}:0]),.c(c[{w-1}:0]),.y(y{i}),.z(z{i}));
always_ff @(posedge clk) begin
if(!rstn)begin vs[{i}]<=0;ys[{i}]<=256'd{35&mask};zs[{i}]<=256'd{55&mask};end
else begin vs[{i}]<=v{i};if(v{i})begin ys[{i}]<=256'(y{i});zs[{i}]<=256'(z{i});end end
end
'''
 text+='endmodule\n';(out/'wrapper.sv').write_text(text)
 driver='''#include "VMulTemplates.h"
#include "verilated.h"
#include <fstream>
#include <iomanip>
#include <iostream>
int main(int argc,char** argv){if(argc!=2)return 2;Verilated::commandArgs(argc,argv);VMulTemplates top;std::ifstream in(argv[1]);unsigned a[4],b[4],c[4],iv,rst;
auto read=[&](unsigned* words){for(int i=0;i<4;++i)if(!(in>>std::hex>>words[i]))return false;return true;};
auto wide=[&](const auto& value){for(int i=7;i>=0;--i)std::cout<<std::hex<<std::setw(8)<<std::setfill('0')<<value[i];};
while(read(a)&&read(b)&&read(c)&&(in>>std::hex>>iv>>rst)){top.clk=0;top.iv=iv;top.rstn=rst;for(int i=0;i<4;++i){top.a[i]=a[i];top.b[i]=b[i];top.c[i]=c[i];}top.eval();top.clk=1;top.eval();
'''+f'''for(int i=0;i<{n};++i){{if(i)std::cout<<' ';std::cout<<std::hex<<unsigned(top.vs[i])<<' ';wide(top.ys[i]);std::cout<<' ';wide(top.zs[i]);}}std::cout<<'\\n';}}}}
'''
 (out/'driver.cpp').write_text(driver)
 rng=random.Random(20261031);pairs=[(0,0),(1,(1<<128)-1),((1<<128)-1,(1<<128)-1),(1<<127,1<<127)]
 pairs += [(1<<i,1<<j) for i in (0,7,12,15,16,23,31,47,63,95,127) for j in (0,7,12,15,16,23,31,47,63,95,127)]
 pairs += [(rng.getrandbits(128),rng.getrandbits(128)) for _ in range(1000)]
 rows=[(a,b,rng.getrandbits(128),int(i<130 or i%7 not in (1,2)),int(i not in (0,1,200,201,700))) for i,(a,b) in enumerate(pairs)]+[(0,0,0,0,1)]*4
 limbs=lambda n:' '.join(format((n>>(32*i))&0xffffffff,'x') for i in range(4))
 (out/'vectors.txt').write_text(''.join(f'{limbs(a)} {limbs(b)} {limbs(c)} {iv:x} {rst:x}\n' for a,b,c,iv,rst in rows))
 (out/'items.json').write_text(json.dumps(items,indent=2)+'\n')
 (out/'build_command.json').write_text(json.dumps(['verilator','--cc','--exe','--build','-j','2','--top-module','MulTemplates','--Mdir',str(out/'obj'),str(out/'wrapper.sv'),*[str(generated/(x['stem']+'.sv')) for x in items],str(out/'driver.cpp')]))
 print({'prepared_modules':n,'cycles':len(rows)})
def verify(out):
 items=json.loads((out/'items.json').read_text());rows=(out/'vectors.txt').read_text().splitlines();actual=(out/'rtl-run.log').read_text().splitlines();assert len(rows)==len(actual)
 held=[(35&((1<<x['R'])-1),55&((1<<x['R'])-1)) for x in items];history=[];counts={'cycles':len(rows),'valid_checks':0,'data_checks':0,'reset_checks':0,'bubble_hold_checks':0,'configurations':len(items)}
 for cycle,(row,line) in enumerate(zip(rows,actual)):
  words=[int(v,16) for v in row.split()];a,b,c=[sum(words[k*4+i]<<(32*i) for i in range(4)) for k in range(3)];iv,rst=words[-2:];values=[int(v,16) for v in line.split()];assert len(values)==3*len(items)
  if not rst:history=[];valid=0;held=[(35&((1<<x['R'])-1),55&((1<<x['R'])-1)) for x in items];counts['reset_checks']+=2*len(items)
  else:
   history.append((a,b,c,iv));valid=int(len(history)>=3 and history[-3][3])
   if valid:
    aa,bb,cc,_=history[-3];held=[]
    for x in items:m=(1<<x['W'])-1;mask=(1<<x['R'])-1;held.append((((aa&m)*(bb&m))&mask,((aa&m)*(cc&m))&mask))
    counts['data_checks']+=2*len(items)
   else:counts['bubble_hold_checks']+=2*len(items)
  for i,(y,z) in enumerate(held):assert values[3*i:3*i+3]==[valid,y,z],(cycle,items[i],values[3*i:3*i+3],[valid,y,z])
  counts['valid_checks']+=len(items)
 (out/'functional.json').write_text(json.dumps({'status':'passed','seed':20261031,'L':3,'II':1,**counts},indent=2)+'\n');print(json.dumps(counts))
if __name__=='__main__':
 if sys.argv[1]=='prepare':prepare(Path(sys.argv[2]).resolve(),Path(sys.argv[3]).resolve())
 elif sys.argv[1]=='verify':verify(Path(sys.argv[2]).resolve())
 elif sys.argv[1]=='build':raise SystemExit(subprocess.call(json.loads(Path(sys.argv[2]).read_text())))
 elif sys.argv[1]=='run':
  p=Path(sys.argv[2]);out=p/'rtl-run.log'
  with out.open('w') as f:raise SystemExit(subprocess.call([str(p/'obj/VMulTemplates'),str(p/'vectors.txt')],stdout=f))
