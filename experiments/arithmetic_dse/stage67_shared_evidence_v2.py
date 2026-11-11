"""Archive-compression receipt successor; inference and verdict unchanged."""
import argparse
import inspect
from pathlib import Path
from . import stage67_shared_evidence_v1 as parent


def package(root,evidence):
    text=inspect.getsource(parent.package)
    old='shared-function-raw-v1.tar.gz.index.json'
    if text.count(old)!=1:raise ValueError('archive receipt callsite drift')
    ns=dict(parent.package.__globals__)
    exec(compile(text.replace(old,'shared-function-raw-v2.tar.gz.index.json'),__file__,'exec'),ns)
    ns['package'](root,evidence)
    m=parent.read(evidence/'manifest.json');m.update(version='shared-function-fit-evidence-v2',archive_compression_timeout_preserved=True)
    parent.write(evidence/'manifest.json',m)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('package','replay'));p.add_argument('--root',type=Path);p.add_argument('--evidence',type=Path,required=True);a=p.parse_args()
    if a.action=='package':package(a.root.resolve(),a.evidence.resolve())
    else:parent.replay(a.evidence.resolve())
