from pathlib import Path
import json,os,subprocess
R=Path.cwd();B=R/'build/step4-interfaces-20261030';out=B/'baselines';out.mkdir(exist_ok=False)
env=os.environ.copy();env['PATH']='/home/zyrv/circt/circt-full-shared-linux-x64/firtool-1.162.0/bin:'+env.get('PATH','');results=[]
for flag,names in [('0',['pipeline-test']),('1',['pipeline-test','pipeline-reset-test','pipeline-valid-test','arithmetic-region-test'])]:
 env['VUL_REGRESSION_CIRCT']=flag
 for name in names:
  cmd=[str(R/'build/step4-rtlzz/testv2'/name)]
  if name=='arithmetic-region-test':cmd += [str(R/'vullib'),str(out/'regions')]
  run=subprocess.run(cmd,cwd=R/'rtlzz',env=env,text=True,capture_output=True)
  stem=name+'-'+flag;(out/(stem+'.stdout')).write_text(run.stdout);(out/(stem+'.stderr')).write_text(run.stderr)
  if run.returncode:raise RuntimeError(stem+': '+run.stdout[-1000:]+run.stderr[-1000:])
  if flag=='0':assert 'SKIP CIRCT checks' in run.stdout
  results.append({'name':name,'CIRCT_enabled':flag=='1','exit_code':run.returncode,'output':run.stdout[-1200:]})
report={'status':'passed','checks':results,'new_PPA_calls':0};(out/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
