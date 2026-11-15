#!/usr/bin/env python3
"""Replay saved measurements of a user-stopped matrix; standard library only."""
import base64
from collections import Counter
from copy import deepcopy
import csv
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import re


def digest(data):return hashlib.sha256(data).hexdigest()


def check_measurement(files,row):
    def read(name):return json.loads(files[name])
    m=row['measurement']
    if m['status']!='completed':
        if m['status'] not in ('failed','failed_before_manifest','clock_readout_failed'):
            raise ValueError('unsettled physical result')
        if not m['failure_reason'] or m['full_setup_minimum_period_ps'] is not None or m['maximum_frequency_MHz'] is not None:
            raise ValueError('failed measurement lacks reason or received fabricated clock numbers')
        if 'manifest' in m and digest(files[m['manifest']])!=m['manifest_sha256']:
            raise ValueError('retained failure manifest changed')
        return
    if digest(files[m['manifest']])!=m['manifest_sha256']:raise ValueError('physical manifest changed')
    if digest(files[m['clock_readout']])!=m['clock_readout_sha256']:raise ValueError('clock receipt changed')
    physical=read(m['manifest']);directory=str(Path(m['manifest']).parent)
    if digest(files[directory+'/input.sv'])!=row['rtl_sha256']:raise ValueError('measured RTL differs from selected RTL')
    metric=next(x for x in physical['metrics'] if x['stage']=='grt')
    for key in ('cell_area_um2','functional_cell_area_um2','sequential_area_um2',
                'sequential_cells','physical_only_area_um2','setup_worst_slack_ps',
                'hold_worst_slack_ps','setup_tns_ps','hold_tns_ps','timing_coverage_complete'):
        if m[key]!=metric[key]:raise ValueError('comparison differs from measured metric: '+key)
    for name,h in physical['evidence_sha256'].items():
        path=directory+'/'+name
        if path in files and digest(files[path])!=h:raise ValueError('archived physical evidence changed')
    c=read(m['clock_readout']);classes=c['classes'];limits=[]
    for name,h in c['fixed_inputs'].items():
        if physical['evidence_sha256'].get(str(Path(name).relative_to(directory)))!=h:
            raise ValueError('clock readout is not bound to measured grt checkpoint')
    raw=metric['raw_reports_prefix']
    scale=metric['raw_report_units']['time']['to_ps']
    for key,suffix,pattern in (
            ('setup_worst_slack_ps','_setup.rpt',r'worst slack max\s+([-+\d.eE]+)'),
            ('hold_worst_slack_ps','_hold.rpt',r'worst slack min\s+([-+\d.eE]+)'),
            ('setup_tns_ps','_setup_tns.rpt',r'tns max\s+([-+\d.eE]+)'),
            ('hold_tns_ps','_hold_tns.rpt',r'tns min\s+([-+\d.eE]+)')):
        match=re.search(pattern,files[raw+suffix].decode())
        if not match or abs(float(match[1])*scale-m[key])>1e-5:raise ValueError('raw timing report differs from metric')
    area=sum(int(r[1])*float(r[2]) for r in
             (line.split('\t') for line in files[raw+'_cells.tsv'].decode().splitlines()) if r[3]!='1')
    if abs(area-m['cell_area_um2'])>1e-5:raise ValueError('raw cell census differs from area')
    if bool(files[raw+'_coverage.rpt'].strip())==m['timing_coverage_complete']:
        raise ValueError('raw timing coverage differs from metric')
    reuse=physical.get('checkpoint_reuse',{})
    proof_physical=physical
    checkpoint=m.get('checkpoint_resume')
    if checkpoint:
        source=read(checkpoint['source']+'/manifest.json')
        if digest(files[checkpoint['source']+'/manifest.json'])!=checkpoint['source_manifest_sha256']:
            raise ValueError('checkpoint continuation source changed')
        for name,h in checkpoint['checkpoints'].items():
            relative='results/asap7/arithmetic_probe/base/'+name
            if source['evidence_sha256'].get(relative)!=h or physical['evidence_sha256'].get(relative)!=h:
                raise ValueError('completed physical checkpoint changed during continuation')
        proof=checkpoint['successful_CTS_proof']
        if checkpoint['completed_phase']=='post_CTS' and proof['kind']=='complete_state_cut_CEC':
            reuse=dict(proof=proof['path'],proof_sha256=proof['sha256'])
            proof_physical=source
        if checkpoint['completed_phase']=='post_CTS' and proof['kind']=='native_full_Kepler_LEC':
            log=files[proof['path']].decode()
            if digest(files[proof['path']])!=proof['sha256']:
                raise ValueError('successful retained CTS LEC receipt changed')
            if ('SAT solver finished: UNSAT' not in log or 'Circuits are IDENTICAL' not in log
                    or 'Found difference' in log):raise ValueError('retained CTS LEC was not successful')
            for side in (0,1):
                for kind,count in proof['boundary'].items():
                    if not re.search(rf'size of {kind} in circuit {side}: {count}(?!\d)',log):
                        raise ValueError('retained complete CTS LEC boundary changed')
                for kind in ('inputs','outputs'):
                    if not re.search(rf'size of diff{side} {kind}: 0(?!\d)',log):
                        raise ValueError('retained complete CTS LEC boundary changed')
    if 'proof' in reuse:
        proof=read(reuse['proof']);proof_directory=str(Path(reuse['proof']).parent)
        if digest(files[reuse['proof']])!=reuse['proof_sha256'] or proof['status']!='passed':
            raise ValueError('resumed physical implementation lacks exact-pair proof')
        result_prefix='results/asap7/arithmetic_probe/base/'
        for side in ('before','after'):
            if proof_physical['evidence_sha256'].get(result_prefix+'4_'+side+'_rsz_lec.v')!=proof[side+'_sha256']:
                raise ValueError('CTS replay differs from proved netlist pair')
        if not {'top_output','register_D','register_CLK'}<=set(proof['negative_controls']):
            raise ValueError('full CEC corruption controls missing')
        for name in ['cec']+['negative-'+n for n in proof['negative_controls']]:
            log=files[proof_directory+'/'+name+'.log']
            if digest(log)!=proof['artifacts'][name+'.log']:raise ValueError('CEC receipt changed')
            marker=b'Networks are equivalent' if name=='cec' else b'Networks are NOT EQUIVALENT'
            if marker.lower() not in log.lower():raise ValueError('CEC verdict or corruption detection missing')
    for name in ('register_to_register','input_to_register','register_to_output'):
        scale=1 if name=='register_to_register' else .8
        expected=row['T_ps']-classes[name]['slack_ps']/scale
        if abs(expected-classes[name]['required_period_ps'])>1e-5:raise ValueError('clock equation changed')
        limits.append(expected)
    threshold=max(limits)
    if (abs(threshold-m['full_setup_minimum_period_ps'])>1e-5
            or classes['threshold_check_-0.1']['slack_ps']>=0
            or classes['threshold_check_0.1']['slack_ps']<0
            or abs(1e6/threshold-m['maximum_frequency_MHz'])>1e-5):
        raise ValueError('full interface clock bracket/frequency changed')


def corruption_controls(files,row):
    controls=[]
    for name in ('area','frequency','clock_checkpoint'):
        changed=deepcopy(row);archive=dict(files)
        if name=='area':changed['measurement']['cell_area_um2']*=1.01
        elif name=='frequency':changed['measurement']['maximum_frequency_MHz']*=1.01
        else:
            path=changed['measurement']['clock_readout'];clock=json.loads(archive[path])
            key=next(iter(clock['fixed_inputs']));clock['fixed_inputs'][key]='wrong-checkpoint'
            archive[path]=json.dumps(clock).encode()
            changed['measurement']['clock_readout_sha256']=digest(archive[path])
        try:check_measurement(archive,changed)
        except ValueError:controls.append(name)
        else:raise ValueError('corrupted actual report accepted: '+name)
    return controls


def replay(directory=None):
    directory=Path(directory or Path(__file__).resolve().parent)
    manifest=json.loads((directory/'manifest.json').read_text())
    assert digest((directory/'replay.py').read_bytes())==manifest['replay_sha256'],'replay identity changed'
    parts=[]
    for record in manifest['chunks']:
        data=(directory/record['file']).read_bytes()
        assert digest(data)==record['sha256'] and len(data)==record['bytes'],'payload identity changed'
        parts.append(data)
    raw=b''.join(parts)
    assert digest(raw)==manifest['payload_sha256'],'combined payload changed'
    for row in manifest['files']:
        data=(directory/row['file']).read_bytes()
        assert digest(data)==row['sha256'] and len(data)==row['bytes'],'archived sidecar changed'
    data=json.loads(gzip.decompress(raw));report=data['report'];prefix=data['original_root']
    files={k:base64.b64decode(v) for k,v in data['files'].items()}
    methods=json.loads(files[prefix+'/methods.json']);admission=json.loads(files[prefix+'/admission.json'])
    assert report['status']=='stopped_by_user' and report['qualification']=='diagnostic_only_not_W6_qualified'
    assert digest(files[prefix+'/methods.json'])==admission['methods_sha256']
    assert digest(files[prefix+'/diagnostic-model.json'])==methods['model_sha256']==report['model_sha256']
    assert digest(files[prefix+'/selection-freeze.json'])==report['selection_freeze_sha256']
    frozen={(row['case'],row['target']['T_ps'],method):value for row in methods['records'] for method,value in row['methods'].items()}
    ownership={(a['case'],a['target']['T_ps'],a['method']):t['id'] for t in admission['tasks'] for a in t['attribution']}
    states={};complete_rows=[]
    for row in report['rows']:
        key=(row['case'],row['T_ps'],row['method']);selected=frozen[key];m=row['measurement']
        assert ownership[key]==m['task'] and selected['rtl_sha256']==row['rtl_sha256']
        assert selected['L']==row['L'] and selected['II']==row['II']
        if m['task'] in states:assert states[m['task']]==m['status']
        states[m['task']]=m['status']
        if m['status']=='completed':
            check_measurement(files,row);complete_rows.append(row)
            assert m['target_met']==(m['timing_coverage_complete'] and m['setup_worst_slack_ps']>=0)
        else:
            assert m['status'] in ('failed','failed_before_manifest','clock_readout_failed','cancelled_by_user','cancelled_before_start','not_attempted','incomplete_at_stop')
            assert m['full_setup_minimum_period_ps'] is None and m['maximum_frequency_MHz'] is None
            assert m.get('failure_reason')
            if m.get('manifest'):assert digest(files[m['manifest']])==m['manifest_sha256']
    counts=dict(Counter(states.values()))
    assert counts==report['physical_status_counts'] and len(states)==67 and len(report['rows'])==78
    assert len(methods['records'])==19 and len({r['case'] for r in methods['records']})==9
    assert counts.get('completed',0)==report['completed_physical_tasks']==data['raw_verification']['physical_results']
    audit=data['raw_verification'];assert audit['status']=='passed_before_bulk_cleanup' and audit['EDA_calls']==0
    assert set(audit['results'])=={row['measurement']['task'] for row in complete_rows}
    entries=report['measurement_cost']['entries']
    assert not any(e['status']=='reserved' for e in entries)
    for stage in ('synth','grt','final'):assert sum(e['stage']==stage for e in entries)==report['measurement_cost'][stage]
    for name in ('walltime_s','CPU_time_s'):assert abs(sum(e[name] for e in entries)-report['measurement_cost'][name])<1e-5
    stop=json.loads((directory/'process-stop.json').read_text())
    assert stop['status']=='stopped' and not stop['remaining_live_pids'] and not stop['remaining_scoped_runners']
    rows=list(csv.DictReader(io.StringIO((directory/'comparison.csv').read_text())))
    assert len(rows)==len(report['rows'])
    for csvrow,row in zip(rows,report['rows']):
        m=row['measurement']
        assert (csvrow['case'],int(csvrow['T_ps']),csvrow['method'],csvrow['status'])==(row['case'],row['T_ps'],row['method'],m['status'])
        for key in ('cell_area_um2','full_setup_minimum_period_ps','maximum_frequency_MHz'):
            if m.get(key) is None:assert csvrow[key]==''
            else:assert math.isclose(float(csvrow[key]),m[key],rel_tol=1e-12)
    controls=corruption_controls(files,complete_rows[0])
    print(dict(status='passed_stopped_diagnostic_result_replay',physical_tasks=67,completed_physical_tasks=counts.get('completed',0),
        physical_status_counts=counts,method_records=78,complete_method_records=len(complete_rows),
        corruption_controls=controls,EDA_calls=0,external_artifact_reads=0,
        physical_databases_included=False,scope='saved reports, clock equations, proof receipts and identities; no STA or CEC rerun'))


if __name__=='__main__':replay()
