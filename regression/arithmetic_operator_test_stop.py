"""Audit acquisition failures with the independent model still frozen.

Only structural/mapping certificates are inspected. No fit, prediction-error
selection, ownership relaxation, retry or test-source replacement is allowed.
"""
import argparse
from pathlib import Path
from types import FunctionType
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha
from experiments.arithmetic_dse import model_physical_labels_v2 as labels,model_qualification_labels as qualified
from experiments.arithmetic_dse import operator_condition_wide as wide,operator_stage4 as stages
from experiments.arithmetic_dse.model_mapped_contract import mapped_contract,operator_port_contract
from experiments.arithmetic_dse.model_m2_live_cec_v3 import verify_proof


def audit(root,selection,out):
    if out.exists():raise ValueError('preserve earlier audit')
    wide.verify_measurement_sources(root);wide.verify_selection(root/'corpus',selection)
    acquisition=read(root/'test-acquisition-v2.json')
    if acquisition['selection_sha256']!=sha(selection):raise ValueError('independent freeze changed')
    manifest=read(root/'corpus/manifest.json');summaries=[]
    errors=read(root/'progress.json')['errors']
    for error in errors:
        source=next(s for s in manifest['sources'] if s['id']==error['source'])
        if source['role']!='locked_test':continue
        if error['error']!='unowned physical cell':raise ValueError('unreviewed independent failure: '+error['error'])
        state=root/'raw'/source['id'];history=read(state/'history.json');target=error['target_ps']
        if history[-1]['status']!='failed' or history[-1]['SDC_ps']!=target:raise ValueError('failed suffix changed')
        folder=state/('target-'+str(target))/'runs'/(source['id']+'-T'+str(target));suffix=Path('asap7/arithmetic_probe/base')
        contract=read(folder/'query-contract.json');pins=read(folder/'liberty-pins.json');design=read(folder/'mapped.json')
        if mapped_contract(design,source['features'],pins)!=read(folder/'mapped-contract.json'):raise ValueError('bank certificate differs')
        if operator_port_contract(design,source['features'],pins)!=read(folder/'operator-port-contract.json'):raise ValueError('operator port certificate differs')
        for line in (folder/'reports'/suffix/'vulsim_grt_cells.tsv').read_text().splitlines():
            master,count,area,filler,kind=line.split('\t')
            if master not in pins:pins[master]=dict(sequential=False,buffer_or_inverter=False,physical_only=True,data_pins=[],pins={},area_um2=0 if filler=='1' else float(area))
        namespace=dict(labels.read_snapshot.__globals__);namespace['extract']=lambda value,*args:value
        capture=FunctionType(labels.read_snapshot.__code__,namespace,closure=labels.read_snapshot.__closure__);capture.__kwdefaults__=labels.read_snapshot.__kwdefaults__
        packet=capture(folder/'reports'/suffix/'context_grt',target,1,pins,contract['nodes'],contract['banks'])
        roots=[]
        for name,master in packet['instances'].items():
            cell=pins[master]
            if '/' in name or cell['sequential'] or cell['buffer_or_inverter'] or cell.get('physical_only') or cell.get('constant_driver'):continue
            inputs=[p for p,v in cell['pins'].items() if v['direction']=='input']
            identical=[other for other,m in packet['instances'].items() if m==master and other!=name and any(other.startswith(scope) for scope in contract['nodes'].values())
                and all(packet['connections'][name+'/'+p]['net']==packet['connections'][other+'/'+p]['net'] for p in inputs)]
            connections={p:packet['connections'][name+'/'+p] for p in cell['pins']}
            roots.append(dict(instance=name,master=master,liberty_function={p:v.get('function') for p,v in cell['pins'].items()},connections=connections,
                net_neighbors={p:[dict(pin=k,connection=v) for k,v in packet['connections'].items() if v['net']==c['net'] and not k.startswith(name+'/')] for p,c in connections.items()},
                same_master_identical_input_scoped_instances=identical,owner_assigned=False))
        if not roots:raise ValueError('unowned combination cell witness absent')
        try:qualified.extract(packet,contract['nodes'],contract['banks'])
        except ValueError as e:
            if str(e)!='unowned physical cell':raise
        else:raise ValueError('refused snapshot unexpectedly accepted')
        if (folder/'grt-labels.json').exists():raise ValueError('invalid grt labels produced')
        for stage in ('synth','grt'):
            if read(folder/(stage+'.command.json'))['exit_code']:raise ValueError('physical implementation command failed')
        verify_proof(folder/'logs'/suffix/'structural_cec/proof.json',folder/'results'/suffix/'4_before_rsz_lec.v',folder/'results'/suffix/'4_after_rsz_lec.v')
        decision=wide.adapter(root/'corpus').next_request(root/'corpus',source['id'],history,selection)['decision']
        if decision['next_request'] is not None:raise ValueError('first-failed source is not stopped')
        summaries.append(dict(source=source['id'],role=source['role'],target_ps=target,root_arithmetic_cells=roots,
            source_stopped=True,valid_prior_points=sum(p['status']=='completed' for p in history),
            exact_CEC_passed=True,FF_and_port_certificates_passed=True,invalid_grt_label_generated=False,history_sha256=sha(state/'history.json')))
    if not summaries:raise ValueError('no independent failure to audit')
    namespace=dict(stages.decisions.__globals__);namespace['collect']=wide.adapter(root/'corpus')
    decisions=FunctionType(stages.decisions.__code__,namespace);pending=decisions(root,['locked_test'],selection)
    completed_batches=sum(any(r['role']=='locked_test' for r in read(p)['source_target_requests']) for p in (root/'batches').glob('batch-*/admission.json'))
    remaining=acquisition['max_batches']-completed_batches
    if remaining<=0 and pending:raise ValueError('original independent finite batch capacity exhausted')
    write(out,dict(version='operator-v2-independent-stop-audit-v1',status='passed_refusal_audit',stops=summaries,
        selection_sha256=sha(selection),pending_sources=len(pending),completed_independent_batches=completed_batches,remaining_original_batch_allowance=remaining,
        next_requests=[dict(source=r['id'],role=r['role'],SDC_ps=q['SDC_ps'],ABC_ps=q['ABC_ps']) for _,r,_,q in pending],
        numerical_test_evaluation_performed=False,parameters_or_domain_changed=False,source_roles_changed=False,new_EDA_calls=0,
        continuation='retain failed source, failed point and all prior labels; other frozen independent sources may finish their original finite scan; acquisition failure remains a failed independent gate',full_D_ready=False))
    print(dict(status='passed_refusal_audit',stops=len(summaries),unowned_cells=sum(len(s['root_arithmetic_cells']) for s in summaries),pending_sources=len(pending),remaining_batches=remaining),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('root','selection','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();audit(a.root.resolve(),a.selection.resolve(),a.out.resolve())
