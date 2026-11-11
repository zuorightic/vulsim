"""Strict stage reader: dynamic and proven constant output bits are exhaustive."""
from .model_fast_preflight import read
from .stage67_analyze_v1 import parse_stage as parent
from .stage67_physical_readout_v1 import table


def parse_stage(folder):
    requests=read(folder/'requests.json');state=read(folder/'mapped-state.json');owners=read(folder/'ownership.json')
    expected={}
    for q in requests.values():
        if q['path_class'] not in ('output_data','output_valid'):continue
        word=next(w for w in state['words'] if w['name']==q['word']);name=word['name'].split('/')[-1]
        constants={r['bit']:r['constant'] for r in word['rows'] if 'constant' in r};ports=[name if word['width']==1 else name+'['+str(i)+']' for i in range(word['width'])]
        wanted={p:constants[i] for i,p in enumerate(ports) if i in constants};dynamic=set(ports)-set(wanted)
        if q.get('constant_to_ports',{})!=wanted or set(q['to_ports'])!=dynamic or len(q['to_ports'])!=len(dynamic):raise ValueError('dynamic/constant top-port partition incomplete or forged')
        if any(p not in owners['top_ports'] or owners['top_ports'][p]['direction']!='output' for p in ports):raise ValueError('actual top-port census differs')
        expected.update(wanted)
    proof=read(folder/'constant-output-proof.json');rows=table(folder/'top-output-logic.tsv');actual={r['port']:r['logic'] for r in rows}
    if len(actual)!=len(rows) or actual!=expected or proof['expected']!=expected:raise ValueError('actual STA constant-output evidence differs')
    value=parent(folder);value.update(proven_constant_output_bits=len(expected),dynamic_and_constant_output_partition_complete=True)
    return value
