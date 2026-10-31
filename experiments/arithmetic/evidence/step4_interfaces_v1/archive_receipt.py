"""Build the step4 successor archive without writing any prior evidence."""
from pathlib import Path
from datetime import datetime,timezone
import gzip,hashlib,json,re,shutil,subprocess,sys
R=Path.cwd();sys.path.insert(0,str(R))
from experiments.arithmetic_dse.budget import usage,cpu_seconds
B=R/'build/step4-interfaces-20261030';A=B/'acceptance';E=R/'experiments/arithmetic/evidence/step4_interfaces_v1';F=R/'experiments/arithmetic/arithmetic_interfaces_freeze_v1.json';P=R/'experiments/arithmetic/backend_freeze_v7.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:str(p.relative_to(R))
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def copy(p,q):
 if p.is_file():q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
def compress(p,q):
 if p.is_file():q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(gzip.compress(p.read_bytes(),mtime=0))
E.mkdir(parents=True,exist_ok=True);before=json.loads((B/'usage-before.json').read_text());after=json.loads((R/'experiments/arithmetic/backend_usage.json').read_text());assert after['entries'][:len(before['entries'])]==before['entries'];extra=after['entries'][len(before['entries']):]
assert not usage(after['entries'])['pending'] and all(e['stage'] is None for e in extra)
copy(B/'usage-before.json',E/'usage_before.json');copy(R/'experiments/arithmetic/backend_usage.json',E/'usage_after.json')
reports=[]
for folder in ('generated','circt-generated'):
 for source in sorted((A/folder).glob('*')):
  if source.suffix in ('.json','.sv','.txt'):copy(source,E/'accepted'/folder/source.name)
 for name in [*(f'mul{w}' for w in (8,16,32,64,128,12,24,48,96)),'mixed_fp']:
  if (A/folder/(name+'.json')).exists():reports.append({'report':rel(E/'accepted'/folder/(name+'.json')),'rtl':rel(E/'accepted'/folder/(name+'.sv'))})
for source in A.glob('*.json'):copy(source,E/'accepted'/source.name)
for source in A.glob('*.sv'):copy(source,E/'accepted'/source.name)
for source in A.glob('*.cpp'):copy(source,E/'accepted'/source.name)
for name in ('vectors.txt','rtl-run.log'):compress(A/name,E/'accepted'/(name+'.gz'))
for platform in ('asap7','nangate45','sky130hd','gf180'):
 copy(A/(platform+'.sv'),E/'accepted'/(platform+'.sv'));reports.append({'report':rel(E/'accepted'/(platform+'.report.json')),'rtl':rel(E/'accepted'/(platform+'.sv'))})
# Preserve actual embedded kernel and its wrapper byte range.
for mode in ('native','software'):
 target=E/'accepted'/('vul-'+mode);source=A/('vul-'+mode)
 for p in source.rglob('*'):
  if p.is_file() and ('obj_dir' not in p.parts) and p.suffix in ('.sv','.cpp','.json','.sh','.hpp','.h','.log','.txt'):
   if p.stat().st_size>1_000_000:compress(p,target/(str(p.relative_to(source))+'.gz'))
   else:copy(p,target/p.relative_to(source))
 copy(A/('vul-'+mode+'-validate.log'),E/'accepted'/('vul-'+mode+'-validate.log'))
for report in sorted((E/'accepted/vul-native').rglob('*.arithmetic.json')):
 data=json.loads(report.read_text());wrapper=E/'accepted/vul-native/sim/top.sv';raw=wrapper.read_bytes();start=raw.index(b'if (1) begin : __vul_pipeline_');start=raw.index(b'\n',start)+1;found=None
 for match in re.finditer(rb'(?m)^end\s*\n',raw[start:]):
  end=start+match.start();body=raw[start:end]
  if hashlib.sha256(body).hexdigest()==data['rtl_sha256']:found=(end,body);break
 if found is None:raise ValueError('cannot identify actual embedded kernel by hash')
 end,body=found;kernel=report.with_suffix('.kernel.sv');kernel.write_bytes(body)
 reports.append({'report':rel(report),'rtl':rel(kernel),'embedded_wrapper':rel(wrapper),'byte_range':[start,end]})
write(E/'report_index.json',reports)
# Keep the successful disabled run separately; actual native RTL is identical.
D=B/'validation-no-circt';copy(D/'regression.json',E/'disabled/regression.json');copy(D/'execution_source_sha256.json',E/'disabled/execution_source_sha256.json');matches=[]
for p in sorted((D/'generated').glob('*.sv')):
 same=sha(p)==sha(A/'generated'/p.name);assert same,p.name;matches.append({'name':p.name,'sha256':sha(p)})
write(E/'disabled/native_RTL_identity.json',{'status':'identical_to_final_acceptance','files':matches,'note':'CIRCT-off full suite executed before a reporting/group-dispatch-only refinement; final native RTL bytes are identical; source variants are retained'})
copy(B/'baselines/results.json',E/'baselines/results.json')
for p in (B/'baselines').glob('*.stdout'):copy(p,E/'baselines'/p.name)
for p in (B/'baselines').glob('*.stderr'):copy(p,E/'baselines'/p.name)
# Every new charge, including development failures and expected rejections.
receipts=[];failed=[]
for entry in extra:
 path=Path(entry['command_record']);record=json.loads(path.read_text());target=E/'commands'/entry['id'];copy(path,target/'command.json');copy(Path(record['gnu_time']),target/'GNU-time.txt');compress(Path(record['log']),target/'log.gz')
 stem=path.name.removesuffix('.command.json');source_manifest=path.with_name(stem+'.sources.json');copy(source_manifest,target/'sources.json')
 expected=stem.startswith('reject-')
 receipts.append({'id':entry['id'],'record':rel(target/'command.json'),'CPU_report':rel(target/'GNU-time.txt'),'log':rel(target/'log.gz'),'expected_rejection':expected,'execution_source_manifest':rel(target/'sources.json') if source_manifest.exists() else None})
 if record['exit_code']!=0:failed.append({'id':entry['id'],'stem':stem,'expected_rejection':expected,'exit_code':record['exit_code'],'source_provenance':'recorded' if source_manifest.exists() else 'development_only; no_source_manifest_at_that_time'})
 assert abs(cpu_seconds(target/'GNU-time.txt')-entry['CPU_time_s'])<1e-8
write(E/'command_index.json',receipts);write(E/'nonzero_commands.json',failed)
# Content-addressed development sources clarify earlier successful/failed variants.
if (B/'source_variants').exists():shutil.copytree(B/'source_variants',E/'execution_source_variants',dirs_exist_ok=True)
# Accepted regression captures all actual compiler sources; archive each exact byte.
for manifest in (A/'execution_source_sha256.json',D/'execution_source_sha256.json'):
 for path,h in json.loads(manifest.read_text()).items():
  target=E/'execution_source_variants'/h
  if target.exists():continue
  p=R/path
  if sha(p)!=h:raise ValueError('missing exact execution source variant: '+path)
  copy(p,target)
write(E/'resources.json',{'new_usage':usage(extra),'cumulative_usage':usage(after['entries']),'new_physical_calls':0,'global_caps_changed':False,'nonzero_leaf_commands':len(failed),'expected_rejections':sum(f['expected_rejection'] for f in failed),'max_sampled_RSS_KiB':max(json.loads((R/r['record']).read_text())['sampled_process_tree_peak_rss_KiB'] for r in receipts)})
# Current source scope includes real emit/reset consumers and the independent oracle.
paths=set()
for base in ('rtlzz/src','experiments/arithmetic_dse'):
 for p in (R/base).rglob('*'):
  if p.is_file() and p.suffix in ('.cpp','.hpp','.h','.py','.json','.md','.sdc','.mk','.tcl','.script') and '__pycache__' not in p.parts:paths.add(rel(p))
paths.update(['CMakeLists.txt','rtlzz/CMakeLists.txt','rtlzz/main/main.cpp','rtlzz/README.md','rtlzz/testv2/arithmetic_interface_test.cpp','rtlzz/testv2/arithmetic_region_test.cpp','rtlzz/testv2/pipeline_test.cpp','rtlzz/testv2/pipeline_reset_test.cpp','rtlzz/testv2/pipeline_valid_test.cpp','src/rtlzz_bridge.hpp','src/rtlzz_bridge.cpp','src/rtlgen.h','src/rtlgen_rtlzz.cpp','tools/vulrtlgen.cpp','regression/arithmetic_interfaces.py','regression/arithmetic_interfaces/rtl_driver.cpp','mission/README.md','mission/lxy-plan-fix.md','experiments/arithmetic/README.md'])
paths.update(rel(p) for p in (R/'vullib').iterdir() if p.is_file())
paths.update(rel(p) for p in (R/'experiments/arithmetic/backend_probe').iterdir() if p.is_file())
for path in paths:copy(R/path,E/'source_v1'/path)
initial=json.loads((B/'before_sha256.json').read_text())
for path,h in initial.items():
 if path=='experiments/arithmetic/backend_usage.json' or not (R/path).is_file() or sha(R/path)==h:continue
 source=B/'previous_source'/path
 if not source.exists():
  prior=json.loads(P.read_text());candidate=R/prior['validated_source_snapshot']/path
  if candidate.exists():source=candidate
 if not source.exists():
  if path.startswith('rtlzz/'):
   data=subprocess.check_output(['git','-C',str(R/'rtlzz'),'show','2d2ae4083655d5322c28ccd90fd897b291cb51b4:'+path[6:]])
  else:data=subprocess.check_output(['git','show','92b0291f48627bf43b55c73ef6fc620dea978677:'+path])
  source=B/'recovered_source'/path;source.parent.mkdir(parents=True,exist_ok=True);source.write_bytes(data)
 if sha(source)!=h:raise ValueError('missing original source snapshot: '+path)
 copy(source,E/'previous_source'/path)
copy(Path(__file__),E/'archive_receipt.py');copy(B/'baseline_checks.py',E/'baseline_checks.py')
for name in ('portable_checks.py','portable_checks.json','static_checks.py','static_checks.json'):copy(B/name,E/name)
prior=json.loads(P.read_text());index=E/'index.json';write(index,{'version':'arithmetic-interfaces-evidence-index-v1','files_sha256':{rel(p):sha(p) for p in sorted(E.rglob('*')) if p.is_file() and p!=index and '__pycache__' not in p.parts and p.suffix!='.pyc'}})
write(F,{'version':'arithmetic-interfaces-freeze-v1','frozen_at':datetime.now(timezone.utc).isoformat(),'files_sha256':{path:sha(R/path) for path in sorted(paths)},'validated_source_snapshot':rel(E/'source_v1'),'historical_freezes':{**prior['historical_freezes'],rel(P):sha(P)},'historical_source_roots':[rel(E/'previous_source'),prior['validated_source_snapshot'],*prior['historical_source_roots']],'retired_active_paths':prior['retired_active_paths'],'evidence_directory':rel(E),'evidence_index':rel(index),'evidence_index_sha256':sha(index),'source_base':'92b0291f48627bf43b55c73ef6fc620dea978677','rtlzz_base':'2d2ae4083655d5322c28ccd90fd897b291cb51b4','planning_reference':'mission/lxy-plan-fix.md 第一章§10.4/§5.1/§5.3；第四章步骤四','scope':'step4 original Mul/atomic FP/request/fixed provider/preflight/report; step5 internal split and step7 model inference pending','new_physical_calls':0,'previous_freezes_modified':False})
print(json.dumps({'source_files':len(paths),'evidence_files':len(json.loads(index.read_text())['files_sha256']),'reports':len(reports),'resources':usage(extra)},indent=2))
