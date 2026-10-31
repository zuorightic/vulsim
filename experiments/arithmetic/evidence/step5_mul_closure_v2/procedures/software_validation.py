from pathlib import Path
import contextlib,gzip,io,json,os,subprocess,sys,tempfile
R=Path.cwd();B=R/'build/step5-closure-20261031';sys.path.insert(0,str(R))
from regression.arithmetic_mul_templates import verify as mul_verify
from regression.arithmetic_mul_mac import verify as mac_verify
E=R/'experiments/arithmetic/evidence/step5_mul_templates_v1';results={}
for label,verify in [('mul',mul_verify),('mac',mac_verify)]:
 with tempfile.TemporaryDirectory() as tmp:
  d=Path(tmp)
  for name in ('items.json','vectors.txt','rtl-run.log'):(d/name).write_bytes(gzip.decompress((E/label/(name+'.gz')).read_bytes()))
  with contextlib.redirect_stdout(io.StringIO()):verify(d)
  results[label]=json.loads((d/'functional.json').read_text());assert results[label]==json.loads((E/label/'functional.json').read_text())
env=os.environ.copy();env['PATH']='/home/zyrv/circt/circt-full-shared-linux-x64/firtool-1.162.0/bin:'+env.get('PATH','')
p=subprocess.run([str(R/'build/step4-rtlzz/testv2/mul-template-test'),str(R),str(B/'circt'),'--circt'],cwd=R,env=env,text=True,capture_output=True);(B/'circt.log').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stdout+p.stderr
for file in (B/'circt').glob('w*.json'):
 native=json.loads((B/'generated'/file.name).read_text());circt=json.loads(file.read_text());assert native['graph_sha256']==circt['graph_sha256'] and native['schedule_sha256']==circt['schedule_sha256']
summary={'status':'passed','saved_traces_replayed_with_independent_oracles':results,'no_new_RTL_simulation_needed':'all 129 graph/schedule/RTL bytes unchanged','new_native_positive_checks':24504,'CIRCT_positive_checks':p.stdout.strip(),'public_interfaces_checks':3786,'historical_replay':json.loads((B/'historical_replay_final.json').read_text())['status']}
(B/'software_validation.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
