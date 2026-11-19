"""Nangate45 N7 whole-design grt plus exact fixed-DB full-clock readout."""
import argparse
from contextlib import contextmanager
import math
import os
from pathlib import Path
from types import FunctionType, SimpleNamespace
from unittest.mock import patch

from . import nangate45_n7 as app
from . import backend, budget, platform_probe, workload_nine_runtime as shared
from . import model_fast_sdc_v3 as sdc
from .platforms import profile
from .processes import run_command


def verify_batch(batch):
    batch=Path(batch);root=batch.parent.parent
    app.verify(root)
    a=app.read(batch/'admission.json');f=app.read(batch/'freeze.json')
    assert a['version']==app.VERSION and a['tasks']==f['tasks']
    assert a['freeze_sha256']==app.sha(batch/'freeze.json') and a['policy_sha256']==app.sha(app.POLICY)
    assert a['source_protocol_sha256']==app.sha(root/'protocol.json')
    for p,h in f['files'].items():
        if app.sha(p)!=h:raise ValueError('N7 admitted selection changed: '+p)
    return a


class ApplicationLedger(shared.NineLedger):
    def __init__(self,batch,task):
        super().__init__();self.batch=Path(batch);self.task=task;self.policy=app.POLICY

    @contextmanager
    def _transaction(self):
        bridge=dict(version=app.VERSION,policy=str(app.POLICY),policy_sha256=app.sha(app.POLICY),
            cumulative_ledger=str(budget.LEDGER),authorization='Nangate45 N7/N8 three applications; three threads; no usage reset')
        with shared.NineLedger()._transaction() as state:
            rows=state.setdefault('caller_policy_bridges',[])
            matches=[r for r in rows if r['version']==app.VERSION]
            if matches and matches!=[bridge]:raise ValueError('N7 resource bridge changed')
            if not matches:rows.append(bridge)
            yield state

    def reserve(self,stage,timeout_s,threads,purpose,command,output,*,context=None):
        a=verify_batch(self.batch);task=self.task
        assert task in a['tasks'] and threads==3 and purpose=='final_evaluation'
        own=[r for r in app.read(self.path)['entries'] if r.get('admission_id')==a['id'] and r.get('task_id')==task['id']]
        if stage in ('synth','grt'):
            assert timeout_s==task[stage+'_timeout_s'] and not any(r['stage']==stage for r in own)
        else:assert stage is None and timeout_s<=task['support_timeout_s'] and sum(r['stage'] is None for r in own)<4
        return budget.Ledger.reserve(self,stage,timeout_s,threads,purpose,command,output,context=context)


def admission(args,p,rtl,ledger):
    a=verify_batch(args.admission.parent);task=next(t for t in a['tasks'] if t['id']==args.task_id)
    expected=dict(platform='nangate45',threads=3,stage='grt',memory_limit_mib=task['memory_limit_MiB'],
        period_ps=task['period_ps'],abc_target_ps=task['period_ps'],top='Workload',
        synth_timeout_s=task['synth_timeout_s'],route_timeout_s=task['grt_timeout_s'])
    assert all(getattr(args,k)==v for k,v in expected.items())
    assert p['profile_sha256']==profile('nangate45')['profile_sha256']
    assert str(rtl)==task['rtl'] and app.sha(rtl)==task['rtl_sha256'] and args.admission_id==a['id']
    assert args.io_delay_max_ps is None and args.resume_synth_from is None
    ledger.check_job_admission()
    return app.sha(args.admission)


def clock_script(task,output):
    p=profile('nangate45')
    template=(app.ROOT/'experiments/arithmetic_dse/reference_assets/workload_minimum_period_v1.tcl').read_text()
    # Timing paths are native ns. All serialized slacks, thresholds and +/-0.1
    # probes are ps; clock/IO/uncertainty commands remain native ns.
    template=template.replace('set s [get_property $path slack]','set s [expr {1000.0 * [get_property $path slack]}]')
    template=template.replace('-period $period','-period [expr {$period/1000.0}]')
    template=template.replace('[expr {0.2*$period}]','[expr {0.2*$period/1000.0}]')
    for key,value in dict(PERIOD=task['period_ps'],OUTPUT=output,TRANSITION=p['clock_transition_ps']/1000,
            SETUP=p['setup_uncertainty_ps']/1000,HOLD=p['hold_uncertainty_ps']/1000).items():
        template=template.replace('@'+key+'@',str(value))
    return template


def install_cts(out):
    from .model_m2_mux_collection import render_cts
    from .model_reference_labels import liberty
    from .model_qualification_labels import with_timing_arcs
    m=app.read(out/'manifest.json');cells=app.read(out/'liberty_cells.json')['cells']
    pins=with_timing_arcs(liberty(m['libraries'],cells),m['libraries'])
    wrapper=out/'nangate45-cts-cec.py'
    wrapper.write_text('import sys\nsys.path.insert(0,'+repr(str(app.ROOT))+')\nfrom experiments.arithmetic_dse.nangate45_n7_cec import main\nmain()\n')
    request=out/'cts-cec-request.json'
    app.write(request,dict(libraries=m['libraries'],admission_sha256=app.sha(out.parent.parent/'admission.json'),
        collection_plan_sha256=m['selection_freeze_sha256'],sequential_clock_pins={n:v['clock_pins'] for n,v in pins.items() if v['sequential']}))
    proof=out/'logs/nangate45/arithmetic_probe/base/structural_cec'
    cts=out/'flow-scripts/cts.tcl';cts.unlink()
    cts.write_text(render_cts((Path('/home/zyrv/OpenROAD-flow-scripts/flow/scripts/cts.tcl')).read_text(),wrapper,request,proof))
    app.write(out/'cts-verification-binding.json',dict(wrapper_sha256=app.sha(wrapper),request_sha256=app.sha(request),cts_sha256=app.sha(cts),
        same_complete_state_D_clock_top_output_CEC_as_N56=True,clock_pin_from_Nangate45_Liberty=True))


def execute(batch,task_id):
    batch=Path(batch).resolve();a=verify_batch(batch);task=next(t for t in a['tasks'] if t['id']==task_id)
    out=batch/'runs'/task_id;ledger=ApplicationLedger(batch,task)
    context=dict(target_platform='nangate45',admission_id=a['id'],task_id=task_id)
    args=SimpleNamespace(out=out,platform='nangate45',threads=3,stage='grt',memory_limit_mib=task['memory_limit_MiB'],
        period_ps=task['period_ps'],period_role='original_A_reference' if task['reference_A'] else 'A_derived_frozen_target',
        abc_target_ps=task['period_ps'],io_delay_max_ps=None,budget_purpose='final_evaluation',admission_id=a['id'],task_id=task_id,
        sample_contract=None,admission=batch/'admission.json',resume_synth_from=None,orfs=Path('/home/zyrv/OpenROAD-flow-scripts'),
        rtl=Path(task['rtl']),top='Workload',synth_timeout_s=task['synth_timeout_s'],route_timeout_s=task['grt_timeout_s'],selection_freeze=batch/'freeze.json')
    def command(cmd,folder,stem,timeout,env,memory_limit_mib=None,**kwargs):
        assert 'NUM_CORES=3' in cmd and 'YOSYS_MAX_THREADS=3' in cmd
        if stem=='grt':install_cts(out)
        return run_command(cmd,folder,stem,timeout,env,memory_limit_mib,**kwargs)
    namespace=dict(backend._evaluate.__globals__)
    namespace.update(POLICY=app.POLICY,rtl_ports=sdc.rtl_ports,verify_sdc=sdc.verify_sdc,SDC_CONTRACT_VERSION=sdc.VERSION,run_command=command)
    evaluate=FunctionType(backend._evaluate.__code__,namespace)
    try:
        with ledger.job(context),patch.object(platform_probe,'verify_admission',admission):
            if evaluate(args,ledger):raise RuntimeError(app.read(out/'manifest.json').get('failure_reason','backend failed'))
            from .nangate45_n7_cec import verify_proof
            results=out/'results/nangate45/arithmetic_probe/base'
            proof=out/'logs/nangate45/arithmetic_probe/base/structural_cec/proof.json'
            verify_proof(proof,results/'4_before_rsz_lec.v',results/'4_after_rsz_lec.v')
            manifest=app.read(out/'manifest.json');base=next(c['command'][:-1] for c in manifest['commands'] if c['log'].endswith('/synth.log'))
            folder=out/'clock-readout';folder.mkdir()
            fixed={str(results/n):app.sha(results/n) for n in ('5_1_grt.odb','5_1_grt.sdc')}
            script=folder/'period.tcl';script.write_text(clock_script(task,folder/'period.tsv'))
            cmd=base+['run','RUN_SCRIPT='+str(script),'RUN_LOG_NAME_STEM=N7_clock_limit','VULSIM_EVAL_DB=5_1_grt.odb','VULSIM_EVAL_SDC=5_1_grt.sdc']
            reservation=ledger.reserve(None,task['support_timeout_s'],3,'final_evaluation',cmd,out/'clock-readout',context=context)
            rec=run_command(cmd,out,'clock-readout',task['support_timeout_s'],dict(os.environ,OMP_NUM_THREADS='3',YOSYS_MAX_THREADS='3',OPENBLAS_NUM_THREADS='3'),
                task['memory_limit_MiB'],cpu_limit_s=reservation['CPU_time_s'])
            ledger.finish(reservation,rec);app.write(out/'clock-readout.command.json',dict(rec,budget_reservation_id=reservation['id']))
            if rec['exit_code']:raise RuntimeError('N7 fixed DB clock readout failed')
            assert all(app.sha(p)==h for p,h in fixed.items())
            rows={n:dict(slack_ps=float(s),required_period_ps=float(v)) for n,s,v in (line.split('\t') for line in (folder/'period.tsv').read_text().splitlines()[1:])}
            assert rows['threshold_check_-0.1']['slack_ps']<0<=rows['threshold_check_0.1']['slack_ps']
            metric=manifest['metrics'][-1];minimum=rows['full_setup_threshold']['required_period_ps']
            assert abs(rows['full_setup_threshold']['slack_ps']-metric['setup_worst_slack_ps'])<.02
            app.write(folder/'result.json',dict(task=task_id,target_ps=task['period_ps'],classes=rows,fixed_inputs=fixed,
                full_setup_minimum_period_ps=minimum,maximum_frequency_MHz=1e6/minimum,area_um2=metric['cell_area_um2'],
                hold_WNS_ps=metric['hold_worst_slack_ps'],setup_met=minimum<=task['period_ps'],hold_met=metric['hold_worst_slack_ps']>=0,
                target_platform='nangate45',timing_coverage_complete=metric['timing_coverage_complete'],scope='fixed grt full RR/IR/RO; 0.2T IO; ns to ps explicit; hold separate'))
            manifest['commands'].append(dict(rec,budget_reservation_id=reservation['id']))
            manifest['whole_clock_readout']=dict(result_sha256=app.sha(folder/'result.json'),CTS_proof_sha256=app.sha(proof),
                CTS_binding_sha256=app.sha(out/'cts-verification-binding.json'))
            app.write(out/'manifest.json',manifest)
        app.write(out/'measurement-outcome.json',dict(status='completed',task_id=task_id,ledger_settled=True,
            manifest_sha256=app.sha(out/'manifest.json'),clock_readout_sha256=app.sha(folder/'result.json'),threads_per_tool=3,
            complete_setup_bracket_checked=True,source_sha256=app.sha(__file__)))
        print('N7_COMPLETE '+task_id,flush=True)
    except Exception as error:
        app.write(out/'measurement-outcome.json',dict(status='failed',task_id=task_id,reason=str(error),source_sha256=app.sha(__file__),automatic_retries=0))
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--batch',type=Path,required=True);p.add_argument('--task-id',required=True);a=p.parse_args()
    execute(a.batch,a.task_id)
