"""Bounded independent followthrough and exact scoped resource closure."""
import argparse
from pathlib import Path

from .model_fast_preflight import read,write,sha
from . import operator_ownership_successor_v1 as successor,operator_stage4 as stages
from .budget import Ledger,usage

ROOT=Path(__file__).resolve().parents[2]


def run(root):
    try:
        successor.run(root)
        report=read(root/'independent-result.json');parent=Path(read(root/'admission.json')['parent_collection'])
        write(root/'followthrough.json',dict(phase='fresh_evaluation_complete',fresh_status=report['status'],
            original_verdict=read(parent/'test-v2/independent-test.json')['status'],original_verdict_retained=True,
            model_sha256=report['model_sha256'],parameters_changed=False,formal_full_domain_release=False,full_D_ready=False))
        stages.support(root,'archive-final-result',[__import__('sys').executable,'-B','-c',
            'from pathlib import Path; from experiments.arithmetic_dse.operator_stage4 import archive; r=Path('+repr(str(root))+'); archive(r,[r/"independent-result.json",r/"independent-evaluation-consumed.json",r/"progress.json",r/"followthrough.json"],"final-independent-result.tar.gz")'],180)
        evidence=ROOT/'experiments/arithmetic/evidence/step7_operator_ownership_fresh_v1'
        if evidence.exists():raise ValueError('preserve previous fresh evidence')
        evidence.mkdir(parents=True)
        for name in ('independent-result.json','followthrough.json','sources.json'):
            __import__('shutil').copy2(root/name,evidence/name)
        write(evidence/'provenance.json',dict(admission_sha256=sha(root/'admission.json'),retained_root=str(root),
            archive_restore=[{k:v for k,v in read(p).items() if k!='members'} for p in (root/'archives').glob('*.index.json')],
            unchanged_model_sha256=report['model_sha256'],old_test_verdict_unchanged=True,full_D_ready=False))
        (evidence/'README.md').write_text('# 归属恢复后的新独立源验证\n\n四个全新完整源、500／1000／1500／3000ps固定请求；参数、覆盖规则和reserve保持原冻结字节。结果见independent-result.json，旧独立失败仍保留；本包不授予完整域或S／G／D联合资格。完整产物及实际恢复归档保留在`'+str(root)+'`，本机同盘不称异机备份。\n')
    except Exception as error:
        stages.atomic(root/'followthrough.json',dict(phase='stopped_preserve_failure',error=str(error),full_D_ready=False));raise
    finally:
        ledger=read(Ledger().path);admission=sha(root/'admission.json')
        entries=[e for e in ledger['entries'] if e.get('admission_sha256')==admission or str(e.get('output','')).startswith(str(root)+'/')]
        write(root/'resource-closure.json',dict(entries=entries,usage=usage(entries),scope='exact successor admission or output root; includes software, physical, report and archive leaves, no parent collection fees',
            old_ledger_not_reset=True,full_D_ready=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();run(a.root.resolve())
