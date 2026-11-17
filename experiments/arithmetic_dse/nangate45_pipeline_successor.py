"""Named readout successor, retaining and reusing the already paid synthesis."""
import inspect
from pathlib import Path
import shutil
from .nangate45_samples import read,write,sha
from . import nangate45_pipeline_samples as samples
from . import nangate45_pipeline_collect as collect
from . import nangate45_pipeline_alias as aliases


def prepare(parent,root):
    parent=Path(parent);root=Path(root)
    if root.exists():raise ValueError('preserve successor admission')
    a=samples.verify(parent);p=read(parent/'progress.json')
    if p['completed'] or len(p['errors'])!=1 or p['errors'][0]['task']!=a['tasks'][0]['id']:raise ValueError('exact first mapped-alias failure required')
    first=parent/'runs'/a['tasks'][0]['id']
    if read(first/'synth.command.json')['exit_code']!=0 or (first/'grt.command.json').exists():raise ValueError('inherit successful synthesis only')
    a['id']='matrix-'+root.name;a['parent']=dict(path=str(parent),admission_sha256=sha(parent/'admission.json'),failure=p['errors'])
    a['tasks'][0]['inherit_synth']=dict(directory=str(first),files={str(p.relative_to(first)):sha(p) for p in first.rglob('*') if p.is_file() and not p.is_symlink()},
        reason='only mapped alias reader changed; original synthesis/RTL/global ABC unchanged')
    for p in Path(__file__).parent.glob('nangate45_pipeline*.py'):a['files'][str(p)]=sha(p)
    root.mkdir();write(root/'admission.json',a);write(root/'progress.json',dict(phase='admitted_successor',completed=[],errors=[]))
    write(root/'simulation-inheritance.json',dict(parent=str(parent),all_sources=[dict(source=s['id'],receipt=str(Path(s['folder'])/'simulation.json'),
        sha256=sha(Path(s['folder'])/'simulation.json')) for s in a['sources']],RTL_changed=False))
    return dict(tasks=len(a['tasks']),new_synth=len(a['tasks'])-1,retained_synth=1)


def inherit(root,task,out):
    item=task['inherit_synth'];origin=Path(item['directory'])
    for p,h in item['files'].items():
        if sha(origin/p)!=h:raise ValueError('inherited synth drift')
    shutil.copytree(origin,out,symlinks=True)
    for p in out.rglob('*'):
        if p.is_file() and not p.is_symlink() and p.suffix in ('.json','.mk','.tcl','.py','.ys'):
            text=p.read_text();p.write_text(text.replace(str(origin),str(out)))
    for n in ('1_synth.odb','1_2_yosys.v'):
        if sha(out/'results'/collect.SUFFIX/n)!=sha(origin/'results'/collect.SUFFIX/n):raise ValueError('inherited mapped physical checkpoint changed')
    write(out/'synthesis-inheritance.json',item)


def point(root,task):
    text=inspect.getsource(collect.point)
    old="if evaluate(args,ledger):raise ValueError('N56 synth failed')"
    new="if task.get('inherit_synth'):inherit(root,task,out)\n        elif evaluate(args,ledger):raise ValueError('N56 synth failed')"
    if text.count(old)!=1:raise ValueError('frozen collection callsite drift')
    namespace=dict(collect.point.__globals__);namespace.update(inherit=inherit,mapped_state=aliases.verify)
    exec(compile(text.replace(old,new),__file__,'exec'),namespace);namespace['point'](root,task)
