"""Charge each public VUL generation/build/run leaf to the shared budget."""
import argparse,json,os,sys
from pathlib import Path
from .budget import Ledger,usage
from .processes import run_command
from .contracts import ROOT

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--sources',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--cases',nargs='+');p.add_argument('--backend',choices=('native','software','circt'),default='native');a=p.parse_args()
 out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);source=a.sources.resolve();items=json.loads((source/'items.json').read_text());names=a.cases or [x['case']['id'] for x in items]
 if len(names)!=len(set(names)) or set(names)-{x['case']['id'] for x in items}:raise ValueError('invalid public VUL case list')
 ledger=Ledger();before=json.loads(ledger.path.read_text());(out/'usage-before.json').write_text(json.dumps(before,indent=2)+'\n');commands=[];env=os.environ.copy();env.update(MAKEFLAGS='-j2',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
 if a.backend=='circt':env['PATH']=str(ROOT/'build/step4-review/circt-bin')+os.pathsep+env['PATH']
 for name in names:
  directory=source/name;target=out/name;tool='vulsimgen' if a.backend=='software' else 'vulrtlgen';cmd=[str(ROOT/'build'/tool),'-m',str(directory/'Main.utb'),'-f','-o',str(target)]
  if a.backend!='software':cmd+=['--arithmetic-request',str(directory/'request.json')]
  if a.backend=='circt':cmd+=['--circt']
  for stage,command,timeout in [('generate',cmd,180),('run',['bash',str(target/'run.sh')],300)]:
   stem=name+'-'+stage;print(a.backend,stem,flush=True);reservation=ledger.reserve(None,timeout,2,'step6_public_VUL_validation',command,out/stem,context={'target_platform':'common','admission_id':'step6-public-software-v1','task_id':a.backend+'-'+stem,'model_version':'not_implemented_step7'})
   record=run_command(command,out,stem,timeout,env,8192,cpu_limit_s=reservation['CPU_time_s']);ledger.finish(reservation,record);commands.append({**record,'reservation_id':reservation['id']});(out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
   if record['exit_code']:print(Path(record['log']).read_text()[-5000:],flush=True);return record['exit_code']
   if stage=='run':(out/(name+'.log')).write_bytes(Path(record['log']).read_bytes())
 after=json.loads(ledger.path.read_text());report={'status':'passed','cases':names,'backend':a.backend,'new_usage':usage(after['entries'][len(before['entries']):]),'physical_calls':0};(out/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
