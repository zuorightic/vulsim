"""MAC carry/truncation and transaction validation, including a 257-bit sum."""
from pathlib import Path
import json,random,subprocess,sys

def prepare(generated,out):
 out.mkdir(exist_ok=False);items=[];files=[];wrapper='''`timescale 1ns/1ps
module MulMAC(input logic clk,iv,input logic [127:0] a,b,input logic [256:0] c,output logic [256:0] ys[0:19],output logic vs[0:19]);\n'''
 for w in (8,16,32,64,128):
  for mode in (0,1,2,3):
   i=len(items);name=f'sensitivity_{w}_1_{mode}';data=json.loads((generated/(name+'.json')).read_text());function=data['graph']['regions'][0]['id'].split('/')[0];text=(generated/(name+'.sv')).read_text().replace('module '+function+'(','module '+name+'(');file=out/(name+'.sv');file.write_text(text);files.append(str(file));items.append({'stem':name,'W':w,'mode':mode,'R':2*w+1})
   wrapper+=f'''wire [{2*w}:0] y{i};wire v{i};{name} u{i}(.clk(clk),.iv(iv),.ov(v{i}),.a(a[{w-1}:0]),.b(b[{w-1}:0]),.c(c[{2*w}:0]),.y(y{i}));
always_ff @(posedge clk)begin vs[{i}]<=v{i};if(v{i})ys[{i}]<=257'(y{i});end\n'''
 wrapper+='endmodule\n';(out/'wrapper.sv').write_text(wrapper)
 driver='''#include "VMulMAC.h"
#include "verilated.h"
#include <fstream>
#include <iomanip>
#include <iostream>
int main(int argc,char** argv){if(argc!=2)return 2;Verilated::commandArgs(argc,argv);VMulMAC top;std::ifstream in(argv[1]);unsigned a[4],b[4],c[9],iv;
auto read=[&](unsigned* words,int n){for(int i=0;i<n;++i)if(!(in>>std::hex>>words[i]))return false;return true;};
while(read(a,4)&&read(b,4)&&read(c,9)&&(in>>std::hex>>iv)){top.clk=0;top.iv=iv;for(int i=0;i<4;++i){top.a[i]=a[i];top.b[i]=b[i];}for(int i=0;i<9;++i)top.c[i]=c[i];top.eval();top.clk=1;top.eval();for(int i=0;i<20;++i){if(i)std::cout<<' ';std::cout<<std::hex<<unsigned(top.vs[i])<<' ';for(int j=8;j>=0;--j)std::cout<<std::setw(8)<<std::setfill('0')<<top.ys[i][j];}std::cout<<'\\n';}}
''';(out/'driver.cpp').write_text(driver)
 rng=random.Random(20261031);rows=[(0,0,0,0)]*4+[(2**128-1,2**128-1,2**257-1,1),(2**127,2**127,2**256,1),(1,1,2**257-1,1)]
 rows += [(rng.getrandbits(128),rng.getrandbits(128),rng.getrandbits(257),int(i<32 or i%7 not in (1,2))) for i in range(1000)];rows += [(0,0,0,0)]*4
 limbs=lambda n,k:' '.join(format((n>>(32*i))&0xffffffff,'x') for i in range(k))
 (out/'vectors.txt').write_text(''.join(f'{limbs(a,4)} {limbs(b,4)} {limbs(c,9)} {iv:x}\n' for a,b,c,iv in rows));(out/'items.json').write_text(json.dumps(items,indent=2)+'\n')
 (out/'build_command.json').write_text(json.dumps(['verilator','--cc','--exe','--build','-j','2','--top-module','MulMAC','--Mdir',str(out/'obj'),str(out/'wrapper.sv'),*files,str(out/'driver.cpp')]))
 print({'modules':len(items),'cycles':len(rows)})
def verify(out):
 items=json.loads((out/'items.json').read_text());rows=(out/'vectors.txt').read_text().splitlines();actual=(out/'rtl-run.log').read_text().splitlines();assert len(rows)==len(actual);history=[];held=[None]*20;valid_checks=data_checks=0;bit256_seen=False
 for cycle,(row,line) in enumerate(zip(rows,actual)):
  words=[int(x,16) for x in row.split()];a=sum(words[i]<<(32*i) for i in range(4));b=sum(words[4+i]<<(32*i) for i in range(4));c=sum(words[8+i]<<(32*i) for i in range(9));iv=words[-1];history.append((a,b,c,iv));values=[int(v,16) for v in line.split()]
  if len(history)<3:continue
  valid=history[-3][3]
  for i,item in enumerate(items):
   assert values[2*i]==valid,(cycle,i,'valid');valid_checks+=1
   if valid:
    aa,bb,cc,_=history[-3];w=item['W'];held[i]=(((aa&((1<<w)-1))*(bb&((1<<w)-1)))+(cc&((1<<(2*w+1))-1)))&((1<<(2*w+1))-1)
   if held[i] is not None:assert values[2*i+1]==held[i],(cycle,i,'MAC data');data_checks+=1
   if item['W']==128 and valid and held[i]>>256:bit256_seen=True
 assert bit256_seen
 report={'status':'passed','cycles':len(rows),'configurations':20,'valid_checks':valid_checks,'data_checks':data_checks,'bit256_carry_observed':True,'reset':'not in this MAC fixture; covered by 88 Mul configurations','L':3,'II':1};(out/'functional.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':
 action=sys.argv[1]
 if action=='prepare':prepare(Path(sys.argv[2]).resolve(),Path(sys.argv[3]).resolve())
 elif action=='build':raise SystemExit(subprocess.call(json.loads(Path(sys.argv[2]).read_text())))
 elif action=='run':
  p=Path(sys.argv[2]);f=(p/'rtl-run.log').open('w');raise SystemExit(subprocess.call([str(p/'obj/VMulMAC'),str(p/'vectors.txt')],stdout=f))
 elif action=='verify':verify(Path(sys.argv[2]))
