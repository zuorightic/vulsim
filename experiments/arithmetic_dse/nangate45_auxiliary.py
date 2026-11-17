"""Seal auxiliary N3/N4 contracts before validation and audit paired flow facts."""
import argparse
from pathlib import Path

from .nangate45_samples import ROOT,read,write,sha,verify
from . import nangate45_fit_sealed as statistics
from . import nangate45_response_features as features


def flow_audit(root):
    a=verify(root);rows=[];issues=[]
    for s in a['sources']:
        for p in s['paired_ASAP7']:
            folder=Path(p['rtl']).parent;mfile=folder/'manifest.json';m=read(mfile);label=read(p['label'])
            target=m.get('period_ps');abc=m.get('abc_target_ps')
            if target!=p['target_ps'] or abc!=p['target_ps']:
                issues.append([s['id'],p['target_ps'],target,abc])
            rows.append(dict(source=s['id'],campaign_role=s['role'],historical_role=p['historical_role'],target_ps=p['target_ps'],
                manifest_path=str(mfile),manifest_sha256=sha(mfile),actual_SDC_ps=target,actual_ABC_ps=abc,
                platform=m.get('target_platform'),profile_sha256=m.get('platform_profile',{}).get('profile_sha256'),
                tools=m.get('tools'),libraries=m.get('libraries'),label_stage=label.get('stage'),
                label_eligible=label.get('physical_training_label_eligible'),label_sha256=sha(p['label'])))
    if issues or any(r['platform']!='asap7' or r['label_stage']!='grt' or not r['label_eligible'] for r in rows):
        raise ValueError('paired existing ASAP7 flow/label incompatible')
    result=dict(rows=rows,clock_identity_mismatches=issues,ASAP7_EDA_calls=0,historical_locked_sources_opened=False)
    path=root/'paired-ASAP7-flow-audit.json'
    if path.exists():
        if read(path)!=result:raise ValueError('paired original flow facts changed')
    else:write(path,result)
    return dict(paired_labels=len(rows),clock_mismatches=0,sha256=sha(path))


def seal(root):
    root=Path(root).resolve();a=verify(root)
    if any((root/'runs'/t['id']).exists() for t in a['tasks'] if t['role']!='train'):
        raise ValueError('auxiliary contracts must precede validation/test collection')
    if not (root/'statistical-contract.json').exists():statistics.preregister(root)
    if not (root/'feature-contract.json').exists():features.preregister(root)
    audit=flow_audit(root);path=root/'N3-analysis-contract.json'
    if not path.exists():
        write(path,dict(version='paired-actual-analysis-v1',forms=['global proportional','family proportional','family affine'],
            fitted_labels='train only, equal source weight',evaluated_roles=['train','validation','test'],
            compiler_prices=False,selected_by_test=False,validation_labels_read=False,test_labels_read=False,
            implementation_sha256=sha(Path(__file__).with_name('nangate45_report.py')),
            original_ASAP7_flow_audit_sha256=sha(root/'paired-ASAP7-flow-audit.json')))
    contract=read(path)
    if contract['implementation_sha256']!=sha(Path(__file__).with_name('nangate45_report.py')):
        raise ValueError('actual-to-actual analysis implementation drift')
    return dict(status='auxiliary contracts sealed',flow_audit=audit)


if __name__=='__main__':
    import json
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('seal','audit'));p.add_argument('--root',type=Path,required=True);a=p.parse_args()
    print(json.dumps(seal(a.root) if a.action=='seal' else flow_audit(a.root),indent=2))
