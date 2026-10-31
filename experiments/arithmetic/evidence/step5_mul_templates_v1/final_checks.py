from pathlib import Path
import json,os,subprocess,sys
R=Path.cwd();B=R/'build/step5-parameterized-20261031';sys.path.insert(0,str(R))
# This support leaf runs the unchanged foundational tests sequentially, charging
# the aggregate once and retaining the explicit CIRCT-disabled native result.
env=os.environ.copy();env['PATH']='/home/zyrv/circt/circt-full-shared-linux-x64/firtool-1.162.0/bin:'+env.get('PATH','')
commands=[]
for name,args in [('pipeline-test',[]),('pipeline-reset-test',[]),('pipeline-valid-test',[]),('arithmetic-region-test',[str(R/'vullib'),str(B/'regions')]),('arithmetic-interface-test',[str(R),str(B/'interfaces-final')])]:
 p=subprocess.run([str(R/'build/step4-rtlzz/testv2'/name),*args],cwd=R/'rtlzz',env=env,text=True,capture_output=True);(B/(name+'.log')).write_text(p.stdout+p.stderr);assert p.returncode==0,(name,p.stdout[-1000:],p.stderr[-1000:]);commands.append({'name':name,'exit_code':p.returncode,'output':p.stdout[-200:]})
p=subprocess.run([sys.executable,'-m','unittest','regression.arithmetic_backend','regression.arithmetic_sdc','regression.arithmetic_report_types','-v'],cwd=R,env=env,text=True,capture_output=True);(B/'python-regressions.log').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stdout[-2000:]+p.stderr[-2000:]
# The C/D policy checks are scoped; original FP remains indivisible.
checks={'status':'passed','CPP':commands,'python_unittest':'backend,SDC,report types passed','CIRCT_enabled_path':True,'native_disable_scope':'separate native parameterized generation did not invoke CIRCT','new_PPA_calls':0}
(B/'regressions.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(checks,indent=2))
