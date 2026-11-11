"""Audit a refused wide point without inventing ownership or rerunning EDA."""
import argparse
from pathlib import Path
from types import FunctionType
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha
from experiments.arithmetic_dse import model_physical_labels_v2 as labels
from experiments.arithmetic_dse import model_qualification_labels as qualified
from experiments.arithmetic_dse import operator_condition_wide as wide,operator_stage4 as stages
from experiments.arithmetic_dse.model_mapped_contract import mapped_contract,operator_port_contract
from experiments.arithmetic_dse.model_m2_live_cec_v3 import verify_proof


def audit(root,out):
    wide.verify_measurement_sources(root);manifest=read(root/'corpus/manifest.json');summaries=[]
    for error in read(root/'progress.json')['errors']:
        if error['error']!='unowned physical cell':raise ValueError('unreviewed stop '+error['error'])
        source=next(s for s in manifest['sources'] if s['id']==error['source'])
        if source['role']=='locked_test':raise ValueError('this audit is limited to fitting stops')
        state=root/'raw'/source['id'];target=error['target_ps'];history=read(state/'history.json')
        if history[-1]['status']!='failed' or history[-1]['SDC_ps']!=target:raise ValueError('failed suffix changed')
        folder=state/('target-'+str(target))/'runs'/(source['id']+'-T'+str(target));suffix=Path('asap7/arithmetic_probe/base')
        contract=read(folder/'query-contract.json');pins=read(folder/'liberty-pins.json');design=read(folder/'mapped.json')
        if mapped_contract(design,source['features'],pins)!=read(folder/'mapped-contract.json'):raise ValueError('bank certificate differs')
        if operator_port_contract(design,source['features'],pins)!=read(folder/'operator-port-contract.json'):raise ValueError('port certificate differs')
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
            same=[other for other,m in packet['instances'].items() if m==master and other!=name and any(other.startswith(scope) for scope in contract['nodes'].values())
                and all(packet['connections'][name+'/'+p]['net']==packet['connections'][other+'/'+p]['net'] for p in inputs)]
            connection={p:packet['connections'][name+'/'+p] for p in cell['pins']}
            neighbors={}
            for pin,net in connection.items():
                neighbors[pin]=[dict(pin=k,connection=v) for k,v in packet['connections'].items() if v['net']==net['net'] and not k.startswith(name+'/')]
            roots.append(dict(instance=name,master=master,liberty_function={p:v.get('function') for p,v in cell['pins'].items()},
                connections=connection,net_neighbors=neighbors,same_master_identical_input_scoped_instances=same,
                owner_assigned=False))
        if not roots:raise ValueError('no actual unowned combinational cells')
        try:qualified.extract(packet,contract['nodes'],contract['banks'])
        except ValueError as e:
            if str(e)!='unowned physical cell':raise
        else:raise ValueError('refused point became eligible')
        if (folder/'grt-labels.json').exists():raise ValueError('invalid grt label created')
        for stage in ('synth','grt'):
            if read(folder/(stage+'.command.json'))['exit_code']:raise ValueError('physical command itself failed')
        verify_proof(folder/'logs'/suffix/'structural_cec/proof.json',folder/'results'/suffix/'4_before_rsz_lec.v',folder/'results'/suffix/'4_after_rsz_lec.v')
        next_request=wide.adapter(root/'corpus').next_request(root/'corpus',source['id'],history)['decision']['next_request']
        if next_request is not None:raise ValueError('failed source continued')
        summaries.append(dict(source=source['id'],role=source['role'],target_ps=target,root_arithmetic_cells=roots,
            valid_prior_points=sum(p['status']=='completed' for p in history),source_stopped=True,
            exact_CEC_passed=True,FF_and_port_certificates_passed=True,invalid_node_label_generated=False,
            classification='root combinational arithmetic outside all declared node scopes; identical-input clone witness reported when present; no owner guessed',
            history_sha256=sha(state/'history.json')))
    namespace=dict(stages.decisions.__globals__);namespace['collect']=wide.adapter(root/'corpus')
    decisions=FunctionType(stages.decisions.__code__,namespace)
    pending=decisions(root,['train','validation'],None)
    write(out,dict(status='passed_refusal_audit',stops=summaries,pending_sources=len(pending),
        no_physical_repeat=True,reader_or_ownership_rules_changed=False,source_roles_changed=False,
        continuation='original first-failure stop retained for failed source; other sources may continue under unchanged exact-request admissions',full_D_ready=False))
    print(dict(status='passed_refusal_audit',new_stops=len(summaries),unowned_cells=sum(len(s['root_arithmetic_cells']) for s in summaries),pending_sources=len(pending)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();audit(a.root.resolve(),a.out.resolve())
