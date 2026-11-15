"""Admit an explicit resource successor from its deepest completed checkpoint.

The executor is the frozen capacity-v1 implementation. This admission only
chooses retained, hashed checkpoints, keeping the selected RTL and recipe.
Post-CTS reuse additionally requires the complete successful CTS LEC receipt.
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import re
import shutil

from .workload_abcd import ROOT,read,write,sha
from .workload_backend_finish import verify as verify_parent
from . import workload_capacity as capacity
from .budget import Ledger,POLICY
from .model_m2_phase_resume import validate_lec

SYNTH=capacity.CHECKPOINTS
GROUPS=(('post_CTS',SYNTH+('4_1_cts.odb','4_cts.odb','4_cts.sdc')),
        ('post_placement',SYNTH+('3_place.odb','3_place.sdc')),
        ('post_floorplan',SYNTH+('2_floorplan.odb','2_floorplan.sdc')),
        ('post_synthesis',SYNTH))


def checkpoints(source,manifest):
    result=source/'results'/capacity.SUFFIX
    if not any(m['stage']=='synth' for m in manifest['metrics']):
        return 'cold_synthesis',{},None
    for phase,names in GROUPS:
        if not all((result/n).is_file() for n in names):
            continue
        hashes={n:sha(result/n) for n in names}
        if any(manifest['evidence_sha256'].get(str(Path('results')/capacity.SUFFIX/n))!=h
               for n,h in hashes.items()):
            raise ValueError('retained completed checkpoint changed')
        proof=None
        if phase=='post_CTS':
            reuse=manifest.get('checkpoint_reuse',{})
            if 'proof' in reuse:
                from .workload_cec import verify_proof
                verify_proof(reuse['proof'],result/'4_before_rsz_lec.v',result/'4_after_rsz_lec.v')
                proof=dict(kind='complete_state_cut_CEC',path=reuse['proof'],sha256=sha(reuse['proof']))
            else:
                path=source/'logs'/capacity.SUFFIX/'4_rsz_lec_check.log'
                text=path.read_text()
                boundary={}
                for kind in ('PIs','POs'):
                    pair=[re.search(rf'size of {kind} in circuit {side}: (\d+)',text) for side in (0,1)]
                    if any(v is None for v in pair) or pair[0][1]!=pair[1][1]:
                        raise ValueError('post-CTS checkpoint lacks complete identical LEC boundaries')
                    boundary[kind]=int(pair[0][1])
                validate_lec(text,boundary['PIs'],boundary['POs'])
                if manifest['evidence_sha256'].get(str(path.relative_to(source)))!=sha(path):
                    raise ValueError('retained successful CTS LEC receipt changed')
                proof=dict(kind='native_full_Kepler_LEC',path=str(path),sha256=sha(path),boundary=boundary)
        return phase,hashes,proof
    raise ValueError('successful synthesis has no complete retained checkpoint')


def admit(root,batch,sources,synth_timeout,grt_timeout):
    _,parent=verify_parent(root);folder=root/'capacity'/batch
    if folder.exists() or not sources or not (300<=synth_timeout<=3600 and 1200<=grt_timeout<=7200):
        raise ValueError('fresh named finite checkpoint admission required')
    tasks=[]
    for source in sources:
        source=source.resolve()
        if not source.is_relative_to(root):raise ValueError('checkpoint source must belong to this frozen comparison')
        m=read(source/'manifest.json')
        failed=[c for c in m['commands'] if c.get('timed_out') or c.get('memory_limit_exceeded')]
        if m['status']!='failed' or not failed or any(c['cleanup']['remaining_live_pids'] for c in failed):
            raise ValueError('explicit checkpoint successor requires a settled resource failure')
        task=next(t for t in parent['tasks'] if t['id']==m['task_id'])
        if any(t['id']==task['id'] for t in tasks):raise ValueError('duplicate successor task')
        if sha(source/'input.sv')!=task['rtl_sha256']:raise ValueError('retained source differs from frozen RTL')
        phase,hashes,proof=checkpoints(source,m)
        tasks.append(dict(task,source=str(source),source_manifest_sha256=sha(source/'manifest.json'),
                          reuse_synth=phase!='cold_synthesis',checkpoints=hashes,
                          completed_phase=phase,successful_CTS_proof=proof))
    wall=sum((0 if t['reuse_synth'] else synth_timeout)+grt_timeout+3*120 for t in tasks)
    limits=read(POLICY)['resources'];used=Ledger().summary()
    if (used['synth']+sum(not t['reuse_synth'] for t in tasks)>limits['max_synthesis_calls']
            or used['grt']+len(tasks)>limits['max_global_route_calls']
            or used['walltime_s']+wall>limits['max_global_walltime_h']*3600
            or used['CPU_time_s']+4*wall>limits['max_tool_CPU_time_h']*3600):
        raise ValueError('finite checkpoint continuation envelope unfunded')
    folder.mkdir(parents=True);hashes={}
    for path in (Path(__file__),Path(capacity.__file__),
                 ROOT/'experiments/arithmetic_dse/reference_assets/workload_minimum_period_v1.tcl'):
        name=path.relative_to(ROOT);dest=folder/'source'/name
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest);hashes[str(name)]=sha(path)
    a=dict(version=capacity.VERSION,admission_producer='nine-workload-deep-checkpoint-v1',
           id=parent['id']+'-'+batch,tasks=tasks,sources=hashes,
           parent_admission_sha256=sha(root/'admission.json'),
           synth_timeout_s=synth_timeout,grt_timeout_s=grt_timeout,threads=4,memory_limit_MiB=8192,
           worst_case_leaf_walltime_s=wall,CPU_envelope_s=4*wall,
           created_at=datetime.now(timezone.utc).isoformat(),automatic_retries=0,
           frozen_selection_unchanged=True,application_PPA_feedback=False,
           rationale='explicit settled resource failures; reuse deepest complete checkpoints; same physical optimization recipe')
    write(folder/'admission.json',a)
    write(folder/'progress.json',dict(completed=[],errors=[],active=[],status='admitted'))
    capacity.verify(root,folder)
    return dict(tasks=[dict(id=t['id'],completed_phase=t['completed_phase']) for t in tasks],wall_envelope_s=wall)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--batch',required=True)
    p.add_argument('--source',type=Path,action='append',required=True)
    p.add_argument('--synth-timeout',type=int,default=1800);p.add_argument('--grt-timeout',type=int,default=3600)
    args=p.parse_args()
    print(admit(args.root.resolve(),args.batch,args.source,args.synth_timeout,args.grt_timeout))
