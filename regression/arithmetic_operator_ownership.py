"""Qualify ownership recovery using real snapshots and structural negatives."""
import argparse
from copy import deepcopy
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha
from experiments.arithmetic_dse import model_logical_ownership_v2 as ownership
from experiments.arithmetic_dse import operator_ownership_replay_v1 as replay
from experiments.arithmetic_dse.platforms import profile,verify_wire_readback
from experiments.arithmetic_dse import model_fast_sdc_v3 as sdc,backend


def validate(root,out):
    if out.exists():raise ValueError('preserve qualification')
    protocol=read(root/'protocol.json');progress=read(root/'progress.json')
    assert progress['phase']=='report_replay_complete' and len(progress['results'])==16
    assert all(r['status']=='passed_replay' for r in progress['results'])
    for name,h in protocol['implementation'].items():assert sha(ROOT/name)==h
    negatives=[];checks=[];boundary_changes=[]
    for t in protocol['tasks']:
        d=root/'tasks'/t['id'];p=read(d/'packet.json');nodes=read(Path(t['folder'])/'query-contract.json')['nodes'];banks=read(Path(t['folder'])/'query-contract.json')['banks'];ports=read(d/'top-ports.json');cert=read(d/'certificate.json')
        result=ownership.extract(p,nodes,banks,ports,cert);stored=read(d/'recovered-labels.json')
        for key in ('nodes','owner_area_um2','operator_delay_ps','comb_area_um2','data_setup_slack_ps','total_cell_area_um2','path_decompositions'):assert result[key]==stored[key],(t['id'],key)
        replay.assert_immutable(t);folder=Path(t['folder']);cfg=profile('asap7')
        sdc_check=sdc.verify_sdc((folder/'results'/replay.SUFFIX/(t['snapshot_stem']+'.sdc')).read_text(),cfg,t['target_ps'],sdc.rtl_ports((folder/'input.sv').read_text(),'ModelBundle'),serialization_stage=t['stage'])
        rc=verify_wire_readback(folder/'reports'/replay.SUFFIX/('vulsim_'+t['stage']+'_layer_rc.tsv'),cfg)
        metrics=stored['total_cell_area_um2'];native=read(folder/'logs'/replay.SUFFIX/(t['snapshot_stem']+'.json'))[('synth' if t['stage']=='synth' else 'globalroute')+'__design__instance__area__stdcell']
        area_check=backend.verify_orfs_area(metrics,native)
        changes=read(d/'boundary-change.json')
        boundary_changes.append(dict(task=t['id'],changes=changes))
        checks.append(dict(task=t['id'],role=t['role'],recovered=[dict(instance=x['instance'],owner=x['owner']) for x in cert['recovered']],
            original_valid=t['was_valid'],strict_label_replay=True,stored_SDC_check=sdc_check,wire_RC_check=rc,ORFS_area_crosscheck=area_check,
            source_and_physical_artifacts_unchanged=True))
        # Remove one actual Liberty arc used by an independent node path.
        found=None
        for row in p['nodes'].values():
            for path in row['output_paths'].values():
                for (a,_),(b,_) in zip(path,path[1:]):
                    ca,pa=a.rsplit('/',1);cb,pb=b.rsplit('/',1)
                    if ca==cb:
                        master=p['instances'][ca]
                        if [pa,pb] in p['liberty'][master].get('timing_arcs',[]):found=(master,pa,pb);break
                if found:break
            if found:break
        assert found,'no actual independent timing arc'
        bad=deepcopy(p);master,a,b=found;bad['liberty'][master]['timing_arcs'].remove([a,b])
        normalized=ownership.normalize(bad,nodes,banks);badcert=ownership.resolve(normalized,nodes,ports)
        try:ownership.extract(bad,nodes,banks,ports,badcert)
        except ValueError as error:
            assert 'arc' in str(error),str(error);negatives.append(dict(task=t['id'],test='actual_Liberty_arc_removed',reason=str(error)))
        else:raise AssertionError('nonexistent actual arc accepted')
        if not cert['recovered']:continue
        normal=ownership.normalize(p,nodes,banks);first=cert['recovered'][0];name=first['instance'];owner=first['owner']
        output=next(pin for pin in normal['connections'] if pin.startswith(name+'/') and normal['connections'][pin]['direction']=='output')
        output_net=normal['connections'][output]['net']
        other=next((n for n,o in cert['owners'].items() if o in nodes and o!=owner and any(v['direction']=='input' for v in normal['liberty'][normal['instances'][n]]['pins'].values())),None)
        foreign_pin=next(other+'/'+pin for pin,v in normal['liberty'][normal['instances'][other]]['pins'].items() if v['direction']=='input') if other else None
        state=next(pin for pin in normal['connections'] if cert['owners'].get(pin.rsplit('/',1)[0])=='native_state' and normal['connections'][pin]['direction']=='input' and pin.rsplit('/',1)[1] in normal['liberty'][normal['instances'][pin.rsplit('/',1)[0]]]['data_pins'])
        incoming=next(name+'/'+pin for pin,v in normal['liberty'][normal['instances'][name]]['pins'].items() if v['direction']=='input')
        mutations=[
            ('state_sink',lambda q,ps:q['connections'][state].update(net=output_net)),
            ('top_port_exposure',lambda q,ps:ps.update(fake_top=dict(direction='output',net=output_net))),
            ('clock_net',lambda q,ps:q['clock_nets'].append(output_net)),
            ('disconnected_input',lambda q,ps:q['connections'][incoming].update(net='<unconnected:negative>')),
            ('missing_census_pin',lambda q,ps:q['connections'].pop(incoming)),
            ('unknown_Liberty_master',lambda q,ps:q['instances'].update({name:'ABSENT_MASTER'}))]
        if foreign_pin:mutations.append(('cross_operator_sink',lambda q,ps:q['connections'][foreign_pin].update(net=output_net)))
        for label,change in mutations:
            q,ps=deepcopy(normal),deepcopy(ports);change(q,ps)
            try:rejected=not ownership.resolve(q,nodes,ps)['complete']
            except (ValueError,KeyError):rejected=True
            assert rejected,(t['id'],label);negatives.append(dict(task=t['id'],test=label,reason='incomplete/ambiguous/invalid actual ownership census refused'))
        forged=deepcopy(cert);forged['owners'][name]='unregistered_owner'
        try:ownership.extract(p,nodes,banks,ports,forged)
        except ValueError as error:negatives.append(dict(task=t['id'],test='forged_owner_certificate',reason=str(error)))
        else:raise AssertionError('forged owner accepted')
        # Recovery depends on connectivity, not a clone spelling or case ID.
        renamed=deepcopy(normal);fresh='arbitrary_logic_instance';renamed['instances'][fresh]=renamed['instances'].pop(name)
        renamed['connections']={(fresh+n[len(name):] if n.startswith(name+'/') else n):v for n,v in renamed['connections'].items()}
        renamed_cert=ownership.resolve(renamed,nodes,ports)
        assert renamed_cert['complete'] and renamed_cert['owners'][fresh]==owner,'instance name whitelist'
    write(root/'boundary-change-review.json',dict(version='logical-ownership-boundary-review-v1',tasks=boundary_changes))
    write(out,dict(version='operator-ownership-recovery-qualification-v1',status='passed_saved_snapshot_qualification',stages=len(checks),
        recovered_failed_stages=4,unchanged_valid_stages=12,recovered_physical_cells=5,negative_checks=negatives,negative_rejections=len(negatives),
        checks=checks,original_failed_gate_unchanged=True,fresh_independent_qualification=False,new_synth=0,new_grt=0,full_D_ready=False))
    print(dict(status='passed_saved_snapshot_qualification',stages=len(checks),negative_rejections=len(negatives)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();validate(a.root.resolve(),a.out.resolve())
