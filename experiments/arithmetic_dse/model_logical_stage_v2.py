"""Same strict labels, bulk independent endpoint STA, no duplicate legacy readout.

Every dynamic output retains an individual maximum witness. The stored actual
snapshot command supplies the DB/SDC identity; a legacy context run is optional.
No synthesis, optimization or database writes occur in this collector.
"""
from pathlib import Path
from .model_fast_preflight import read,write
from . import model_logical_ownership_v2 as ownership,model_logical_labels_v1 as labels
from . import operator_ownership_replay_v1 as parent

VERSION='logical-snapshot-v2-bulk-independent-endpoints'


def report_command(task,out,script,tag):
    folder=Path(task['folder']);stage=task['stage']
    choices=[folder/('qual-'+stage+'-snapshot.command.json'),folder/('context-'+stage+'.command.json')]
    command=next((read(p)['command'] for p in choices if p.exists()),None)
    if command is None:raise ValueError('actual completed snapshot command required')
    remove=('RUN_SCRIPT=','RUN_LOG_NAME_STEM=','LOG_DIR=','REPORTS_DIR=','OBJECTS_DIR=')
    return [x for x in command if not x.startswith(remove)]+[
        'RUN_SCRIPT='+str(script),'RUN_LOG_NAME_STEM='+tag,'LOG_DIR='+str(out/'tool-logs'),
        'REPORTS_DIR='+str(out/'tool-reports'),'OBJECTS_DIR='+str(out/'tool-objects')]


def collect(folder,stage,target,pins,nodes,banks,execute):
    folder=Path(folder);task=dict(folder=str(folder),stage=stage,target_ps=target)
    d=folder/('logical-v2-'+stage);d.mkdir(exist_ok=False)
    script=d/'census.tcl';prefix=d/'census'
    script.write_text(parent.load_script(task)+'set ownership_prefix {'+str(prefix)+'}\nsource {'+str(parent.ASSETS/'ownership_census_v1.tcl')+'}\n')
    execute(report_command(task,d,script,'logical_v2_census'),'logical-v2-'+stage+'-census')
    packet=dict(origin='physical_snapshot',period_ps=target,time_to_ps=1,
        instances=dict(line.split('\t') for line in Path(str(prefix)+'_instances.tsv').read_text().splitlines()),liberty=pins,
        connections={r['instance']+'/'+r['pin']:dict(direction=r['direction'],net=r['net']) for r in parent.table(Path(str(prefix)+'_connections.tsv'))},
        clock_nets=[r['net'] for r in parent.table(Path(str(prefix)+'_clock_nets.tsv'))],nodes={},pin_logic={},data_requests={},data_paths={})
    ports={r['port']:dict(direction=r['direction'],net=r['net']) for r in parent.table(Path(str(prefix)+'_ports.tsv'))}
    normalized=ownership.normalize(packet,nodes,banks);certificate=ownership.resolve(normalized,nodes,ports)
    write(d/'ownership-certificate.json',certificate);write(d/'top-ports.json',ports)
    if not certificate['complete']:raise ValueError('logical ownership remains unresolved')
    def tcl(v):
        if any(x in v for x in '{}\n\r'):raise ValueError('unsafe Tcl spelling')
        return '{'+v+'}'
    members={n:o for n,o in certificate['owners'].items() if o in nodes}
    setup='set context_logical_owners {'+' '.join(tcl(n)+' '+tcl(o) for n,o in members.items())+'}\n'
    setup+='set context_logical_masters {'+' '.join(tcl(n)+' '+tcl(normalized['instances'][n]) for n in members)+'}\n'
    script=d/'read-context.tcl';prefix=d/'context'
    script.write_text(parent.load_script(task)+'source {'+str(folder/'query-contract.tcl')+'}\n'+setup+
        'set context_prefix {'+str(prefix)+'}\nsource {'+str(parent.ASSETS/'context_readout_logical_v2.tcl')+'}\n')
    execute(report_command(task,d,script,'logical_v2_context'),'logical-v2-'+stage+'-readout')
    return labels.read_snapshot(prefix,target,1,pins,nodes,banks,top_ports=ports,ownership_certificate=certificate)
