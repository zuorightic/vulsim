"""Read-only step6 graph, cycle, failure and resource evidence verification.

Default verification needs repository evidence only. --verify-external also
reads every catalogued archive member; it does not rerun a compiler or EDA.
"""
import argparse
import contextlib
import gzip
import hashlib
import io
import json
import tarfile
import tempfile
from pathlib import Path

from .budget import usage, cpu_seconds
from .interfaces_evidence import verify_report, same
from .step5_analysis import validate_selection
from .block_tree_evidence import verify_block_trees
from .whole_graph_checks import verify_safe_divisors
from .sdc import rtl_ports, verify_sdc

ROOT = Path(__file__).resolve().parents[2]
FREEZE = 'experiments/arithmetic/whole_graph_freeze_v1.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    path = Path(path)
    raw = path.read_bytes()
    return (gzip.decompress(raw) if path.suffix == '.gz' else raw).decode()


def document(path):
    return json.loads(read(path))


def graph_checks(root, evidence, graphs):
    features = document(root/'experiments/arithmetic_dse/configs/beir_cost_features_v1.json')
    schema = document(root/'experiments/arithmetic_dse/configs/arithmetic_compiler_interfaces_v1.json')['report_schemas']
    items = document(evidence/'implementations.json.gz')
    from .case_generator import generate_manifest
    formal = generate_manifest()['cases']
    expected = {c['id']+'_'+g for c in formal for g in ('A','B','C')}
    names = [x['name'] for x in items]
    if len(names) != len(set(names)) or len(names) != 176:
        raise ValueError('incorrect implementation inventory')
    same({x['name'] for x in items if not x['case'].get('diagnostic')}, expected, 'all formal A/B/C implementations')
    totals = dict(reports=0, nodes=0, regions=0, candidates=0, block_regions=0, safe_Div_Mod=0)
    bindings = document(evidence/'trace_bindings.json.gz')
    for item in items:
        name = item['name']
        r = document(graphs/'reports'/(name+'.json.gz'))
        rtl = read(graphs/'reports'/(name+'.sv.gz'))
        stats = verify_report(r, rtl, features, report_schemas=schema)
        same(r['request']['L'], item['L'], 'frozen latency')
        same(r['request']['II'], 1, 'fixed II')
        same(r['request']['candidate_policy'], 'mul-candidates-v1' if item['group']=='C' else 'core-original-v1', 'group selection policy')
        totals['reports'] += 1
        for key in ('nodes','regions'):
            totals[key] += stats[key]
        totals['candidates'] += validate_selection(r)
        totals['block_regions'] += verify_block_trees(r)
        totals['safe_Div_Mod'] += verify_safe_divisors(r)
        binding = bindings[name]
        for key in ('graph_sha256','schedule_sha256'):
            same(binding[key], r[key], 'executed/current graph identity')
        executed_rtl = read(graphs/'execution_RTL'/(name+'.sv.gz')) if binding['comments_changed'] else rtl
        same(hashlib.sha256(executed_rtl.encode()).hexdigest(), binding['executed_rtl_sha256'], 'actual trace RTL')
        if binding['comments_changed']:
            import re
            clean = lambda text: re.sub(r'//[^\n]*','',text)
            same(clean(executed_rtl), clean(rtl), 'source-location comments only')
        if item['case'].get('diagnostic') == 'shared_divrem':
            nodes = r['graph']['nodes']
            counts = {op:sum(n['kind']==4 and n['opcode']==code for n in nodes) for op,code in (('Div',4),('Mod',5),('Mul',3),('Sub',2))}
            same(counts, {'Div':1,'Mod':0,'Mul':1,'Sub':1}, 'explicit quotient reuse, no fictitious fusion')
    same(totals, {k:document(evidence/'software_audit.json')[k] for k in totals}, 'independent graph totals')
    public=document(evidence/'public_bindings.json')
    same({x['case'] for x in public},{c['id'] for c in formal},'public VUL implementation inventory')
    same(len(public),43,'unique public VUL implementations')
    for row in public:
        name=row['case'];report=graphs/'public'/(name+'.json.gz')
        r=document(report);wrapper=read(graphs/'public'/(name+'.sv.gz')).encode()
        same(hashlib.sha256(wrapper).hexdigest(),row['wrapper_sha256'],'public wrapper bytes')
        same(hashlib.sha256(read(report).encode()).hexdigest(),row['report_sha256'],'public actual report')
        start,end=row['byte_range'];kernel=wrapper[start:end].decode()
        verify_report(r,kernel,features,embedded=True,report_schemas=schema)
        validate_selection(r);verify_block_trees(r);verify_safe_divisors(r)
        same(r['request']['L'],row['L'],'public VUL fixed latency')
        if not wrapper[:start].rstrip().endswith(b'if (1) begin : __vul_pipeline_core'):
            raise ValueError('public kernel byte range is not the actual PIPELINE body')
    representatives=0
    for variant in ('circt','nangate45','sky130hd','gf180'):
        reports=list((graphs/'representatives'/variant).glob('*.json.gz'))
        same(len(reports),6,'representative coverage '+variant)
        for path in reports:
            name=path.name.removesuffix('.json.gz');r=document(path)
            verify_report(r,read(path.with_name(name+'.sv.gz')),features,report_schemas=schema)
            validate_selection(r);verify_block_trees(r);verify_safe_divisors(r)
            baseline=document(graphs/'reports'/(name+'.json.gz'))
            for key in ('graph','stages','protocol','graph_sha256','schedule_sha256'):
                same(r[key],baseline[key],'native/representative '+variant+'/'+key)
            representatives+=1
    return {**totals,'public_reports_recomputed':43,'representative_reports_recomputed':representatives}


def cycles(evidence):
    from regression.arithmetic_whole_graph import verify as replay
    from regression.arithmetic_vul_suite import verify as replay_public
    results = {}
    for name in ('native','exhaustive8','circt'):
        source = evidence/'replays'/name
        with tempfile.TemporaryDirectory(prefix='step6-replay-') as tmp:
            out = Path(tmp)
            for filename in ('items.json','vectors.txt','rtl-run.log','mode.json'):
                path = source/(filename+'.gz')
                if path.exists():
                    (out/filename).write_text(read(path))
            with contextlib.redirect_stdout(io.StringIO()):
                replay(out)
            actual = document(out/'functional.json')
        saved = document(source/'functional.json')
        # Native scope prose was clarified after execution. Numeric checks and
        # every implementation's counters must still match the archived trace.
        if name=='native' and 'exhaustive_8bit_pairs' not in saved:
            # This receipt predates the added exhaustive-run mode. Its actual
            # 1222 input rows are replayed above; it is not an exhaustive run.
            saved['exhaustive_8bit_pairs']=0
        same(set(actual),set(saved),'cycle receipt fields '+name)
        for key in actual:
            if key!='scope':same(actual[key],saved[key],'cycle replay '+name+'/'+key)
        results[name] = {k:v for k,v in actual.items() if k not in ('per_implementation','scope')}
    source = evidence/'replays/public'
    with tempfile.TemporaryDirectory(prefix='step6-public-replay-') as tmp:
        out = Path(tmp)
        items = document(source/'items.json.gz')
        for item in items:
            name = item['case']['id']
            directory = out/name
            directory.mkdir()
            (directory/'vectors.json').write_text(read(source/(name+'.vectors.json.gz')))
            (out/(name+'.log')).write_text(read(source/(name+'.log.gz')))
            item['directory'] = str(directory)
        (out/'items.json').write_text(json.dumps(items))
        with contextlib.redirect_stdout(io.StringIO()):
            replay_public(out,out)
        actual = document(out/'functional.json')
    same(actual,document(source/'functional.json'),'43 public VUL cycle traces')
    same(actual['public_VUL_cases'],43,'all public cases')
    results['public'] = {k:v for k,v in actual.items() if k!='reports'}
    return results


def physical(evidence):
    admission = document(evidence/'admission.json')
    same(admission['call_caps'],dict(synth=6,grt=2,final=0),'finite original capacity envelope')
    tasks = {t['id']:t for t in admission['tasks']}
    outcome = document(evidence/'outcome.json')
    same({r['task_id'] for r in outcome['runs']},set(tasks),'all physical tasks accounted')
    attempted = []
    for row in outcome['runs']:
        t = tasks[row['task_id']]
        if row['status']=='not_run':
            same(row['physical_calls'],0,'paused control consumes no physical call')
            if t['stage']!='synth':
                raise ValueError('capacity attempt missing')
            continue
        attempted.append(row['task_id'])
        run = evidence/'runs'/row['task_id']
        m = document(run/'manifest.json.gz')
        command = document(run/'synth.command.json')
        same(row['status'],m['status'],'outcome agrees with original manifest')
        same(row['failure_code'],m['failure_code'],'original failure classification')
        same(row['actual_synth_command_exit'],command['exit_code'],'actual physical command result')
        same(m['status'],'failed','original failure retained')
        same(m['metrics'],[],'no accepted PPA from a failed baseline')
        same(command['cleanup']['remaining_live_pids'],[],'physical cleanup')
        same(command['unexpected_live_descendants'],False,'no stray descendants')
        same(sha(run/'input.sv.gz'),row['stored_rtl_sha256'],'archived actual input')
        same(hashlib.sha256(read(run/'input.sv.gz').encode()).hexdigest(),t['rtl_sha256'],'admitted circuit bytes')
        if t['kernel']=='udr_unsigned_128':
            same(m['failure_code'],'memory_limit','actual UDR capacity limit')
            same(command['memory_limit_exceeded'],True,'UDR observed memory limit')
            if command['sampled_process_tree_peak_rss_KiB']<=8192*1024:
                raise ValueError('memory failure lacks observed peak')
        else:
            same(m['failure_code'],'stage_evidence_rejected','original parser failure retained')
            same(command['exit_code'],0,'FP synthesis command completed')
            result = verify_sdc(read(run/'1_synth.sdc.gz'),m['platform_profile'],m['period_ps'],rtl_ports(read(run/'input.sv.gz'),t['top']))
            same(result,document(evidence/'postmortem.json')['corrected_static_SDC_check'],'scoped top postmortem')
    same(len(attempted),2,'no new physical retry')
    return dict(attempted_baselines=2,successful_grt=0,paused_synth_controls=4,
                UDR128='synth memory_limit at 8192 MiB; this implementation only',
                F2='synth command completed; original stage rejected by interface reader; static SDC now passes; grt unmeasured',
                training_or_main_matrix_released=False)


def ledger_entries(root,path):
    d = document(path)
    return (ledger_entries(root,root/d['prefix']) if 'prefix' in d else [])+d['entries']


def resources(root,evidence):
    delta = document(evidence/'usage_delta.json')
    same(sha(root/delta['prefix']),delta['prefix_sha256'],'immutable usage prefix')
    entries = ledger_entries(root,evidence/'usage_delta.json')
    table = document(evidence/'resources.json')
    same(usage(entries),table['cumulative_usage'],'all cumulative charges')
    same(usage(delta['entries']),table['new_usage'],'new charges')
    same(usage(entries)['pending'],0,'settled ledger')
    same([e['stage'] for e in delta['entries'] if e['stage'] is not None],['synth','synth'],'only two physical attempts')
    receipts = document(evidence/'receipts.json.gz')
    same({r['id'] for r in receipts},{e['id'] for e in delta['entries']},'all charged leaf receipts')
    for row in receipts:
        charge = next(e for e in delta['entries'] if e['id']==row['id'])
        record = row['record']
        same(record['walltime_s'],charge['walltime_s'],'actual charged wall time')
        same(record['exit_code'],charge['exit_code'],'actual charged outcome')
        same(record['cleanup']['remaining_live_pids'],[],'leaf cleanup')
        same(record['unexpected_live_descendants'],False,'leaf descendants')
        if charge.get('CPU_accounting')=='full_reservation_missing_CPU_evidence':
            same(charge['CPU_time_s'],record['CPU_limit_s'],'conservative CPU settlement')
            if row['GNU_time'].strip():
                raise ValueError('conservative settlement has unexpected GNU time data')
        else:
            with tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp)/'time.txt';path.write_text(row['GNU_time'])
                same(cpu_seconds(path),charge['CPU_time_s'],'GNU time actual CPU')
    live=root/'experiments/arithmetic/backend_usage.json'
    if live.exists():
        same(document(live)['entries'][:len(entries)],entries,'live ledger prefix unchanged')
    return table


def verify_original(root=ROOT,external=False,parents=True):
    root=Path(root);f=document(root/FREEZE)
    from .freeze_history import source_location
    for path,h in f['files_sha256'].items():
        same(sha(source_location(root,FREEZE,path,h)),h,'active source '+path)
        same(sha(root/f['source_snapshots'][path]),h,'source snapshot '+path)
    for path,h in f['historical_freezes'].items():
        same(sha(root/path),h,'parent freeze unchanged')
    for path,h in document(root/f['preservation']).items():
        same(sha(root/path),h,'historical payload unchanged')
    for package in f['packages']:
        same(sha(root/package['index']),package['sha256'],'package index')
        index=document(root/package['index'])['files_sha256']
        sizes=[]
        for path,h in index.items():
            same(sha(root/path),h,'evidence identity '+path);sizes.append((root/path).stat().st_size)
        sizes.append((root/package['index']).stat().st_size)
        if package['role']=='software':sizes.append((root/FREEZE).stat().st_size)
        if max(sizes)>1048576 or sum(sizes)>5242880:
            raise ValueError('new evidence storage target exceeded')
    evidence=root/f['evidence_directory'];capacity=root/f['capacity_directory']
    totals=graph_checks(root,evidence,root/f['graph_directory']);replays=cycles(evidence);probes=physical(capacity);charges=resources(root,evidence)
    admission=document(capacity/'admission.json')
    policy=document(root/'experiments/arithmetic_dse/configs/backend_policy_v5.json')['resources']
    same(admission['worst_case_walltime_s'],6000,'finite launch walltime envelope')
    same(admission['CPU_envelope_s'],12000,'finite launch CPU envelope')
    launch=admission['starting_usage_live']
    if (launch['pending'] or launch['walltime_s']+6000>policy['max_global_walltime_h']*3600
            or launch['CPU_time_s']+12000>policy['max_tool_CPU_time_h']*3600):
        raise ValueError('original finite launch envelope was not funded')
    same(charges['global_caps_changed'],False,'global budget unchanged')
    for key,limit in (('walltime_s',1800),('CPU_time_s',3600)):
        if charges['post_admission_support_usage'][key]>limit:
            raise ValueError('post-admission support envelope exceeded')
    if external:
        for artifact in document(capacity/'artifact_catalog.json.gz'):
            path=root/artifact['location']
            if not path.is_file():raise ValueError('artifact_unavailable: '+artifact['location'])
            same(sha(path),artifact['stored_sha256'],'actual external bytes')
            same(path.stat().st_size,artifact['stored_size_bytes'],'external archive size')
            with tarfile.open(path,'r:gz') as tar:
                same(tar.getnames(),[m['relative_member_path'] for m in artifact['members']],'external member inventory')
                for member in artifact['members']:
                    stream=tar.extractfile(member['relative_member_path']);h=hashlib.sha256();size=0
                    while chunk:=stream.read(1024*1024):h.update(chunk);size+=len(chunk)
                    same(h.hexdigest(),member['sha256'],'actual external member');same(size,member['content_size_bytes'],'member size')
    parent_status=None
    if parents:
        from .metric_scope_evidence import verify as inherited
        parent_status=inherited(root)['status']
    return dict(status='passed',scope='step6 software and bounded failed-capacity evidence; no full physical or D acceptance',
                graphs=totals,cycles=replays,capacity=probes,new_usage=charges['new_usage'],
                cumulative_usage=charges['cumulative_usage'],parent_status=parent_status,
                external_artifacts='actual local bytes verified; remote retention unconfirmed' if external else 'not requested; compact evidence only',
                requires_compiler_or_EDA=False)


def verify(root=ROOT,external=False,parents=True):
    if (Path(root)/'experiments/arithmetic/whole_graph_freeze_v2.json').exists():
        from .whole_graph_review_evidence import verify as review
        return review(root,external,parents)
    return verify_original(root,external,parents)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--verify-external',action='store_true')
    p.add_argument('--no-parents',action='store_true')
    a=p.parse_args()
    print(json.dumps(verify(a.root,a.verify_external,not a.no_parents),indent=2))


if __name__=='__main__':main()
