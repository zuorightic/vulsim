"""Train-only, portable characterization boundary receipts for equivalent T.

This summarizes existing timing responsibility. It never refits an arithmetic
response and never reads application PPA or validation/independent labels.
"""
import base64
from collections import defaultdict
import gzip
import hashlib
import json
import math
from pathlib import Path
from statistics import median

ROOT=Path(__file__).resolve().parents[2]
VERSION='characterization-body-window-diagnostic-v1'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def canonical(value):
    # JSON object keys are strings on disk. Normalize BEFORE sorting so an
    # owner-keyed receipt hashes identically before and after JSON round-trip.
    def normalize(v):
        if isinstance(v,dict):return {str(k):normalize(x) for k,x in v.items()}
        if isinstance(v,(tuple,list)):return [normalize(x) for x in v]
        return v
    return json.dumps(normalize(value),sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def collect_training_receipts():
    sources=[('v10','experiments/arithmetic/evidence/common_transition_incidence_v10/train-data.json.gz'),
             ('inherited_mul','experiments/arithmetic/evidence/common_model_repair_v1/unified-fit--operator-train-data.json.gz')]
    rows=[];labels={};inputs=[];support={}
    for kind,name in sources:
        raw=(ROOT/name).read_bytes();data=json.loads(gzip.decompress(raw))
        if any(data.get(k,False) for k in ('validation_used','validation_labels_read','independent_labels_read')):
            raise ValueError('characterization boundary source must be train-only')
        inputs.append(dict(path=name,sha256=sha(raw)))
        families={f:data['data'][f] for f in ('Add','Mux','G')} if kind=='v10' else {
            'Mul':[r for r in data['rows'] if r.get('operation',r.get('query',{}).get('local_context',{}).get('producer',{}).get('operation'))=='mul']}
        for family,selected in families.items():
            for row in selected:
                if row['role']!='train':raise ValueError('nontrain boundary label')
                path=row.get('label_path',row.get('physical_label_path'))
                expected=row.get('label_sha256',row.get('physical_label_sha256'))
                label_raw=Path(path).read_bytes()
                if sha(label_raw)!=expected:raise ValueError('raw train label hash mismatch')
                labels[expected]=base64.b64encode(label_raw).decode()
                directory=Path(row.get('directory',Path(path).parent))
                checks={}
                for name in ('mapped-contract.json','query-contract.json','synth.command.json',
                             'effective-environment.txt','input.sv','manifest.json'):
                    data=(directory/name).read_bytes();identity=sha(data)
                    checks[name]=identity;support[identity]=base64.b64encode(data).decode()
                rows.append(dict(family=family,source=row['source'],
                    source_group=row.get('source_group',row['source']),role='train',
                    target_ps=row['target_ps'],query=row['query'],label_sha256=expected,
                    original_label_path=path,source_file=inputs[-1]['path'],support_sha256=checks))
    return dict(version=VERSION,inputs=inputs,rows=rows,raw_labels_base64=labels,
                sampling_support_base64=support,
                application_labels_read=False,validation_labels_read=False,independent_labels_read=False)


def derive_contract(receipts):
    if receipts['version']!=VERSION or any(receipts[k] for k in (
            'application_labels_read','validation_labels_read','independent_labels_read')):
        raise ValueError('wrong characterization receipts/data roles')
    groups=defaultdict(lambda:defaultdict(list));audit=[];profiles=set()
    for r in receipts['rows']:
        raw=base64.b64decode(receipts['raw_labels_base64'][r['label_sha256']],validate=True)
        if sha(raw)!=r['label_sha256'] or r['role']!='train':raise ValueError('boundary receipt changed')
        label=json.loads(raw);paths=label['path_decompositions'];q=r['query'];target=r['target_ps']
        support={}
        for name,expected in r['support_sha256'].items():
            data=base64.b64decode(receipts['sampling_support_base64'][expected],validate=True)
            if sha(data)!=expected:raise ValueError('sampling support hash changed')
            support[name]=data
        mapped=json.loads(support['mapped-contract.json']);manifest=json.loads(support['manifest.json'])
        synth=json.loads(support['synth.command.json'])
        env=dict(line.strip().split('=',1) for line in support['effective-environment.txt'].decode().splitlines() if '=' in line)
        abc=[float(s.split('=',1)[1]) for s in synth['command'] if s.startswith('ABC_CLOCK_PERIOD_IN_PS=')]
        if abc!=[float(target)] or float(env['ABC_CLOCK_PERIOD_IN_PS'])!=target or synth['exit_code']!=0:
            raise ValueError('actual characterization ABC target differs')
        if manifest['period_ps']!=target or manifest['abc_target_ps']!=target:
            raise ValueError('sampling manifest timing context differs')
        if sha(support['mapped-contract.json'])!=label['mapped_contract_sha256'] or mapped['status']!='passed':
            raise ValueError('sampling launch/capture contract differs')
        check=label['stored_SDC_check']
        if label['stage']!='grt' or label['source_role']!='train' or check['status']!='passed':
            raise ValueError('incompatible characterization flow')
        profile=label['metrics']['platform_profile_sha256'];profiles.add(profile)
        if label['metrics']['target_platform']!='asap7' or label['metrics']['target_period_ps']!=target:
            raise ValueError('characterization label platform/period differs')
        period=check['actual_clock_periods_native']['core_clk']*check['time_to_ps']
        if abs(period-target)>1e-3:raise ValueError('SDC T differs from training request')
        if r['family']!='G':
            if q['flow_context']['target_period_ps']!=target or q['flow_context']['abc_target_ps']!=target:
                raise ValueError('characterization SDC/ABC query mismatch')
            if q['flow_context']['profile_sha256']!=profile:
                raise ValueError('characterization query profile differs')
        entry={k:r[k] for k in ('family','source','source_group','target_ps','label_sha256')}
        entry.update(actual_ABC_ps=abc[0],actual_SDC_ps=period,
                     sampling_RTL_sha256=r['support_sha256']['input.sv'],
                     query_contract_sha256=r['support_sha256']['query-contract.json'])
        if len(paths)!=1:
            audit.append(dict(entry,status='excluded',reason='aggregate_min_slack_without_per_path_slacks',path_count=len(paths)))
            continue
        p=paths[0]
        if not p['increments_owned_exactly_once'] or 'producer' not in p['node_delay_ps']:
            raise ValueError('unowned or producer-free characterization path')
        # Slack and arithmetic MUST refer to the same path. Independently
        # maximized operator_delay_ps is intentionally not used here.
        arithmetic=sum(p['node_delay_ps'].values())
        h=target-label['data_setup_slack_ps']-arithmetic
        if not math.isfinite(h) or h<0:raise ValueError('invalid characterized boundary')
        groups[r['family']][r['source_group']].append(h)
        audit.append(dict(entry,status='eligible',alpha=1.,H_char_ps=h,
            path_arithmetic_ps=arithmetic,data_setup_slack_ps=label['data_setup_slack_ps'],
            path_Q_to_D_ps=p['Q_to_D_ps'],other_arithmetic_owners=[n for n in p['node_order'] if n!='producer']))
    families={}
    for family in ('Mul','Add','Mux','G'):
        source_values={s:median(v) for s,v in sorted(groups[family].items())}
        if not source_values:raise ValueError('no identifiable training boundary for '+family)
        values=[v for vs in groups[family].values() for v in vs]
        families[family]=dict(alpha=1.,H_char_ps=median(source_values.values()),
            source_medians_ps=source_values,sources=len(source_values),eligible_rows=len(values),
            H_row_range_ps=[min(values),max(values)],
            excluded_rows=sum(r['family']==family and r['status']=='excluded' for r in audit))
    if len(profiles)!=1:raise ValueError('mixed characterization platform profiles')
    return dict(version=VERSION,profile_sha256=next(iter(profiles)),qualified=False,precision_validation_pending=True,
        formula='min_p(alpha_p*T - H_char,p - D_other,char,p)',
        summary_rule='median per whole source, then median across sources; family-shared fixed H',
        derivation='T_char - same-path data_setup_slack - sum(same-path arithmetic ownership)',
        shell='service reset/valid-held launch; unconditional data capture; observer outside data path',
        boundary_includes='FF clock-to-Q/setup/uncertainty/skew, service logic, external wires; excludes ALL arithmetic',
        direct_capture_alpha=1.,consumers='immediate characterization consumer at same T; no downstream chain',
        virtual_G_consumer='actual region query, diagnostic context adaptation; embedded validation pending',
        whole_design_boundary_separate=True,virtual_register_area_added=False,
        operator_response_refitted=False,application_PPA_used=False,families=families,audit=audit,
        receipts_sha256=sha(canonical(receipts)))
