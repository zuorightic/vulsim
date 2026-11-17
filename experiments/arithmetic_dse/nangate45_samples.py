"""Finite paired N3 campaign; all physical products live outside Git.

Existing ASAP7 training sources are reused byte for byte. Campaign folds are
shared by both platforms; the held-out fold tests new-backend labels, not an
unseen structure for the already trained ASAP7 response. Locked historical
independent sources are never opened here.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import shutil

from . import budget, workload_nine_runtime as runtime
from .platforms import profile

ROOT = Path(__file__).resolve().parents[2]
VERSION = 'nangate45-N34-paired-v1'
CLOCKS = (500, 1500, 3000)
# A complete source, including every clock/load variant and platform copy,
# receives one campaign role. Historical roles are recorded separately.
SOURCES = {
 'Mul': {
  'train': ['operator-0e3e802d6fe79d53','operator-22ed3945e82bd47f','wide-5660be387111d809'],
  'validation': ['wide-febe867d4f6e6a5b'],
  'test': ['operator-5c6f82abc0f8c1c3','wide-64eb4ca46ec8e799']},
 'Add': {
  'train': ['operator-7ab4f32d7bb9b588','wide-951cc96c1fb88338','wide-6c1e33e2246ff438',
            'wide-d232ec69b47f206a','wide-d3d779a9d9167355','wide-74b91cebde906039'],
  'validation': ['operator-0733f1ef9a9165d4','wide-f826704868db02bf'],
  'test': ['wide-4299d1c9f59e7b66','wide-d842786f167bb36d']},
 'G': {
  'train': ['new/G-a4736d1f1d9438c7','new/G-c9bad07c2b1f226b'],
  'validation': ['repair/G-0b07a9ff77ffdf9d'],
  'test': ['G-73053738e9cc1ee8']}}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def catalogs():
    base = ROOT/'experiments/arithmetic/evidence'
    p = base/'common_transition_incidence_v10/train-data.json.gz'
    q = base/'common_model_repair_v1/unified-fit--operator-train-data.json.gz'
    data = json.loads(gzip.decompress(p.read_bytes()))['data']
    data['Mul'] = [r for r in json.loads(gzip.decompress(q.read_bytes()))['rows'] if r['family'] == 'mul']
    return data, (p,q)


def prepare(root,parent=None):
    root = Path(root).resolve()
    if root.is_relative_to(ROOT) or root.exists():
        raise ValueError('a new external artifact root is required')
    data, indexes = catalogs(); sources=[]; tasks=[]; files={str(p):sha(p) for p in indexes}
    for family, folds in SOURCES.items():
        for role, names in folds.items():
            for name in names:
                rows = sorted([r for r in data[family] if r['source'] == name],key=lambda r:r['target_ps'])
                if [r['target_ps'] for r in rows] != list(CLOCKS) or any(r['role'] != 'train' for r in rows):
                    raise ValueError('only complete existing training clocks: '+name)
                refs=[]; source_hashes=set()
                for r in rows:
                    label = Path(r.get('label_path',r.get('physical_label_path')))
                    expected = r.get('label_sha256',r.get('physical_label_sha256'))
                    if sha(label) != expected: raise ValueError('old label changed: '+str(label))
                    rtl = Path(r.get('directory',str(label.parent)))/'input.sv'; source_hashes.add(sha(rtl))
                    files[str(rtl)] = sha(rtl)
                    refs.append(dict(target_ps=r['target_ps'],label=str(label),label_sha256=expected,
                                     rtl=str(rtl),rtl_sha256=sha(rtl),query=r['query'],
                                     historical_role=r['role'],campaign_role=role))
                if len(source_hashes) != 1: raise ValueError('clock changes RTL: '+name)
                local = rows[0]['query'].get('local_context')
                short = name.replace('/','--')
                dest = root/'sources'/short/'input.sv'
                dest.parent.mkdir(parents=True);shutil.copyfile(refs[0]['rtl'],dest)
                query = rows[0]['query']
                source = dict(id=name,family=family,role=role,historical_role='train',
                              independent_of_ASAP7_training=False,rtl=str(dest),rtl_sha256=sha(dest),
                              local_context=local,query=query,paired_ASAP7=refs)
                sources.append(source)
                for t in CLOCKS:
                    tasks.append(dict(id=short+'-T'+str(t),source=name,family=family,role=role,
                                      rtl=str(dest),rtl_sha256=sha(dest),period_ps=t))
    # Train/validation are collected first; test labels are opened only after
    # the selected model and all numerical parameters have been frozen.
    tasks.sort(key=lambda t:({'train':0,'validation':1,'test':2}[t['role']],t['family'],t['source'],t['period_ps']))
    modules = list((ROOT/'experiments/arithmetic_dse').glob('*.py'))
    assets = list((ROOT/'experiments/arithmetic_dse/reference_assets').glob('*.tcl'))
    paths = [*modules,*assets,runtime.POLICY,runtime.BRIDGE,budget.POLICY,budget.CHECKPOINT,
             ROOT/'experiments/arithmetic_dse/configs/platforms/nangate45.json']
    files.update({str(p):sha(p) for p in paths})
    state=read(budget.LEDGER);used=budget.usage(state['entries']);limits=read(runtime.POLICY)['resources']
    # Seven support leaves: synth tool versions(3), mapped JSON, boundary
    # census, snapshot, logical census/readout = eight (allow ten per point).
    n=len(tasks);wall=n*(300+1200+10*120)
    if (used['walltime_s']+wall > 3600*limits['max_global_walltime_h'] or
        used['CPU_time_s']+2*wall > 3600*limits['max_tool_CPU_time_h'] or
        used['synth']+n > limits['max_synthesis_calls'] or used['grt']+n > limits['max_global_route_calls'] or
        shutil.disk_usage(root.parent).free < 20*1024**3):
        raise ValueError('finite collection not funded or insufficient external storage')
    inheritance=None
    if parent:
        parent=Path(parent).resolve();old=read(parent/'admission.json');p=read(parent/'progress.json')
        if p['completed'] or len(p['errors'])!=1 or p['errors'][0]['task']!=tasks[0]['id']:
            raise ValueError('one retained initial PDN failure required')
        prior=parent/'runs'/tasks[0]['id']
        log=(prior/'grt.log').read_text() if (prior/'grt.log').exists() else ''
        grt_complete=(prior/'results/nangate45/arithmetic_probe/base/5_1_grt.odb').exists() and (
            ((prior/'grt.command.json').exists() and read(prior/'grt.command.json')['exit_code']==0) or old['tasks'][0].get('inherit_grt'))
        cec=('StopIteration' in log and (prior/'results/nangate45/arithmetic_probe/base/4_1_post_repair_pre_lec.odb').exists())
        if not grt_complete and not cec and (not any(s in log for s in ('[ERROR PDN-0185]','Floorplan initialization methods are mutually exclusive')) or (prior/'results/nangate45/arithmetic_probe/base/3_1_place_gp.odb').exists()):
            raise ValueError('only the diagnosed initial integration failure may continue')
        paths=[p for p in prior.rglob('*') if p.is_file() and not p.is_symlink()]
        tasks[0]['inherit_synth']=dict(directory=str(prior),files={str(p.relative_to(prior)):sha(p) for p in paths},
                                     reason='same mapped checkpoint; fresh floorplan with common minimum 60um core before placement')
        if cec:tasks[0]['inherit_post_repair']=True
        if grt_complete:
            tasks[0]['inherit_grt']=True
            tasks[0]['inherited_CEC_root']=old['tasks'][0].get('inherited_CEC_root',str(prior))
        inheritance=dict(path=str(parent/'admission.json'),sha256=sha(parent/'admission.json'),
                         retained_failed_grt=1,synthesis_repeated=False,labels_produced=0)
    a=dict(version=VERSION,id='matrix-nangate45-N34-paired-'+root.name.rsplit('-',1)[-1],purpose='offline_paired_operators',
           platform='nangate45',profile_sha256=profile('nangate45')['profile_sha256'],
           sources=sources,tasks=tasks,files=files,clocks_ps=list(CLOCKS),
           call_caps=dict(synth=n-int(bool(inheritance)),grt=n-int(bool(tasks[0].get('inherit_grt'))),final=0,support=10*n),serial_workers=1,threads=2,
           memory_limit_MiB=4096,minimum_available_MiB=12288,synth_timeout_s=300,grt_timeout_s=1200,
           support_timeout_s=120,worst_case_leaf_walltime_s=wall,CPU_envelope_s=2*wall,
           external_storage_envelope_GiB=20,starting_usage=used,ledger=str(budget.LEDGER),automatic_retries=0,
           stop='first physical failure, unresolved ownership/units/CEC, budget or hash drift; retain evidence',
           roles='campaign source groups shared across clocks/load variants/platforms; historical train only; no historical independent labels',
           model_candidates=['global_scale','family_scale','family_affine','shared_log_feature_ridge'],
           ridge_alpha=[0.1,1.0,10.0],request_time_scale_candidates=[0.5,1.0,2.0],
           selection='train only parameters; source-balanced validation median then P95 then complexity; freeze before test labels',
           error_contract=dict(source_aggregation='median APE across clocks per source; numpy linear quantile across sources',
                               median_APE_max=0.15,P95_APE_max=0.35,source_median_APE_max=0.35),
           labels='grt exclusive producer internal maximum delay and combinational area; not shell Tmin',
           sampling_layout_overrides=dict(minimum_core_side_um=60,core_utilization_percent=40,core_margin_um=5),parent=inheritance,
           sampling_flow_difference='square core ceil(sqrt(synth_area/0.4)), minimum 60um; profile margin 5um; N5/N6 embedding validation required',
           full_D_ready=False,application_PPA_used=False,R1_R5_modified=False)
    write(root/'admission.json',a)
    write(root/'progress.json',dict(completed=[],phase='admitted',errors=[]))
    return dict(sources=len(sources),tasks=n,role_sources=dict(Counter(s['role'] for s in sources)),admission_sha256=sha(root/'admission.json'))


def verify(root):
    a=read(Path(root)/'admission.json')
    if a['version'] != VERSION:raise ValueError('unknown sampling admission')
    for p,h in a['files'].items():
        if sha(p)!=h:raise ValueError('sampling source drift: '+p)
    for s in a['sources']:
        if sha(s['rtl'])!=s['rtl_sha256']:raise ValueError('sample RTL drift')
    if profile(a['platform'])['profile_sha256']!=a['profile_sha256']:raise ValueError('platform drift')
    return a


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','verify'));p.add_argument('--root',type=Path,required=True);p.add_argument('--parent',type=Path);a=p.parse_args()
    print(json.dumps(prepare(a.root,a.parent) if a.action=='prepare' else dict(status='passed',tasks=len(verify(a.root)['tasks'])),indent=2))
