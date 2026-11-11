"""Actual pilot packets: strict path/owner and mapped-state negative controls."""
import argparse
from copy import deepcopy
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha
from experiments.arithmetic_dse.stage67_analyze_v1 import parse_stage,path_partition,verify_ownership_packet
from experiments.arithmetic_dse.stage67_mapped_state_v2 import verify as mapped_verify
from experiments.arithmetic_dse.stage67_state_semantics_v1 import verify as semantic_verify


def run(root,out):
    if out.exists():raise ValueError('preserve qualification attempt')
    out.mkdir(parents=True);a=read(root/'admission.json');positive=[];negative=[]
    def rejects(name,fn):
        try:fn()
        except (ValueError,KeyError):negative.append(name)
        else:raise ValueError('qualification negative accepted '+name)
    for task in a['tasks']:
        bank=root/'runs'/task['id'];pointer=bank/'physical-directory.json';directory=Path(read(pointer)['path']) if pointer.exists() else bank
        design=read(directory/'mapped.json');pins=read(directory/'liberty-pins.json');contract=read(task['endpoint_contract']);source=read(Path(task['input_directory'])/'source.json');rtl=(directory/'input.sv').read_text()
        mapped=mapped_verify(design,pins,contract,source,rtl)
        if mapped!=read(bank/'mapped-state.json'):raise ValueError('mapped FF proof replay differs')
        functional=semantic_verify(directory,mapped,rtl,contract)
        if functional!=read(root/'state-semantics-v2'/(task['id']+'.json')):raise ValueError('actual state Boolean proof replay differs')
        broken=deepcopy(contract);slot=next(x for x in broken['state_slots'] if not x['external_capture'] and not x['valid']);slot['variable_mask_hex'][0]=hex(int(slot['variable_mask_hex'][0],16)^1)[2:]
        rejects(task['id']+'/forged_variable_mask',lambda:mapped_verify(design,pins,broken,source,rtl))
        broken=deepcopy(mapped);w=next(x for x in broken['words'] if x['owner']=='native_state' and not x['valid']);w['enable']='unconditional'
        rejects(task['id']+'/removed_actual_enable',lambda:semantic_verify(directory,broken,rtl,contract))
        broken=deepcopy(mapped);w=next(x for x in broken['words'] if x['valid']);w['reset']=1
        rejects(task['id']+'/forged_reset',lambda:semantic_verify(directory,broken,rtl,contract))
        broken=deepcopy(mapped);w=next(x for x in broken['words'] if x['owner']=='native_state' and x['valid']);w['rows'][0]['logical_output_inverted']=not w['rows'][0]['logical_output_inverted']
        rejects(task['id']+'/forged_FF_output_polarity',lambda:semantic_verify(directory,broken,rtl,contract))
        for stage in ('synth','grt'):
            folder=root/'readout-v1'/task['id']/stage;label=parse_stage(folder);owners=read(folder/'ownership.json')
            positive.append(dict(task=task['id'],stage=stage,endpoint_checks=label['endpoint_checks'],nodes=len(label['nodes']),FF_bits=sum(label['owner_FF_bits'].values()),actual_state_functions=True))
            first=next(iter(label['node_paths']));part=next(iter(label['node_paths'][first].values()));points=[]
            for s in part['segments']:
                if not points:points.append((s['from_pin'],0.))
                points.append((s['to_pin'],points[-1][1]+s['delay_ps']))
            start,end=[part['start']],part['end']
            cellstep=next(s for s in part['segments'] if s['kind']=='node_cell');cell,term=cellstep['from_pin'].rsplit('/',1);target=cellstep['to_pin'].rsplit('/',1)[1];master=owners['instances'][cell]
            broken=deepcopy(owners);arcs=broken['liberty'][master]['timing_arcs'];arcs.remove([term,target])
            rejects(task['id']+'/'+stage+'/deleted_real_Liberty_arc',lambda:path_partition(points,broken,start,end,first))
            broken=deepcopy(owners);broken['liberty'][master]['pins'][target]['direction']='input'
            rejects(task['id']+'/'+stage+'/wrong_actual_pin_direction',lambda:path_partition(points,broken,start,end,first))
            wire=next(s for s in part['segments'] if s['kind']=='node_wire');broken=deepcopy(owners);broken['connections'][wire['to_pin']]['net']='disconnected-negative'
            rejects(task['id']+'/'+stage+'/disconnected_actual_wire',lambda:path_partition(points,broken,start,end,first))
            broken=deepcopy(owners);broken['owners'][cell]='native_state'
            rejects(task['id']+'/'+stage+'/forged_arithmetic_owner',lambda:verify_ownership_packet(broken))
            broken=deepcopy(owners);broken['connections'][wire['to_pin']]['net']='changed-full-census'
            rejects(task['id']+'/'+stage+'/stale_ownership_certificate',lambda:verify_ownership_packet(broken))
    result=dict(status='passed_actual_stage67_packet_qualification',positive_stages=len(positive),checks=positive,negative_rejections=len(negative),negatives=negative,
        node_model_sha256=a['model']['sha256'],state_coefficients_changed=False,physical_calls=0,independent_joint_tests_unlocked=False,full_D_ready=False)
    write(out/'proof.json',result);print(dict(status=result['status'],positive_stages=len(positive),negative_rejections=len(negative)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();run(a.root.resolve(),a.out.resolve())
