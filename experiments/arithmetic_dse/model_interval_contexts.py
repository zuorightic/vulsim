"""Verified capture-load contexts for native arithmetic interval sampling."""
import argparse
import json
from pathlib import Path
from .model_collection import PROTOCOL,sha,write
from .model_mul_intervals import interval,source,context_features
from .budget import POLICY,Ledger,usage
from .platforms import profile
from .model_mul_intervals import key

CONFIG=Path(__file__).with_name('configs')/'model_mul_interval_contexts_v1.json'

def prepare_collection(graphs,out,predecessor):
    """Keep exact eligible F1 measurements; create only new load sources."""
    out.mkdir(parents=True,exist_ok=False);cfg=json.loads(CONFIG.read_text());old_path=predecessor/'admission.json'
    old=json.loads(old_path.read_text());tasks=[];p=profile('asap7');counts={};ref=1500
    blocked={t['rtl_sha256'] for t in old['tasks'] if t['split']=='test'}
    for split,widths in cfg['splits'].items():
        for fanout in cfg['capture_fanouts'][split]:
            if fanout==1:
                if split=='test':raise ValueError('failed predecessor test cannot be reused')
                inherited=[t for t in old['tasks'] if t['split']==split]
                for original in inherited:
                    directory=predecessor/'runs'/original['id'];m=json.loads((directory/'manifest.json').read_text())
                    if m['status']!='completed' or original['profile_sha256']!=p['profile_sha256']:raise ValueError('unqualified predecessor measurement')
                    if sha(original['rtl'])!=original['rtl_sha256'] or sha(directory/'input.sv')!=original['rtl_sha256'] or sha(directory/'sample-contract.json')!=original['sample_contract_sha256']:raise ValueError('changed inherited F1 source')
                    contract=json.loads(Path(original['sample_contract']).read_text())
                    if any(s['fanout']!=1 or s['width'] not in widths for s in contract['labels']):raise ValueError('inherited sample differs from declared split/load')
                    task=dict(original,capture_fanout=1,reuse_directory=str(directory.resolve()),reuse_manifest_sha256=sha(directory/'manifest.json'),
                              reuse_admission=str(old_path.resolve()),reuse_admission_sha256=sha(old_path))
                    tasks.append(task)
                counts[split+'/F1']={'tasks':len(inherited),'samples':sum(t['samples'] for t in inherited),'inherited':True}
                continue
            items=[]
            for path in sorted(graphs.glob('*.json')):
                report=json.loads(path.read_text());region=report['graph']['regions'][0]
                if region['parameters']['lhs_width'] not in widths:continue
                for first in range(len(region['legal_groups'])):
                    for last in range(first,len(region['legal_groups'])):items.append((report,interval(report,first,last)))
            packs=[];pack=[];inputs=captures=0;limits=cfg['pack_limit']
            for item in items:
                ins=sum(item[1]['input_widths']);caps=item[1]['capture_width']*fanout
                if pack and (len(pack)>=limits['samples'] or inputs+ins>limits['input_variable_bits'] or captures+caps>limits['total_capture_variable_bits']):
                    packs.append(pack);pack=[];inputs=captures=0
                pack.append(item);inputs+=ins;captures+=caps
            if pack:packs.append(pack)
            for number,pack in enumerate(packs):
                name=f'{split}-F{fanout}-b{number:03d}';folder=out/name;folder.mkdir()
                text,labels=source(pack,capture_fanout=fanout);rtl=folder/'input.sv';rtl.write_text(text)
                contract=folder/'contract.json';write(contract,{'version':'arithmetic-model-labels-v1','source_group':name,'split':split,
                    'protocol_sha256':sha(CONFIG),'capture_fanout':fanout,'labels':labels})
                if sha(rtl) in blocked:raise ValueError('predecessor independent-test source entered new collection')
                tasks.append({'id':'asap7-'+name,'platform':'asap7','profile_sha256':p['profile_sha256'],'top':'ModelBundle',
                    'period_ps':ref,'abc_target_ps':ref,'stage':'grt','rtl':str(rtl.resolve()),'rtl_sha256':sha(rtl),
                    'sample_contract':str(contract.resolve()),'sample_contract_sha256':sha(contract),'source_group':name,'split':split,
                    'samples':len(labels),'capture_fanout':fanout,'static_launch_bits':sum(sum(s['input_widths']) for s in labels),
                    'static_capture_bits':sum(s['capture_width']*fanout for s in labels),
                    'capacity_scope':'<=32 native intervals, max6 cores, input<=640 and total capture<=2048 unless single-core; finite new-load probes prerequisite',
                    'synth_timeout_s':300,'route_timeout_s':1200,'memory_limit_MiB':8192})
            counts[split+'/F'+str(fanout)]={'tasks':len(packs),'samples':len(items),'inherited':False}
    new=sum(not t.get('reuse_directory') for t in tasks)
    admission={'version':'arithmetic-model-collection-admission-v1','id':out.name,'purpose':'arithmetic_model_collection',
        'protocol_sha256':sha(PROTOCOL),'policy_sha256':sha(POLICY),'supplemental_protocol':{'path':str(CONFIG.resolve()),'sha256':sha(CONFIG)},
        'tasks':tasks,'not_training':False,'test_read_after_fit_only':True,'automatic_retries':0,
        'call_caps':{'synth':new,'grt':new,'final':0},'support_walltime_s':10800,'worst_case_leaf_walltime_s':new*1860+10800,
        'later_work_reserved':{'walltime_s':86400,'CPU_time_s':172800,'synth':688,'grt':688},
        'main_matrix_authorized':False,'counts':counts,'blocked_predecessor_test_sources':sorted(blocked),
        'predecessor_admission':str(old_path.resolve()),'predecessor_admission_sha256':sha(old_path),
        'independence_claim':cfg['independence_claim'],'production_query_scope':cfg['production_query_scope'],
        'storage':{'full':'local ignored retained runs and explicit catalog; remote retention unconfirmed','planning_bytes':new*512*1024*1024}}
    current=usage(json.loads(Ledger().path.read_text())['entries']);limits=json.loads(POLICY.read_text())['resources']
    if current['walltime_s']+admission['worst_case_leaf_walltime_s']+86400>limits['max_global_walltime_h']*3600:raise ValueError('new-load collection and later reserve not funded')
    if current['CPU_time_s']+2*admission['worst_case_leaf_walltime_s']+172800>limits['max_tool_CPU_time_h']*3600:raise ValueError('new-load CPU reserve not funded')
    write(out/'admission.json',admission)
    print(json.dumps({'counts':counts,'new_physical_tasks':new,'inherited_tasks':len(tasks)-new,'worst_case_wall_s':admission['worst_case_leaf_walltime_s']}))


def extract(folder,splits,selection_freeze=None):
    from .model_mul_interval_fit import verify_measurement
    from .model_samples import verify_capture_banks
    from .model_collection import verify_test_release
    admission_path=folder/'admission.json';a=json.loads(admission_path.read_text())
    if a.get('not_training') is not False or a.get('test_read_after_fit_only') is not True or a['supplemental_protocol']['sha256']!=sha(CONFIG):raise ValueError('frozen model collection required, capacity probes are not fitting data')
    if 'test' in splits:verify_test_release(admission_path,selection_freeze,['asap7'])
    rows=[];failures=[]
    for t in a['tasks']:
        if t['split'] not in splits:continue
        if t['rtl_sha256'] in a['blocked_predecessor_test_sources']:raise ValueError('old independent-test source is sealed')
        directory=Path(t['reuse_directory']) if t.get('reuse_directory') else folder/'runs'/t['id']
        manifest_path=directory/'manifest.json'
        if not manifest_path.is_file():failures.append({'task':t['id'],'status':'not_run'});continue
        m=json.loads(manifest_path.read_text())
        if m['status']!='completed':failures.append({'task':t['id'],'status':m['status'],'reason':m.get('failure_reason')});continue
        origin=a;origin_task=t;origin_hash=sha(admission_path)
        if t.get('reuse_directory'):
            if sha(manifest_path)!=t['reuse_manifest_sha256'] or sha(t['reuse_admission'])!=t['reuse_admission_sha256']:raise ValueError('changed inherited measurement identity')
            origin=json.loads(Path(t['reuse_admission']).read_text());origin_hash=t['reuse_admission_sha256'];origin_task=next(x for x in origin['tasks'] if x['id']==t['id'])
            if origin_task['split']=='test':raise ValueError('old test may never become fitting data')
        if sha(directory/'input.sv')!=t['rtl_sha256'] or sha(directory/'sample-contract.json')!=t['sample_contract_sha256']:raise ValueError('changed context source/contract')
        contract=json.loads((directory/'sample-contract.json').read_text());cells=json.loads((directory/'liberty_cells.json').read_text())['cells']
        verify_measurement(directory,m,origin_task,origin,cells)
        for stage in m['metrics']:
            prefix=directory/f'reports/{t["platform"]}/arithmetic_probe/base/vulsim_{stage["stage"]}'
            instance_path=Path(str(prefix)+'_instances.tsv');actual=[line.split('\t')[:2] for line in instance_path.read_text().splitlines()]
            banks=verify_capture_banks(prefix,directory/'sample-contract.json',cells)
            if banks!=stage.get('model_capture_banks',{}):raise ValueError('actual bank witness differs from recorded stage')
            labels={x['id']:x for x in stage['model_labels']}
            for spec in contract['labels']:
                label=labels[spec['id']];comb=0.;capture=launch=0
                for name,master in actual:
                    if not name.startswith(spec['instance_scope']) or master not in cells:continue
                    cell=cells[master]
                    if cell['sequential']:
                        capture+=int(name.startswith(spec['instance_scope']+'dst') or name.startswith(spec['instance_scope']+'y'))
                        launch+=int(name.startswith(spec['instance_scope']+'src'))
                    elif name.startswith(spec['arithmetic_scope']):comb+=cell['area_um2']
                fanout=t['capture_fanout']
                if fanout!=spec['fanout'] or not 0<capture<=fanout*spec['capture_width'] or not 0<launch<=sum(spec['input_widths']) or comb<=0:raise ValueError('invalid actual context boundary/area')
                if fanout>1 and (banks[spec['id']]['capture_DFFs']!=capture or banks[spec['id']]['launch_DFFs']!=launch):raise ValueError('bank and scope count disagreement')
                rows.append({'id':t['id']+'/'+spec['id']+'/'+stage['stage'],'platform':t['platform'],'stage':stage['stage'],'split':t['split'],
                    'interval_key':key(spec),'features':context_features(spec,fanout),'spec':spec,'delay_ps':label['data_delay_ps'],'comb_area_um2':comb,
                    'capture_DFFs':capture,'launch_DFFs':launch,'capture_bank_counts':banks.get(spec['id'],{}).get('capture_bank_counts',{spec['id']:capture}),
                    'bank_path_ids':[b['id'] for b in spec.get('capture_banks',[])] or [spec['id']],
                    'source_sha256':t['rtl_sha256'],'contract_sha256':t['sample_contract_sha256'],'manifest_sha256':sha(manifest_path),
                    'source_admission_sha256':origin_hash,'source_admission_id':origin['id'],'reused_measurement':bool(t.get('reuse_directory')),
                    'instances_sha256':sha(instance_path),'points_sha256':label['points_sha256'],'profile_sha256':t['profile_sha256'],
                    'period_ps':t['period_ps'],'abc_target_ps':t['abc_target_ps']})
    return {'version':'arithmetic-mul-interval-context-dataset-v1','protocol_sha256':sha(CONFIG),'admission_sha256':sha(admission_path),
            'admission_path':str(admission_path.resolve()),'rows':rows,'failures':failures,'not_training':False,
            'old_independent_test_excluded':True,'capacity_probes_excluded':True,'independence_claim':a['independence_claim']}

def prepare_probe(graphs,out):
    out.mkdir(parents=True,exist_ok=False)
    indexed={}
    for path in graphs.glob('*.json'):
        graph=json.loads(path.read_text());parameters=graph['graph']['regions'][0]['parameters']
        indexed[parameters['lhs_width'],parameters['block_width'],parameters['result_width']]=graph
    specifications=[(16,8,32,0,0,2),(16,4,32,1,3,3),(32,8,64,0,0,4),(32,8,32,1,4,4)]
    tasks=[];p=profile('asap7');ref=1500
    for number,(width,block,result,first,last,fanout) in enumerate(specifications):
        graph=indexed[width,block,result];spec=interval(graph,first,last);text,labels=source([(graph,spec)],capture_fanout=fanout)
        name=f'asap7-load-probe-{number:02d}-F{fanout}-W{width}';folder=out/name;folder.mkdir()
        rtl=folder/'input.sv';rtl.write_text(text)
        contract=folder/'contract.json';write(contract,{'version':'arithmetic-model-labels-v1','source_group':name,
            'split':'capacity_probe','not_training':True,'protocol_sha256':sha(CONFIG),'labels':labels})
        write(folder/'graph.json',graph)
        tasks.append({'id':name,'platform':'asap7','profile_sha256':p['profile_sha256'],'top':'ModelBundle',
            'period_ps':ref,'abc_target_ps':ref,'stage':'grt','rtl':str(rtl.resolve()),'rtl_sha256':sha(rtl),
            'sample_contract':str(contract.resolve()),'sample_contract_sha256':sha(contract),
            'source_group':name,'split':'capacity_probe','samples':1,'capture_fanout':fanout,
            'static_launch_bits':sum(spec['input_widths']),'static_capture_bits':spec['capture_width']*fanout,
            'capacity_scope':'single actual native interval, W16/W32, verified capture fanout2/3/4; not a model-quality test',
            'synth_timeout_s':300,'route_timeout_s':1200,'memory_limit_MiB':8192})
    admission={'version':'arithmetic-model-collection-admission-v1','id':out.name,'purpose':'arithmetic_model_collection',
        'protocol_sha256':sha(PROTOCOL),'policy_sha256':sha(POLICY),'supplemental_protocol':{'path':str(CONFIG.resolve()),'sha256':sha(CONFIG)},
        'tasks':tasks,'not_training':True,'test_read_after_fit_only':False,'automatic_retries':0,
        'call_caps':{'synth':4,'grt':4,'final':0},'support_walltime_s':1800,'worst_case_leaf_walltime_s':9240,
        'later_work_reserved':{'walltime_s':86400,'CPU_time_s':172800,'synth':688,'grt':688},
        'main_matrix_authorized':False,'scope':'finite new-load boundary/function/capacity audit only; all labels excluded from fitting, margin selection and independent model tests',
        'evidence_basis':{'prior_single_bank_peak_grt_s':294.7359190369025,'prior_single_bank_peak_RSS_MiB':834.50390625,
            'limitation':'new capture loads require these probes; no inference of bulk completion or model quality'},
        'storage':{'estimate_bytes':4*512*1024*1024,'portable':'small contracts/RTL/raw labels and receipts','full':'local retained runs, remote persistence unconfirmed'}}
    current=usage(json.loads(Ledger().path.read_text())['entries']);limits=json.loads(POLICY.read_text())['resources']
    if current['walltime_s']+9240+86400>limits['max_global_walltime_h']*3600:raise ValueError('new-context probes and later reserve are not funded')
    write(out/'admission.json',admission);print(json.dumps({'tasks':len(tasks),'not_training':True,'admission':str(out/'admission.json')}))


def audit_probe(folder,out):
    from .model_mul_interval_fit import verify_measurement
    from .model_samples import verify_capture_banks
    admission=json.loads((folder/'admission.json').read_text())
    if admission.get('not_training') is not True or admission['supplemental_protocol']['sha256']!=sha(CONFIG):raise ValueError('frozen capacity-only context admission required')
    results=[]
    for task in admission['tasks']:
        directory=folder/'runs'/task['id'];manifest=json.loads((directory/'manifest.json').read_text())
        if manifest['status']!='completed':raise ValueError('new-context capacity task failed')
        if sha(directory/'input.sv')!=task['rtl_sha256'] or sha(directory/'sample-contract.json')!=task['sample_contract_sha256']:raise ValueError('changed new-context source')
        cells=json.loads((directory/'liberty_cells.json').read_text())['cells']
        verify_measurement(directory,manifest,task,admission,cells)
        for stage in manifest['metrics']:
            prefix=directory/f'reports/asap7/arithmetic_probe/base/vulsim_{stage["stage"]}'
            banks=verify_capture_banks(prefix,directory/'sample-contract.json',cells)
            if banks!=stage['model_capture_banks']:raise ValueError('changed actual bank-count witness')
            results.append({'task':task['id'],'stage':stage['stage'],'banks':banks,
                            'bank_path_witnesses':len(stage['model_labels'])-1,'manifest_sha256':sha(directory/'manifest.json')})
    report={'version':'native-interval-load-probe-audit-v1','status':'passed','admission_sha256':sha(folder/'admission.json'),
            'not_training':True,'numerical_quality_claim':False,'results':results}
    write(out,report);print(json.dumps(report,indent=2))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['prepare-probe','audit-probe','prepare','extract'])
    parser.add_argument('--graphs',type=Path);parser.add_argument('--folder',type=Path);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--predecessor',type=Path);parser.add_argument('--selection-freeze',type=Path);parser.add_argument('--splits',nargs='+',choices=['train','validation','test'],default=['train','validation'])
    args=parser.parse_args()
    if args.action=='prepare-probe':
        if args.graphs is None:parser.error('--graphs required')
        prepare_probe(args.graphs,args.out)
    elif args.action=='audit-probe':
        if args.folder is None:parser.error('--folder required')
        audit_probe(args.folder,args.out)
    elif args.action=='prepare':
        if args.graphs is None or args.predecessor is None:parser.error('--graphs and --predecessor required')
        prepare_collection(args.graphs,args.out,args.predecessor)
    else:
        if args.folder is None:parser.error('--folder required')
        write(args.out,extract(args.folder,args.splits,args.selection_freeze))


if __name__=='__main__':main()
