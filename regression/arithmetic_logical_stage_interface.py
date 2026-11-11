"""Exercise the new collector label callback on an unchanged saved stage."""
import argparse
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha
from experiments.arithmetic_dse import model_logical_stage_v1 as logical,operator_stage4 as stages
from experiments.arithmetic_dse import operator_ownership_replay_v1 as replay


def run(root,out):
    if out.exists():raise ValueError('preserve callback verification')
    out.mkdir(parents=True)
    protocol=read(root/'protocol.json');task=next(t for t in protocol['tasks'] if t['source']=='s32e03528a3472a5c')
    original=Path(task['folder']);folder=out/'saved-stage';folder.mkdir()
    for name in ('context-grt.command.json','query-contract.tcl'):(folder/name).symlink_to(original/name)
    contract=read(original/'query-contract.json');pins=read(root/'tasks'/task['id']/'liberty-pins.json')
    def execute(command,name):stages.support(out,name,command,120)
    label=logical.collect(folder,'grt',task['target_ps'],pins,contract['nodes'],contract['banks'],execute)
    expected=read(root/'tasks'/task['id']/'recovered-labels.json')
    for key in ('nodes','operator_delay_ps','comb_area_um2','data_setup_slack_ps','owner_area_um2','path_decompositions'):assert label[key]==expected[key],key
    replay.assert_immutable(task)
    write(out/'proof.json',dict(status='passed_actual_saved_stage_collector_interface',snapshot=task['id'],
        reader_sha256=sha(Path(logical.__file__)),physical_artifacts_unchanged=True,all_scalar_node_owner_path_outputs_match=True,
        new_synth=0,new_grt=0,source_role='not_training_repair_review',full_D_ready=False))
    print('LOGICAL_STAGE_INTERFACE_PASS no_physical_optimization',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();run(a.root.resolve(),a.out.resolve())
