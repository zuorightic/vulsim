"""Reuse the existing full physical qualifier with an explicit successor reader."""
from pathlib import Path
from types import FunctionType
import os

from .model_fast_preflight import read,write
from . import model_steps123_qualification as parent,model_logical_stage_v1 as logical
from .processes import run_command


def task_run(folder,t):
    captured={}
    class CapturingLedger(parent.QualificationLedger):
        def __init__(self,*args):super().__init__(*args);captured['ledger']=self
    # task_run imports its labels module locally. Replace that single binding
    # via an explicit source successor, leaving all physical/CEC/FF/SDC checks.
    import ast,inspect,textwrap
    tree=ast.parse(textwrap.dedent(inspect.getsource(parent.task_run)))
    class ReplaceLabels(ast.NodeTransformer):
        def visit_ImportFrom(self,node):
            if node.level==1 and any(n.name=='model_qualification_labels' for n in node.names):
                return ast.copy_location(ast.Assign(targets=[ast.Name(id='labels',ctx=ast.Store())],value=ast.Name(id='successor_labels',ctx=ast.Load())),node)
            return node
    tree=ReplaceLabels().visit(tree);ast.fix_missing_locations(tree)
    from . import model_qualification_labels as original
    records=[]
    def reader(prefix,period,scale,pins,nodes,banks):
        if scale!=1:raise ValueError('ASAP7 successor requires verified ps units')
        stage='synth' if str(prefix).endswith('_synth') else 'grt'
        out=folder/'runs'/t['id'];ledger=captured['ledger']
        def execute(command,name):
            reservation=ledger.reserve(None,120,4,'logical_owner_report',command,out/name,context=dict(task_id=t['id']))
            env=os.environ.copy();env.update(OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',PYTHONDONTWRITEBYTECODE='1',QT_QPA_PLATFORM='offscreen')
            record=run_command(command,out,name,120,env,8192,cpu_limit_s=reservation['CPU_time_s']);ledger.finish(reservation,record)
            records.append(dict(**record,budget_reservation_id=reservation['id']));write(out/'logical-qualification-commands.json',records)
            if record['exit_code']:raise ValueError('logical ownership report failed '+record['log'])
        return logical.collect(out,stage,period,pins,nodes,banks,execute)
    from types import SimpleNamespace
    namespace=dict(parent.task_run.__globals__);namespace.update(QualificationLedger=CapturingLedger,
        successor_labels=SimpleNamespace(with_timing_arcs=original.with_timing_arcs,read_snapshot=reader))
    exec(compile(tree,str(Path(__file__)),'exec'),namespace)
    namespace['task_run'](folder,t)
