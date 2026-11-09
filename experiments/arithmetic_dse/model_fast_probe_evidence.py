"""Raw replay and portable diagnosis evidence; never fits on probe labels."""
import argparse
from collections import defaultdict
from contextlib import redirect_stdout
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile

from .model_fast_preflight import read,write,sha
from .budget import Ledger,cpu_seconds,usage
from . import model_fast_probe as collection
from . import model_fast_measurement as measurement
from . import model_fast_sdc
from .backend import stage_metrics,verify_orfs_area
from .platforms import profile,verify_wire_readback,library_data
from .model_reference_labels import liberty
from .model_m2_live_cec_v3 import verify_proof

ROOT=collection.ROOT;SUFFIX=collection.SUFFIX
VERSION='arithmetic-fast-probe-evidence-v1'


class Audit:
    def __init__(self,entries):
        self.entries={e['id']:e for e in entries};self.commands=set();self.directories={};self.hashed={};self.library_tables={}
    def digest(self,path):
        path=Path(path).resolve()
        if path not in self.hashed:self.hashed[path]=sha(path)
        return self.hashed[path]
    def ancestry(self,directory,visiting=None):
        directory=Path(directory).resolve()
        if directory in self.directories:return
        visiting=set() if visiting is None else visiting
        if directory in visiting:raise ValueError('cyclic fast diagnosis ancestry')
        visiting=visiting|{directory};m=read(directory/'manifest.json');a=read(directory.parent.parent/'admission.json');owner=self.digest(directory.parent.parent/'admission.json')
        if m['admission_id']!=a['id']:raise ValueError('fast physical owner differs')
        for command in m['commands']:
            entry=self.entries[command['budget_reservation_id']]
            if (entry['command']!=command['command'] or entry['status']!=('failed' if command['exit_code'] else 'completed')
                    or entry.get('admission_sha256')!=owner or entry.get('task_id')!=m['task_id']
                    or entry.get('admission_id')!=a['id'] or entry.get('job_id')!=m['budget_job_id']
                    or command['cleanup']['remaining_live_pids'] or command['timed_out'] or command['memory_limit_exceeded']
                    or command['CPU_limit_exceeded'] or abs(entry['CPU_time_s']-cpu_seconds(command['gnu_time']))>1e-8):
                raise ValueError('fast diagnosis leaf unpaid or incorrectly settled')
            if command['exit_code'] and entry['stage'] is not None:raise ValueError('failed physical leaf cannot be inherited')
            saved=read(Path(command['log'].removesuffix('.log')+'.command.json'))
            if saved not in (command,{k:v for k,v in command.items() if k!='budget_reservation_id'}):raise ValueError('fast command sidecar differs')
            self.digest(command['log']);self.digest(command['gnu_time']);self.commands.add(entry['id'])
        for name,h in m.get('evidence_sha256',{}).items():
            if self.digest(directory/name)!=h:raise ValueError('fast raw artifact changed: '+name)
        for name,h in m.get('source_sha256',{}).items():
            if self.digest(directory/'source'/name)!=h:raise ValueError('fast backend producer changed')
        for name,h in m['files_sha256'].items():
            if self.digest(name)!=h:raise ValueError('fast effective physical file changed: '+name)
        for item in [*m['tools'].values(),*m['libraries']]:
            if self.digest(item['path'])!=item['sha256']:raise ValueError('fast actual tool/library changed')
        signature=tuple((x['path'],x['sha256']) for x in m['libraries'])
        if signature not in self.library_tables:
            libraries,cells=library_data([Path(x['path']) for x in m['libraries']],profile('asap7'))
            if libraries!=m['libraries']:raise ValueError('fast actual Liberty identities differ')
            self.library_tables[signature]=cells
        if read(directory/'liberty_cells.json')['cells']!=self.library_tables[signature]:raise ValueError('fast Liberty area/FF table differs')
        if m.get('checkpoint_reuse'):
            reuse=m['checkpoint_reuse'];previous=Path(reuse['directory'])
            if self.digest(previous/'manifest.json')!=reuse['manifest_sha256'] or reuse['new_Yosys_ABC_calls']:
                raise ValueError('inherited synthesis manifest changed or was repeated')
            for name in ('1_synth.odb','1_synth.sdc','1_2_yosys.v'):
                if self.digest(previous/'results'/SUFFIX/name)!=self.digest(directory/'results'/SUFFIX/name):raise ValueError('exact synthesis checkpoint differs')
            if self.digest(previous/'logs'/SUFFIX/'1_synth.json')!=self.digest(directory/'logs'/SUFFIX/'1_synth.json'):raise ValueError('paid synthesis native metadata differs')
            if any(self.entries[c['budget_reservation_id']]['stage']=='synth' for c in m['commands']):raise ValueError('inherited synthesis charged again')
            self.ancestry(previous,visiting)
        if m['status']=='completed':
            with redirect_stdout(io.StringIO()):verify_proof(directory/'logs'/SUFFIX/'structural_cec/proof.json',directory/'results'/SUFFIX/'4_before_rsz_lec.v',directory/'results'/SUFFIX/'4_after_rsz_lec.v')
        elif m['status']!='failed' or any(self.entries[c['budget_reservation_id']]['stage']=='grt' for c in m['commands']):
            raise ValueError('unexpected failed diagnosis ancestor')
        self.directories[directory]=m


def reparse(directory,task,pins,p):
    m=read(directory/'manifest.json');cells=read(directory/'liberty_cells.json')['cells']
    if m['status']!='completed' or m.get('data_role')!='not_training' or m.get('model_fit_allowed'):
        raise ValueError('complete not-training fast measurement required')
    if sha(directory/'input.sv')!=task['rtl_sha256'] or sha(directory/'fast-contract.json')!=task['contract_sha256']:
        raise ValueError('measurement source/contract differs')
    result=[]
    for stage,stem in (('synth','1_synth'),('grt','5_1_grt')):
        prefix=directory/'reports'/SUFFIX/('vulsim_'+stage)
        g=stage_metrics(prefix.parent,stage,cells,task['period_ps'],selected=p)
        observed=measurement.observations(prefix,task['spec'],task['period_ps'],g['raw_report_units']['time']['to_ps'],pins,p,task['geometry'])
        if observed!=read(directory/('fast-'+stage+'-observations.json')):raise ValueError('raw fast paths/owners/FFs differ')
        old=next(x for x in m['metrics'] if x['stage']==stage)
        if any(old.get(k)!=v for k,v in g.items()) or observed!=old['fast_measurement']:raise ValueError('fast metrics do not replay')
        rc=verify_wire_readback(Path(str(prefix)+'_layer_rc.tsv'),p)
        if rc is not None and old['wire_RC_readback']!=rc:raise ValueError('fast wire RC differs')
        actual=model_fast_sdc.verify_sdc((directory/'results'/SUFFIX/(stem+'.sdc')).read_text(),p,task['period_ps'],model_fast_sdc.rtl_ports((directory/'input.sv').read_text(),'ModelBundle'))
        if actual!=m['sdc_contracts'][stage]:raise ValueError('fast SDC does not replay')
        native=read(directory/'logs'/SUFFIX/(stem+'.json'))[('synth' if stage=='synth' else 'globalroute')+'__design__instance__area__stdcell']
        verify_orfs_area(g['cell_area_um2'],native)
        if not g['timing_coverage_complete']:raise ValueError('fast timing coverage incomplete')
        result.append(dict(stage=stage,period_ps=task['period_ps'],data_delay_ps=observed['data_delay_ps'],
            combinational_area_um2=observed['combinational_area_um2'],total_area_um2=g['cell_area_um2'],
            setup_slack_ps=g['setup_worst_slack_ps'],hold_slack_ps=g['hold_worst_slack_ps'],
            mapped_capture_banks=observed['mapped_capture_banks'],paths=len(observed['paths']),
            mapped_netlist_sha256=old.get('mapped_netlist_sha256'),source_role='not_training'))
    return result


def analyze(folder,out):
    a=collection.verify(folder);progress=read(folder/'progress.json')
    if progress['phase']!='diagnostic_collection_complete' or progress['active'] or progress['errors'] or set(progress['completed'])!={t['id'] for t in a['tasks']}:
        raise ValueError('complete finite diagnosis required before full raw replay')
    out.mkdir(parents=True,exist_ok=False);audit=Audit(read(Ledger().path)['entries']);p=profile('asap7');pins=read(folder/'liberty-pins.json');rows=[];paths={}
    # Include prior paid failures and support-only stops, not just the successful leaves.
    histories=[]
    for admission in sorted(folder.parent.glob('probes-v*/admission.json')):
        historical=read(admission)
        if historical['source_role']!='not_training':continue
        histories.append(dict(admission=str(admission),sha256=sha(admission)))
        for manifest in (admission.parent/'runs').glob('*/manifest.json'):audit.ancestry(manifest.parent)
    for task in a['tasks']:
        directory=Path(task['inherit_completed']['directory']) if task.get('inherit_completed') else folder/'runs'/task['id']
        audit.ancestry(directory);m=read(directory/'manifest.json')
        if liberty(m['libraries'],read(directory/'liberty_cells.json')['cells'])!=pins:raise ValueError('actual Liberty pin/function/area table differs')
        observed=reparse(directory,task,pins,p);paths[task['id']]=str(directory)
        rows.extend(dict(task_id=task['id'],source_group=task['source_group'],**row) for row in observed)
    response=[]
    for group in sorted({t['source_group'] for t in a['tasks']}):
        selected=[r for r in rows if r['source_group']==group and r['stage']=='grt'];slow=next(r for r in selected if r['period_ps']==1500);tight=next(r for r in selected if r['period_ps']==750)
        response.append(dict(source_group=group,SDC_ps=[1500,750],data_delay_ps=[slow['data_delay_ps'],tight['data_delay_ps']],
            combinational_area_um2=[slow['combinational_area_um2'],tight['combinational_area_um2']],
            data_delay_change_percent=100*(tight['data_delay_ps']/slow['data_delay_ps']-1),
            combinational_area_change_percent=100*(tight['combinational_area_um2']/slow['combinational_area_um2']-1),
            mapped_netlist_same=next(r for r in rows if r['source_group']==group and r['stage']=='synth' and r['period_ps']==1500)['mapped_netlist_sha256']==next(r for r in rows if r['source_group']==group and r['stage']=='synth' and r['period_ps']==750)['mapped_netlist_sha256']))
    result=dict(version=VERSION,status='passed',admission=str(folder/'admission.json'),admission_sha256=sha(folder/'admission.json'),
        measurement_points=len(a['tasks']),stage_rows=len(rows),raw_path_rows=sum(r['paths'] for r in rows),rows=rows,response=response,
        run_directories=paths,historical_admissions=histories,paid_leaves_checked=len(audit.commands),raw_files_hashed=len(audit.hashed),
        audit=dict(actual_Liberty_checked=True,exact_saved_CTS_CEC_verified=True,full_area_partition_checked=True,all_mapped_banks_checked=True,
            SDC_RC_checked=True,all_failed_support_retained=True),source_role='not_training',model_fitting_allowed=False,new_PPA_calls=0,full_D_ready=False)
    write(out/'audit.json',result)
    write(out/'raw-hashes.json',{str(p):h for p,h in sorted(audit.hashed.items(),key=lambda x:str(x[0]))})
    with (out/'response.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','response','run_directories','historical_admissions')},ensure_ascii=False),flush=True)


def stage_files(directory,stage):
    prefix=directory/'reports'/SUFFIX/('vulsim_'+stage)
    for p in prefix.parent.glob(prefix.name+'*'):
        if p.is_file():yield p


def seal(folder,audit_path,evidence):
    if evidence.exists():raise ValueError('preserve prior diagnosis evidence')
    a=collection.verify(folder);audit=read(audit_path)
    if audit['status']!='passed' or audit['admission_sha256']!=sha(folder/'admission.json'):raise ValueError('audited finite diagnosis required')
    files={};items=[]
    def add(name,path):files[name]=Path(path)
    for task in a['tasks']:
        directory=Path(audit['run_directories'][task['id']]);base='runs/'+task['id']+'/'
        for name in ('input.sv','fast-contract.json','liberty_cells.json','manifest.json'):add(base+name,directory/name)
        for stage,stem in (('synth','1_synth'),('grt','5_1_grt')):
            for p in stage_files(directory,stage):add(base+'reports/'+p.name,p)
            add(base+'results/'+stem+'.sdc',directory/'results'/SUFFIX/(stem+'.sdc'))
            add(base+'logs/'+stem+'.json',directory/'logs'/SUFFIX/(stem+'.json'))
        items.append(dict(task=task,base=base,manifest_file=base+'manifest.json'))
    for name in ('admission.json','software-proof.json','liberty-pins.json'):add(name,folder/name)
    add('audit.json',audit_path)
    # Pure numerical/raw-report replay sources; no installed EDA dependencies.
    for name in a['sources']:add('source/'+name,folder/'source'/name)
    for path in (ROOT/'experiments/arithmetic_dse').glob('*.py'):add('source/'+str(path.relative_to(ROOT)),path)
    for path in (ROOT/'experiments/arithmetic_dse/configs').rglob('*.json'):add('source/'+str(path.relative_to(ROOT)),path)
    add('source/experiments/arithmetic_dse/model_fast_probe_evidence.py',Path(__file__))
    pool={};index={}
    for name,path in sorted(files.items()):
        text=path.read_text();h=sha(path);pool.setdefault(h,text);index[name]=h
    raw=json.dumps(dict(index=index,pool=pool),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode();compressed=gzip.compress(raw,mtime=0)
    evidence.mkdir(parents=True);chunks=[]
    for i in range(0,len(compressed),512*1024):
        p=evidence/f'raw-{i//(512*1024):03d}.gzpart';p.write_bytes(compressed[i:i+512*1024]);chunks.append(p.name)
    write(evidence/'replay.json',dict(version=VERSION,chunks=chunks,profile=profile('asap7'),items=items,original_folder=str(folder),audit_sha256=sha(audit_path),
        full_actual_tool_Liberty_CEC_replay_requires_external=True))
    shutil.copy2(audit_path,evidence/'audit.json');shutil.copy2(audit_path.parent/'response.csv',evidence/'response.csv')
    (evidence/'README.md').write_text('''# 近速度极限采样：实际FF／标签与有限物理诊断

5类源×1500／750ps共10点，20个synth／grt阶段、52条数据／valid路径。全部源为not_training，未拟合或消费独立测试；两点响应不证明已达到饱和或连续时钟最优。D等速带和建库取点带分别按用户确认登记5%。

每阶段核对真实FF／独立capture银行、实际Liberty pin/function/area、原始Q-D／core／capture后缀、互斥面积归属、完整SDC／RC／覆盖及已存完整CTS CEC。前序名称绑定、make只读计划和单比特端口拼写停止保留，综合／完成grt的检查点明确继承，未重复综合或重采已完成物理点。

便携核验：`python3 -B -m experiments.arithmetic_dse.model_fast_probe_evidence verify --folder experiments/arithmetic/evidence/step7_fast_probe_v1`
便携包从已保存原始报告和冻结pin表重算路径、面积、FF、SDC／RC；不执行新EDA／SAT／拟合，不冒称包含ODB和全部CEC图。完整本机核验增加`--external`，从audit记录的build目录核对实际Liberty／工具、全部原始文件和完整已存CEC及计费祖先；文件不可获得时该级别失败。

大ODB／完整CEC工作产物仍在build/step7-fast-measurement-20261109各版本目录，其哈希及来源在audit／原始核验索引中。它们是本机工作存储，持久交付位置仍待落实。此包只授予采集方法和本有限诊断范围，不是已发布小算子模型、S／G或D资格。full_D_ready=false。
''')
    write(evidence/'manifest.json',dict(version=VERSION,files={p.name:sha(p) for p in evidence.iterdir() if p.is_file()}))
    print(json.dumps(dict(status='sealed',compressed_raw_bytes=len(compressed),files=len(files),bytes=sum(p.stat().st_size for p in evidence.iterdir()))),flush=True)


def unpack(folder,temp):
    manifest=read(folder/'manifest.json')
    if manifest['version']!=VERSION or any(sha(folder/name)!=h for name,h in manifest['files'].items()):raise ValueError('fast diagnosis evidence identity mismatch')
    spec=read(folder/'replay.json');raw=b''.join((folder/name).read_bytes() for name in spec['chunks']);data=json.loads(gzip.decompress(raw))
    for name,h in data['index'].items():
        if Path(name).is_absolute() or '..' in Path(name).parts:raise ValueError('unsafe diagnosis member')
        text=data['pool'][h]
        if hashlib.sha256(text.encode()).hexdigest()!=h:raise ValueError('diagnosis raw content differs')
        p=temp/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    return spec


def verify(folder,external=False):
    with tempfile.TemporaryDirectory(prefix='fast-raw-replay-') as td:
        temp=Path(td);spec=unpack(folder,temp);pins=read(temp/'liberty-pins.json');p=spec['profile'];count=0
        for item in spec['items']:
            base=temp/item['base'];task=item['task'];cells=read(base/'liberty_cells.json')['cells'];manifest=read(temp/item['manifest_file'])
            for stage,stem in (('synth','1_synth'),('grt','5_1_grt')):
                prefix=base/'reports'/('vulsim_'+stage);g=stage_metrics(prefix.parent,stage,cells,task['period_ps'],selected=p)
                old=next(x for x in manifest['metrics'] if x['stage']==stage)
                if any(k!='raw_reports_prefix' and old.get(k)!=v for k,v in g.items()):raise ValueError('portable fast stage metrics differ')
                observed=measurement.observations(prefix,task['spec'],task['period_ps'],g['raw_report_units']['time']['to_ps'],pins,p,task['geometry'])
                if observed!=old['fast_measurement']:raise ValueError('portable fast raw paths/owners/banks differ')
                rc=verify_wire_readback(Path(str(prefix)+'_layer_rc.tsv'),p)
                if rc is not None and rc!=old['wire_RC_readback']:raise ValueError('portable fast RC differs')
                actual=model_fast_sdc.verify_sdc((base/'results'/(stem+'.sdc')).read_text(),p,task['period_ps'],model_fast_sdc.rtl_ports((base/'input.sv').read_text(),'ModelBundle'))
                if actual!=manifest['sdc_contracts'][stage]:raise ValueError('portable fast SDC differs')
                native=read(base/'logs'/(stem+'.json'))[('synth' if stage=='synth' else 'globalroute')+'__design__instance__area__stdcell'];verify_orfs_area(g['cell_area_um2'],native);count+=1
        if external:
            original=Path(spec['original_folder']);a=collection.verify(original);audit=Audit(read(Ledger().path)['entries'])
            for row in read(folder/'audit.json')['historical_admissions']:
                if sha(row['admission'])!=row['sha256']:raise ValueError('external diagnosis admission changed')
                for m in (Path(row['admission']).parent/'runs').glob('*/manifest.json'):audit.ancestry(m.parent)
            for task in a['tasks']:
                directory=Path(task['inherit_completed']['directory']) if task.get('inherit_completed') else original/'runs'/task['id'];audit.ancestry(directory)
                if liberty(a['libraries'],read(directory/'liberty_cells.json')['cells'])!=pins:raise ValueError('external Liberty table differs')
                reparse(directory,task,pins,p)
    print(json.dumps(dict(status='passed',stages=count,portable_raw_replay=True,actual_tools_Liberty_full_CEC_external=external,new_PPA_calls=0,model_fit_allowed=False)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('analyze','seal','verify'));p.add_argument('--folder',type=Path,required=True);p.add_argument('--out',type=Path);p.add_argument('--audit',type=Path);p.add_argument('--external',action='store_true');a=p.parse_args()
    if a.action=='analyze':analyze(a.folder.resolve(),a.out.resolve())
    elif a.action=='seal':seal(a.folder.resolve(),a.audit.resolve(),a.out.resolve())
    else:verify(a.folder.resolve(),a.external)
