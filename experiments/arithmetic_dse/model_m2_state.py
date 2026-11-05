"""Compare actual Liberty-derived state graphs across drive-strength changes."""
import hashlib
import json


def state_graph(model):
    if set(model.get('attributes',{}))-{'area'}:raise ValueError('unsupported state module attributes')
    for net in model.get('netnames',{}).values():
        if set(net.get('attributes',{}))-{'capacitance'}:raise ValueError('unsupported functional state net attributes')
    cells=[]
    for cell in model['cells'].values():
        if cell.get('attributes') or not cell['type'].startswith('$_'):raise ValueError('unsupported state primitive')
        cells.append({k:cell.get(k,{}) for k in ('type','parameters','port_directions','connections')})
    # Preserve every primitive, edge/polarity parameter, pin direction and bit
    # connection. Numeric bit renaming may conservatively reject a valid pair.
    # Only nonfunctional cell/net names and area/capacitance are omitted.
    return {'ports':model['ports'],'parameters':model.get('parameter_default_values',{}),
            'cells':sorted(cells,key=lambda c:json.dumps(c,sort_keys=True))}


def compare_interfaces(before,after):
    b,bs,bc=before;a,as_,ac=after
    if b!=a or bc!=ac or set(bs)!=set(as_):raise ValueError('state boundary or instance set changed')
    changes=[]
    for name,left in bs.items():
        right=as_[name]
        if left['pins']!=right['pins'] or left['parameters']!=right['parameters']:
            raise ValueError('state pin/parameter correspondence changed')
        lg=state_graph(left['model']);rg=state_graph(right['model'])
        if lg!=rg:raise ValueError('actual sequential logical graph differs')
        if left['type']!=right['type']:
            changes.append({'instance':name,'before_master':left['type'],'after_master':right['type'],
                'logical_graph_sha256':hashlib.sha256(json.dumps(lg,sort_keys=True,separators=(',',':')).encode()).hexdigest()})
    return {'state_count':len(bs),'drive_master_changes':changes,'all_logical_state_graphs_equal':True}
