"""Collect a logical-ownership label from one already loaded stage database.

The injected executor charges report-only leaves to the original task Ledger;
there is no nested job, synthesis, routing or physical netlist modification.
"""
from pathlib import Path
import csv

from .model_fast_preflight import read,write
from . import model_logical_ownership_v2 as ownership,model_logical_labels_v1 as labels
from . import operator_ownership_replay_v1 as replay


def collect(folder,stage,target,pins,nodes,banks,execute):
    task=dict(folder=str(folder),stage=stage,target_ps=target);d=folder/('logical-'+stage);d.mkdir(exist_ok=False)
    script=d/'census.tcl';prefix=d/'census'
    script.write_text(replay.load_script(task)+'set ownership_prefix {'+str(prefix)+'}\nsource {'+str(replay.ASSETS/'ownership_census_v1.tcl')+'}\n')
    execute(replay.report_command(task,d,script,'logical_census'),'logical-'+stage+'-census')
    packet=dict(origin='physical_snapshot',period_ps=target,time_to_ps=1,instances=dict(line.split('\t') for line in Path(str(prefix)+'_instances.tsv').read_text().splitlines()),liberty=pins,
        connections={r['instance']+'/'+r['pin']:dict(direction=r['direction'],net=r['net']) for r in replay.table(Path(str(prefix)+'_connections.tsv'))},
        clock_nets=[r['net'] for r in replay.table(Path(str(prefix)+'_clock_nets.tsv'))],nodes={},pin_logic={},data_requests={},data_paths={})
    ports={r['port']:dict(direction=r['direction'],net=r['net']) for r in replay.table(Path(str(prefix)+'_ports.tsv'))}
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
    script.write_text(replay.load_script(task)+'source {'+str(folder/'query-contract.tcl')+'}\n'+setup+
        'set context_prefix {'+str(prefix)+'}\nsource {'+str(replay.ASSETS/'context_readout_logical_v1.tcl')+'}\n')
    execute(replay.report_command(task,d,script,'logical_context'),'logical-'+stage+'-readout')
    return labels.read_snapshot(prefix,target,1,pins,nodes,banks,top_ports=ports,ownership_certificate=certificate)
