"""Accounted step-two contract and generated-kernel validation, without PPA."""
import argparse
import json
import os
from pathlib import Path
import sys

from .budget import Ledger, usage
from .case_generator import (build_graph, generate_manifest, source_files,
                             validation_main, validation_vectors)
from .contracts import ROOT
from .processes import run_command
from .reference import evaluate_spec

NATIVE_CASES = ('MUL_128', 'MAC_128', 'DOT2_128', 'H_M_128', 'F2')


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def prepare(out, case_ids):
    manifest = generate_manifest()
    selected = [c for c in manifest['cases'] if c['id'] in case_ids]
    if {c['id'] for c in selected} != set(case_ids):
        raise ValueError('unknown case ID in validation list')
    suite = out/'sources'
    suite.mkdir()
    for case in selected:
        directory = suite/case['id']
        directory.mkdir()
        for name, text in source_files(case).items():
            (directory/name).write_text(text)
        rows = validation_vectors(case)
        write_json(directory/'vectors.json', rows)
        (directory/'vectors.txt').write_text(str(len(rows))+'\n'+''.join(
            ' '.join(f'{row[name]:x}' for name in case['inputs'])+'\n' for row in rows))
        (directory/'Main.utb').write_text(validation_main(case,directory/'vectors.txt'))
    write_json(out/'generated-manifest.json', manifest)
    print(json.dumps({'status':'prepared','cases':len(selected),'seed':20261030}))


def check_traces(out, case_ids, backend):
    manifest = generate_manifest()
    reports = []
    for case in manifest['cases']:
        if case['id'] not in case_ids:
            continue
        rows = json.loads((out/'sources'/case['id']/'vectors.json').read_text())
        trace = out/f'{backend}-{case["id"]}-run.log'
        count = checks = 0
        completed = False
        for line in trace.read_text().splitlines():
            if line.startswith('ROW '):
                values = line.split()
                if int(values[1]) != count or count >= len(rows):
                    raise ValueError(f'{case["id"]}: trace sequence mismatch')
                expected = evaluate_spec(case,rows[count])
                actual = [int(v,16) for v in values[2:]]
                if actual != list(expected.values()):
                    raise ValueError(f'{case["id"]} row {count}: {actual} != {expected}')
                checks += len(expected)
                count += 1
            elif line.startswith('CASE RUN PASS'):
                if completed or line != f'CASE RUN PASS rows={len(rows)}':
                    raise ValueError('invalid completion marker')
                completed = True
        if not completed or count != len(rows):
            raise ValueError(f'{case["id"]}: incomplete trace')
        reports.append({'case':case['id'],'rows':count,'output_values_compared':checks,
                        'backend':backend,'largest_output_width':max(case['outputs'].values())})
    if len(reports) != len(case_ids):
        raise ValueError('trace suite incomplete')
    result = {'status':'passed','scope':'combination_SERVICE; no_fixed_L_pipeline_claim',
              'cases':reports,'output_values_compared':sum(r['output_values_compared'] for r in reports)}
    write_json(out/(backend+'-checks.json'),result)
    print(json.dumps(result,indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--cases',nargs='+',help='optional bounded smoke subset; default all 43')
    parser.add_argument('--skip-contracts',action='store_true')
    parser.add_argument('--phase',choices=['prepare','check'])
    parser.add_argument('--backend',choices=['sim','native'])
    args = parser.parse_args()
    out = args.output.resolve()
    cases = args.cases or [c['id'] for c in generate_manifest()['cases']]
    if len(cases) != len(set(cases)):
        parser.error('duplicate case IDs')
    if args.phase == 'prepare':
        prepare(out,cases)
        return 0
    if args.phase == 'check':
        if not args.backend:
            parser.error('--backend required for check')
        check_traces(out,cases,args.backend)
        return 0
    if out.exists():
        parser.error('use a new output directory to retain evidence')
    out.mkdir(parents=True)
    ledger = Ledger()
    before = json.loads(ledger.path.read_text())
    write_json(out/'usage-before.json',before)
    env = os.environ.copy()
    env.update(MAKEFLAGS='-j2',CMAKE_BUILD_PARALLEL_LEVEL='2')
    commands = []
    report = {'version':'step2-generated-kernels-v1','status':'running','case_ids':cases,
              'native_case_ids':[c for c in NATIVE_CASES if c in cases],
              'native_dynamic_divmod':'step6_pending; current_s8_rejects_nonconstant_rhs',
              'commands':commands,'physical_calls':{'synth':0,'grt':0,'final':0}}
    def run(command,stem,timeout=120):
        reservation = ledger.reserve(None,timeout,2,'step2_contract_generation_validation',command,out/stem)
        record = run_command(command,out,stem,timeout,env,cpu_limit_s=reservation['CPU_time_s'])
        ledger.finish(reservation,record)
        commands.append({**record,'budget_reservation_id':reservation['id']})
        write_json(out/'validation.json',report)
        if record['exit_code']:
            raise RuntimeError(f'{stem}: see {record["log"]}')
    try:
        if not args.skip_contracts:
            env['ARITHMETIC_REPORT'] = str(out/'contracts.json')
            run([sys.executable,str(ROOT/'regression/arithmetic_contracts.py')],'contracts')
            for name, source in [('division',ROOT/'regression/fixint_division.cpp'),
                                 ('fixint',ROOT/'vullib/test/fixint.cpp')]:
                executable = out/('test-'+name)
                run(['c++','-std=c++20','-O2','-I'+str(ROOT/'vullib'),str(source),'-o',str(executable)],name+'-build')
                run([str(executable)],name+'-unit')
        run([sys.executable,'-m',__spec__.name,'--output',str(out),'--phase','prepare','--cases',*cases],'prepare')
        for backend, tool, ids in [('sim','vulsimgen',cases),('native','vulrtlgen',report['native_case_ids'])]:
            for case_id in ids:
                target = out/backend/case_id
                run([str(ROOT/'build'/tool),'-m',str(out/'sources'/case_id/'Main.utb'),'-f','-o',str(target)],
                    f'{backend}-{case_id}-generate')
                run(['bash',str(target/'run.sh')],f'{backend}-{case_id}-run',300)
            if ids:
                run([sys.executable,'-m',__spec__.name,'--output',str(out),'--phase','check',
                     '--backend',backend,'--cases',*ids],backend+'-check')
        report['status'] = 'passed'
    except Exception as error:
        report.update(status='failed',failure_reason=str(error))
    after = json.loads(ledger.path.read_text())
    if after['entries'][:len(before['entries'])] != before['entries']:
        raise ValueError('historical ledger entries changed')
    write_json(out/'usage-after.json',after)
    report.update(new_usage=usage(after['entries'][len(before['entries']):]),cumulative_usage=usage(after['entries']))
    write_json(out/'validation.json',report)
    print(json.dumps({'status':report['status'],'output':str(out),'new_usage':report['new_usage'],
                      'failure_reason':report.get('failure_reason')},indent=2))
    return 0 if report['status']=='passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
