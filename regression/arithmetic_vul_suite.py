"""Public VUL PIPELINE fixtures and independent cycle/reset trace replay."""
from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.arithmetic_dse.case_generator import generate_manifest,source_files,validation_vectors,vul_type
from experiments.arithmetic_dse.whole_graph import reset_inputs,expected,logic_source,port_name
from experiments.arithmetic_dse.contracts import fixed_latency

def integer_expr(n,w):
 if w==1:return 'true' if n else 'false'
 if w<=64:return f'Int<{w}>({n}ull)'
 words=[(n>>(64*k))&((1<<64)-1) for k in range((w+63)//64)];result=f'Int<64>({words[-1]}ull)'
 for value in reversed(words[:-1]):result=f'Cat({result},Int<64>({value}ull))'
 return f'Int<{w}>({result})'

def prepare(fixtures,out):
 out=Path(out);out.mkdir(parents=True,exist_ok=False);items=json.loads((Path(fixtures)/'items.json').read_text());items={x['case']['id']:x for x in items if x['group']=='C' and not x['case'].get('diagnostic')};result=[]
 for case in generate_manifest()['cases']:
  directory=out/case['id'];directory.mkdir();L=fixed_latency(case);reset=reset_inputs(case)
  (directory/'header.uh').write_text(source_files(case)['header.uh']+'#include <arithmetic.hpp>\n')
  params=[f'IREG({port_name(n)},{vul_type(w)}){{{port_name(n)}={integer_expr(reset[n],w)};}}' for n,w in case['inputs'].items()]+['IVALID(iv)']+[f'OREG({n},{vul_type(w)})' for n,w in case['outputs'].items()]+['OVALID(ov)']
  body=logic_source(case,'top').split('void top(){\n',1)[1].rsplit('}',1)[0]
  top='#include "header.uh"\nINTERFACE(){SERVICE(push,ARG(CaseInput) value,ARG(bool) v);QUERY(result,CaseOutput);QUERY(valid,bool);}\nUSE_VERSION(main);VERSION(main){\n'+f'PIPELINE(core,{L},'+','.join(params)+'){\n'+body+'}\nSERVICE(push,ARG(CaseInput) value,ARG(bool) v){'+''.join(f'{port_name(n)}.setnext(value.{n});' for n in case['inputs'])+'iv.setnext(v);}'+'\nQUERY(result,CaseOutput){return CaseOutput{'+','.join(case['outputs'])+'};}QUERY(valid,bool){return ov;}\n}\n'
  (directory/'Top.vul').write_text(top)
  rows=validation_vectors(case,random_count=64)+[{n:0 for n in case['inputs']}]*5
  vectors=[{'inputs':row,'iv':int(i<32 or i%7 not in (1,2)) if i<len(rows)-5 else 0,'reset':i in (0,1,31,90)} for i,row in enumerate(rows)]
  (directory/'vectors.json').write_text(json.dumps(vectors,indent=2)+'\n');(directory/'vectors.txt').write_text(str(len(vectors))+'\n'+''.join(' '.join(f'{row["inputs"][n]:x}' for n in case['inputs'])+f' {row["iv"]:x} {int(row["reset"]):x}\n' for row in vectors))
  driver='''#include <run.hpp>
#include <cstdlib>
#include <cstdio>
#include <fstream>
TOP("Top.vul");PROJECT(".");REQUEST(push,ARG(CaseInput) value,ARG(bool) v);QUERY(result,CaseOutput);QUERY(valid,bool);
GLOBAL(){
template<uint32_t W> Int<W> hexread(std::istream& s){std::string text;s>>text;Int<W> r(0);for(unsigned i=0;i<text.size();++i){unsigned digit=text[text.size()-1-i]>='a'?text[text.size()-1-i]-'a'+10:text[text.size()-1-i]-'0';for(unsigned k=0;k<4;++k)if(i*4+k<W){if constexpr(W==1)r=(digit>>k)&1;else r.template pick<1>(i*4+k)=(digit>>k)&1;}}return r;}
template<uint32_t W>void hexprint(Int<W> v){auto words=v.get_data();std::putchar(' ');for(int i=(W+3)/4-1;i>=0;--i){unsigned digit=0;for(unsigned k=0;k<4;++k)if(i*4+k<W&&((words[(i*4+k)/64]>>((i*4+k)%64))&1))digit|=1u<<k;std::putchar("0123456789abcdef"[digit]);}}
void print_result(){auto r=result();
'''+''.join(f'hexprint(Int<{w}>(r.{n}));' for n,w in case['outputs'].items())+'''std::putchar('\n');}}
SIMULATION(){
'''+f'std::ifstream stream("{directory.resolve()/"vectors.txt"}");unsigned count;stream>>count;for(unsigned i=0;i<count;++i){{CaseInput in;'+''.join(f'in.{n}=hexread<{w}>(stream)'+('.to<bool>()' if w==1 else '')+';' for n,w in case['inputs'].items())+'''unsigned v,reset;stream>>std::hex>>v>>reset;if(reset){sim_reset();std::printf("RESET %u %u",i,unsigned(valid()));print_result();}push(in,bool(v));sim_nextcycle();std::printf("ROW %u %u",i,unsigned(valid()));print_result();}std::printf("PUBLIC VUL PASS rows=%u\n",count);}
'''
  # Keep an actual escaped newline in the generated C++ character literal.
  driver=driver.replace("std::putchar('\n')","std::putchar('\\n')")
  driver=driver.replace('PUBLIC VUL PASS rows=%u\n','PUBLIC VUL PASS rows=%u\\n')
  (directory/'Main.utb').write_text(driver);request=Path(items[case['id']]['request']);(directory/'request.json').write_bytes(request.read_bytes());result.append({'case':case,'L':L,'directory':str(directory.resolve()),'reset_inputs':reset,'reset_outputs':expected(case,reset)})
 (out/'items.json').write_text(json.dumps(result,indent=2)+'\n');print({'public_VUL_cases':len(result)})

def verify(out,logs,cases=None):
 out=Path(out);logs=Path(logs);items=json.loads((out/'items.json').read_text());reports=[]
 if cases:items=[x for x in items if x['case']['id'] in cases]
 for item in items:
  case=item['case'];vectors=json.loads((Path(item['directory'])/'vectors.json').read_text());lines=(logs/(case['id']+'.log')).read_text().splitlines();rows={};resets={}
  for line in lines:
   if line.startswith(('ROW ','RESET ')):
    tag,i,v,*values=line.split();target=rows if tag=='ROW' else resets;assert int(i) not in target;target[int(i)]=(int(v),[int(x,16) for x in values])
  assert len(rows)==len(vectors),(case['id'],'missing public rows',len(rows),len(vectors));history=[];held=list(item['reset_outputs'].values());valid_checks=data_checks=reset_checks=0
  for i,vector in enumerate(vectors):
   if vector['reset']:
    history=[];held=list(item['reset_outputs'].values());assert resets[i]==(0,held),(case['id'],i,'public reset');reset_checks+=len(held)
   history.append(vector);source=i  # callback/query adds the existing IREG acceptance edge
   valid=bool(len(history)>item['L'] and history[-item['L']-1]['iv'])
   if valid:held=list(expected(case,history[-item['L']-1]['inputs']).values());data_checks+=len(held)
   assert rows[i]==(int(valid),held),(case['id'],i,rows[i],(int(valid),held));valid_checks+=1
  reports.append({'case':case['id'],'L':item['L'],'query_observation':'after service push+sim_nextcycle; source history[-L-1], inherited IREG interface edge separately accounted','cycles':len(vectors),'valid_checks':valid_checks,'data_checks':data_checks,'reset_checks':reset_checks})
 result={'status':'passed','public_VUL_cases':len(reports),'reports':reports,'new_physical_calls':0};(out/'functional.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({**result,'reports':'per-case in functional.json'},indent=2))
if __name__=='__main__':
 if sys.argv[1]=='prepare':prepare(*map(Path,sys.argv[2:4]))
 elif sys.argv[1]=='verify':verify(*map(Path,sys.argv[2:4]),cases=sys.argv[4:])
