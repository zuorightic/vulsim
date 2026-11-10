"""Finite wide-load qualification replay; never refit or consume test labels."""
import argparse
from copy import deepcopy
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha
from experiments.arithmetic_dse import model_qualification_labels as labels
from experiments.arithmetic_dse.model_mapped_contract import mapped_contract,operator_port_contract
from experiments.arithmetic_dse.model_m2_live_cec_v3 import verify_proof,check_result
from regression.arithmetic_physical_label_contract import packet
from regression.arithmetic_liberty_arc_contract import witness,remove_arc,through_data

SUFFIX=Path('asap7/arithmetic_probe/base')


def verify(root,out,portable=False):
    if out.exists():raise ValueError('preserve replay result')
    out.mkdir(parents=True)
    sources=read(root/'new-sources.json')['sources'];rows=[];checks=[];points=[]
    for source in sources:
        state=root/'raw'/source['id'];history=read(state/'history.json') if (state/'history.json').exists() else []
        if source['role']=='locked_test':
            if state.exists():raise ValueError('physical independent test touched')
            continue
        for p in history:
            if p['status']!='completed':raise ValueError('qualification failed; preserve unsupported context')
            t=p['SDC_ps'];folder=state/('target-'+str(t))/'runs'/(source['id']+'-T'+str(t))
            design=read(folder/'mapped.json');pins=read(folder/'liberty-pins.json')
            if mapped_contract(design,source['features'],pins)!=read(folder/'mapped-contract.json'):
                raise ValueError('actual FF/bank aliases differ')
            if operator_port_contract(design,source['features'],pins)!=read(folder/'operator-port-contract.json'):
                raise ValueError('operator port semantics differ')
            if not portable:
                if sha(folder/'input.sv')!=source['rtl_sha256']:raise ValueError('source RTL changed')
                manifest=read(folder/'manifest.json')
                for name,h in manifest['evidence_sha256'].items():
                    if sha(folder/name)!=h:raise ValueError('physical evidence changed '+name)
                cfg=read(folder.parents[1]/'admission.json')
                freeze=folder.parents[1]/'source'
                for name,h in cfg['source_sha256'].items():
                    if sha(freeze/name)!=h:raise ValueError('point runtime freeze changed')
            for stage in ('synth','grt'):
                raw,c=packet(folder,stage);result=labels.extract(raw,c['nodes'],c['banks'])
                saved=read(folder/(stage+'-labels.json'))
                # The raw reader deliberately cannot grant lifecycle eligibility.
                # The collector sets it after the role admission and exact CEC.
                changed=[k for k,v in result.items() if k!='physical_training_label_eligible' and saved[k]!=v]
                if changed:raise ValueError('saved raw label changed '+str(changed))
                if saved['source_role']!=source['role'] or not saved['physical_training_label_eligible']:
                    raise ValueError('source role eligibility changed')
                if result['path_decompositions']!=through_data(raw,c):raise ValueError('complete path boundary changed')
                for kind in ('independent_node','through_data'):
                    w=witness(raw,kind);broken=remove_arc(raw,w)
                    try:
                        labels.extract(broken,c['nodes'],c['banks']) if kind=='independent_node' else through_data(broken,c)
                    except ValueError as error:
                        if 'actual Liberty timing arc' not in str(error):raise
                        checks.append(dict(source=source['id'],target_ps=t,stage=stage,kind=kind,deleted_arc=w))
                    else:raise ValueError('unregistered actual path arc accepted')
                rows.append(dict(source=source['id'],role=source['role'],target_ps=t,stage=stage,
                    operation=source['features']['producer']['operation'],
                    producer=source['features']['producer'],consumer_specs=[c['spec'] for c in source['features']['consumers']],
                    operator_delay_ps=result['operator_delay_ps'],comb_area_um2=result['comb_area_um2'],
                    data_setup_slack_ps=result['data_setup_slack_ps'],hold_slack_ps=saved['metrics']['hold_worst_slack_ps'],
                    shell_setup_feasible=saved['metrics']['setup_worst_slack_ps']>=0,
                    retained_FF=read(folder/'mapped-contract.json')['mapped_sequential_cells'],
                    all_node_endpoints_measured=True,exclusive_area_conserved=True,all_saved_fields_unchanged=True))
            cec=folder/'logs'/SUFFIX/'structural_cec';proof=read(cec/'proof.json')
            if portable:
                check_result((cec/'cec.log').read_text(),True)
                for name in proof['negative_controls']:check_result((cec/('negative-'+name+'.log')).read_text(),False)
            else:
                verify_proof(cec/'proof.json',folder/'results'/SUFFIX/'4_before_rsz_lec.v',folder/'results'/SUFFIX/'4_after_rsz_lec.v')
            points.append(dict(source=source['id'],target_ps=t,role=source['role'],directory=str(folder),
                live_CEC_exact_pair_and_artifacts_checked=not portable,CEC_logs_checked=True))
    if len(points)!=6 or len(rows)!=12:raise ValueError('finite qualification inventory differs')
    write(out/'proof.json',dict(status='passed',points=points,stages=len(rows),rows=rows,
        single_arc_negative_checks=checks,negative_checks=len(checks),new_EDA_calls=0,
        new_independent_model_evaluation=False,physical_test_sources_touched=0,
        scope='five wide-load source contexts, six points; measurements are not prediction accuracy or continuous-domain qualification',
        portable=portable,full_D_ready=False))
    print(dict(status='passed',points=len(points),stages=len(rows),negative_arcs=len(checks)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--portable',action='store_true');a=p.parse_args();verify(a.root.resolve(),a.out.resolve(),a.portable)
