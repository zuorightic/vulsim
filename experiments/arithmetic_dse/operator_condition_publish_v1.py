"""Concrete reviewable step-5 publication; qualified nodes, separate joint gate."""
import argparse
from copy import deepcopy
import gzip
import hashlib
import json
import math
from pathlib import Path
import shutil
import tarfile
import tempfile

from .model_fast_preflight import read,write,sha
from . import operator_condition_model as inference,operator_collection as collection
from . import operator_condition_release_v1 as release,operator_ownership_replay_v1 as physical
from . import model_logical_ownership_v2 as ownership,model_physical_labels_v2 as raw_reader
from .operator_stage4 import archive
from .budget import Ledger,usage

ROOT=Path(__file__).resolve().parents[2]


def publish(root,node,fresh,evidence,models):
    if evidence.exists() or models.exists():raise ValueError('preserve publication version')
    consumer=root/'public-consumer-v2'
    acceptance=read(root/'acceptance.json');native=read(root/'native-parity.json');public=read(consumer/'proof.json')
    if acceptance['status']!='passed_bounded_node_release' or native['status']!='passed' or public['status']!='passed_actual_production_node_consumer':raise ValueError('release validation incomplete')
    model=read(root/'operators.json');release.restore_functional_identity(read(node/'fit-v2/candidate.json'),model)
    if public['published_model_sha256']!=sha(root/'operators.json') or native['actual_release_model_sha256']!=sha(root/'operators.json'):raise ValueError('validated another function')
    if public['candidate_permission_used'] or not public['full_D_joint_gate_retained']:raise ValueError('publication scope gate missing')
    calls=0
    for t in public['targets']:
        for v in t['views']:
            for q in v['node_prices']:
                answer=inference.query(model,q['descriptor'])
                if answer['status']!='covered':raise ValueError('real D query unsupported')
                for k in ('operator_delay_ps','delay_reserve_ps','comb_area_um2'):
                    if not math.isclose(answer[k],q[k],rel_tol=1e-10,abs_tol=1e-8):raise ValueError('real native/Python D price differs')
                calls+=1
    if calls!=2752:raise ValueError('incomplete real demand check')
    joint=read(consumer/'joint-refusal.json')
    if joint['formal_D_selection'] or joint['coverage_complete']:raise ValueError('unqualified S/G accepted')
    provenance=read(root/'provenance.json')
    for p,h in provenance['dependencies'].items():
        if sha(Path(p))!=h:raise ValueError('publication evidence dependency changed')
    # Shape generalization is an evidence report, not a support whitelist.
    fit=read(node/'fit-data.json')['rows'];fresh_rows=read(root/'fresh-data.json')['rows']
    train_shapes={json.dumps(r['descriptor']['local_context']['producer'],sort_keys=True) for r in fit if r['role']=='train'}
    fit_shapes={json.dumps(r['descriptor']['local_context']['producer'],sort_keys=True) for r in fit}
    source_summary=[]
    for sid in sorted({r['source_id'] for r in fresh_rows}):
        r=next(r for r in fresh_rows if r['source_id']==sid);shape=json.dumps(r['descriptor']['local_context']['producer'],sort_keys=True)
        source_summary.append(dict(source=sid,operation=r['operation'],unseen_training_producer_shape=shape not in train_shapes,
            unseen_fitting_producer_shape=shape not in fit_shapes,source_context_unseen=True,source_ids_used_as_predictors=False))
    write(root/'generalization.json',dict(fresh_sources=source_summary,exact1000ps_independent=True,continuous_support_not_exact_T_lookup=True,
        known_stage7_uncovered_structures='shared, shifted wide reduction and some saved-value shapes retain their documented cost_uncovered; no stage7 qualification granted',full_D_ready=False))
    # Capture actual independent packets for isolated metrology replay.
    packets=[]
    for task in read(fresh/'admission.json')['tasks']:
        folder=fresh/'runs'/task['id'];contract=read(folder/'query-contract.json');pins0=read(folder/'liberty-pins.json')
        for stage in ('synth','grt'):
            pins=dict(pins0)
            for line in (folder/'reports'/physical.SUFFIX/('vulsim_'+stage+'_cells.tsv')).read_text().splitlines():
                n,count,area,filler,kind=line.split('\t')
                if n not in pins:pins[n]=dict(sequential=False,buffer_or_inverter=False,physical_only=True,data_pins=[],pins={},area_um2=0 if filler=='1' else float(area))
            d=folder/('logical-'+stage);packet=physical.packet_at(d/'context',dict(target_ps=task['period_ps']),pins,contract)
            packets.append(dict(task=task['id']+'/'+stage,packet=packet,nodes=contract['nodes'],banks=contract['banks'],
                ports=read(d/'top-ports.json'),certificate=read(d/'ownership-certificate.json'),label=read(folder/(stage+'-labels.json'))))
    evidence.mkdir(parents=True);models.mkdir(parents=True)
    for name in ('operators.json','acceptance.json','native-parity.json','physical-replay.json','generalization.json','provenance.json'):
        shutil.copy2(root/name,evidence/name)
    shutil.copy2(root/'operators.json',models/'operators.json')
    example=next(r['descriptor'] for r in fresh_rows if r['target_ps']==1000);write(models/'example-query-1000ps.json',example)
    files={}
    for n in set(collection.measurement_sources())|set(read(node/'fit-v2/selection-freeze.json')['implementation_sources']):files['source/'+n]=(ROOT/n).read_text()
    for p in list((ROOT/'experiments/arithmetic_dse').glob('model_logical_*.py'))+[Path(release.__file__),Path(__file__),ROOT/'regression/arithmetic_step5_release_replay.py',ROOT/'rtlzz/testv2/operator_release_consumer.cpp']:
        files['source/'+str(p.relative_to(ROOT))]=p.read_text()
    for n in ('experiments/__init__.py','experiments/arithmetic_dse/__init__.py'):
        if (ROOT/n).exists():files['source/'+n]=(ROOT/n).read_text()
    for n in ('operators.json','acceptance.json','fresh-data.json','native-input.json','native-output.json','generalization.json'):
        files['release/'+n]=(root/n).read_text()
    files['release/public-consumer.json']=(consumer/'proof.json').read_text()
    files['release/joint-refusal.json']=(consumer/'joint-refusal.json').read_text()
    files['ancestor/candidate.json']=(node/'fit-v2/candidate.json').read_text();files['ancestor/independent-test.json']=(node/'test-v2/independent-test.json').read_text()
    files['fresh/independent-result.json']=(fresh/'independent-result.json').read_text();files['fresh/admission.json']=(fresh/'admission.json').read_text()
    pool=dict(files=files,physical_packets=packets);raw=json.dumps(pool,sort_keys=True,separators=(',',':')).encode();compressed=gzip.compress(raw,mtime=0);chunks={}
    for i,at in enumerate(range(0,len(compressed),512*1024)):
        p=evidence/f'pool-{i:03d}.gzpart';p.write_bytes(compressed[at:at+512*1024]);chunks[p.name]=sha(p)
    shutil.copy2(ROOT/'regression/arithmetic_step5_release_replay.py',evidence/'replay.py')
    public_files={n:sha(evidence/n) for n in ('operators.json','acceptance.json','native-parity.json','physical-replay.json','generalization.json','provenance.json')}
    write(evidence/'manifest.json',dict(version='step5-published-node-function-evidence-v1',chunks=chunks,payload_sha256=hashlib.sha256(raw).hexdigest(),
        replay_sha256=sha(evidence/'replay.py'),public_files=public_files,physical_stages=len(packets),restored_members=len(files),published_model_sha256=sha(models/'operators.json'),full_D_ready=False))
    write(models/'release.json',dict(version='asap7-conditional-operator-release-v1',status='passed_bounded_node_release',model='operators.json',model_sha256=sha(models/'operators.json'),
        scope='node functions only, independent S/G/stage validation required',target_interval_ps=[500,3000],model_evidence=str(evidence.relative_to(ROOT)),
        native_consumer_queries=calls,parameters_inherited_from_candidate_sha256=provenance['dependencies'][str(node/'fit-v2/candidate.json')],
        failed_ancestor_report=str(node/'test-v2/independent-test.json'),old_verdict_unchanged=True,full_D_ready=False))
    write(root/'publication-paths.json',dict(models=str(models),evidence=str(evidence),model_sha256=sha(models/'operators.json'),state='awaiting_isolated_replay'))
    payload=root/'publication-source';payload.mkdir()
    for n,v in files.items():
        p=payload/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(v)
    (root/'restore').mkdir(exist_ok=True)
    receipt=archive(root,[root/'operators.json',root/'acceptance.json',root/'physical-replay.json',root/'native-parity.json',consumer,root/'provenance.json',root/'generalization.json',root/'fresh-data.json',payload],
        'step5-published-function.tar.gz')
    write(evidence/'restore-proof.json',{k:v for k,v in receipt.items() if k!='members'}|dict(member_count=len(receipt['members'])))
    if sum(p.stat().st_size for p in evidence.iterdir())>5*1024**2 or any(p.stat().st_size>1024**2 for p in evidence.iterdir()):raise ValueError('compact evidence limit')
    print(dict(status='published_pending_isolated_replay',model_sha256=sha(models/'operators.json'),physical_stages=len(packets),public_node_queries=calls,evidence_bytes=sum(p.stat().st_size for p in evidence.iterdir())),flush=True)


def restore_existing(root,evidence):
    """Finish a paid archive whose creation succeeded before restore setup."""
    target=root/'archives/step5-published-function.tar.gz';index=target.with_suffix(target.suffix+'.index.json')
    if index.exists() or (evidence/'restore-proof.json').exists():raise ValueError('preserve existing restoration')
    (root/'restore').mkdir(exist_ok=True);expected={}
    with tarfile.open(target,'r:gz') as bundle:
        for member in bundle:
            p=Path(member.name)
            if not member.isfile() or p.is_absolute() or '..' in p.parts or member.name in expected:raise ValueError('unsafe/duplicate archive member')
            original=root/p
            expected[member.name]=dict(sha256=sha(original),bytes=original.stat().st_size)
    with tempfile.TemporaryDirectory(prefix='publication-restore-',dir=root/'restore') as d:
        restored=Path(d)
        with tarfile.open(target,'r:gz') as bundle:bundle.extractall(restored,filter='data')
        actual={str(p.relative_to(restored)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in restored.rglob('*') if p.is_file()}
        if actual!=expected:raise ValueError('actual archive restore differs')
    receipt=dict(version='operator-full-artifact-restore-v1',status='passed',archive=str(target),archive_sha256=sha(target),archive_bytes=target.stat().st_size,
        logical_bytes=sum(v['bytes'] for v in expected.values()),members=expected,actual_restore_and_every_member_hash_checked=True,
        failed_initial_restoration_setup_preserved=True,paid_archive_reused=True,no_raw_artifacts_deleted=True,off_machine_backup=False)
    write(index,receipt);write(evidence/'restore-proof.json',{k:v for k,v in receipt.items() if k!='members'}|dict(member_count=len(expected)))
    print(dict(status='passed_existing_archive_restore',members=len(expected),new_EDA_calls=0),flush=True)


def close(root,work):
    paths=read(root/'publication-paths.json');evidence=Path(paths['evidence']);models=Path(paths['models'])
    receipts=[p for p in work.glob('release-isolated-replay-*/commands.json') if read(p)[0]['exit_code']==0]
    if not receipts:raise ValueError('no successful isolated replay receipt')
    receipt=sorted(receipts)[-1];proof=read(receipt)[0]
    if proof['exit_code'] or 'passed_step5_release_isolated_replay' not in Path(proof['log']).read_text():raise ValueError('isolated release replay not passed')
    manifest=read(evidence/'manifest.json');assert sha(models/'operators.json')==manifest['published_model_sha256']
    ids={r['budget_reservation_id'] for p in work.rglob('commands.json') for r in read(p)}
    entries=[e for e in read(Ledger().path)['entries'] if e['id'] in ids];u=usage(entries)
    if u['pending']:raise ValueError('publication cost unsettled')
    write(evidence/'publication-closure.json',dict(status='passed_step5_bounded_node_release',model_sha256=sha(models/'operators.json'),
        manifest_sha256=sha(evidence/'manifest.json'),isolated_replay_receipt_sha256=sha(receipt),
        entries=entries,usage=u,source_parameters_and_old_verdicts_preserved=True,full_D_ready=False))
    paths['state']='passed_step5_bounded_node_release';write(root/'publication-paths.json',paths)
    print(dict(status=paths['state'],usage=u,model=paths['models']+'/operators.json'),flush=True)


def package_successor(root,node,previous,evidence,models):
    if evidence.exists():raise ValueError('preserve evidence successor')
    m=read(previous/'manifest.json');compressed=b''
    for n,h in m['chunks'].items():
        if sha(previous/n)!=h:raise ValueError('parent evidence part changed')
        compressed+=(previous/n).read_bytes()
    raw=gzip.decompress(compressed)
    if hashlib.sha256(raw).hexdigest()!=m['payload_sha256']:raise ValueError('parent evidence payload changed')
    pool=json.loads(raw)
    for name,h in read(node/'fit-v2/selection-freeze.json')['implementation_sources'].items():
        if sha(ROOT/name)!=h:raise ValueError('frozen inference source changed')
        pool['files']['source/'+name]=(ROOT/name).read_text()
    for p in (Path(__file__),ROOT/'regression/arithmetic_step5_release_replay.py'):pool['files']['source/'+str(p.relative_to(ROOT))]=p.read_text()
    raw=json.dumps(pool,sort_keys=True,separators=(',',':')).encode();compressed=gzip.compress(raw,mtime=0)
    evidence.mkdir(parents=True);parts={}
    for i,at in enumerate(range(0,len(compressed),512*1024)):
        p=evidence/f'pool-{i:03d}.gzpart';p.write_bytes(compressed[at:at+512*1024]);parts[p.name]=sha(p)
    for name in m['public_files']:shutil.copy2(previous/name,evidence/name)
    shutil.copy2(ROOT/'regression/arithmetic_step5_release_replay.py',evidence/'replay.py')
    write(evidence/'manifest.json',dict(m,chunks=parts,payload_sha256=hashlib.sha256(raw).hexdigest(),replay_sha256=sha(evidence/'replay.py'),
        restored_members=len(pool['files']),parent_evidence_sha256=sha(previous/'manifest.json'),
        successor_reason='include complete frozen numeric-inference dependencies; original packaging failure preserved, model and labels unchanged'))
    write(evidence/'parent-archive-restore.json',read(previous/'restore-proof.json'))
    staging=root/'sealed-evidence-v2';staging.mkdir()
    for p in evidence.iterdir():shutil.copy2(p,staging/p.name)
    restored=archive(root,[staging],'step5-publication-evidence-v2.tar.gz')
    write(evidence/'restore-proof.json',{k:v for k,v in restored.items() if k!='members'}|dict(member_count=len(restored['members'])))
    metadata=read(models/'release.json');metadata['model_evidence']=str(evidence.relative_to(ROOT));write(models/'release.json',metadata)
    paths=read(root/'publication-paths.json');paths.update(evidence=str(evidence),state='awaiting_isolated_replay');write(root/'publication-paths.json',paths)
    print(dict(status='repackaged_unchanged_model',restored_members=len(pool['files']),bytes=sum(p.stat().st_size for p in evidence.iterdir())),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('publish','restore-existing','package-successor','close'));p.add_argument('--root',type=Path,required=True)
    for n in ('node','fresh','evidence','models','work','previous'):p.add_argument('--'+n,type=Path)
    a=p.parse_args()
    if a.action=='publish':publish(a.root.resolve(),a.node.resolve(),a.fresh.resolve(),a.evidence.resolve(),a.models.resolve())
    elif a.action=='restore-existing':restore_existing(a.root.resolve(),a.evidence.resolve())
    elif a.action=='package-successor':package_successor(a.root.resolve(),a.node.resolve(),a.previous.resolve(),a.evidence.resolve(),a.models.resolve())
    else:close(a.root.resolve(),a.work.resolve())
