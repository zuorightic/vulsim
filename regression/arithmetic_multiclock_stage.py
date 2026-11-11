"""Actual-path negative controls for numerical-T whole-stage validation."""
import argparse
from copy import deepcopy
from pathlib import Path
import shutil
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write
from experiments.arithmetic_dse.stage67_parse_v2 import parse_stage
from experiments.arithmetic_dse.stage67_analyze_v1 import verify_ownership_packet,path_partition


def qualify(root):
    folder=root/'readout-v1/validation_p20-T500/grt';label=parse_stage(folder);owners=read(folder/'ownership.json');negative=[]
    def rejects(name,fn):
        try:fn()
        except (ValueError,KeyError):negative.append(name)
        else:raise ValueError('accepted negative '+name)
    bad=deepcopy(owners);key=next(iter(bad['owners']));bad['owners'][key]='fake'
    rejects('forged_unique_owner',lambda:verify_ownership_packet(bad))
    p=next(iter(next(iter(label['node_paths'].values())).values()));segments=p['segments'];step=next(s for s in segments if s['kind']=='node_cell')
    cell,source=step['from_pin'].rsplit('/',1);dest=step['to_pin'].rsplit('/',1)[1];master=owners['instances'][cell]
    points=[(p['start'],0.)];time=0.
    for s in segments:time+=s['delay_ps'];points.append((s['to_pin'],time))
    bad=deepcopy(owners);arcs=bad['liberty'][master]['timing_arcs']
    if [source,dest] not in arcs:raise ValueError('actual traversed Liberty arc missing in positive packet')
    arcs.remove([source,dest])
    rejects('only_actual_traversed_Liberty_arc_deleted',lambda:path_partition(points,bad,[p['start']],p['end'],owners['owners'][cell]))
    bad=deepcopy(owners);bad['liberty'][master]['pins'][dest]['direction']='input'
    rejects('actual_cell_direction_forged',lambda:path_partition(points,bad,[p['start']],p['end'],owners['owners'][cell]))
    wire=next(s for s in segments if s['kind']=='node_wire');bad=deepcopy(owners);bad['connections'][wire['to_pin']]['net']='<unconnected-negative>'
    rejects('actual_wire_disconnected',lambda:path_partition(points,bad,[p['start']],p['end'],owners['owners'][cell]))
    with tempfile.TemporaryDirectory(prefix='stage-negative-') as tmp:
        copy=Path(tmp)/'stage';shutil.copytree(folder,copy)
        proof=read(copy/'constant-output-proof.json');proof['expected']['forged[0]']='0';write(copy/'constant-output-proof.json',proof)
        rejects('forged_constant_output_partition',lambda:parse_stage(copy))
    value=dict(status='passed_real_full_path_reader',target_ps=500,endpoint_checks=label['endpoint_checks'],node_count=len(label['nodes']),
        negative_rejections=negative,arcs_removed=1,other_Liberty_arcs_retained=True,physical_calls=0,full_D_ready=False)
    write(root/'reader-qualification.json',value);print(value,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);a=p.parse_args();qualify(a.root.resolve())
