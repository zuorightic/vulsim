"""Parameterized step6 fixed-latency source, requests and validation fixtures.

The 43 formal/holdout definitions remain cases_v2. Extra nonpower/shared/single
operation fixtures are diagnostics and never enter its 688-row denominator.
"""
import hashlib,json,re
from pathlib import Path
from .case_generator import case_spec,generate_manifest,build_graph,kernel_body
from .contracts import ROOT,fixed_latency
from .reference import evaluate_spec,udivrem

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def port_name(name):return 'sel' if name=='select' else name
def write(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2)+'\n')
def reset_inputs(case):
 values={}
 for name,w in case['inputs'].items():
  if case['width'] is None:values[name]={'a':0x7f800000,'b':0,'c':0x3f800000,'bypass':0x7f812345,'select':0}.get(name,0)
  elif name in ('d','e'):values[name]=0
  elif name=='s':values[name]=(1<<w)-1
  elif w==1:values[name]=1
  else:values[name]=((1<<(w-1))|((1<<65) if w>65 else 0)|0x35)&((1<<w)-1)
 return values
def expected(case,inputs):
 if case.get('diagnostic') in ('shared_divrem','single_div','single_mod'):
  q,r=udivrem(inputs['a'],inputs['d'],case['width']);return {n:(q if n=='q' else r) for n in case['outputs']}
 return evaluate_spec(case,inputs)
def logic_source(case,name):
 declarations=[]
 for direction in ('inputs','outputs'):
  for port,w in case[direction].items():
   rtl_port=port_name(port);declarations += [f'{"bool" if w==1 else f"Int<{w}>"} {rtl_port};',f'#pragma {"input" if direction=="inputs" else "output"}_port {rtl_port}']
 if case.get('diagnostic')=='shared_divrem':
  w=case['width'];body=f'Int<{2*w}> packed=vularith::UDivRemShared(a,d); q=Int<{w}>(packed);r=Int<{w}>(packed>>{w}u);'
 elif case.get('diagnostic') in ('single_div','single_mod'):
  w=case['width'];port=next(iter(case['outputs']));op='/' if port=='q' else '%';zero='~Int<'+str(w)+'>(0)' if port=='q' else 'a'
  body=f'bool zero=d==Int<{w}>(0);Int<{w}> safe=zero?Int<{w}>(1):d;{port}=zero?{zero}:Int<{w}>(a{op}safe);'
 else:
  body=kernel_body(build_graph(case['family'],case['width']))
  for port in case['inputs']:body=body.replace('value.'+port,port)
  for port in case['outputs']:body=body.replace('result.'+port,port)
 body=re.sub(r'\bselect\b','sel',body)
 return '#include <fixint.hpp>\n#include <arithmetic.hpp>\n#include <unsigned_divrem.hpp>\nbool iv,ov;\n#pragma input_port iv\n#pragma output_port ov\n'+'\n'.join(declarations)+f'\nvoid {name}(){{\n{body}\n}}\n'
def prepare(out,root=ROOT):
 out=Path(out);out.mkdir(parents=True,exist_ok=False);root=Path(root)
 formal=generate_manifest()['cases'];extra=[]
 for w in (12,24,48,96):
  for family in ('MUL','MAC','DOT2','UDR','DIVSEL','MIX','H_M','H_D'):
   case=case_spec(family,w);case['diagnostic']='nonpower';extra.append(case)
 for w in (8,16,32,64,128):
  for kind in ('shared_divrem','single_div','single_mod'):
   outputs={'q':w,'r':w} if kind=='shared_divrem' else {'q' if kind=='single_div' else 'r':w}
   extra.append({'id':kind+'_'+str(w),'family':'UDR','width':w,'inputs':{'a':w,'d':w},'outputs':outputs,'diagnostic':kind})
 jobs=[];items=[]
 for case in formal+extra:
  for group in ('A','B','C') if case in formal else ('C',):
   name=case['id']+'_'+group;L=1 if group=='A' else (fixed_latency(case) if case in formal or case.get('diagnostic')=='nonpower' else 2)
   # Single/shared diagnostic latency is deliberately explicit, not an override
   # of any formal-case L or a response to a physical result.
   request={'version':'arithmetic-request-v1','target_platform':'asap7','platform_profile':str(root/'experiments/arithmetic_dse/configs/platforms/asap7.json'),'platform_profile_sha256':sha(root/'experiments/arithmetic_dse/configs/platforms/asap7.json'),'cost_mode':'fixed','fixed_cost_table':str(root/'experiments/arithmetic_dse/configs/fixed_op_width_v1.json'),'fixed_cost_table_sha256':sha(root/'experiments/arithmetic_dse/configs/fixed_op_width_v1.json'),'model_bundle':'','model_bundle_sha256':'','candidate_policy':'mul-candidates-v1' if group=='C' else 'core-original-v1','semantic_profile':'arithmetic-semantics-v2','L':L,'II':1,'target_period_ps':1500,'template_parameters':{}}
   reset=reset_inputs(case);reset_output=expected(case,reset)
   limbs=lambda n,w:[(n>>(64*i))&((1<<64)-1) for i in range((w+63)//64)]
   directory=out/name;directory.mkdir();source=directory/'source.cpp';source.write_text(logic_source(case,name));write(directory/'request.json',request)
   jobs.append({'name':name,'source':str(source),'request':str(directory/'request.json'),'reset':{'iv':[0],**{port_name(p):limbs(v,case['inputs'][p]) for p,v in reset.items()}},'expected_reset':{'ov':[0],**{p:limbs(v,case['outputs'][p]) for p,v in reset_output.items()}}})
   items.append({'name':name,'case':case,'group':group,'L':L,'II':1,'reset_inputs':reset,'reset_outputs':reset_output,'request':str(directory/'request.json'),'source_sha256':sha(source)})
 write(out/'jobs.json',jobs);write(out/'items.json',items)
 return {'formal_cases':43,'diagnostic_cases':len(extra),'implementations':len(items),'D':'same graph/request interface reserved; no inference before step7','PPA_calls':0}
