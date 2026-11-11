"""Finite report-only ownership recovery on retained, unchanged physical stages."""
import argparse
import csv
from copy import deepcopy
from pathlib import Path
import shutil
import sys
from types import FunctionType

from .model_fast_preflight import read,write,sha
from . import model_physical_labels_v2 as raw,model_qualification_labels as qualified
from . import model_logical_ownership_v1 as owners,operator_stage4 as stages,backend
from .model_mapped_contract import mapped_contract,operator_port_contract
from .model_m2_live_cec_v3 import verify_proof
from .platforms import profile,verify_wire_readback
from . import model_fast_sdc_v2 as sdc

ROOT=Path(__file__).resolve().parents[2]
SUFFIX=Path('asap7/arithmetic_probe/base')
ASSETS=Path(__file__).with_name('reference_assets')
SOURCES=[Path(__file__),Path(owners.__file__),ASSETS/'ownership_census_v1.tcl',ASSETS/'context_readout_logical_v1.tcl']


def table(p):return list(csv.DictReader(p.read_text().splitlines(),delimiter='\t'))


def packet_at(prefix,task,pins,contract):
    namespace=dict(raw.read_snapshot.__globals__);namespace['extract']=lambda p,*args:p
    fn=FunctionType(raw.read_snapshot.__code__,namespace);fn.__kwdefaults__=raw.read_snapshot.__kwdefaults__
    return fn(prefix,task['target_ps'],1,pins,contract['nodes'],contract['banks'])


def inputs(task):
    folder=Path(task['folder']);manifest=read(folder/'manifest.json');contract=read(folder/'query-contract.json');pins=read(folder/'liberty-pins.json')
    for lib in manifest['libraries']:
        if sha(Path(lib['path']))!=lib['sha256']:raise ValueError('Liberty changed')
    for line in (folder/'reports'/SUFFIX/('vulsim_'+task['stage']+'_cells.tsv')).read_text().splitlines():
        name,count,area,filler,kind=line.split('\t')
        if name not in pins:pins[name]=dict(sequential=False,buffer_or_inverter=False,physical_only=True,data_pins=[],pins={},area_um2=0 if filler=='1' else float(area))
    return manifest,contract,pins


def prepare(out,node_root):
    if out.exists():raise ValueError('preserve prior successor')
    out.mkdir(parents=True);(out/'restore').mkdir();tasks=[]
    parent=Path(read(node_root/'collection.json')['parent_collection_root'])
    for root in (parent,node_root):
        manifest=read(root/'corpus/manifest.json');byid={r['id']:r for r in manifest['sources']}
        for error in read(root/'progress.json')['errors']:
            if error['error']!='unowned physical cell':continue
            source=byid[error['source']];t=error['target_ps'];folder=root/'raw'/source['id']/('target-'+str(t))/'runs'/(source['id']+'-T'+str(t))
            tasks.append(dict(id='failure-'+source['id']+'-'+str(t),source=source['id'],role=source['role'],features=source['features'],target_ps=t,stage='grt',folder=str(folder),was_valid=False))
    # Six preregistered valid fitting points, three per operation across operand
    # widths. Selection uses descriptors only, never error or model predictions.
    fit=read(node_root/'fit-data.json');manifest=read(node_root/'corpus/manifest.json');byid={r['id']:r for r in manifest['sources']}
    for op in ('mul','add'):
        unique={}
        for r in fit['rows']:
            if r['stage']=='grt' and r['operation']==op:unique.setdefault(r['source_id'],r)
        rows=sorted(unique.values(),key=lambda r:(max(r['descriptor']['local_context']['producer'][k] for k in ('lhs_width','rhs_width')),r['source_id']))
        for index in (0,len(rows)//2,len(rows)-1):
            row=rows[index];source=byid[row['source_id']]
            for stage in ('synth','grt'):
                tasks.append(dict(id='control-'+source['id']+'-'+str(row['target_ps'])+'-'+stage,source=source['id'],role=source['role'],features=source['features'],
                    target_ps=row['target_ps'],stage=stage,folder=row['measurement_path'],was_valid=True))
    if len({t['id'] for t in tasks})!=len(tasks) or len(tasks)!=16:raise ValueError('expected four refused stages and twelve valid controls')
    for t in tasks:
        folder=Path(t['folder']);m=read(folder/'manifest.json');stem='1_synth' if t['stage']=='synth' else '5_1_grt'
        paths=[folder/'input.sv',folder/'mapped.json',folder/'mapped-contract.json',folder/'operator-port-contract.json',folder/'query-contract.json',folder/'liberty-pins.json']
        paths += [p for p in (folder/'results'/SUFFIX).iterdir() if p.is_file()]
        paths += list((folder/'reports'/SUFFIX).glob('context_'+t['stage']+'*'))
        paths += [folder/'logs'/SUFFIX/'structural_cec/proof.json']
        if (folder/(t['stage']+'-labels.json')).exists():paths.append(folder/(t['stage']+'-labels.json'))
        t.update(snapshot_stem=stem,original_sha256={str(p):sha(p) for p in paths},original_history_sha256=sha(folder.parents[2]/'history.json'),
            original_command_sha256=sha(folder/('context-'+t['stage']+'.command.json')))
    frozen={str(p.relative_to(ROOT)):sha(p) for p in SOURCES}
    write(out/'protocol.json',dict(version='operator-ownership-recovery-replay-v1',tasks=tasks,implementation=frozen,
        rule='single declared arithmetic owner closes every actual driver and sink, with unique drivers, complete census and known Liberty function; no top/state/clock or unresolved neighbour',
        no_name_master_shape_whitelist=True,no_physical_netlist_rename=True,no_prediction_feature_added=True,
        source_roles_unchanged=True,old_test_is_repair_review_not_fresh_independent=True,
        frozen_model_unchanged=True,old_failed_gate_not_waived=True,max_synth=0,max_grt=0,max_report_leaves=32,
        acceptance=['unique ownership','every original physical/source artifact unchanged','strict actual Liberty arcs/connectivity',
            'recomputed full node endpoints and per-output maximum','exclusive area equals full-stage area','old valid control scalar/node/owner labels unchanged','real negative controls remain refused'],
        future_reserve=dict(synth=688,grt=688,wall_s=86400,cpu_s=172800,storage_gib=30),full_D_ready=False))
    freeze=out/'implementation';freeze.mkdir()
    for p in SOURCES:
        target=freeze/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
    print(dict(status='preregistered_report_replay',tasks=len(tasks),physical_optimization_calls=0),flush=True)


def assert_immutable(task):
    for name,h in task['original_sha256'].items():
        if sha(Path(name))!=h:raise ValueError('original artifact modified '+name)
    folder=Path(task['folder'])
    if sha(folder.parents[2]/'history.json')!=task['original_history_sha256']:raise ValueError('original source history modified')


def report_command(task,out,script,tag):
    folder=Path(task['folder']);old=read(folder/('context-'+task['stage']+'.command.json'))['command']
    remove=('RUN_SCRIPT=','RUN_LOG_NAME_STEM=','LOG_DIR=','REPORTS_DIR=','OBJECTS_DIR=')
    cmd=[x for x in old if not x.startswith(remove)]
    cmd += ['RUN_SCRIPT='+str(script),'RUN_LOG_NAME_STEM='+tag,'LOG_DIR='+str(out/'tool-logs'),'REPORTS_DIR='+str(out/'tool-reports'),'OBJECTS_DIR='+str(out/'tool-objects')]
    return cmd


def load_script(task):
    return 'source $::env(SCRIPTS_DIR)/load.tcl\nload_design $::env(VULSIM_EVAL_DB) $::env(VULSIM_EVAL_SDC)\n'+(
        'set_propagated_clock [all_clocks]\nestimate_parasitics -global_routing\n' if task['stage']=='grt' else '')


def run(out):
    protocol=read(out/'protocol.json')
    for n,h in protocol['implementation'].items():
        if sha(ROOT/n)!=h:raise ValueError('replay implementation changed')
    progress=[]
    for task in protocol['tasks']:
        d=out/'tasks'/task['id'];d.mkdir(parents=True,exist_ok=False);assert_immutable(task)
        m,contract,pins=inputs(task);script=d/'census.tcl';prefix=d/'census'
        script.write_text(load_script(task)+'set ownership_prefix {'+str(prefix)+'}\nsource {'+str(ASSETS/'ownership_census_v1.tcl')+'}\n')
        stages.support(out,task['id']+'-census',report_command(task,d,script,'ownership_census'),180)
        empty=dict(origin='physical_snapshot',period_ps=task['target_ps'],time_to_ps=1,instances=dict(line.split('\t') for line in Path(str(prefix)+'_instances.tsv').read_text().splitlines()),liberty=pins,
            connections={r['instance']+'/'+r['pin']:dict(direction=r['direction'],net=r['net']) for r in table(Path(str(prefix)+'_connections.tsv'))},
            clock_nets=[r['net'] for r in table(Path(str(prefix)+'_clock_nets.tsv'))],nodes={},pin_logic={},data_requests={},data_paths={})
        ports={r['port']:dict(direction=r['direction'],net=r['net']) for r in table(Path(str(prefix)+'_ports.tsv'))}
        normalized=owners.normalize(empty,contract['nodes'],contract['banks']);certificate=owners.resolve(normalized,contract['nodes'],ports)
        write(d/'certificate.json',certificate);write(d/'top-ports.json',ports);write(d/'liberty-pins.json',pins)
        if not certificate['complete']:
            progress.append(dict(task=task['id'],status='unresolved',unresolved=certificate['unresolved']));write(out/'progress.json',dict(phase='running',results=progress));continue
        def tcl(v):
            if any(x in v for x in '{}\n\r'):raise ValueError('unsafe Tcl spelling')
            return '{'+v+'}'
        members={n:o for n,o in certificate['owners'].items() if o in contract['nodes']}
        setup='set context_logical_owners {'+' '.join(tcl(n)+' '+tcl(o) for n,o in members.items())+'}\n'
        setup+='set context_logical_masters {'+' '.join(tcl(n)+' '+tcl(normalized['instances'][n]) for n in members)+'}\n'
        script=d/'read-logical-context.tcl';new_prefix=d/'logical_context'
        script.write_text(load_script(task)+'source {'+str(Path(task['folder'])/'query-contract.tcl')+'}\n'+setup+
            'set context_prefix {'+str(new_prefix)+'}\nsource {'+str(ASSETS/'context_readout_logical_v1.tcl')+'}\n')
        stages.support(out,task['id']+'-readout',report_command(task,d,script,'logical_readout'),180)
        packet=packet_at(new_prefix,task,pins,contract);write(d/'packet.json',packet)
        label=owners.extract(packet,contract['nodes'],contract['banks'],ports,certificate)
        folder=Path(task['folder']);design=read(folder/'mapped.json')
        if mapped_contract(design,task['features'],pins)!=read(folder/'mapped-contract.json'):raise ValueError('mapped bank proof changed')
        if operator_port_contract(design,task['features'],pins)!=read(folder/'operator-port-contract.json'):raise ValueError('mapped port proof changed')
        verify_proof(folder/'logs'/SUFFIX/'structural_cec/proof.json',folder/'results'/SUFFIX/'4_before_rsz_lec.v',folder/'results'/SUFFIX/'4_after_rsz_lec.v')
        metrics=backend.stage_metrics(folder/'reports'/SUFFIX,task['stage'],read(folder/'liberty_cells.json')['cells'],task['target_ps'],selected=profile('asap7'))
        if abs(label['total_cell_area_um2']-metrics['cell_area_um2'])>1e-5:raise ValueError('exclusive physical area does not conserve whole stage')
        if task['was_valid']:
            old=read(folder/(task['stage']+'-labels.json'))
            for key in ('operator_delay_ps','comb_area_um2','data_setup_slack_ps','nodes','owner_area_um2','total_cell_area_um2','path_decompositions'):
                if label[key]!=old[key]:raise ValueError('successful control label changed: '+task['id']+'/'+key)
        assert_immutable(task);label.update(stage=task['stage'],source_role=task['role'],original_snapshot_unchanged=True,
            mapped_bank_port_CEC_rechecked=True,full_stage_area_conserved=True,repair_review_only=True,full_D_ready=False)
        write(d/'recovered-labels.json',label)
        original_packet=packet_at(folder/'reports'/SUFFIX/('context_'+task['stage']),task,pins,contract)
        boundary_diff={node:{k:dict(removed=sorted(set(original_packet['nodes'][node][k])-set(packet['nodes'][node][k])),
            added=sorted(set(packet['nodes'][node][k])-set(original_packet['nodes'][node][k]))) for k in ('inputs','outputs','constants')} for node in contract['nodes']}
        write(d/'boundary-change.json',boundary_diff)
        progress.append(dict(task=task['id'],status='passed_replay',source_role=task['role'],recovered_cells=certificate['recovered'],
            old_valid_label_unchanged=task['was_valid'],operator_delay_ps=label['operator_delay_ps'],comb_area_um2=label['comb_area_um2'],
            repaired_owner_areas={r['owner']:label['owner_area_um2'][r['owner']] for r in certificate['recovered']},
            source_history_and_physical_artifacts_unchanged=True))
        write(out/'progress.json',dict(phase='running',results=progress));print('OWNERSHIP_REPLAY '+task['id']+' recovered='+str(len(certificate['recovered'])),flush=True)
    write(out/'progress.json',dict(phase='report_replay_complete',results=progress,new_synth=0,new_grt=0,full_D_ready=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','run'));p.add_argument('--out',type=Path,required=True);p.add_argument('--node-root',type=Path)
    a=p.parse_args()
    if a.action=='prepare':prepare(a.out.resolve(),a.node_root.resolve())
    else:run(a.out.resolve())
