#!/usr/bin/env python3
"""Standard-library replay of frozen diagnostic ABCD identities and receipts."""
import base64
from copy import deepcopy
import gzip
import hashlib
import json
import re
from pathlib import Path


def digest(data):return hashlib.sha256(data).hexdigest()


def check_queue_bindings(files,prefix):
    queued=0
    for path in sorted(files):
        if not path.startswith(prefix+'/capacity/') or not path.endswith('/queue-admission.json'):continue
        q=json.loads(files[path]);folder=str(Path(path).parent)
        a=json.loads(files[folder+'/admission.json'])
        if (q['version'] not in ('nine-workload-capacity-slot-queue-v1','nine-workload-resume-slot-queue-v1')
                or digest(files[folder+'/admission.json'])!=q['capacity_admission_sha256']
                or digest(files[q['source']])!=q['source_sha256']
                or digest(files[folder+'/queue-driver.py'])!=q['source_sha256']
                or q['tasks']!=[t['id'] for t in a['tasks']]
                or q['added_physical_calls']!=0 or q['automatic_retries']!=0
                or a['memory_limit_MiB']!=8192 or a['threads']!=4):
            raise ValueError('capacity slot queue changed its frozen source or admitted scope')
        queued+=len(q['tasks'])
    return queued


def check_proof_settlement(files,prefix):
    count=0
    for path in sorted(files):
        if not path.startswith(prefix+'/proofs/') or not path.endswith('/admission.json'):continue
        folder=str(Path(path).parent);command=folder+'/command.json'
        if command not in files:raise ValueError('proof is still queued or running')
        record=json.loads(files[command])
        if record['cleanup']['remaining_live_pids']:raise ValueError('proof descendants remain alive')
        receipts=[json.loads(files[p]) for p in (folder+'/proof.json',folder+'/result/proof.json') if p in files]
        if not record['exit_code'] and not any(p['status'] in ('passed','failed') for p in receipts):
            raise ValueError('proof lacks its terminal validation receipt')
        count+=1
    return count


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


def replay(directory=Path(__file__).resolve().parent):
    manifest=json.loads((directory/'manifest.json').read_text())
    if digest((directory/'replay.py').read_bytes())!=manifest['replay_sha256']:raise ValueError('replay changed')
    parts=[]
    for row in manifest['chunks']:
        data=(directory/row['file']).read_bytes()
        if digest(data)!=row['sha256'] or len(data)>512*1024:raise ValueError('portable part changed')
        parts.append(data)
    raw=b''.join(parts)
    if digest(raw)!=manifest['payload_sha256']:raise ValueError('portable payload changed')
    package=json.loads(gzip.decompress(raw));files={n:base64.b64decode(v) for n,v in package['files'].items()}
    prefix=manifest['original_root']
    queued=check_queue_bindings(files,prefix)
    def read(name):return json.loads(files[name])
    for fname in ('selection-freeze.json','baselines-freeze.json'):
        freeze=read(prefix+'/'+fname)
        for n,h in freeze['files'].items():
            if digest(files[n])!=h:raise ValueError('frozen input changed: '+n)
    methods=read(prefix+'/methods.json');admission=read(prefix+'/admission.json');report=read(prefix+'/comparison.json')
    if (report['status'] not in ('completed','settled_with_failures')
            or report['qualification']!='diagnostic_only_not_W6_qualified'):
        raise ValueError('comparison completion or diagnostic qualification changed')
    if (digest(files[prefix+'/methods.json'])!=admission['methods_sha256']
            or digest(files[prefix+'/diagnostic-model.json'])!=methods['model_sha256']):
        raise ValueError('model or method matrix changed')
    ranks=0;rtl=set();measured=set();count=0
    for row in methods['records']:
        base=f"{prefix}/diagnostic-scores/{row['case']}/T{row['target']['T_ps']}-L{row['target']['L']}"
        for method,d in row['methods'].items():
            count+=1;rtl.add(d['rtl_sha256'])
            if digest(files[d['rtl']])!=d['rtl_sha256'] or d['L']!=(1 if method=='A' else row['target']['L']):
                raise ValueError('RTL or cycle contract changed')
            receipt=d.get('simulation_receipt',str(Path(d['rtl']).with_name('simulation.log')))
            if b'PASS' not in files[receipt]:raise ValueError('missing functional receipt')
            if method not in ('D','D_static_cal'):continue
            selection=read(base+('/model/selection.json' if method=='D' else '/static-cal/selection.json'))
            candidates=selection['candidates']
            if any(c['prediction']['status']!='diagnostic_complete' for c in candidates):
                raise ValueError('unpriced candidate disappeared')
            feasible=[c for c in candidates if c['prediction']['target_met']]
            def score(c):
                p=c['prediction'];tail=(p['total_area_um2'],c['structure'],int(c['view']))
                return tail if feasible else (p['violation_ps'],)+tail
            winner=min(feasible or candidates,key=score)
            if (winner['structure'],winner['view'])!=(d['structure'],d['view']):raise ValueError('D ranking changed')
            if digest(files[d['prediction_path']])!=d['prediction_sha256']:raise ValueError('selected full price changed')
            full=json.loads(gzip.decompress(files[d['prediction_path']]))
            if (full['total_area_um2']!=d['prediction']['total_area_um2'] or full['qualified']):
                raise ValueError('full price or diagnostic identity changed')
            ranks+=1
    ownership={(a['case'],a['target']['T_ps'],a['method']):t['id']
               for t in admission['tasks'] for a in t['attribution']}
    frozen={(r['case'],r['target']['T_ps'],name):data for r in methods['records']
            for name,data in r['methods'].items()}
    states={}
    for row in report['rows']:
        identity=(row['case'],row['T_ps'],row['method']);selected=frozen[identity]
        if (ownership[identity]!=row['measurement']['task'] or selected['rtl_sha256']!=row['rtl_sha256']
                or selected['L']!=row['L'] or selected['II']!=row['II']):
            raise ValueError('reported method differs from frozen measurement attribution')
        measured.add(row['measurement']['task'])
        task=row['measurement']['task'];status=row['measurement']['status']
        if task in states and states[task]!=status:raise ValueError('shared physical task has inconsistent statuses')
        states[task]=status
        check_measurement(files,row)
    if (len(methods['records'])!=19 or len({r['case'] for r in methods['records']})!=9
            or count!=78 or ranks!=21 or len(measured)!=manifest['physical_tasks']):
        raise ValueError('finite nine-case matrix changed')
    if (sum(s=='completed' for s in states.values())!=report['completed_physical_tasks']
            or sum(s!='completed' for s in states.values())!=report['failed_physical_tasks']
            or report['settled_physical_tasks']!=len(states)):
        raise ValueError('physical completion/failure counts changed')
    cost=report['measurement_cost'];entries=cost['entries']
    if (any(e['status']=='reserved' or not e['admission_id'].startswith(admission['id']) for e in entries)
            or cost['pending']!=0 or len({e['id'] for e in entries})!=len(entries)):
        raise ValueError('comparison accounting has unfinished, duplicate or unrelated leaves')
    proofs=check_proof_settlement(files,prefix)
    for stage in ('synth','grt','final'):
        if sum(e['stage']==stage for e in entries)!=cost[stage]:raise ValueError('physical call count changed')
    if (sum(e['stage'] is None for e in entries)!=cost['support_calls']
            or sum(e['status']=='failed' for e in entries)!=cost['failed_leaves']
            or any(abs(sum(e[k] for e in entries)-cost[k])>1e-5 for k in ('walltime_s','CPU_time_s'))):
        raise ValueError('retained failures or actual comparison costs changed')
    complete=next((r for r in report['rows'] if r['measurement']['status']=='completed'),None)
    controls=corruption_controls(files,complete) if complete else []
    print(dict(status='passed_diagnostic_ABCD_portable_replay',cases=9,targets=19,method_records=count,
               model_and_static_cal_rankings=ranks,unique_RTL=len(rtl),physical_tasks=len(measured),
               completed_physical_tasks=report['completed_physical_tasks'],
               failed_physical_tasks=report['failed_physical_tasks'],
               qualification=report['qualification'],EDA_calls=0,external_artifact_reads=0,
               queued_capacity_tasks=queued,
               settled_proof_admissions=proofs,
               raw_physical_reports_checked=True,exact_pair_CEC_receipts_checked=True,
               report_corruption_controls=controls))


if __name__=='__main__':replay()
