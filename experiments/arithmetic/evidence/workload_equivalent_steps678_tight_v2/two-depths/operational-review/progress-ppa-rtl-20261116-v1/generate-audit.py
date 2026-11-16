"""Read-only snapshot of the live matrix, selected RTL and backend timings.

Run from the repository root. Writes only this evidence directory; does not
publish controller state, settle jobs, invoke EDA or change frozen inputs.
"""
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
import csv
import gzip
import hashlib
import json
from pathlib import Path
import re
import statistics
import sys

ROOT = Path(__file__).resolve().parents[7]
sys.path.insert(0, str(ROOT))
from experiments.arithmetic_dse import workload_latency_matrix as matrix
from experiments.arithmetic_dse.workload_two_depths_run import collect, live_json
from experiments.arithmetic_dse.workload_two_depths_monitor import review

OUT = Path(__file__).resolve().parent
LIVE = Path('/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1')
METHODS = ('A', 'B', 'C', 'D')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def save(name, value):
    (OUT/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def md(name, lines):
    (OUT/name).write_text('\n'.join(lines)+'\n')


def csvout(name, rows, fields):
    with (OUT/name).open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)


def link(path, label=None, line=None):
    target = str(path)+(f':{line}' if line else '')
    return f'[{label or Path(path).name}]({target})'


def quantile(values, q):
    a = sorted(values)
    if not a:
        return None
    at = (len(a)-1)*q
    i = int(at)
    return a[i]+(a[min(i+1,len(a)-1)]-a[i])*(at-i)


def stats(values):
    return dict(n=len(values), total_s=sum(values), median_s=statistics.median(values),
                p90_s=quantile(values,.9), max_s=max(values)) if values else dict(n=0)


def cell(row):
    if row['status'] == 'measured_grt':
        return f'{row["Tmin_ps"]:.1f} / {row["area_um2"]:.1f}'+(' ✓' if row['setup_met'] else '')
    return dict(failed='失败', running='运行中', not_started='排队',
                not_registered='软件待就绪', awaiting_A_reference='待A参考').get(row['status'],row['status'])


def table_header():
    return ['| 案例 | 比较L | 目标T ps | A | B | C | D |',
            '| --- | ---: | ---: | --- | --- | --- | --- |']


def raw_tail(path, size=65536):
    with path.open('rb') as f:
        f.seek(max(0,path.stat().st_size-size))
        return f.read().decode(errors='replace')


def elapsed(text):
    matches=re.findall(r'Elapsed time: ([\d:.]+)\[h:\]min:sec\.',text)
    if not matches:
        return None
    parts=[float(x) for x in matches[-1].split(':')]
    return sum(v*60**i for i,v in enumerate(reversed(parts)))


def loginfo(path):
    text=path.read_text(errors='replace')
    timing=[]
    for i,line in enumerate(text.splitlines(),1):
        found=re.search(r'Took (\d+(?:\.\d+)?) seconds: (.*)',line)
        runtime=re.search(r'\[INFO RSZ-(0505|0506)\] Runtime: ([\d.]+)s',line)
        if found:
            timing.append(dict(line=i,seconds=float(found[1]),command=found[2]))
        if runtime:
            timing.append(dict(line=i,seconds=float(runtime[2]),command=(
                'setup_repair_internal' if runtime[1]=='0505' else 'hold_repair_internal')))
    return dict(log=str(path),elapsed_s=elapsed(text),last_lines=text.splitlines()[-10:],
                internal_timings=timing,pin_access_groups=re.findall(r'Complete (\d+) groups',text)[-1:])


def backend_report(rows, monitor, stamp):
    aliases=defaultdict(list)
    for r in rows:
        aliases[r['measurement']['run']].append(f'{r["case"]}/L{r["comparison_L"]}/T{r["T_ps"]}/{r["method"]}')
    for p in LIVE.glob('backend/montgomery-A-reference-*/runs/*/manifest.json'):
        aliases[str(p.parent)].append('Montgomery A参考；非主矩阵结果')
    reservations={x['task']:x for x in monitor['active_reservations']}
    runs=[]
    for name,names in sorted(aliases.items()):
        run=Path(name)
        manifest=live_json(run/'manifest.json')
        if not manifest:
            continue
        commands=[]
        for c in manifest.get('commands',[]):
            commands.append(dict(stage=Path(c['log']).stem,walltime_s=c['walltime_s'],
                CPU_s=c.get('sampled_process_tree_CPU_s'),timed_out=c.get('timed_out'),
                memory_limit_exceeded=c.get('memory_limit_exceeded'),
                rss_KiB=c.get('sampled_process_tree_peak_rss_KiB'),log=c['log']))
        sub=[]
        logs=run/'logs/asap7/arithmetic_probe/base'
        for f in sorted(logs.glob('[2345]_*.log')):
            if f.stem.endswith('lec_check'):
                continue
            if f.stem.endswith('.tmp') and f.with_name(f.stem[:-4]+'.log').exists():
                continue
            stage=f.stem.removesuffix('.tmp')
            item=dict(stage=stage,log=str(f),elapsed_s=elapsed(raw_tail(f)))
            if stage in ('4_1_cts','5_1_grt'):
                item.update(loginfo(f))
            sub.append(item)
        metrics={}
        for f in (logs/'4_1_cts.json',logs/'5_1_grt.json'):
            if f.exists():
                metrics[f.stem]={k:v for k,v in read(f).items() if any(
                    x in k for x in ('count__setup_buffer','count__hold_buffer','timing__setup__ws',
                                    'timing__hold__ws','instance__count__stdcell'))}
        grt=next((c['walltime_s'] for c in commands if c['stage']=='grt'),None)
        reservation=reservations.get(run.name)
        if grt is None and reservation and reservation['stage']=='grt':
            grt=reservation['elapsed_s']
        done=sum(s['elapsed_s'] for s in sub if s['elapsed_s'] is not None)
        unfinished=[s for s in sub if s['elapsed_s'] is None]
        # Only infer a remainder when one physical substage is unfinished.
        residual=(max(0,grt-done) if grt is not None and len(unfinished)==1 else None)
        runs.append(dict(run=name,aliases=names,status=manifest['status'],
            failure_reason=manifest.get('failure_reason'),threads=manifest['threads_per_tool'],
            manifest_sha256=sha(run/'manifest.json'),commands=commands,substages=sub,metrics=metrics,
            active_reservation=reservation,unfinished_substage_remainder_s=residual,
            remainder_scope='Approximate grt command remainder including make/LEC/other overhead; lower bound if running'))
    bycommand=defaultdict(list)
    bysub=defaultdict(list)
    bythread=defaultdict(lambda:defaultdict(list))
    for r in runs:
        for c in r['commands']:
            bycommand[c['stage']].append(c['walltime_s'])
            bythread[r['threads']][c['stage']].append(c['walltime_s'])
        for s in r['substages']:
            if s['elapsed_s'] is not None:
                bysub[s['stage']].append(s['elapsed_s'])
    doc=dict(snapshot=stamp,scope='Unique physical runs referenced by current 37-group matrix, plus current Montgomery reference',
        running_durations_are_lower_bounds=True,command_stats={k:stats(v) for k,v in bycommand.items()},
        substage_completed_stats={k:stats(v) for k,v in bysub.items()},
        command_stats_by_threads={k:{a:stats(b) for a,b in v.items()} for k,v in bythread.items()},runs=runs)
    save('backend-timing.json',doc)
    lines=['# 后端耗时：命令与ORFS子阶段', '',f'快照：{stamp}。', '',
        '按当前矩阵引用的唯一物理目录去重，另列Montgomery当前A参考；不将共享ABCD记录重复计时。',
        '表中累计时长是各任务耗时之和，包含并发重叠，不能当作机器经过的墙钟时间。命令统计使用已返回的命令（含超时）；运行命令只在逐任务表列下界。',
        '`grt`命令包含floorplan、placement、CTS和global-route整个流程；下表ORFS子阶段用于继续定位。未结束的长阶段没有Elapsed，不进入“已结束子阶段”分位数，所以该表存在幸存偏差。', '',
        '| 命令 | 已返回次数 | 累计任务小时 | 中位秒 | P90秒 | 最大秒 |',
        '| --- | ---: | ---: | ---: | ---: | ---: |']
    for k,v in sorted(doc['command_stats'].items(),key=lambda x:-x[1]['total_s']):
        lines.append(f'| {k} | {v["n"]} | {v["total_s"]/3600:.2f} | {v["median_s"]:.1f} | {v["p90_s"]:.1f} | {v["max_s"]:.1f} |')
    lines+=['','| 已结束ORFS子阶段 | 次数 | 累计任务小时 | 中位秒 | P90秒 | 最大秒 |',
            '| --- | ---: | ---: | ---: | ---: | ---: |']
    for k,v in sorted(doc['substage_completed_stats'].items(),key=lambda x:-x[1]['total_s']):
        lines.append(f'| {k} | {v["n"]} | {v["total_s"]/3600:.2f} | {v["median_s"]:.1f} | {v["p90_s"]:.1f} | {v["max_s"]:.1f} |')
    lines+=['','| 任务（去重） | 线程 | 状态 | synth秒 | grt秒 | 当前／终止阶段 | 未完成阶段余时估计秒 |',
            '| --- | ---: | --- | ---: | ---: | --- | ---: |']
    for r in sorted(runs,key=lambda x:x['run']):
        c={x['stage']:x['walltime_s'] for x in r['commands']}
        g=c.get('grt',r['active_reservation']['elapsed_s'] if r['active_reservation'] and r['active_reservation']['stage']=='grt' else None)
        last=r['substages'][-1]['stage'] if r['substages'] else '尚未进入物理阶段'
        remain=r['unfinished_substage_remainder_s']
        lines.append('| '+' | '.join([link(r['run'],Path(r['run']).name),str(r['threads']),r['status'],
            f'{c["synth"]:.1f}' if 'synth' in c else '—',f'{g:.1f}'+('（运行下界）' if 'grt' not in c else '') if g is not None else '—',
            last,f'{remain:.1f}' if remain is not None else '—'])+' |')
    lines+=['', '逐任务原始日志、命令与修复内部计时见[JSON](backend-timing.json)。`repair_timing`外层包含setup/hold内部修复，不能将三者再次相加。',
        '约束过紧可触发漫长setup repair；hold repair受短路径、使能／保持逻辑和状态规模影响，放宽setup周期不能保证消除。引脚访问检查发生在5_1_grt真正路由之前，大网表规模会独立拖慢。',
        '运行配置为每任务NUM_CORES=2；进程树线程数包含辅助线程、多个进程或工具内部线程，不能仅凭瞬时线程数把任务称为全部2核已吃满。实际CPU/墙钟及分线程汇总见JSON。',
        '诊断不修改当前队列。后继可先检查setup修复、hold缓冲、LEC和pin_access分别占比；优化拆分／寄存器状态规模，再独立登记容量／时限／工具后继。改变修复策略或跳过检查会改变评价口径，不能悄悄应用到本轮。']
    md('backend-timing.md',lines)
    return doc


def rtl_detail(m):
    rtl=Path(m['rtl']);folder=rtl.parent
    graph=read(folder/'graph.json'); owners=read(folder/'owners.json');state=read(folder/'state.json')
    assert sha(rtl)==m['rtl_sha256']
    lines=rtl.read_text().splitlines();decl=defaultdict(list);writes=defaultdict(list)
    top_line=None; module_line=None; in_core=False
    for number,line in enumerate(lines,1):
        if re.match(r'module WorkloadCore\(',line):
            in_core=True
        if re.match(r'module Workload\(',line):
            in_core=False;top_line=number
        for found in re.finditer(r'\b(?:logic|reg|wire)\s+(?:signed\s+)?(?:\[[^\]]*\]\s*)?(\w+)',line):
            decl[found[1]].append(number)
        for found in re.finditer(r'\b(\w+)\s*(?:\[[^\]]*\])?\s*<=',line):
            writes[found[1]].append(number)
    nodes={n['id']:n for n in graph['nodes']};place=m['placement'];L=m['L']
    stages=[dict(stage=i,operators=[],G_regions=[],functional_logic=[],capture_slots=[]) for i in range(L)]
    for owner in owners['operators']:
        p=owner['query']['local_context']['producer']
        stages[owner['stage']]['operators'].append(dict(node=owner['node'],**p))
    for owner in owners['G_regions']:
        stages[owner['stage']]['G_regions'].append({k:owner[k] for k in ('root','members','terms','output_bits')})
    for owner in owners['functional_logic']:
        node = owner if isinstance(owner,int) else owner['node']
        stages[place[node]]['functional_logic'].append(nodes[node])
    slots=[];errors=[]
    for slot in state['slots']:
        n=nodes[slot['origin']]; item=dict(slot,
            source_operation=n['operation'],source_width=n['width'],source_operands=n['operands'],
            source_placement=place[slot['origin']],declaration_lines=decl[slot['name']],
            assignment_lines=writes[slot['name']])
        if not item['assignment_lines']:
            errors.append(f'no register write for {slot["name"]}')
        if slot['valid']:
            item['role']='valid pipeline'
        elif slot['external_capture']:
            item['role']='output capture'
        elif n['operation']=='input':
            item['role']='operand alignment'
        elif item['source_placement']<slot['stage']-1:
            item['role']='saved result forwarded through another stage'
        else:
            item['role']='capture of current-stage result'
        slots.append(item);stages[slot['stage']-1]['capture_slots'].append(item)
    assert not errors,errors
    assert sum(s['variable_bits'] for s in slots if not s['valid'])==state['features']['data_bits']
    for s in stages:
        s['operator_summary']=dict(Counter(f'{o["operation"]}({o["lhs_width"]},{o["rhs_width"]})->{o["result_width"]}' for o in s['operators']))
        s['G_summary']=dict(Counter(f'{len(g["terms"])}项/{g["output_bits"]}bit' for g in s['G_regions']))
        s['capture_data_bits']=sum(q['variable_bits'] for q in s['capture_slots'] if not q['valid'])
        s['capture_valid_bits']=sum(q['variable_bits'] for q in s['capture_slots'] if q['valid'])
    return dict(rtl=str(rtl),rtl_sha256=m['rtl_sha256'],L=L,grammar=m['grammar'],
        graph_sha256=sha(folder/'graph.json'),state_sha256=sha(folder/'state.json'),owners_sha256=sha(folder/'owners.json'),
        features=state['features'],input_variable_bits=state['input_variable_bits'],
        service_wrapper_line=top_line,placement=place,graph=graph,stages=stages,register_slots=slots,verification_errors=errors)


def rtl_report(main, selected, stamp):
    byhash={};aliases=defaultdict(list);inventory=[]
    for r in main:
        key=(r['case'],r['comparison_L'],r['T_ps'],r['method']);m=selected.get(key)
        if not m:
            continue
        h=m['rtl_sha256'];aliases[h].append(dict(case=r['case'],comparison_L=r['comparison_L'],
            T_ps=r['T_ps'],method=r['method'],status=r['status']))
        inventory.append(dict(case=r['case'],comparison_L=r['comparison_L'],T_ps=r['T_ps'],
            method=r['method'],status=r['status'],actual_L=m['L'],mul_block=m['grammar'][0],
            add_limb=m['grammar'][1],rtl=m['rtl'],rtl_sha256=h))
    needed={h for h,a in aliases.items() if any(x['status']!='measured_grt' for x in a)}
    methods_byhash={m['rtl_sha256']:m for m in selected.values()}
    for h in sorted(needed):
        byhash[h]=rtl_detail(methods_byhash[h]);byhash[h]['aliases']=aliases[h]
    with gzip.open(OUT/'unmeasured-rtl-detail.json.gz','wt') as f:
        json.dump(dict(snapshot=stamp,implementations=byhash),f,ensure_ascii=False)
    regs=[]
    for h,d in byhash.items():
        for slot in d['register_slots']:
            regs.append(dict(slot,rtl_sha256=h,rtl=d['rtl'],
                assignment_lines=','.join(map(str,slot['assignment_lines'])),
                declaration_lines=','.join(map(str,slot['declaration_lines'])),
                variable_mask_hex=json.dumps(slot['variable_mask_hex'])))
    with gzip.open(OUT/'unmeasured-registers.csv.gz','wt',newline='') as f:
        fields=['rtl_sha256','rtl','name','stage','enable_stage','role','origin','source_operation','source_width',
            'source_placement','declared_width','variable_bits','variable_mask_hex','valid','external_capture',
            'declaration_lines','assignment_lines']
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(regs)
    csvout('rtl-inventory.csv',inventory,list(inventory[0]))
    lines=['# 未完成后端测量项：ABCD的实际RTL拆分与寄存器', '',f'快照：{stamp}。', '',
        '只解释已冻结选中RTL；失败、运行中和未启动都属于尚无合格完整实测。尚未冻结的项目单列，不用中间候选代替最终RTL。',
        'A实际L=1，保留原数学源中的算法展开和原子操作；B不切原子算术，只在它们之间放寄存器；C用静态表选结构／位置；D用本体预算→等效训练T→冻结模型选结构／位置。C/D都可以选不进一步拆分。',
        '块宽b表示将现有乘法展开为b位小乘（末块可更窄）、固定移位和归约树；limb w表示按位段生成add/sub/ADC及进位依赖，高位操作数、carry和部分结果按周期对齐。b=0/w=0是没有继续切对应算术；Karatsuba和NTT源中的算法展开仍存在。',
        '下表逻辑级采用0起编号。每级后capture s=k+1；s=L是外部输出capture，已经计入L。完整图和放置表确定每个节点的所在级；跨级值会被保存，必要时逐级传递。数据位数采用variable_bits，不把已知零位当作触发器位。',
        '服务外壳还含输入保存寄存器l_*及liv，额外服务输入偏移为1周期；它与内部流水寄存器及最终y/ov capture在RTL中分别定位。enable按前级valid、异步／同步reset和保持行为以实际RTL为准。', '',
        '| 案例 | 比较L/T ps | 方法 | 后端状态 | 实际L | 乘法块/加法limb | 冻结RTL |',
        '| --- | --- | --- | --- | ---: | --- | --- |']
    for r in main:
        if r['status']=='measured_grt':
            continue
        key=(r['case'],r['comparison_L'],r['T_ps'],r['method']);m=selected.get(key)
        lines.append('| '+' | '.join([r['case'],f'{r["comparison_L"]}/{r["T_ps"] or "待定"}',r['method'],r['status'],
            str(m['L']) if m else '—','/'.join(map(str,m['grammar'])) if m else '待冻结',
            f'[实现 {m["rtl_sha256"][:12]}](#rtl-{m["rtl_sha256"][:12]})' if m else '尚无最终RTL'])+' |')
    for h,d in byhash.items():
        lines+=['',f'<a id="rtl-{h[:12]}"></a>', '',f'## 实现 {h[:12]}：L{d["L"]}，块/limb={d["grammar"]}', '',
            '对应记录：'+'；'.join(f'{a["case"]} L{a["comparison_L"]} T{a["T_ps"]} {a["method"]}（{a["status"]}）' for a in aliases[h])+'。', '',
            f'实际源码：{link(d["rtl"],"workload.sv")}；输入服务外壳：{link(d["rtl"],"Workload",d["service_wrapper_line"])}。', '',
            '| 逻辑级 | 独立算术所有者（输入位宽→结果位宽×个数） | 融合G（项数/输出位宽×个数） | capture数据位/valid位 | 具体寄存器示例 |',
            '| ---: | --- | --- | --- | --- |']
        for s in d['stages']:
            examples=[]
            for slot in sorted(s['capture_slots'],key=lambda x:(x['valid'],-x['variable_bits'],x['name']))[:3]:
                examples.append(link(d['rtl'],f'{slot["name"]}←#{slot["origin"]} {slot["source_operation"]}（{slot["variable_bits"]}位）',slot['assignment_lines'][-1]))
            lines.append('| '+' | '.join([str(s['stage']),'; '.join(f'{k} ×{v}' for k,v in s['operator_summary'].items()) or '无独立正价算术',
                '; '.join(f'{k} ×{v}' for k,v in s['G_summary'].items()) or '—',
                f'{s["capture_data_bits"]}/{s["capture_valid_bits"]}','; '.join(examples) or '无'])+' |')
        if any(s['functional_logic'] for s in d['stages']):
            lines+=['','其他功能逻辑另列在详细JSON中，不因算术表为空而忽略。']
        lines+=['',f'全部{len(d["register_slots"])}个寄存器信号、源节点／位掩码、保存链、声明与赋值行号见压缩JSON/CSV。G成员由融合模块实现，不能把raw graph中的每个Add再次当成独立模块。']
    lines+=['','[完整方法清单](rtl-inventory.csv)；[逐节点图／位置／所有者／寄存器JSON](unmeasured-rtl-detail.json.gz)；[全部寄存器CSV](unmeasured-registers.csv.gz)。',
        '未冻结项目只具备A/B/C/D的一般合同，不能预告最终块宽、具体切点或寄存器表。Montgomery两档仍被有效A参考阻塞；NTT8×64 L8的软件状态见快照，后续就绪不改写本报告时间点。']
    md('unmeasured-rtl.md',lines)
    return dict(frozen_method_records=len(inventory),unmeasured_unique_RTL=len(byhash),
                register_signals_verified=len(regs),register_write_errors=0)


def main():
    stamp=datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S +08:00')
    rows=collect(LIVE); monitor=review(LIVE)
    # The matrix rows are the snapshot authority; monitor can be a few seconds newer.
    existing={(r['case'],r['comparison_L'],r['T_ps'],r['method']):r for r in rows}
    selected={};plans=[]
    for p in sorted((LIVE/'plans').glob('*.json')):
        doc=read(p);selection=Path(doc['selection']);sel=read(selection)
        plans.append(dict(path=str(p),sha256=sha(p),selection=str(selection),selection_sha256=sha(selection)))
        for group in sel['records']:
            for name,m in group['methods'].items():
                selected[(doc['case'],doc['L'],group['target']['T_ps'],name)]=m
    target=read(LIVE/'target-matrix.json');allmain=[];groups=[]
    for t in target['rows']:
        for slot,T in enumerate(t.get('targets_ps',[None,None]),1):
            part=[]
            for method in METHODS:
                row=existing.get((t['case'],t['L'],T,method))
                if row is None:
                    row=dict(case=t['case'],comparison_L=t['L'],T_ps=T,method=method,
                        status='awaiting_A_reference' if T is None else 'not_registered',
                        target_slot=slot,L=1 if method=='A' else t['L'])
                allmain.append(row);part.append(row)
            groups.append(dict(case=t['case'],L=t['L'],T_ps=T,target_slot=slot,records=part))
    counts=dict(Counter(r['status'] for r in allmain));measured=[r for r in allmain if r['status']=='measured_grt']
    snap=dict(snapshot=stamp,scope='current two-depths 37-group 148-main-record matrix',
        counts=counts,main_measured=len(measured),unique_measured_runs=len({r['measurement']['run'] for r in measured}),
        setup_met_main=sum(r['setup_met'] for r in measured),hold_met_main=sum(r['hold_met'] for r in measured),
        unique_setup_met_runs=len({r['measurement']['run'] for r in measured if r['setup_met']}),
        plans=plans,rows=rows,all_main=allmain,monitor=monitor,
        model_refitted=False,new_EDA_calls=0,frozen_sources_changed=False)
    save('snapshot.json',snap)
    flat=[]
    for r in allmain:
        flat.append(dict(r,grammar='/'.join(map(str,r.get('grammar',[]))),
            run=r.get('measurement',{}).get('run'),inherited=r.get('measurement',{}).get('inherited'),
            threads=r.get('measured_threads',r.get('measurement',{}).get('threads')),
            predicted_Tmin_ps=r.get('prediction',{}).get('critical_required_ps'),
            predicted_area_um2=r.get('prediction',{}).get('total_area_um2')))
    fields=['case','comparison_L','T_ps','target_slot','method','L','grammar','status','failure_reason',
        'Tmin_ps','frequency_MHz','area_um2','setup_met','hold_WNS_ps','hold_met','threads','inherited',
        'rtl_sha256','predicted_Tmin_ps','predicted_area_um2','period_error','area_error','run']
    csvout('all-main-records.csv',flat,fields)
    csvout('measured-main-records.csv',[r for r in flat if r['status']=='measured_grt'],fields)
    lines=['# 当前两档流水级数：全部ABCD比较', '',f'快照：{stamp}。', '',
        f'主方法实测{len(measured)}/148，独立实测物理目录{snap["unique_measured_runs"]}个；setup通过{snap["setup_met_main"]}条，对应{snap["unique_setup_met_runs"]}个独立物理任务。状态：`{counts}`。',
        '单元格为“完整setup Tmin ps / 总面积µm²”；✓只表示setup通过，hold另看逐行表。A实际L=1，其他方法的L为比较L；II=1，额外输入服务偏移1周期。',
        '所有读数为grt阶段固定实现的RR/IR/RO完整setup最小周期，经±0.1ps阈值复核。未测与失败不填写预测值。相同RTL/T/流程可能共享一次物理测量；4线程继承结果与2线程新结果在CSV分别标识。', '',*table_header()]
    for g in groups:
        lines.append('| '+' | '.join([g['case'],str(g['L']),str(g['T_ps']) if g['T_ps'] else f'待A参考/档{g["target_slot"]}',*[cell(r) for r in g['records']]])+' |')
    lines+=['','## 已测逐项：完整数值、hold及来源', '',
        '| 案例 | 比较L/T | 方法 | 实际L | 块/limb | Tmin ps | MHz | 面积µm² | setup | hold WNS ps | 线程 | 原始测量 |',
        '| --- | --- | --- | ---: | --- | ---: | ---: | ---: | --- | ---: | ---: | --- |']
    for r in measured:
        lines.append('| '+' | '.join([r['case'],f'{r["comparison_L"]}/{r["T_ps"]}',r['method'],str(r['L']),'/'.join(map(str,r['grammar'])),
            f'{r["Tmin_ps"]:.6f}',f'{r["frequency_MHz"]:.3f}',f'{r["area_um2"]:.6f}',str(r['setup_met']),f'{r["hold_WNS_ps"]:.6f}',
            str(r['measured_threads']),link(Path(r['measurement']['run'])/'clock-readout/result.json','readout')])+' |')
    lines+=['','[全部148条CSV](all-main-records.csv)；[全部已测CSV](measured-main-records.csv)；[带来源的快照JSON](snapshot.json)。',
        '同池静态归因是第五种对照，不混入ABCD主表，原始rows保存在快照JSON。', '',
        '历史版本保持独立：[v10停止队列完整比较](../../../..//../../workload_diagnostic_stopped_v1/comparison.md)、[原紧目标矩阵](../../../README.md)、[Dot16 L4/L5版本](../../../../dot16-L45/README.md)。本表未把旧周期、旧模型的实测混成当前148条。']
    # Use explicit repository-relative historical links, independent of depth counting.
    lines[-1]='历史版本保持独立：'+link(ROOT/'experiments/arithmetic/evidence/workload_diagnostic_stopped_v1/comparison.md','v10停止队列完整比较')+'；'+link(ROOT/'experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/README.md','原紧目标矩阵')+'；'+link(ROOT/'experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/dot16-L45/README.md','Dot16 L4/L5版本')+'。未混用旧周期、旧模型。'
    md('abcd-comparison.md',lines)
    timing=backend_report(rows,monitor,stamp)
    rtl=rtl_report(allmain,selected,stamp)
    verify=dict(snapshot=stamp,main_records=len(allmain),groups=len(groups),registered_main=len(existing)-sum(k[3] not in METHODS for k in existing),
        counts=counts,measured_records=len(measured),unique_measured_runs=snap['unique_measured_runs'],**rtl,
        backend_unique_run_directories=len(timing['runs']),new_EDA_calls=0,new_fit_calls=0,
        script_sha256=sha(__file__))
    assert len(allmain)==148 and len(groups)==37
    save('verification.json',verify)
    md('README.md',['# 进度、ABCD、后端耗时与未测RTL审计', '',f'快照：{stamp}。', '',
        '[全部ABCD比较与已测逐项](abcd-comparison.md)；[后端命令／子阶段耗时](backend-timing.md)；[未测RTL的拆分和寄存器](unmeasured-rtl.md)。',
        '当前队列只读，报告不改模型、选择、周期、RTL、准入或后端配置；未发射EDA或拟合。',
        '[快照JSON](snapshot.json)、[验证收据](verification.json)、[生成脚本](generate-audit.py)。',
        '脚本可从仓库根用python3执行；再次执行会以新的时间点覆盖本目录报告，须另存旧目录才能比较快照。'])
    print(json.dumps(verify,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
