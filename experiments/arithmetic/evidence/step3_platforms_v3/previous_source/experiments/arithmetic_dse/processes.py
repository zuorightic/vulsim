"""Linux process-tree accounting and cancellation across nested sessions."""
import os
from pathlib import Path
import signal
import subprocess
import threading
import time
import uuid


def _process_table():
    table = {}
    for stat in Path('/proc').glob('[0-9]*/stat'):
        try:
            fields = stat.read_text().rsplit(')', 1)[1].split()
            table[int(stat.parent.name)] = {
                'ppid':int(fields[1]), 'start':int(fields[19]), 'state':fields[0],
                'rss_KiB':int(fields[21])*os.sysconf('SC_PAGE_SIZE')//1024,
                'CPU_s':(int(fields[11])+int(fields[12]))/os.sysconf('SC_CLK_TCK'),
                'threads':int(fields[17])}
        except (OSError, ValueError, IndexError):
            continue
    return table


def _observe(root_pid, known, token):
    table = _process_table()
    if not known and root_pid in table:
        known[root_pid] = table[root_pid]['start']
    owners = {pid for pid, start in known.items() if pid in table and table[pid]['start'] == start}
    # A short-lived parent can exit before the next sample. An inherited token
    # also identifies its orphaned/setsid descendants after that race.
    for pid in table.keys()-owners:
        try:
            for variable in Path(f'/proc/{pid}/environ').read_bytes().split(b'\0'):
                if variable.startswith(b'VULSIM_COMMAND_ANCESTRY=') and token.encode() in variable.split(b'=',1)[1].split(b':'):
                    owners.add(pid)
                    known[pid] = table[pid]['start']
                    break
        except OSError:
            continue
    while True:
        children = {pid for pid, row in table.items() if row['ppid'] in owners and pid not in owners}
        if not children:
            break
        owners.update(children)
        known.update({pid:table[pid]['start'] for pid in children})
    # Keep identities after reparenting, and never signal a reused PID.
    return {pid:table[pid] for pid in owners if table[pid]['state'] != 'Z'}


def _signal_members(members, signum):
    sent = []
    for pid, row in members.items():
        try:
            fields = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
            if int(fields[19]) == row['start'] and fields[0] != 'Z':
                os.kill(pid, signum)
                sent.append(pid)
        except (OSError, ValueError, IndexError):
            continue
    return sent


def _terminate_tree(process, known, token, grace_s=2):
    members = _observe(process.pid, known, token)
    term_sent = set(_signal_members(members, signal.SIGTERM))
    deadline = time.monotonic()+grace_s
    while members and time.monotonic() < deadline:
        time.sleep(0.02)
        process.poll()  # Reap the immediate child, even if grandchildren linger.
        members = _observe(process.pid, known, token)
        new = {pid:row for pid, row in members.items() if pid not in term_sent}
        term_sent.update(_signal_members(new, signal.SIGTERM))
    kill_sent = set()
    deadline = time.monotonic()+2
    while members:
        kill_sent.update(_signal_members(members, signal.SIGKILL))
        process.poll()
        time.sleep(0.02)
        members = _observe(process.pid, known, token)
        if time.monotonic() >= deadline:
            break
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        members = _observe(process.pid, known, token)
    return {'term_sent':len(term_sent), 'kill_sent':len(kill_sent),
            'remaining_live_pids':sorted(members)}


def run_command(command, directory, stem, timeout_s, env, memory_limit_mib=8192, cpu_limit_s=None):
    """Account for and terminate descendants, including nested setsid groups."""
    # Import lazily to keep the process helper usable without backend resources.
    from .backend import write_json
    log = directory/f'{stem}.log'
    resource_log = directory/f'{stem}.resources.txt'
    wrapped = ['/usr/bin/time', '-v', '-o', str(resource_log), *map(str, command)]
    start = time.monotonic()
    peak_rss, peak_threads = 0, 0
    timed_out, memory_limit_exceeded = False, False
    cancelled_signal = None
    unexpected_live_descendants = False
    cpu_by_identity = {}
    cpu_limit_exceeded = False
    cleanup = {'term_sent':0, 'kill_sent':0, 'remaining_live_pids':[]}
    previous_handlers = {}
    def cancel(signum, frame):
        nonlocal cancelled_signal
        cancelled_signal = signum
    if threading.current_thread() is threading.main_thread():
        for signum in (signal.SIGTERM, signal.SIGINT):
            previous_handlers[signum] = signal.signal(signum, cancel)
    known = {}
    token = uuid.uuid4().hex
    child_env = env.copy()
    child_env['VULSIM_COMMAND_ANCESTRY'] = ':'.join(filter(None,[env.get('VULSIM_COMMAND_ANCESTRY'),token]))
    process = None
    try:
        with log.open('w') as output:
            process = subprocess.Popen(wrapped, stdout=output, stderr=subprocess.STDOUT,
                                       env=child_env, start_new_session=True)
            while True:
                members = _observe(process.pid, known, token)
                rss = sum(row['rss_KiB'] for row in members.values())
                peak_rss = max(peak_rss, rss)
                peak_threads = max(peak_threads, sum(row['threads'] for row in members.values()))
                for pid, row in members.items():
                    identity = (pid, row['start'])
                    cpu_by_identity[identity] = max(cpu_by_identity.get(identity, 0), row['CPU_s'])
                cpu_limit_exceeded = cpu_limit_s is not None and sum(cpu_by_identity.values()) >= cpu_limit_s
                remaining = timeout_s-(time.monotonic()-start)
                timed_out = remaining <= 0
                memory_limit_exceeded = rss > memory_limit_mib*1024
                if timed_out or memory_limit_exceeded or cancelled_signal or cpu_limit_exceeded:
                    cleanup = _terminate_tree(process, known, token)
                    break
                if process.poll() is not None:
                    # A group leader's exit does not establish descendant exit.
                    members = _observe(process.pid, known, token)
                    if members:
                        unexpected_live_descendants = True
                        cleanup = _terminate_tree(process, known, token)
                    break
                try:
                    process.wait(timeout=min(0.5, remaining))
                except subprocess.TimeoutExpired:
                    pass
    except BaseException:
        if process is not None:
            _terminate_tree(process, known, token)
        raise
    finally:
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)
    failed = timed_out or memory_limit_exceeded or cpu_limit_exceeded or cancelled_signal or unexpected_live_descendants or cleanup['remaining_live_pids']
    record = {'command':list(map(str, command)),
              'exit_code':process.returncode if not failed or process.returncode else 125,
              'process_exit_code':process.returncode, 'timed_out':timed_out,
              'CPU_limit_s':cpu_limit_s, 'CPU_limit_exceeded':cpu_limit_exceeded,
              'sampled_process_tree_CPU_s':sum(cpu_by_identity.values()),
              'cancelled_signal':cancelled_signal, 'walltime_s':time.monotonic()-start,
              'unexpected_live_descendants':unexpected_live_descendants,
              'memory_limit_exceeded':memory_limit_exceeded, 'memory_limit_MiB':memory_limit_mib,
              'sampled_process_tree_peak_rss_KiB':peak_rss,
              'sampled_process_tree_peak_threads':peak_threads,
              'resource_scope':'descendants_across_sessions_with_PID_starttime_and_inherited_token',
              'resource_sampling_interval_s':0.5, 'cleanup':cleanup,
              'log':str(log), 'gnu_time':str(resource_log)}
    write_json(directory/f'{stem}.command.json', record)
    return record
