from pathlib import Path
import json,shutil,sys
R=Path.cwd();sys.path.insert(0,str(R));B=R/'build/step6-integration-20261031';out=B/'public-combined';out.mkdir(exist_ok=False);items=[];bindings=[]
from regression.arithmetic_vul_suite import verify
for k,item in enumerate(json.loads((B/'vul-v5/items.json').read_text())):
 source=B/('public-final' if k<20 else 'public-remaining');fixture=B/('vul-v4' if k<20 else 'vul-v5')/item['case']['id'];item['directory']=str(fixture);items.append(item);path=source/(item['case']['id']+'.log');shutil.copy2(path,out/path.name);bindings.append({'case':item['case']['id'],'actual_log':str(path),'actual_fixture':str(fixture)})
(out/'items.json').write_text(json.dumps(items,indent=2)+'\n');(out/'execution_bindings.json').write_text(json.dumps(bindings,indent=2)+'\n');verify(out,out)
