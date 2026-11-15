"""Steps 4 regression on portable, already consumed component/composition data.

No final application labels, locked sources, fitting, or EDA are used. The
inverse diagnostic uses an observed window; it is not a new blind experiment.
"""
import argparse
import base64
from collections import Counter, defaultdict
from copy import deepcopy
import gzip
import itertools
import json
import math
from pathlib import Path
from statistics import median

from .sampling_time_contract import ROOT, canonical, sha
from .workload_equivalent_run import read, write, compressed
from .workload_equivalent import CharacterizationAdapter, request_at, optimize
from .workload_diagnostic import DiagnosticPrices
from .workload_demand import Graph
from . import wide_arithmetic as arithmetic

BASE=ROOT/'experiments/arithmetic/evidence/workload_equivalent_mac32_v1'
DEFAULT=ROOT/'experiments/arithmetic/evidence/workload_equivalent_steps45_v1'


def wide_spec(s):
    if 'arithmetic_width' in s:
        arithmetic.validate(s)
        return deepcopy(s)
    op={'addcarry':'adc'}.get(s['operation'],s['operation'])
    a,b,w=s['lhs_width'],s['rhs_width'],s['result_width']
    return arithmetic.spec(op,a,b,w,control=s.get('carry','zero'),
        za=int(s.get('lhs_zero_hex','0'),16),zb=int(s.get('rhs_zero_hex','0'),16),
        oa=int(s.get('lhs_one_hex','0'),16),ob=int(s.get('rhs_one_hex','0'),16),
        banks=s.get('capture_banks',1))


def query_v2(query):
    """Preserve actual maps/loads, enrich old modulo specs without truncation."""
    q=deepcopy(query)
    if 'flow_context' not in q:return q
    q['version']='arithmetic-workload-query-v2'
    q['local_context']['producer']=wide_spec(q['local_context']['producer'])
    for c in q['local_context']['consumers']:
        c['spec']=wide_spec(c['spec'])
        c['operation']=c['spec']['operation']
        for binding in c['bindings']:binding.setdefault('role','data')
    return q


def portable_pool(folder):
    path=ROOT/'experiments/arithmetic/evidence'/folder
    m=read(path/'manifest.json');parts=[]
    for name,expected in sorted(m['chunks'].items()):
        raw=(path/name).read_bytes()
        if sha(raw)!=expected:raise ValueError('composition chunk changed')
        parts.append(raw)
    raw=gzip.decompress(b''.join(parts))
    if sha(raw)!=m['payload_sha256']:raise ValueError('composition payload changed')
    pool=json.loads(raw)
    # Both archive formats bind individual text bytes as well as the payload.
    index=m.get('files')
    if index:
        for name,expected in index.items():
            if sha(pool[name].encode())!=expected:raise ValueError('composition member changed')
    return pool,sha((path/'manifest.json').read_bytes())


def collect(root):
    root=Path(root);old=read(BASE/'characterization-train-receipts.json.gz')
    rows=[];excluded=[];origins=[]
    for r in old['rows']:
        raw=base64.b64decode(old['raw_labels_base64'][r['label_sha256']])
        if sha(raw)!=r['label_sha256']:raise ValueError('train label changed')
        rows.append(dict(r,label=json.loads(raw),role='train_diagnostic'))
    path=ROOT/'experiments/arithmetic/evidence/common_transition_incidence_v10/evaluation--data.json.gz'
    data=read(path);origins.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path.read_bytes())))
    for i,r in enumerate(data['rows']):
        if r.get('role')!='validation':
            excluded.append(dict(index=i,source=r['source'],reason='missing_or_nonvalidation_role'));continue
        name=r.get('label_path',r.get('physical_label_path'))
        expected=r.get('label_sha256',r.get('physical_label_sha256'))
        raw=Path(name).read_bytes()
        if sha(raw)!=expected:raise ValueError('regression physical label changed')
        q=r['query'];family='G' if 'flow_context' not in q else {
            'add':'Add','adc':'Add','mul':'Mul','mux':'Mux'}[q['local_context']['producer']['operation']]
        rows.append(dict(family=family,source=r['source'],source_group=r.get('source_group',r['source']),
            target_ps=r['target_ps'],query=q,label=json.loads(raw),label_sha256=expected,
            original_label_path=name,role='consumed_validation_regression'))
    combinations=[]
    for folder,kinds in [('step67_combination_batch1_v2',['parallel','bypass']),('step67_joint_pilot_v2',['serial'])]:
        pool,identity=portable_pool(folder);origins.append(dict(archive=folder,manifest_sha256=identity))
        for kind in kinds:
            for number in (0,1):
                task=f'{kind}-placement-{number}-T1500'
                label_name=f'expected/{task}-grt-labels.json'
                if kind=='serial':
                    export=json.loads(pool['software/serial/export.json']);v=export['variants'][number]
                    target=next(t for t in v['targets'] if t['target_ps']==1500)
                    queries=target['queries'];rich=None
                else:
                    pred=json.loads(pool[f'batch/inputs/{task}/prediction.json'])
                    export=json.loads(pool[f'batch/inputs/{task}/export.json'])
                    v=next(x for x in export['variants'] if x['id']==f'placement-{number}')
                    queries=pred['queries'];rich=pred['graph']
                combinations.append(dict(task=task,kind=kind,placement=number,T_clk_ps=1500,
                    export_graph=export['graph'],rich_graph=rich,view=v,queries=queries,
                    label=json.loads(pool[label_name]),label_sha256=sha(pool[label_name].encode()),
                    archive=folder,archive_manifest_sha256=identity,
                    role='consumed_composition_regression'))
    compressed(root/'reuse-inputs.json.gz',dict(rows=rows,excluded=excluded,origins=origins,
        combinations=combinations,application_PPA_read=False,independent_sources_read=False))
    return dict(rows=len(rows),excluded=len(excluded),combinations=len(combinations))


def quantile(values,p):
    values=sorted(values)
    if not values:return None
    at=(len(values)-1)*p;lo=int(at);hi=min(lo+1,len(values)-1)
    return values[lo]*(hi-at)+values[hi]*(at-lo) if hi!=lo else values[lo]


def error_metrics(rows,metric):
    groups=defaultdict(list)
    for r in rows:
        if metric in r:groups[r['source']].append(abs(r[metric]))
    per={s:dict(rows=len(v),median_APE=median(v),P95_APE=quantile(v,.95)) for s,v in sorted(groups.items())}
    values=[v['median_APE'] for v in per.values()]
    med=median(values) if values else None;p95=quantile(values,.95)
    return dict(rows=sum(len(v) for v in groups.values()),sources=len(values),
        source_median_APE=med,source_P95_APE=p95,per_source=per,
        gate_pass=bool(values and med<=.15 and p95<=.35 and max(values)<=.5))


def single_owner(q,prices,contract):
    owners=dict(operators=[],G_regions=[])
    if 'flow_context' in q:owners['operators']=[dict(node=0,query=q)]
    else:owners['G_regions']=[dict(root=0,query=q)]
    return CharacterizationAdapter(owners,prices,contract)


def component_regression(inputs,prices,contract):
    out=[]
    for r in inputs['rows']:
        q=query_v2(r['query']);label=r['label'];family=r['family'];t=r['target_ps']
        flow=label.get('metrics',{})
        compatible=(label.get('stage')=='grt' and flow.get('platform_profile_sha256')==contract['profile_sha256']
                    and label.get('stored_SDC_check',{}).get('status')=='passed')
        row={k:r[k] for k in ('family','source','source_group','role','target_ps','label_sha256')}
        if not compatible:
            out.append(dict(row,status='flow_incompatible'));continue
        price=prices.reduction_price if family=='G' else prices.operator_price
        baseline=price(q)
        actual=dict(delay_ps=label['operator_delay_ps'],area_um2=label['comb_area_um2'])
        row.update(status='baseline_only',actual=actual,baseline=baseline,
            baseline_delay_error=baseline['delay_ps']/actual['delay_ps']-1,
            baseline_area_error=baseline['area_um2']/actual['area_um2']-1)
        paths=label['path_decompositions']
        if len(paths)!=1:
            row['inverse_excluded']='aggregate_min_slack_has_no_same_path_identity';out.append(row);continue
        path=paths[0]
        if not path.get('increments_owned_exactly_once') or 'producer' not in path['node_delay_ps']:
            raise ValueError('unowned characterization path')
        h=t-label['data_setup_slack_ps']-sum(path['node_delay_ps'].values())
        other=sum(v for n,v in path['node_delay_ps'].items() if n!='producer')
        budget=t-h-other
        row.update(observed_H_ps=h,observed_other_arithmetic_ps=other,observed_body_window_ps=budget)
        if budget<=0:
            row['inverse_excluded']='nonpositive_observed_window';out.append(row);continue
        adapter=single_owner(q,prices,contract);conv=adapter.convert(0,budget);row['inverse']=conv
        if conv['status']=='converted':
            root=min(conv['roots'],key=lambda x:abs(x['tau_ps']-t))
            # Closest-to-original root is a diagnostic comparison only, never a
            # root-selection policy for online inference.
            row.update(status='inverse_diagnostic',equivalent=root['price'],tau_ps=root['tau_ps'],
                request_error=root['tau_ps']/t-1,
                equivalent_delay_error=root['price']['delay_ps']/actual['delay_ps']-1,
                equivalent_area_error=root['price']['area_um2']/actual['area_um2']-1)
        sweep=[]
        for fraction in (.5,1.,1.5):
            c=adapter.convert(0,budget*fraction)
            sweep.append(dict(budget_ps=budget*fraction,status=c['status'],
                roots=[{k:x[k] for k in ('tau_ps','price','local_request_met')} for x in c['roots']]))
        row['budget_sweep']=sweep;out.append(row)
    summaries={}
    for role,family in sorted({(r['role'],r['family']) for r in out}):
        subset=[r for r in out if r['role']==role and r['family']==family]
        summaries[role+'/'+family]={m:error_metrics(subset,m) for m in (
            'baseline_delay_error','baseline_area_error','equivalent_delay_error','equivalent_area_error','request_error')}
    pairs=[]
    for (role,source),rs in itertools.groupby(sorted(out,key=lambda r:(r['role'],r['source'],r['target_ps'])),key=lambda r:(r['role'],r['source'])):
        valid=[r for r in rs if 'actual' in r]
        for a,b in itertools.combinations(valid,2):
            if a['target_ps']==b['target_ps']:continue
            for metric in ('delay_ps','area_um2'):
                actual=b['actual'][metric]/a['actual'][metric]-1
                predicted=b['baseline'][metric]/a['baseline'][metric]-1
                pairs.append(dict(source=source,role=role,metric=metric,targets=[a['target_ps'],b['target_ps']],
                    actual_response=actual,predicted_response=predicted,
                    actual_tie=abs(actual)<=.05,predicted_tie=abs(predicted)<=.05,
                    correct_direction_or_tie=abs(actual)<=.05 or actual*predicted>0))
    return dict(rows=out,summary=summaries,response_pairs=pairs,
        physical_embedded_request_validation=False,inverse_diagnostic_not_blind=True)


def adapted_combination(item):
    """Timing-only legacy graph adapter; use exact original owner queries/maps.

    Serial archive has only parent edges. Transparent nodes have zero timing;
    this adapter makes no claim to reconstruct bit-level functional semantics.
    """
    original=item['export_graph'];queries={r['trace']['node']:query_v2(r['descriptor']) for r in item['queries']}
    nodes=[]
    for n in original['nodes']:
        i=n['id'];op=queries[i]['local_context']['producer']['operation'] if i in queries else 'input' if not n['parents'] else 'wire'
        nodes.append(dict(id=i,width=n['width'],operation=op,
            operands=[dict(node=p,width=original['nodes'][p]['width'],literal_hex=None,signed=False) for p in n['parents']],
            constant=n['constant'],known_zero_hex='0',known_one_hex='0',lo=0,hi=0,bit=0))
    raw=dict(version='prospective-workload-graph-v1',nodes=nodes,ports=original['ports'],regions=[])
    graph=Graph(raw);view=dict(directory=str(item['placement']),placement=item['view']['placement'])
    state=item['view']['state'];owners=dict(graph_sha256=state['graph_sha256'],layout_sha256=state['layout_sha256'],
        target_ps=1500,operators=[dict(node=i,query=q,stage=view['placement'][i]) for i,q in queries.items()],
        G_regions=[],functional_logic=[])
    return graph,view,state,owners


def combinations_regression(inputs,prices,contract):
    out=[]
    for item in inputs['combinations']:
        graph,view,state,owners=adapted_combination(item)
        result=optimize(graph,view,state,owners,prices,contract)
        label=item['label'];physical=label['whole_shell_metrics'];node_errors=[]
        for mode,pred in [('global',result['baseline']),('equivalent',result['prediction'])]:
            for owner in pred['owners']:
                name='node_'+str(owner['node'])
                if name not in label['nodes']:raise ValueError('owner/physical label mismatch')
                actual=label['nodes'][name]
                node_errors.append(dict(mode=mode,node=owner['node'],
                    delay_error=owner['delay_ps']/actual['operator_delay_ps']-1,
                    area_error=owner['area_um2']/actual['comb_area_um2']-1))
        stages=[]
        for stage in range(2):
            paths=[p for p in label['functional_paths'] if p['stage']==stage and p['path_class'] in ('native_data','external_data')]
            if not paths:raise ValueError('composition data-stage coverage missing')
            measured=max(1500-p['slack_ps'] for p in paths)
            stages.append(dict(stage=stage,measured_data_required_ps=measured,
                global_predicted_ps=result['baseline']['stages'][stage]['required_ps'],
                equivalent_predicted_ps=result['prediction']['stages'][stage]['required_ps']))
        out.append(dict(task=item['task'],kind=item['kind'],placement=item['placement'],source=item['kind'],
            label_sha256=item['label_sha256'],status=result['status'],qualified=False,
            adapter='legacy parent-edge timing and exact queries; not bit-level functional adapter',
            global_prediction=result['baseline'],equivalent_prediction=result['prediction'],
            optimization=result,node_errors=node_errors,stages=stages,
            actual_Tmin_ps=physical['minimum_clock_period_ps'],actual_area_um2=physical['cell_area_um2'],
            timing_coverage_complete=physical['timing_coverage_complete'],
            equivalent_delay_error=result['prediction']['critical_required_ps']/physical['minimum_clock_period_ps']-1,
            equivalent_area_error=result['prediction']['total_area_um2']/physical['cell_area_um2']-1))
        Graph.origins.cache_clear();Graph.roots.cache_clear()
    ranking=[]
    for kind in ('serial','parallel','bypass'):
        a,b=sorted([r for r in out if r['kind']==kind],key=lambda r:r['placement'])
        for metric,actual in [('critical_required_ps','actual_Tmin_ps'),('total_area_um2','actual_area_um2')]:
            delta=b[actual]/a[actual]-1
            pred=b['equivalent_prediction'][metric]/a['equivalent_prediction'][metric]-1
            ranking.append(dict(source=kind,metric=metric,actual_relative_delta=delta,predicted_relative_delta=pred,
                actual_tie=abs(delta)<=.05,correct_direction_or_tie=abs(delta)<=.05 or delta*pred>0))
    return dict(rows=out,ranking=ranking,
        summary={m:error_metrics(out,m) for m in ('equivalent_delay_error','equivalent_area_error')},
        virtual_G_embedded_validation=False,independent_qualification=False)


def run(root=DEFAULT,output=None):
    root=Path(root);inputs=read(root/'reuse-inputs.json.gz');prices=DiagnosticPrices(read(BASE/'diagnostic-model.json'))
    contract=read(BASE/'characterization-contract.json');out=Path(output or root/'validation');out.mkdir(exist_ok=False)
    component=component_regression(inputs,prices,contract);compressed(out/'components.json.gz',component)
    combination=combinations_regression(inputs,prices,contract);compressed(out/'combinations.json.gz',combination)
    gates={key:{name:value['gate_pass'] for name,value in metrics.items()} for key,metrics in component['summary'].items()}
    summary=dict(status='step4_evaluation_complete_diagnostic_only',qualified=False,
        component_rows=len(component['rows']),component_status=dict(Counter(r['status'] for r in component['rows'])),
        excluded_rows=inputs['excluded'],combinations=len(combination['rows']),component_gates=gates,
        component_summary=component['summary'],combination_summary=combination['summary'],ranking=combination['ranking'],
        response_pairs=len(component['response_pairs']),model_response_refits=0,EDA_calls=0,
        calibration_decision='retain unchanged shared functions; boundary/response and S gaps need new compatible evidence, not regression fitting',
        qualification_gaps=['inverse test is observed-window diagnostic','no new embedded local-request physical measurements',
            'Mul -> virtual G sampling shell not physically matched','S/shared full-stage qualification failures retained',
            'legacy compositions already consumed; independent sources remain locked'])
    write(out/'summary.json',summary)
    write(out/'manifest.json',dict(inputs_sha256=sha((root/'reuse-inputs.json.gz').read_bytes()),
        protocol_sha256=sha((root/'protocol.json').read_bytes()),model_sha256=sha((BASE/'diagnostic-model.json').read_bytes()),
        contract_sha256=sha((BASE/'characterization-contract.json').read_bytes()),
        files={str(p.relative_to(out)):sha(p.read_bytes()) for p in sorted(out.iterdir()) if p.is_file()}))
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['collect','run']);p.add_argument('--root',type=Path,default=DEFAULT)
    args=p.parse_args();print(json.dumps(collect(args.root) if args.action=='collect' else run(args.root),ensure_ascii=False,indent=2))
