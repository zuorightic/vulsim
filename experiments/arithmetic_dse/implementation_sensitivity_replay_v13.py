"""Portable offline replay of train-only implementation sensitivity evidence."""
import argparse
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

from .rtl_sensitivity_v13 import reorder_independent_clocked, commute_expression
from .rebuffer_context_replay_v6 import verify_path


def load(path):
    raw=Path(path).read_bytes()
    return json.loads(gzip.decompress(raw) if str(path).endswith('.gz') else raw)


def close(a,b):
    if isinstance(a,dict):
        if set(a)!=set(b):raise ValueError('replay mapping keys differ')
        for k in a:close(a[k],b[k])
    elif isinstance(a,list):
        if len(a)!=len(b):raise ValueError('replay sequence length differs')
        for x,y in zip(a,b,strict=True):close(x,y)
    elif isinstance(a,(int,float)) and not isinstance(a,bool):
        if abs(a-b)>1e-7*max(1,abs(a)):raise ValueError('replay numerical difference')
    elif a!=b:raise ValueError('replay value differs')


def delta(a,b):return dict(before=a,after=b,absolute=b-a,relative=(b-a)/a if a else None)


def replay(root=None):
    repo=Path(__file__).resolve().parents[2]
    root=Path(root) if root else repo/'experiments/arithmetic/evidence/common_implementation_sensitivity_v13'
    identity=load(root/'identity.json')
    for name,h in identity['files'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=h:raise ValueError('evidence changed '+name)
    for name,h in identity['source_sha256'].items():
        if hashlib.sha256((repo/name).read_bytes()).hexdigest()!=h:raise ValueError('source changed '+name)
    archive=load(root/'source-and-tools.json.gz')['files']
    for name,row in archive.items():
        if hashlib.sha256(row['text'].encode()).hexdigest()!=row['sha256']:raise ValueError('archive changed '+name)
    protocol=load(root/'protocol.json.gz');analysis=load(root/'analysis.json.gz');software=load(root/'software-proof.json.gz')
    pool=load(root/'proof-receipts.json.gz');folds=load(root/'fold-bindings.json.gz')
    if len(protocol['tasks'])!=8 or len(protocol['sources'])!=4 or protocol['independent_sources_locked']!=20:raise ValueError('finite study scope differs')
    if any(analysis[k] for k in ('model_fits','validation_labels_read','independent_labels_read','public_D_changed')):raise ValueError('mechanism evidence used as price qualification')
    if software['status']!='passed' or software['positive_equivalence']!=4 or software['negative_controls']!=4 or not software['source_RTL_unchanged']:raise ValueError('nonvacuous equivalence not complete')
    certificates=0
    with patch('subprocess.Popen',side_effect=AssertionError('unexpected replay subprocess')):
        with patch('builtins.open',side_effect=AssertionError('unexpected transformation file read')):
            with patch('pathlib.Path.open',side_effect=AssertionError('unexpected transformation path read')):
                for s in protocol['sources']:
                    text=pool['source_RTL'][s['id']]
                    if hashlib.sha256(text['original'].encode()).hexdigest()!=s['baseline_RTL_sha256']:raise ValueError('baseline RTL differs')
                    if s['certificate']['kind']=='independent_nonblocking_process_order':variant,certificate=reorder_independent_clocked(text['original'])
                    else:variant,certificate=commute_expression(text['original'],s['certificate']['original'],s['certificate']['swapped'])
                    if variant!=text['variant'] or certificate!=s['certificate'] or variant==text['negative']:raise ValueError('RTL change not registered')
                    certificates+=1
    for s in protocol['sources']:
        proof=pool['equivalence'][s['id']]
        if 'Equivalence successfully proven!' not in proof['positive_log'] or 'Equivalence successfully proven!' in proof['negative_log'] or 'ERROR: Found' not in proof['negative_log'] or 'unproven' not in proof['negative_log']:raise ValueError('wrong equivalence conclusion')
        for kind in ('positive','negative'):
            script=proof[kind+'_script']
            if script.count('setattr -mod -unset keep_hierarchy')!=2 or script.count('setattr -unset keep_hierarchy')!=2 or script.count('select -assert-none')!=2:raise ValueError('hierarchy gate missing')
        fold=next(x for x in folds['bindings'] if x['source']==s['id'])
        if not fold['future_all_T_and_parent_family_joint_exclusion'] or fold['enters_fit_now']:raise ValueError('parent family not bound')
    sf=[r['fold'] for r in folds['bindings'] if r['family']=='S']
    if len(sf)!=2 or sf[0]!=sf[1]:raise ValueError('paired reset sources separated')
    first=pool['first_failed_preflight']
    if 'Equivalence successfully proven!' not in first['negative_log'] or not first['failure']['failed_negative_control']:raise ValueError('first proof failure erased')
    for name,record in pool['physical_CEC'].items():
        receipt=record['receipt']
        if receipt['status']!='passed' or receipt['version']!='m2-live-structural-cec-v4':raise ValueError('physical CEC not passed')
        if hashlib.sha256(record['before'].encode()).hexdigest()!=receipt['before_sha256'] or hashlib.sha256(record['after'].encode()).hexdigest()!=receipt['after_sha256']:raise ValueError('CEC pair identity differs')
        if 'Networks are equivalent' not in record['positive_log']:raise ValueError('physical positive CEC absent')
        for key in receipt['negative_controls']:
            if 'Networks are NOT EQUIVALENT' not in record['negative_logs'][key]:raise ValueError('physical negative CEC absent')
    pathproof=load(root/'path-proof-cases.json.gz');negatives=0
    for case in pathproof['cases']:
        verify_path(case,pathproof['pin_classes'])
        if case['arcs']:
            master,src,dst=case['arcs'][0];bad=deepcopy(pathproof['pin_classes']);bad[master]['timing_arcs']=[x for x in bad[master]['timing_arcs'] if x!=[src,dst]]
            try:verify_path(case,bad)
            except ValueError:negatives+=1
            else:raise ValueError('missing Liberty arc accepted')
    if negatives!=pathproof['missing_arc_negatives']:raise ValueError('negative path count differs')
    impl=analysis['implementations'];comparisons=0;paths=0
    for row in analysis['comparisons']:
        left,right=row['comparison'].split('_to_')
        pair=[next(x for x in impl if x['source']==row['source'] and x['kind']==kind) for kind in (left,right)]
        a,b=[next(s for s in x['stages'] if s['stage']==row['stage']) for x in pair]
        if row['identical_normalized_mapped_netlist']!=(pair[0]['normalized_mapped_netlist_sha256']==pair[1]['normalized_mapped_netlist_sha256']):raise ValueError('mapped identity comparison differs')
        close(row['total_area'],delta(a['area_um2'],b['area_um2']))
        close(row['setup_slack'],delta(a['setup_worst_slack_ps'],b['setup_worst_slack_ps']))
        close(row['hold_slack'],delta(a['hold_worst_slack_ps'],b['hold_worst_slack_ps']))
        if row['identical_master_census']!=(a['census']['master_counts']==b['census']['master_counts']):raise ValueError('census comparison differs')
        if row['family']=='S':
            close(row['bank_valid_R'],delta(a['bank_valid_R_ps'],b['bank_valid_R_ps']))
            by={x['label']['id']:x for x in b['paths']}
            for source,observed in zip(a['paths'],row['paths'],strict=True):
                target=by[source['label']['id']]
                for key,field in [('R','R_ps'),('cell','cell_ps'),('wire','wire_ps')]:close(observed[key],delta(source[field],target[field]))
                for key,field in [('d','delay_ps'),('H','H_ps')]:close(observed[key],delta(source['label'][field],target['label'][field]))
                for record in (source,target):
                    label=record['label'];period=pair[0]['T_ps'];close(record['R_ps'],(.8 if label['kind']=='port' else 1)*period-label['slack_ps']);close(record['R_ps'],label['delay_ps']+label['H_ps'])
                paths+=1
        else:
            close(row['comb_area'],delta(a['comb_area_um2'],b['comb_area_um2']));close(row['operator_delay'],delta(a['delay_ps'],b['delay_ps']))
        comparisons+=1
    for row in analysis['reset_contrasts']:
        pair=[next(x for x in impl if x['source']==s['id'] and x['kind']==row['kind']) for s in protocol['sources'] if s['family']=='S']
        a,b=[next(y for y in x['stages'] if y['stage']==row['stage']) for x in pair]
        close(row['bank_valid_R'],delta(a['bank_valid_R_ps'],b['bank_valid_R_ps']))
    settlement=load(root/'settlement.json');increment=settlement['increment']
    if increment['synth']!=8 or increment['grt']!=8 or increment['final'] or settlement['physical_failures'] or settlement['automatic_retries'] or settlement['after']['pending']:raise ValueError('physical settlement differs')
    if settlement['support_exit_nonzero']!=4 or settlement['failed_semantic_preflight_attempts']!=1:raise ValueError('negative/failed proof accounting differs')
    counts={stage:sum(e['stage']==stage for e in settlement['entries']) for stage in ('synth','grt')}
    if counts!={'synth':8,'grt':8}:raise ValueError('paid stage entries differ')
    return dict(status='passed',physical_points=8,existing_parent_sources=4,new_independent_sources=0,
        certificates=certificates,nonvacuous_equivalence=4,negative_equivalence_controls=4,
        retained_failed_preflights=1,physical_CEC_pairs=len(pool['physical_CEC']),strict_S_paths=len(pathproof['cases']),
        missing_arc_negatives=negatives,comparisons=comparisons,compared_S_paths=paths,
        source_files=len(identity['source_sha256']),archived_text_files=len(archive),
        new_model_fits=0,online_EDA_calls=0,independent_labels_read=False,public_D_changed=False,full_D_ready=False)


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root',type=Path);args=ap.parse_args()
    print(json.dumps(replay(args.root),indent=2))
