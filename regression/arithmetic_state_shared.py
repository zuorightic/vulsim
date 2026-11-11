"""Topology qualification for training attribution; frozen prices untouched."""
import argparse
from copy import deepcopy
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write,key
from experiments.arithmetic_dse.conditional_boundary_binding import frozen_fit,raw_context
from experiments.arithmetic_dse.stage67_state_shared_train_v1 import trace_roots,primitive_areas
from experiments.arithmetic_dse.model_physical_path_v2 import canonical


def qualify(root,out):
    if out.exists():raise ValueError('preserve training attribution proof')
    out.mkdir(parents=True);audit=read(root/'derivation-v5/training-audit.json');row=audit['area_rows'][0];fit,_=frozen_fit()
    r=next(r for r in fit['rows'] if 'S/'+r['source_group']==row['source'] and r['period_ps']==row['target_ps'] and r['stage']=='grt');directory=next(x['directory'] for x in fit['runs'] if x['task_id']==r['task_id'])
    pins,instances,nets=raw_context(directory,'grt');original=read(Path(directory)/'general-grt-ownership.json');owners={canonical(v['instance']):'root_repair' if v['owner']=='root_boundary_repair' else v['owner'] for v in original['ownership']}
    for name in row['clock_incident_loads_reassigned']:owners[name]='shared_clock'
    packet=dict(instances=instances,nets=nets,owners=owners)
    if key(packet)!=row['complete_census_sha256']:raise ValueError('real training witness identity differs')
    proof=trace_roots(instances,pins,nets,owners)
    if proof!=row['root_proof'] or primitive_areas(pins)!=audit['primitive_baseline']:raise ValueError('raw train root/primitive replay differs')
    negatives=[]
    def rejects(name,fn):
        try:fn()
        except (ValueError,KeyError):negatives.append(name)
        else:raise ValueError('accepted actual attribution negative '+name)
    instrument=next(n for n,v in proof.items() if v['instrumentation_only'] and v['immediate_terminal_loads']);target=proof[instrument]['immediate_terminal_loads'][0].rsplit('/',1)[0]
    wrong=deepcopy(owners);wrong[target]='native_state';reclassified=trace_roots(instances,pins,nets,wrong)
    if reclassified[instrument]['instrumentation_only']:raise ValueError('branch touching real state was discarded')
    renamed={n:'renamed_'+str(i) for i,n in enumerate(proof)}
    def cell(n):return renamed.get(n,n)
    def pin(n):c,p=n.rsplit('/',1);return cell(c)+'/'+p
    named=trace_roots({cell(n):v for n,v in instances.items()},pins,{pin(n):v for n,v in nets.items()},{cell(n):v for n,v in owners.items()})
    if any(named[cell(n)]['sink_owners']!=v['sink_owners'] or named[cell(n)]['instrumentation_only']!=v['instrumentation_only'] for n,v in proof.items()):raise ValueError('name-dependent root classification')
    bad=deepcopy(nets);full=instrument+'/'+next(p for p,v in pins[instances[instrument]]['pins'].items() if v['direction']=='input');bad[full]['net']='<unconnected-negative>'
    rejects('disconnected_actual_root_input',lambda:trace_roots(instances,pins,bad,owners))
    bad=deepcopy(nets);terms=[n for n,v in nets.items() if v['direction']=='output' and n.rsplit('/',1)[0]!=instrument];bad[terms[0]]['net']=nets[full]['net']
    rejects('multiply_driven_actual_root_net',lambda:trace_roots(instances,pins,bad,owners))
    # Verify the source and capture FFs used by plain native transfers have
    # the same plain positive-clock/data interface used in service banks.
    interfaces=[]
    for p in r['boundary_paths']:
        if p['id'] not in ('birth_data','native_data','external_data'):continue
        pair=[]
        for name in (p['start_pin'],p['end_pin']):
            cell_name=canonical(name).rsplit('/',1)[0];meta=pins[instances[cell_name]];inputs=[n for n,v in meta['pins'].items() if v['direction']=='input']
            if not meta['sequential'] or len(meta['clock_pins'])!=1 or len(meta['data_pins'])!=1 or len(inputs)!=2:raise ValueError('plain forwarding FF class not demonstrated')
            pair.append(dict(master=instances[cell_name],clock_pins=meta['clock_pins'],data_pins=meta['data_pins']))
        interfaces.append(dict(path_class=p['id'],endpoints=pair))
    write(out/'witness.json',dict(**packet,liberty=pins,expected_root_proof=proof,plain_FF_classes=interfaces))
    value=dict(status='passed_train_root_and_plain_FF_class_qualification',roots=len(proof),instrumentation_branches=sum(v['instrumentation_only'] for v in proof.values()),
        actual_clock_load_reassignments=len(row['clock_incident_loads_reassigned']),real_state_touch_preserved=True,root_names_irrelevant=True,
        negative_rejections=len(negatives),negatives=negatives,old_parameters_changed=False,validation_used=False,full_D_ready=False)
    write(out/'proof.json',value);print(value,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();qualify(a.root.resolve(),a.out.resolve())
