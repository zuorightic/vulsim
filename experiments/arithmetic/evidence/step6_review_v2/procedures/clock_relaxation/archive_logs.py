"""Organize failed UDR logs without breaking historic receipts or hashes."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os

R=Path.cwd();B=R/'build/step6-relaxed-clock-20261102';old=R/'build/step6-review-20261102'
archive=old/'archived_udr_logs';index=B/'previous-logs-index.json'
assert not index.exists() and not archive.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[]
for base in ('physical','physical-threads','physical-complete'):
    for run in (old/base).glob('*udr*'):
        if not run.is_dir():continue
        files.extend(p for p in run.rglob('*.log') if p.is_file() and not p.is_symlink())
        driver=run.with_name(run.name+'.driver.log')
        if driver.is_file():files.append(driver)
rows=[]
for p in sorted(set(files)):
    h=sha(p);size=p.stat().st_size;target=archive/p.relative_to(old)
    target.parent.mkdir(parents=True,exist_ok=True)
    assert not target.exists()
    p.rename(target)
    p.symlink_to(os.path.relpath(target,p.parent))
    assert sha(p)==h and sha(target)==h
    rows.append({'original_path':str(p.relative_to(R)),'archived_path':str(target.relative_to(R)),
                 'sha256':h,'bytes':size,'original_path_readable_via_relative_symlink':True})
index.write_text(json.dumps({'version':'failed-UDR-log-archive-v1','created_at':datetime.now(timezone.utc).isoformat(),
    'scope':'v2/v3/v4 UDR logs only; manifests, charges, results, freezes and original bytes preserved',
    'method':'move logs into named archive, retain relative path links for existing receipts',
    'log_count':len(rows),'total_bytes':sum(x['bytes'] for x in rows),'members':rows},indent=2)+'\n')
m=json.loads((old/'physical-complete/asap7-step6-udr_unsigned_128-capacity-complete-v4/manifest.json').read_text())
s=next(x for x in m['metrics'] if x['stage']=='synth');c=next(x for x in m['commands'] if x['log'].endswith('/grt.log'))
cts=old/'physical-complete/asap7-step6-udr_unsigned_128-capacity-complete-v4/logs/asap7/arithmetic_probe/base/4_1_cts.log'
assert 'Took 10280 seconds: repair_timing' in cts.read_text()
(B/'diagnosis.json').write_text(json.dumps({'source_manifest':str((old/'physical-complete/asap7-step6-udr_unsigned_128-capacity-complete-v4/manifest.json').relative_to(R)),
    'source_manifest_sha256':sha(old/'physical-complete/asap7-step6-udr_unsigned_128-capacity-complete-v4/manifest.json'),
    'source_CTS_log':str(cts.relative_to(R)),'source_CTS_log_sha256':sha(cts),
    'old_period_ps':m['period_ps'],'synth_setup_slack_ps':s['setup_worst_slack_ps'],
    'synth_core_clk_minimum_period_ps':s['minimum_clock_period_ps'],
    'physical_command_walltime_s':c['walltime_s'],'CTS_repair_timing_s':10280,
    'CTS_repair_fraction':10280/c['walltime_s'],'timed_out':c['timed_out'],
    'CPU_limit_exceeded':c['CPU_limit_exceeded'],'memory_limit_exceeded':c['memory_limit_exceeded'],
    'new_period_ps':100000,'new_ABC_target_ps':1500,'new_fixed_IO_delay_max_ps':300,
    'interpretation':'tight setup constraint strongly implicated; direct termination was wall timeout; no new speed/completion claim before results'},indent=2)+'\n')
print(json.dumps({'archived_logs':len(rows),'bytes':sum(x['bytes'] for x in rows),'index':str(index)}))
