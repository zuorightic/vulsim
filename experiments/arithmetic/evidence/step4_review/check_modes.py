from pathlib import Path
import json,os,shlex,shutil,subprocess,sys,time
root=Path.cwd();base=root/'build/step4-review';base.mkdir(parents=True,exist_ok=True)
real=Path('/home/zyrv/circt/circt-full-shared-linux-x64/firtool-1.162.0/bin/circt-opt')
spy=base/'circt-bin';spy.mkdir(exist_ok=True)
marker=base/'circt-invocations.log'
wrapper=spy/'circt-opt'
wrapper.write_text('#!/bin/sh\nprintf "invoked\\n" >> '+shlex.quote(str(marker))+'\nexec '+shlex.quote(str(real))+' "$@"\n');wrapper.chmod(0o755)
records=[]
for name,path,flag in [('absent-disabled','/usr/bin:/bin','0'),('present-disabled',str(spy)+':/usr/bin:/bin','0'),('present-enabled',str(spy)+':/usr/bin:/bin','1')]:
 env=os.environ.copy();env['PATH']=path;env['VUL_REGRESSION_CIRCT']=flag
 out=base/name;out.mkdir(exist_ok=True)
 before=len(marker.read_text().splitlines()) if marker.exists() else 0
 command=[sys.executable,str(root/'regression/arithmetic_regions.py'),'--skip-build','--output',str(out)]
 if flag=='1':command+=['--softfloat','/home/zyrv/temp/rv64-archsem软著/softfloat']
 start=time.monotonic()
 with (out/'run.log').open('w') as log:p=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT)
 after=len(marker.read_text().splitlines()) if marker.exists() else 0
 record={'scenario':name,'CIRCT_enabled':flag=='1','tool_on_PATH':shutil.which('circt-opt',path=path),
         'command':command,'exit_code':p.returncode,'walltime_s':time.monotonic()-start,'observed_CIRCT_invocations':after-before}
 records.append(record)
 if p.returncode:raise RuntimeError((record,(out/'run.log').read_text()[-3500:]))
 report=json.loads((out/'report.json').read_text())
 assert report['region_checks']=='PASS arithmetic regions checks=55'
 assert report['host_vectors']==20484 and report['RTL_combinational_output_checks']==245808
 for r in report['VUL_end_to_end']:assert r['status']==('skipped' if flag=='0' and r['backend']=='circt' else 'passed')
 assert (after-before>0) if flag=='1' else (after==before)
 print(json.dumps(record),flush=True)
(base/'mode_matrix.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
# An enabled run without the tool must fail clearly before builds/tests.
env=os.environ.copy();env['PATH']='/usr/bin:/bin';env['VUL_REGRESSION_CIRCT']='1'
p=subprocess.run([sys.executable,'regression/arithmetic_regions.py','--skip-build','--output',str(base/'absent-enabled')],env=env,text=True,capture_output=True)
assert p.returncode!=0 and 'CIRCT checks are enabled but circt-opt is not on PATH' in p.stderr
(base/'missing_tool.json').write_text(json.dumps({'exit_code':p.returncode,'stderr':p.stderr},indent=2)+'\n')
# A direct --circt request must also respect the explicit disable policy.
env['VUL_REGRESSION_CIRCT']='0';direct=[]
for name in ['pipeline-test','pipeline-reset-test','pipeline-valid-test']:
 command=[str(root/'build/step4-rtlzz/testv2'/name),'--circt']
 p=subprocess.run(command,cwd=root/'rtlzz',env=env,text=True,capture_output=True)
 assert p.returncode==0 and 'SKIP CIRCT' in p.stdout,(name,p.stdout,p.stderr)
 direct.append({'command':command,'exit_code':p.returncode,'stdout':p.stdout})
(base/'direct_disabled.json').write_text(json.dumps(direct,indent=2)+'\n')
print('PASS three CIRCT modes, enabled/missing-tool diagnosis, and direct C++ disabled policy',flush=True)
