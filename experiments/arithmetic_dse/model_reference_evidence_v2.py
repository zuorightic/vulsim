"""Explicit live-ledger binding for external replay of immutable reference evidence.

The frozen v1 replay is self-contained. Its external mode incorrectly looked
for the live ledger under the unpacked producer tree. Bind that one external
dependency explicitly; preserve the original package and failed receipt.
"""
import argparse
from pathlib import Path

from . import model_reference_evidence as base
from .budget import LEDGER


def verify(folder, *, external=False, ledger_path=LEDGER):
    if not external:
        return base.verify(folder)
    original = base.frozen_modules
    def with_external_ledger(source):
        modules = original(source)
        class ExternalLedger:
            path = Path(ledger_path).resolve()
        modules['model_reference_audit'].Ledger = ExternalLedger
        return modules
    base.frozen_modules = with_external_ledger
    try:
        return base.verify(folder, external=True)
    finally:
        base.frozen_modules = original


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder',type=Path,required=True)
    parser.add_argument('--external',action='store_true')
    parser.add_argument('--ledger',type=Path,default=LEDGER)
    args=parser.parse_args()
    verify(args.folder.resolve(),external=args.external,ledger_path=args.ledger)
