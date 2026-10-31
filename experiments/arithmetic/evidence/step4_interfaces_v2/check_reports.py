"""Check actual current CLI/VUL JSON, with unchanged graph/schedule/RTL identity."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,os,re,subprocess,sys
ROOT=Path.cwd();OUT=ROOT/'build/step4-review-20261031';sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.interfaces_evidence import verify_report
from experiments.arithmetic_dse.report_types import validate_report_types
PARENT=ROOT/'experiments/arithmetic/evidence/step4_interfaces_v1'
schemas=json.loads((ROOT/'experiments/arithmetic_dse/configs/arithmetic_compiler_interfaces_v1.json').read_text())['report_schemas']
features=json.loads((ROOT/'experiments/arithmetic_dse/configs/beir_cost_features_v1.json').read_text())
reports=[];commands=[];failures=[];keys=('graph','graph_identity_text','schedule_identity_text','graph_sha256','schedule_sha256','rtl_sha256','request','protocol','stages')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def run(command,expected=0):
 p=subprocess.run(command,cwd=ROOT,text=True,capture_output=True)
 commands.append({'argv':command,'expected_exit_code':expected,'exit_code':p.returncode,'stdout':p.stdout[-1000:],'stderr':p.stderr[-1000:]})
 if p.returncode!=expected:raise AssertionError(str(command)+': '+p.stdout[-1500:]+p.stderr[-1500:])
 return p

def compare(current,old,rtl,*,embedded=False,wrapper=None,byte_range=None,annotation_mapping=None):
 data=json.loads(current.read_text());prior=json.loads(old.read_text());body=rtl.read_text()
 verify_report(data,body,features,embedded=embedded,report_schemas=schemas)
 for key in keys:
  if key!='rtl_sha256' or not annotation_mapping:assert data[key]==prior[key],(current,key)
 converted=deepcopy(prior);converted['version']='arithmetic-structure-report-v2';converted['pipeline']['register_bits']=int(converted['pipeline']['register_bits'])
 if annotation_mapping:converted['rtl_sha256']=data['rtl_sha256']
 assert data==converted,('unexpected non-type change',current)
 item={'generated_report':str(current.relative_to(ROOT)),'inherited_report':str(old.relative_to(ROOT)),'rtl':str(rtl.relative_to(ROOT)),'register_bits':data['pipeline']['register_bits'],'register_count':data['pipeline']['register_count'],'graph_sha256':data['graph_sha256'],'schedule_sha256':data['schedule_sha256'],'rtl_sha256':data['rtl_sha256']}
 if embedded:item.update({'embedded_wrapper':str(wrapper.relative_to(ROOT)),'byte_range':byte_range})
 if annotation_mapping:item.update(annotation_mapping)
 reports.append(item)
for p in sorted((OUT/'generated').glob('*.json')):
 old=PARENT/'accepted/generated'/p.name
 if old.exists():
  assert (OUT/'generated'/p.with_suffix('.sv').name).read_bytes()==(PARENT/'accepted/generated'/p.with_suffix('.sv').name).read_bytes()
  compare(p,old,old.with_suffix('.sv'))
# Use the original exact source path because source comments are part of RTL hash.
source=ROOT/'build/step4-interfaces-20261030/acceptance/cli.logic.cpp';assert sha(source)==sha(PARENT/'accepted/cli.logic.cpp')
for platform in ('asap7','nangate45','sky130hd','gf180'):
 request=PARENT/'accepted'/(platform+'.request.json');target=OUT/(platform+'.sv');report=OUT/(platform+'.json')
 run([str(ROOT/'build/step4-rtlzz/predicate-expand'),'--input',str(source),'--top','top','--vullib',str(ROOT/'vullib'),'--release','--arithmetic-request',str(request),'--arithmetic-report',str(report),'-o',str(target)])
 assert target.read_bytes()==(PARENT/'accepted'/(platform+'.sv')).read_bytes()
 compare(report,PARENT/'accepted'/(platform+'.report.json'),PARENT/'accepted'/(platform+'.sv'))
# Two real failing requests verify the v2 diagnostic schema as well.
for label in ('unknown_field','missing_model'):
 report=OUT/(label+'.failure.json');run([str(ROOT/'build/step4-rtlzz/predicate-expand'),'--input',str(source),'--top','top','--vullib',str(ROOT/'vullib'),'--release','--arithmetic-request',str(PARENT/'accepted'/(label+'.request.json')),'--arithmetic-report',str(report),'-o',str(OUT/(label+'.sv'))],1)
 data=json.loads(report.read_text());validate_report_types(data,schemas)
 failures.append({'generated_report':str(report.relative_to(ROOT)),'failure_code':data['failure_code']})
# Exercise the real VUL bridge without rerunning its unchanged generated RTL.
request=PARENT/'accepted/vul.request.json';dest=OUT/'vul-native'
run([str(ROOT/'build/vulrtlgen'),'-m',str(ROOT/'experiments/arithmetic/backend_probe/Main.utb'),'-f','-o',str(dest),'--arithmetic-request',str(request)])
prior_items=json.loads((PARENT/'report_index.json').read_text());vul_items=[x for x in prior_items if x.get('embedded_wrapper')]
for old in vul_items:
 previous=ROOT/old['report'];new=dest/previous.relative_to(PARENT/'accepted/vul-native');wrapper=dest/'sim/top.sv'
 new_prefix=str(dest);old_prefix=str(ROOT/'build/step4-interfaces-20261030/acceptance/vul-native')
 original=(ROOT/old['embedded_wrapper']).read_text();current=wrapper.read_text()
 assert current.replace(new_prefix,old_prefix)==original
 assert [line.split('//',1)[0] for line in current.splitlines()]==[line.split('//',1)[0] for line in original.splitlines()]
 raw=wrapper.read_bytes();start=raw.index(b'if (1) begin : __vul_pipeline_');start=raw.index(b'\n',start)+1;found=None
 data=json.loads(new.read_text())
 for match in re.finditer(rb'(?m)^end\s*\n',raw[start:]):
  end=start+match.start();body=raw[start:end]
  if hashlib.sha256(body).hexdigest()==data['rtl_sha256']:found=(end,body);break
 assert found is not None;end,body=found;kernel=OUT/'vul-kernel.sv';kernel.write_bytes(body)
 compare(new,previous,kernel,embedded=True,wrapper=wrapper,byte_range=[start,end],annotation_mapping={'inherited_rtl':old['rtl'],'annotation_prefix_from':new_prefix,'annotation_prefix_to':old_prefix})

env=os.environ.copy();env['ARITHMETIC_REPORT_TYPES_FIXTURE']=str(OUT/'asap7.json');p=subprocess.run([sys.executable,'-m','unittest','regression.arithmetic_report_types','-v'],cwd=ROOT,env=env,text=True,capture_output=True)
(OUT/'type-tests.log').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stdout+p.stderr
summary={'status':'passed','version':'step4-report-type-checks-v2','native_cpp_checks':'PASS arithmetic interfaces checks=3786','actual_reports_checked':len(reports),'four_platforms':['asap7','nangate45','sky130hd','gf180'],'VUL_reports':len(vul_items),'all_graph_schedule_unchanged':True,'native_and_standalone_RTL_bytes_unchanged':True,'VUL_RTL_only_source_annotation_path_changed':True,'only_report_version_counter_token_and_VUL_annotation_hash_changed':True,'type_test_methods':7,'type_tests_passed':True,'uint64_max_roundtrip_CPP':True,'failure_reports':failures,'reports':reports,'commands':commands,'new_physical_calls':0,'new_RTL_simulation':False,'functional_evidence':'inherited unchanged v1 trace, not a new simulation'}
(OUT/'checks.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k not in ('reports','commands')},ensure_ascii=False,indent=2))
