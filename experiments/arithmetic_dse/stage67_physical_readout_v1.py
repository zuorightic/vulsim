"""Report-only ownership/state/endpoints over the two saved pilot snapshots."""
import argparse
from collections import defaultdict
from copy import deepcopy
import csv
from pathlib import Path
import os

from .model_fast_preflight import read,write,sha
from .budget import Ledger
from . import stage67_physical_probe_v1 as physical,model_logical_ownership_v2 as ownership
from .model_qualification_labels import canonical


def table(path):return list(csv.DictReader(Path(path).read_text().splitlines(),delimiter='\t'))
def tcl(value):
    if isinstance(value,dict):return '{'+' '.join(tcl(k)+' '+tcl(v) for k,v in value.items())+'}'
    if isinstance(value,(list,tuple)):return '{'+' '.join(tcl(x) for x in value)+'}'
    value=str(value)
    if any(c in value for c in '{}\n\r'):raise ValueError('unsafe Tcl spelling')
    return '{'+value+'}'


def census(directory,stage):
    prefix=directory/('census-'+stage)
    instances=dict(line.split('\t') for line in Path(str(prefix)+'_instances.tsv').read_text().splitlines())
    nets={r['instance']+'/'+r['pin']:dict(direction=r['direction'],net=r['net']) for r in table(str(prefix)+'_connections.tsv')}
    ports={r['port']:dict(direction=r['direction'],net=r['net']) for r in table(str(prefix)+'_ports.tsv')}
    return instances,nets,ports,[r['net'] for r in table(str(prefix)+'_clock_nets.tsv')]


def certificate(directory,physical_directory,stage,contract):
    instances,nets,ports,clocks=census(directory,stage);pins=read(physical_directory/'liberty-pins.json')
    for line in (physical_directory/'reports'/physical.SUFFIX/('vulsim_'+stage+'_cells.tsv')).read_text().splitlines():
        name,count,area,filler,kind=line.split('\t')
        if name not in pins:pins[name]=dict(sequential=False,buffer_or_inverter=False,physical_only=True,data_pins=[],pins={},area_um2=0 if filler=='1' else float(area))
    scopes={'node_'+str(r['node']):r['scope']+'/' for r in contract['operator_scopes']}
    # Proof-only namespace: preserve the frozen ownership rules while giving
    # real native and external banks their existing explicit state owners.
    aliases={}
    for name in instances:
        n=canonical(name)
        if n.startswith('external_capture/'):aliases[n]='observer/__external__/'+n[len('external_capture/'):]
        elif n.startswith('core/') and not any(n.startswith(p) for p in scopes.values()):aliases[n]='capture/__native__/'+n[len('core/'):]
    if len(set(aliases.values()))!=len(aliases) or set(aliases.values())&set(instances):raise ValueError('proof namespace collision')
    def pin(n):
        c,p=canonical(n).rsplit('/',1);return aliases.get(c,c)+'/'+p
    packet=dict(origin='physical_snapshot',period_ps=1500,time_to_ps=1,instances={aliases.get(canonical(n),canonical(n)):m for n,m in instances.items()},
        liberty=pins,connections={pin(n):dict(v,net=canonical(v['net'])) for n,v in nets.items()},clock_nets=[canonical(n) for n in clocks],nodes={},pin_logic={},data_requests={},data_paths={})
    normalized=ownership.normalize(packet,scopes,{})
    cert=ownership.resolve(normalized,scopes,ports)
    if not cert['complete']:raise ValueError('unresolved actual arithmetic/state owner '+repr(cert['unresolved']))
    reverse={v:k for k,v in aliases.items()};owners={reverse.get(n,n):('external_state' if o=='observer' else o) for n,o in cert['owners'].items()}
    return dict(version='stage67-physical-ownership-v1',owners=owners,instances={canonical(n):m for n,m in instances.items()},
        connections={canonical(n):dict(v,net=canonical(v['net'])) for n,v in nets.items()},top_ports={canonical(n):dict(v,net=canonical(v['net'])) for n,v in ports.items()},
        clock_nets=[canonical(n) for n in clocks],liberty=normalized['liberty'],scopes=scopes,proof_aliases=aliases,certificate=cert,
        area_owned_once=True,physical_design_modified=False)


def requests(state,owners):
    ports=owners['top_ports'];words=state['words'];requests={}
    def portword(name):
        found=[n for n in ports if n==name or n.startswith(name+'[')]
        if not found:raise ValueError('missing actual top port '+name)
        return sorted(found)
    def pins(word,key):return [r['cell']+'/'+r[key] for r in word['rows'] if 'cell' in r]
    dataQ=[p for w in words if not w['valid'] for p in pins(w,'Q')]
    validQ=[p for w in words if w['valid'] and w['owner']!='external_state' for p in pins(w,'Q')]
    for i,w in enumerate(words):
        capture=pins(w,'D');stage=max(0,w['stage']-1)
        def add(kind,from_pins=None,from_ports=None,to_pins=None,to_ports=None):
            requests[kind+'_'+str(i)]=dict(path_class=kind,stage=stage,word=w['name'],from_pins=from_pins or [],from_ports=from_ports or [],
                through_pins=[],to_pins=to_pins if to_pins is not None else capture,to_ports=to_ports or [])
        if w['owner']=='input_service':
            n=w['origin']
            if w['valid']:add('input_valid',from_ports=portword('iv_data')+portword('iv_wen'))
            else:
                add('input_data',from_ports=portword(n+'_data'));add('input_enable',from_ports=portword(n+'_wen'))
        elif w['valid']:add('external_valid' if w['owner']=='external_state' else 'native_valid',from_pins=validQ)
        else:
            add('external_data' if w['owner']=='external_state' else 'native_data',from_pins=dataQ)
            if w['owner']=='native_state':add('native_enable',from_pins=validQ)
        add('reset',from_ports=portword('rstn'))
        if w['owner']=='external_state':
            add('output_valid' if w['valid'] else 'output_data',from_pins=pins(w,'Q'),to_pins=[],to_ports=portword('ov' if w['valid'] else w['name'].split('/')[-1]))
    return requests


def collect(root,result):
    from .processes import run_command
    if result.exists():raise ValueError('preserve report attempt')
    result.mkdir(parents=True);a=read(root/'admission.json');records=[]
    for task in a['tasks']:
        bank=root/'runs'/task['id'];pointer=bank/'physical-directory.json';directory=Path(read(pointer)['path']) if pointer.exists() else bank
        state=read(bank/'mapped-state.json');contract=read(task['endpoint_contract']);export=read(Path(task['input_directory'])/'export.json')
        variant=next(v for v in export['variants'] if v['id']==task['placement'])
        m=read(directory/'manifest.json');base=next(c['command'][:-1] for c in m['commands'] if c['log'].endswith('/synth.log'))
        for stage,stem in (('synth','1_synth'),('grt','5_1_grt')):
            owners=certificate(bank,directory,stage,contract);q=requests(state,owners);folder=result/task['id']/stage;folder.mkdir(parents=True)
            write(folder/'ownership.json',owners);write(folder/'requests.json',q);write(folder/'mapped-state.json',state)
            # Every actual sequential instance must match the independently
            # resolved compiler state; CTS cannot silently add/merge storage.
            actual={n for n,master in owners['instances'].items() if owners['liberty'][master]['sequential']}
            expected={canonical(r['cell']) for w in state['words'] for r in w['rows'] if 'cell' in r}
            if actual!=expected:raise ValueError('physical FF inventory differs from mapped state certificate')
            template=(physical.ROOT/'experiments/arithmetic_dse/reference_assets/stage7_readout_v1.tcl').read_text()
            template=template.replace('set targets [s7_pins [dict get $q to_pins]]','set targets [s7_pins [dict get $q to_pins]]\n        if {[dict exists $q to_ports]} {foreach name [dict get $q to_ports] {set p [get_ports [list $name]];if {[llength $p]!=1 || [get_full_name [lindex $p 0]] ne $name} {error "stage67 missing output port"};lappend targets [lindex $p 0]}}')
            template=template.replace('[dict get $q class]','[dict get $q path_class]')
            # Node requests in the boundary adapter use the same field name.
            template=template.replace('[dict get $q path_class]','[expr {[dict exists $q path_class] ? [dict get $q path_class] : [dict get $q class]}]')
            adapted=folder/'readout.tcl';adapted.write_text(template)
            node_stages={'node_'+str(n):variant['placement'][n] for n in export['arithmetic_nodes']}
            prefix=folder/'timing';script=folder/'load-readout.tcl'
            script.write_text('source $::env(SCRIPTS_DIR)/load.tcl\nload_design $::env(VULSIM_EVAL_DB) $::env(VULSIM_EVAL_SDC)\n'+
                ('set_propagated_clock [all_clocks]\nestimate_parasitics -global_routing\n' if stage=='grt' else '')+
                'set stage7_prefix '+tcl(prefix)+'\nset stage67_owners '+tcl(owners['owners'])+'\nset stage67_masters '+tcl(owners['instances'])+
                '\nset stage67_node_stages '+tcl(node_stages)+'\nset stage7_requests '+tcl(q)+'\nset stage67_readout_script '+tcl(adapted)+'\nsource '+tcl(physical.ROOT/'experiments/arithmetic_dse/reference_assets/stage67_context_v1.tcl')+'\n')
            command=base+['run','RUN_SCRIPT='+str(script),'RUN_LOG_NAME_STEM=stage67_'+stage,'VULSIM_EVAL_STAGE='+stage,'VULSIM_EVAL_DB='+stem+'.odb','VULSIM_EVAL_SDC='+stem+'.sdc']
            ctx=dict(target_platform='asap7',admission_id=result.name,task_id=task['id']+'-'+stage);ledger=Ledger()
            env=os.environ.copy();env.update(OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',PYTHONDONTWRITEBYTECODE='1',QT_QPA_PLATFORM='offscreen')
            with ledger.job(ctx):
                reservation=ledger.reserve(None,120,4,'stage67_report_only',command,folder/'readout',context=ctx)
                rec=run_command(command,folder,'readout',120,env,8192,cpu_limit_s=reservation['CPU_time_s']);ledger.finish(reservation,rec)
            records.append(dict(**rec,budget_reservation_id=reservation['id']));write(result/'commands.json',records)
            if rec['exit_code']:raise ValueError('stage67 readout failed '+rec['log'])
            print('STAGE67_SAVED_READOUT_COMPLETE '+task['id']+'/'+stage,flush=True)
    write(result/'status.json',dict(status='saved_readout_complete',physical_calls=0,stages=4,full_D_ready=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--result',type=Path,required=True);a=p.parse_args();collect(a.root.resolve(),a.result.resolve())
