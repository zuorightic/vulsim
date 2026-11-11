"""Saved batch snapshots: strict constant endpoints, aliases and CEC controls."""
import argparse
from copy import deepcopy
from pathlib import Path
import shutil
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write
from experiments.arithmetic_dse.stage67_parse_v2 import parse_stage
from experiments.arithmetic_dse.stage67_state_semantics_v1 import verify as semantics
from experiments.arithmetic_dse.stage67_mapped_state_v3 import verify as census
from experiments.arithmetic_dse.stage67_analyze_v1 import path_partition,verify_ownership_packet
from experiments.arithmetic_dse.stage67_physical_probe_v1 import SUFFIX
from experiments.arithmetic_dse.model_m2_live_cec_v4 import verify_proof,negative_targets


def run(root,out):
    if out.exists():raise ValueError('preserve batch qualification')
    out.mkdir(parents=True);a=read(root/'admission.json');negative=[];rows=[]
    def rejects(name,fn):
        try:fn()
        except (ValueError,KeyError):negative.append(name)
        else:raise ValueError('accepted qualification negative '+name)
    for task in a['tasks']:
        d=root/'runs'/task['id'];contract=read(task['endpoint_contract']);source=read(Path(task['input_directory'])/'source.json');rtl=(d/'input.sv').read_text();state=read(d/'mapped-state.json')
        computed=census(read(d/'mapped.json'),read(d/'liberty-pins.json'),contract,source,rtl)
        for key in ('words','owner_FF_bits','constant_bits_checked','all_FFs_accounted_once'):
            if computed[key]!=state[key]:raise ValueError('actual state/unique FF census replay differs')
        actual=semantics(d,state,rtl,contract)
        if actual!=read(root/'state-semantics-v3'/(task['id']+'.json')):raise ValueError('actual logical state Boolean replay differs')
        verify_proof(d/'logs'/SUFFIX/'structural_cec/proof.json',d/'results'/SUFFIX/'4_before_rsz_lec.v',d/'results'/SUFFIX/'4_after_rsz_lec.v')
        if computed['physical_alias_groups']:
            members=next(iter(computed['physical_alias_groups'].values()));word=members[-1]['word'];slot=next(s for s in contract['state_slots'] if 'core/'+s['name']==word)
            for field in ('stage','enable_stage'):
                bad=deepcopy(contract);target=next(s for s in bad['state_slots'] if s['name']==slot['name']);target[field]+=1
                rejects(task['id']+'/aliased_'+field+'_mismatch',lambda:census(read(d/'mapped.json'),read(d/'liberty-pins.json'),bad,source,rtl))
            bad=deepcopy(state);w=next(w for w in bad['words'] if w['name']==word);w['enable']='unconditional'
            rejects(task['id']+'/aliased_reference_wrong_enable',lambda:semantics(d,bad,rtl,contract))
            bad=deepcopy(state);w=next(w for w in bad['words'] if w['name']==word);w['reset']^=1
            rejects(task['id']+'/aliased_reference_wrong_reset',lambda:semantics(d,bad,rtl,contract))
        for stage in ('synth','grt'):
            folder=root/'readout-v2'/task['id']/stage;label=parse_stage(folder);owners=read(folder/'ownership.json')
            first=next(iter(label['node_paths']));part=next(iter(label['node_paths'][first].values()));points=[]
            for s in part['segments']:
                if not points:points.append((s['from_pin'],0.))
                points.append((s['to_pin'],points[-1][1]+s['delay_ps']))
            cellstep=next(s for s in part['segments'] if s['kind']=='node_cell');cell,term=cellstep['from_pin'].rsplit('/',1);target=cellstep['to_pin'].rsplit('/',1)[1];master=owners['instances'][cell]
            bad=deepcopy(owners);bad['liberty'][master]['timing_arcs'].remove([term,target]);rejects(task['id']+'/'+stage+'/deleted_actual_Liberty_arc',lambda:path_partition(points,bad,[part['start']],part['end'],first))
            bad=deepcopy(owners);bad['owners'][cell]='native_state';rejects(task['id']+'/'+stage+'/forged_owner',lambda:verify_ownership_packet(bad))
            with tempfile.TemporaryDirectory(prefix='batch1-endpoint-negative-') as directory:
                temporary=Path(directory)/'packet';shutil.copytree(folder,temporary)
                q=read(temporary/'requests.json');request=next(v for v in q.values() if v['path_class']=='output_data');request['to_ports'].pop();write(temporary/'requests.json',q)
                rejects(task['id']+'/'+stage+'/omitted_dynamic_output',lambda:parse_stage(temporary))
            if label['proven_constant_output_bits']:
                with tempfile.TemporaryDirectory(prefix='batch1-constant-negative-') as directory:
                    temporary=Path(directory)/'packet';shutil.copytree(folder,temporary);p=read(temporary/'constant-output-proof.json');name=next(iter(p['expected']));p['expected'][name]=str(1-int(p['expected'][name]));write(temporary/'constant-output-proof.json',p)
                    rejects(task['id']+'/'+stage+'/forged_constant_output',lambda:parse_stage(temporary))
            rows.append(dict(task=task['id'],stage=stage,endpoints=label['endpoint_checks'],constant_outputs=label['proven_constant_output_bits'],
                physical_FF_bits=sum(computed['owner_FF_bits'].values()),logical_FF_references=actual['checked_FF_bits'],alias_groups=len(computed['physical_alias_groups'])))
    full=[['output','0','0','y'],['output','33','33','y'],['output','64','0','cec_state_'+b'ff\0D'.hex()],['output','65','0','cec_state_'+b'ff\0CLK'.hex()]]
    targets=negative_targets((full,[dict(index=33,symbol='y[33]',literal=0)]))
    if targets['constant_top_output']!=33 or 'constant_register_D' in targets:raise ValueError('vector constant CEC selector regressed')
    targets=negative_targets((full,[dict(index=64,symbol=full[2][3],literal=0)]))
    if targets['constant_register_D']!=64:raise ValueError('constant FF D selector regressed')
    rejects('missing_actual_clock_class',lambda:negative_targets((full[:-1],[])))
    result=dict(status='passed_batch1_actual_packet_qualification',physical_stages=len(rows),checks=rows,negative_rejections=len(negative),negatives=negative,
        vector_constant_and_FF_constant_CEC_indices_checked=True,physical_calls=0,zero_G_joint_qualified=False,full_D_ready=False)
    write(out/'proof.json',result);print(dict(status=result['status'],physical_stages=len(rows),negative_rejections=len(negative)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();run(a.root.resolve(),a.out.resolve())
