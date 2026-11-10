"""Actual raw report replay and corruptions; no new EDA or model test labels."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
from types import FunctionType
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse import model_qualification_labels as labels
from experiments.arithmetic_dse import model_physical_labels_v2 as raw_reader
from experiments.arithmetic_dse.model_mapped_contract import mapped_contract,operator_port_contract
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha


def packet(folder,stage):
    contract=read(folder/'query-contract.json');pins=read(folder/'liberty-pins.json')
    tables=folder/'reports/asap7/arithmetic_probe/base';all_pins=dict(pins)
    for line in (tables/('vulsim_'+stage+'_cells.tsv')).read_text().splitlines():
        master,count,area,filler,kind=line.split('\t')
        if master not in all_pins:all_pins[master]=dict(sequential=False,buffer_or_inverter=False,physical_only=True,data_pins=[],pins={},area_um2=0 if filler=='1' else float(area))
    namespace=dict(raw_reader.read_snapshot.__globals__);namespace['extract']=lambda value,*args:value
    fn=FunctionType(raw_reader.read_snapshot.__code__,namespace,closure=raw_reader.read_snapshot.__closure__);fn.__kwdefaults__=raw_reader.read_snapshot.__kwdefaults__
    saved=read(folder/(stage+'-labels.json'));p=fn(tables/('context_'+stage),saved['metrics']['target_period_ps'],1,all_pins,contract['nodes'],contract['banks'])
    return p,contract


def verify(folder,out):
    out.mkdir(parents=True,exist_ok=False);a=read(folder/'admission.json');rows=[];examples=[];negatives=[]
    for task in a['tasks']:
        location=Path(task['inherit_completed']['directory']) if task.get('inherit_completed') else folder/'runs'/task['id']
        design=read(location/'mapped.json');pins=read(location/'liberty-pins.json');expected=mapped_contract(design,task['features'],pins)
        if expected!=read(location/'mapped-contract.json'):raise ValueError('physical FF/bank/alias replay changed')
        if operator_port_contract(design,task['features'],pins)!=read(location/'operator-port-contract.json'):raise ValueError('semantic output certificate differs')
        for stage in ('synth','grt'):
            raw,c=packet(location,stage);result=labels.extract(raw,c['nodes'],c['banks']);saved=read(location/(stage+'-labels.json'))
            for key in result:
                if result[key]!=saved[key]:raise ValueError('raw physical label replay changed '+task['id']+'/'+stage+'/'+key)
            rows.append(dict(task=task['id'],stage=stage,operator_delay_ps=result['operator_delay_ps'],comb_area_um2=result['comb_area_um2'],data_slack_ps=result['data_setup_slack_ps'],
                dynamic_outputs={n:v['independent_dynamic_outputs'] for n,v in result['nodes'].items()},area_conservation_error=abs(result['total_cell_area_um2']-saved['metrics']['cell_area_um2'])))
            if task['id']=='mul-load-1500' and stage=='synth':examples=[raw,c,design,pins,task['features']]
    raw,c,design,pins,features=examples
    def reject(name,mutate):
        p=deepcopy(raw);mutate(p)
        try:labels.extract(p,c['nodes'],c['banks'])
        except (ValueError,KeyError):negatives.append(name)
        else:raise ValueError('corrupted physical input accepted '+name)
    reject('missing_independent_output',lambda p:p['nodes']['producer']['output_paths'].pop(next(iter(p['nodes']['producer']['output_paths']))))
    reject('missing_through_constraint',lambda p:p['data_requests'][next(iter(p['data_requests']))]['through'].clear())
    reject('nonfinite_slack',lambda p:p['data_paths'][next(iter(p['data_paths']))].update(slack_ps=float('nan')))
    reject('missing_signal_pin',lambda p:p['connections'].pop(next(iter(p['pin_logic']))))
    reject('clock_as_data_end',lambda p:p['data_paths'][next(iter(p['data_paths']))].update(end=p['data_paths'][next(iter(p['data_paths']))]['end'].rsplit('/',1)[0]+'/CLK'))
    reject('whole_shell_slack_substitution',lambda p:p.update(setup_worst_slack_ps=0))
    def no_output_arcs(p):
        p['liberty']={name:dict(cell,timing_arcs=[]) for name,cell in p['liberty'].items()}
    reject('unregistered_output_to_output_cell_arc',no_output_arcs)
    broken=deepcopy(design);top=broken['modules']['ModelBundle'];capture=broken['modules'][top['cells']['capture']['type']]
    width=len(capture['ports']['data']['bits'])
    # Alias the second bank to the first data bit; numerical FF counts alone
    # would miss this semantic loss, so require the mapped bit certificate.
    capture['ports']['data']['bits'][width//2]=capture['ports']['data']['bits'][0]
    try:mapped_contract(broken,features,pins)
    except ValueError:negatives.append('captured_logical_bits_or_banks_merged')
    else:raise ValueError('merged captured bits accepted')
    write(out/'proof.json',dict(status='passed',points=4,stages=len(rows),rows=rows,negative_checks=negatives,
        raw_operator_and_through_data_replayed=True,semantic_FF_and_port_certificates_replayed=True,source_role='not_training',new_EDA_calls=0,training_labels_consumed=0))
    print(dict(status='passed',points=4,stages=len(rows),negative_checks=len(negatives)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--folder',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();verify(a.folder.resolve(),a.out.resolve())
