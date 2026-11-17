"""Report-only Nangate45 tap/filler master classification from actual LEF census."""
from copy import deepcopy
import inspect
import os
from pathlib import Path
from unittest.mock import patch
from .nangate45_samples import read,write,sha
from . import nangate45_pipeline_collect as collect
from . import stage67_physical_readout_v2 as reader
from .platforms import profile
from .processes import run_command
BASE_REPORT=collect.report
BASE_REQUESTS=reader.requests


def report(out,source,task,pins,execute,base):
    original=reader.read;p=profile('nangate45');classified=deepcopy(original(out/'liberty-pins.json'))
    for line in (out/'reports'/collect.SUFFIX/'vulsim_grt_cells.tsv').read_text().splitlines():
        name,count,area,filler,kind=line.split('\t')
        if filler=='1' or kind in p['physical_master_types']:
            meta=classified.get(name,{})
            if any(v['direction'] in ('input','output') for v in meta.get('pins',{}).values()):raise ValueError('physical-only master has signal pins')
            classified[name]=dict(meta,sequential=False,buffer_or_inverter=False,physical_only=True,data_pins=[],pins={},area_um2=0. if filler=='1' else float(area))
    from .nangate45_pipeline_wire import is_wire
    owners=read(Path(source['folder'])/'owners.json');wires={'node_'+str(r['node']) for r in owners['operators'] if is_wire(r['query'])}
    contract=read(source['endpoint_contract']);contract['operator_scopes']=[r for r in contract['operator_scopes'] if 'node_'+str(r['node']) not in wires]
    owners['operators']=[r for r in owners['operators'] if 'node_'+str(r['node']) not in wires]
    def collection_read(path):
        if Path(path)==Path(source['endpoint_contract']):return contract
        if Path(path)==Path(source['folder'])/'owners.json':return owners
        return original(path)
    def patched_read(path):return classified if Path(path)==out/'liberty-pins.json' else original(path)
    def actual_requests(state,certificate):
        queries=BASE_REQUESTS(state,certificate);result={}
        words={w['name']:w for w in state['words']}
        for name,q in queries.items():
            if q['to_pins'] or q.get('to_ports'):result[name]=q;continue
            if any('cell' in r for r in words[q['word']]['rows']):raise ValueError('dynamic bank unexpectedly lacks capture endpoint')
        return result
    text=inspect.getsource(BASE_REPORT).replace("folder=out/'readout';folder.mkdir()","folder=out/'readout-v3';folder.mkdir()")
    namespace=dict(BASE_REPORT.__globals__);namespace['read']=collection_read
    exec(compile(text,__file__,'exec'),namespace)
    def report_execute(cmd,name,*args,**kwargs):return execute(cmd,'readout-v3' if name=='readout' else name,*args,**kwargs)
    with patch.object(reader,'read',patched_read),patch.object(reader,'requests',actual_requests):result=namespace['report'](out,source,task,pins,report_execute,base)
    for name in wires:result['nodes'][name]=dict(operator_delay_ps=0.,comb_area_um2=0.,exact_Boolean_wire=True)
    result['exact_Boolean_wire_owners']=sorted(wires)
    return result


def complete_saved(root,task):
    a=collect.campaign.verify(root);s=next(s for s in a['sources'] if s['id']==task['source']);out=root/'runs'/task['id']
    m=read(out/'manifest.json');base=read(out/'grt.command.json')['command'][:-1]
    recovery=dict(task,id=task['id']+'-readout-v3')
    ctx=dict(target_platform='nangate45',admission_id=a['id'],task_id=recovery['id']);ledger=collect.PipelineLedger(root,recovery)
    env=dict(os.environ,OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',YOSYS_MAX_THREADS='2',PYTHONDONTWRITEBYTECODE='1',QT_QPA_PLATFORM='offscreen')
    with ledger.job(ctx):
        def execute(cmd,name,timeout=120,stage=None):
            if stage:raise ValueError('report-only recovery forbids physical calls')
            r=ledger.reserve(None,timeout,2,'N56_report_only_recovery',cmd,out/name,context=ctx)
            rec=run_command(cmd,out,name,timeout,env,4096,cpu_limit_s=r['CPU_time_s']);ledger.finish(r,rec)
            if rec['exit_code']:raise ValueError('N56 report leaf failed '+rec['log'])
        pins=read(out/'liberty-pins.json');d=report(out,s,task,pins,execute,base)
        metrics=collect.backend.stage_metrics(out/'reports'/collect.SUFFIX,'grt',read(out/'liberty_cells.json')['cells'],task['period_ps'],selected=profile('nangate45'))
        metrics['stored_SDC']=collect.sdc.verify_sdc((out/'results'/collect.SUFFIX/'5_1_grt.sdc').read_text(),profile('nangate45'),task['period_ps'],
            collect.sdc.rtl_ports(Path(s['rtl']).read_text(),'ModelBundle'),serialization_stage='grt')
        metrics['wire_RC']=collect.verify_wire_readback(out/'reports'/collect.SUFFIX/'vulsim_grt_layer_rc.tsv',profile('nangate45'))
        collect.verify_proof(out/'logs'/collect.SUFFIX/'structural_cec/proof.json',out/'results'/collect.SUFFIX/'4_before_rsz_lec.v',out/'results'/collect.SUFFIX/'4_after_rsz_lec.v')
        if abs(d['total_area_um2']-metrics['cell_area_um2'])>1e-5:raise ValueError('N56 exclusive area conservation')
        d.update(whole_shell_metrics=metrics,CTS_CEC_sha256=sha(out/'logs'/collect.SUFFIX/'structural_cec/proof.json'))
        write(out/'pipeline-labels.json',d);write(out/'pipeline-status.json',dict(status='completed',label_sha256=sha(out/'pipeline-labels.json'),report_only_recovery=True))
