"""Read-only status, with no recursive scans or backend calls."""
import argparse
from collections import Counter
from datetime import datetime
import fcntl
import json
from pathlib import Path


def locked(path):
    if not path.exists():return False
    with path.open('r') as stream:
        try:fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return True
        return False


def main():
    root=Path(__file__).resolve().parents[2]
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--folder',type=Path,default=root/'build/step7-target-load-20261103/asap7-parallel-v1')
    args=ap.parse_args();folder=args.folder.resolve()
    def read(path):return json.loads(path.read_text())
    plan=read(folder/'plan.json');driver=locked(folder/'advance.lock')
    progress=read(folder/'advance-progress.json') if (folder/'advance-progress.json').exists() else {'phase':'not_started'}
    print(datetime.now().astimezone().isoformat(timespec='seconds'))
    print('驱动：'+('运行中' if driver else '未运行')+'；状态：'+progress['phase'])
    counts={name:Counter() for name in ('baseline','validation','conditional','test')}
    active=[]
    for t in plan['tasks']:
        mode=t['split'] if t['split']!='train' else ('baseline' if 'absolute-2250' in t['target_roles'] else 'conditional')
        d=Path(t['inherited_run']['directory']) if t.get('inherited_run') else folder/'runs'/t['id']
        mp=d/'manifest.json'
        try:
            m=read(mp) if mp.exists() else {};status=m.get('status','not_started' if not d.exists() else 'starting')
        except (OSError,json.JSONDecodeError):m={};status='updating'
        counts[mode][status]+=1
        if status in ('running','starting','updating'):active.append((t['id'],m.get('active_stage','preflight')))
    for mode,c in counts.items():print(f'{mode}: 完成 {c["completed"]}/{sum(c.values())}；'+str(dict(c)))
    ledger=read(root/'experiments/arithmetic/backend_usage.json')
    entries=[e for e in ledger['entries'] if e['status']=='reserved']
    for tid,stage in active:print('任务：',tid,'阶段：',stage)
    for e in entries:print('当前命令：',e.get('task_id','support'),e['stage'] or 'support',Path(e['output']).name)
    print('未结算命令：',len(entries),'；计划：最多 4 任务，每任务 4 线程')
    phase=progress['phase']
    if phase=='initial_collection_complete':print('首批 340 个任务采集完成。可以请助手继续提取、拟合与验证。')
    elif phase=='conditional_collection_complete':print('条件训练采集完成。可以请助手继续提取、拟合与验证；独立测试尚未启动。')
    elif phase=='test_collection_complete':
        evaluated=False
        for wave in sorted((folder/'waves').glob('test-*.json'),reverse=True):
            if wave.name.endswith('.outcome.json'):continue
            selected=read(wave).get('selection_freeze')
            if not selected:continue
            marker=Path(selected).parent/'independent-test-consumption.json'
            if marker.exists():
                consumption=read(marker)
                if consumption.get('status')=='completed':
                    result=read(Path(consumption['output'])/'independent-test.json')
                    print('独立测试已评价，quality_status='+result['quality_status']+'；测试已消费，请勿重复评价或用于调参。')
                    evaluated=True
                elif consumption.get('status') in ('started','failed_after_claim'):
                    print('一次性评价状态：'+consumption['status']+'；请由助手核对消费记录后处理。')
                    evaluated=True
            break
        if not evaluated:print('独立测试采集完成。可以请助手继续一次性评价、核验与发布判定。')
    elif phase in ('stopped_on_error','paused'):print('已停止，请把本输出交给助手。',progress.get('error',''))
    elif not driver:print('驱动没有持锁，不能视为正常完成；请联系助手检查。')
    else:print('仍在自动推进；OpenROAD 暂时不出现可能是在综合、快照或任务切换。')


if __name__=='__main__':main()
