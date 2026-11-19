"""Command-line entry: compile, select a complete candidate and emit RTL."""
import argparse
import json
from pathlib import Path
import subprocess

from .resources import ROOT, EXAMPLES, runtime, verify_models


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('build', help='build RTLzz from the checked-out source')
    p.add_argument('--build-dir', type=Path, default=ROOT / 'build/autopipe')
    p.add_argument('--jobs', type=int, default=4)
    p = commands.add_parser('generate', help='select using frozen costs and emit the selected RTL')
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument('--workload', choices=sorted(p.name for p in EXAMPLES.iterdir() if p.is_dir()))
    source.add_argument('--source-request', type=Path)
    p.add_argument('--platform', choices=['asap7', 'nangate45'], default='asap7')
    p.add_argument('--period-ps', type=float, required=True)
    p.add_argument('--latency', type=int, required=True, help='L includes output capture; input launch adds one service cycle')
    p.add_argument('--method', choices=['A', 'B', 'C', 'D'], default='D')
    p.add_argument('--build-dir', type=Path, default=ROOT / 'build/autopipe')
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--mul-block-widths', help='comma-separated finite grammar, for example 0,8,16')
    p.add_argument('--add-limb-widths', help='comma-separated finite grammar, for example 0,32,64,128')
    p.add_argument('--timeout-s', type=float, default=300)
    p.add_argument('--candidate-limit', type=int, default=256)
    p.add_argument('--check', action='store_true', help='run a 96-cycle Icarus reference check for a bundled workload')
    commands.add_parser('check-models', help='verify frozen parameter identities and load both models')
    args = parser.parse_args()
    try:
        if args.command == 'build':
            from .compiler import build
            build(args.build_dir, args.jobs)
        elif args.command == 'generate':
            from .generate import generate
            result = generate(args)
            print(json.dumps(dict(method=result['method'], platform=result['platform'],
                selection_status=result['selection_status'], rtl=result['rtl'],
                predicted_area_um2=result['prediction']['total_area_um2'],
                predicted_period_ps=result['prediction']['critical_required_ps'],
                complete_candidates=result['complete_candidates'],
                simulation=result.get('simulation')), ensure_ascii=False, indent=2))
        else:
            manifest = verify_models()
            for platform in ['asap7', 'nangate45']:
                runtime(platform)
            print(json.dumps(dict(status='passed', platforms=['asap7', 'nangate45'],
                                  resources=len(manifest['files_sha256']), inference_backend_calls=0), indent=2))
    except (ValueError, KeyError, OSError, TimeoutError, subprocess.SubprocessError) as error:
        parser.exit(2, 'autopipe: ' + str(error) + '\n')


if __name__ == '__main__':
    main()
