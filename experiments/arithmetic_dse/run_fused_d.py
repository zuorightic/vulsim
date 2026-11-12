"""Offline D selection with qualified operator/S functions and G reductions.

Each region is priced from bit geometry and numerical T, then emitted under
the same fusion policy. No candidate implementation is measured for selection.
"""
import argparse
from copy import deepcopy
from pathlib import Path
import subprocess
import tempfile
from .model_fast_preflight import read,write,sha

ROOT=Path(__file__).resolve().parents[2]
DEFAULT_BUNDLE=ROOT/'experiments/arithmetic/models/asap7_fused_D_prototype_v1/bundle.json'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-request',type=Path,required=True)
    p.add_argument('--period-ps',type=float,required=True)
    p.add_argument('--latency',type=int,required=True,help='L includes output capture and excludes input service launch')
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--bundle',type=Path,default=DEFAULT_BUNDLE)
    p.add_argument('--binary',type=Path,default=ROOT/'build/G-reduction-20261112/rtlzz-fused-d')
    p.add_argument('--assignment-limit',type=int,default=1000000)
    a=p.parse_args();manifest=read(a.bundle);base=a.bundle.resolve().parent
    if manifest['output_scope']!='prototype-no-reset-timing-v1' or manifest['full_D_ready'] or manifest['reset_timing_checked']:
        p.error('unsupported D bundle scope')
    deps={}
    for n,d in manifest['dependencies'].items():
        path=(base/d['path']).resolve()
        if sha(path)!=d['sha256']:p.error('D dependency changed: '+n)
        deps[n]=path
    for n,h in manifest['consumer_sources'].items():
        if sha(ROOT/n)!=h:p.error('D consumer source changed: '+n)
    if sha(a.binary)!=manifest['consumer_binary_sha256']:p.error('D executable differs from verified delivery')
    document=deepcopy(read(a.source_request));source=document['source'];path=Path(source['source'])
    if not path.is_absolute():path=a.source_request.resolve().parent/path
    if sha(path)!=source['generated_source_sha256']:p.error('C++ source identity differs')
    source['source']=str(path.resolve())
    with tempfile.TemporaryDirectory(prefix='fused-D-request-') as tmp:
        request=Path(tmp)/'source-request.json';write(request,dict(version='D-source-metadata-v1',source=source))
        cmd=[str(a.binary.resolve()),'--root',str(ROOT),'--source-request',str(request),
             '--node-model',str(deps['operators']),'--state-binding',str(deps['S_binding']),
             '--composition-policy',str(deps['composition']),'--G-model',str(deps['G_reduction']),
             '--period-ps',str(a.period_ps),'--latency',str(a.latency),
             '--output-scope',manifest['output_scope'],'--assignment-limit',str(a.assignment_limit),'--out',str(a.out.resolve())]
        result=subprocess.run(cmd)
    if result.returncode==0:
        report=read(a.out/'selection.json');write(a.out/'invocation.json',dict(bundle_sha256=sha(a.bundle),consumer_binary_sha256=sha(a.binary),
            original_source_request_sha256=sha(a.source_request),target_period_ps=a.period_ps,L=a.latency,
            selection_status=report['selection_status'],reduction_policy=manifest['reduction_policy'],candidate_PPA_calls=0,full_D_ready=False))
    raise SystemExit(result.returncode)


if __name__=='__main__':main()
