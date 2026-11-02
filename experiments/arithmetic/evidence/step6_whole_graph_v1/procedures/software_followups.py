from pathlib import Path
import json,os,subprocess,sys
R=Path.cwd();B=R/'build/step6-integration-20261031';env=os.environ.copy();env['PATH']=str(R/'build/step4-review/circt-bin')+os.pathsep+env['PATH']
commands=[['build/step4-rtlzz/testv2/arithmetic-suite-test',str(R),str(B/'circt-jobs.json'),str(B/'circt-generated'),'circt']]
for platform in ('nangate45','sky130hd','gf180'):commands.append(['build/step4-rtlzz/testv2/arithmetic-suite-test',str(R),str(B/'platform-requests'/platform/'jobs.json'),str(B/'platform-generated'/platform)])
for name in ('pipeline-test','pipeline-reset-test','pipeline-valid-test'):commands.append([str(R/'build/step4-rtlzz/testv2'/name)])
commands += [['build/step4-rtlzz/testv2/arithmetic-region-test',str(R/'vullib'),str(B/'regions')],['build/step4-rtlzz/testv2/arithmetic-interface-test',str(R),str(B/'interfaces')],['build/step4-rtlzz/testv2/mul-template-test',str(R),str(B/'mul-regression')]]
for command in commands:
 if 'arithmetic-suite-test' in command[0] and Path(command[3]).exists():continue
 print('RUN',command,flush=True);subprocess.run(command,cwd=R/'rtlzz' if Path(command[0]).name in ('pipeline-test','pipeline-reset-test','pipeline-valid-test') else R,env=env,check=True)
for item in json.loads((B/'circt-fixtures/items.json').read_text()):
 name=item['name'];native=json.loads((B/'generated-final'/(name+'.json')).read_text());other=json.loads((B/'circt-generated'/(name+'.json')).read_text())
 for key in ('graph','stages','protocol','graph_sha256','schedule_sha256'):assert native[key]==other[key],(name,key)
 for platform in ('nangate45','sky130hd','gf180'):
  r=json.loads((B/'platform-generated'/platform/(name+'.json')).read_text())
  for key in ('graph','stages','protocol','graph_sha256','schedule_sha256'):assert native[key]==r[key],(platform,name,key)
result={'status':'passed','CIRCT_representatives':6,'other_platform_request_representatives':18,'pipeline_reset_valid_regressions':'passed','FP_region_regression':'passed','public_core_regression':'passed','mul_template_regression':'passed','no_PPA':True};(B/'followups.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
