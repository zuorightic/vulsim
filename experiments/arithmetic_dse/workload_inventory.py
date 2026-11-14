"""Public W1/W2 application source, structural search and demand entry point.

The frozen mathematical source is expanded by RTLzz, never by handwritten
pipeline RTL. This software inventory exposes missing prices without selecting
a D implementation. It does not run an EDA tool or consume model test labels.
"""
import argparse
import gzip
import hashlib
import itertools
import json
import os
from pathlib import Path
import subprocess
import time
import shlex
from . import workload_contracts as contracts, workload_sources as sources, workload_demand as demand

REPO = Path(__file__).resolve().parents[2]


def inventory(out, binary, case_id, *, timeout_s=120, verify_rtl=False):
    if not 1 <= timeout_s <= 3600:
        raise ValueError('finite software timeout required')
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    doc = contracts.load()
    case = next(c for c in doc['cases'] if c['id'] == case_id)
    if case['unresolved'] or not case['formal_targets']:
        raise ValueError('application source and finite targets must first be confirmed')
    spec = sources.prepare_case(out / 'source', case_id)
    policy = case['structural_search']
    choices = list(itertools.product(policy['mul_block_widths'], policy['add_sub_limb_widths']))
    if len(choices) > policy['max_structures']:
        raise ValueError('declared structure list exceeds finite admission; no silent prefix')
    rows = []
    env = dict(os.environ)
    if verify_rtl:
        sentinels=out/'no-eda-bin';sentinels.mkdir()
        marker=out/'forbidden-backend-attempt'
        for name in ('yosys','abc','yosys-abc','openroad','opensta','sta'):
            entry=sentinels/name
            entry.write_text('#!/bin/sh\nprintf "forbidden backend\\n" > '+shlex.quote(str(marker))+'\nexit 97\n');entry.chmod(0o755)
        env['PATH']=str(sentinels)+os.pathsep+env['PATH']
    for number, (mul, limb) in enumerate(choices):
        dest = out / f'structure-{number}'
        first = case['formal_targets'][0]
        L = first['L']
        if any(t['L'] != L for t in case['formal_targets']):
            raise ValueError('this inventory version groups one L; explicit successor needed')
        cmd = [str(binary), str(REPO), str(out / 'source/request.json'), str(L), str(limb),
               str(policy['beam_width']), str(policy['max_extensions_per_structure']), str(dest), str(mul), str(first['T_ps'])]
        row = dict(structure=number, mul_block_width=mul, add_sub_limb_width=limb, directory=dest.name)
        start = time.perf_counter()
        try:
            p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, timeout=timeout_s, env=env)
            (out / f'structure-{number}.log').write_text(p.stdout)
            row['exit_code'] = p.returncode
            row['software_export_wall_s'] = time.perf_counter() - start
            if (dest / 'inventory.json').exists():
                inv = json.loads((dest / 'inventory.json').read_text())
                row['search'] = inv['search']
                row['search_ms'] = inv['search_ms']
                row['status'] = 'software_exported' if inv['views'] else 'search_no_complete_placement'
                row['demand_files'] = []
                for target in case['formal_targets']:
                    q = demand.extract(dest, target['T_ps'])
                    relative = f'demand-T{target["T_ps"]}.json.gz'
                    (dest / relative).write_bytes(gzip.compress(json.dumps(q, separators=(',', ':')).encode(), mtime=0))
                    row['demand_files'].append(relative)
                if verify_rtl:
                    from .workload_software_validation import bench, run
                    row['functional']=[]
                    for view in inv['views']:
                        directory=dest/view['directory']
                        tb,checks=bench(spec,view['artifact'],L)
                        (directory/'tb.sv').write_text(tb)
                        run(['iverilog','-g2012','-s','tb','-o',directory/'sim.out',directory/'workload.sv',directory/'tb.sv'],directory/'iverilog.log',env,timeout_s)
                        run(['vvp',directory/'sim.out'],directory/'simulation.log',env,timeout_s)
                        row['functional'].append(dict(view=view['directory'],cycles=96,result_checks=checks))
            else:
                row['status'] = 'software_export_failed'
        except subprocess.TimeoutExpired as error:
            (out / f'structure-{number}.log').write_text(str(error))
            row['status'] = 'software_timeout'
        rows.append(row)
    report = dict(version='nine-workload-structural-inventory-v1', case=case,
                  contract_sha256=hashlib.sha256(contracts.DEFAULT.read_bytes()).hexdigest(),
                  source_spec=spec, declared_structures=len(choices), attempted_structures=len(rows),
                  structures=rows, graph_search_domain='homogeneous Mul block choice and global Add/Sub limb choice; canonical earliest wiring',
                  model_selection_performed=False, cost_coverage_status='not_qualified; inventory does not request or substitute prices',
                  full_D_ready=False, new_EDA_calls=0, independent_labels_read=False,
                  formal_target_timings_are_requests=True)
    if verify_rtl and marker.exists():
        raise ValueError('backend startup attempted during software inventory')
    (out / 'inventory.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--case', choices=sorted(contracts.CASE_IDS))
    group.add_argument('--all', action='store_true')
    parser.add_argument('--binary', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--timeout-s', type=int, default=120)
    parser.add_argument('--verify-rtl', action='store_true')
    args = parser.parse_args()
    selected = [c['id'] for c in contracts.load()['cases']] if args.all else [args.case]
    if args.all:
        args.out.mkdir(parents=True, exist_ok=False)
    summaries = []
    for case_id in selected:
        report = inventory(args.out / case_id if args.all else args.out, args.binary.resolve(), case_id, timeout_s=args.timeout_s, verify_rtl=args.verify_rtl)
        summary = dict(case=case_id, statuses={state: sum(r['status'] == state for r in report['structures'])
                       for state in sorted({r['status'] for r in report['structures']})},
                       declared_structures=report['declared_structures'], new_EDA_calls=0)
        summaries.append(summary)
        print(json.dumps(summary), flush=True)
    if args.all:
        (args.out / 'summary.json').write_text(json.dumps(summaries, indent=2)+'\n')
