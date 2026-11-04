import json
import pathlib
import re
import subprocess
import time
import traceback

ROOT = pathlib.Path('/mnt/share/z00943141/qwen3_nightly_20261103_124914290773')
LATEST = 'z00943141_qwen3_nightly_test'
CI = 'z00943141_qwen3_nightly_ci_pinned'
LABEL = '124914290773'
FOLDERS = ['ci_pinned03', 'ci_pinned04']
state = {'started_at': time.time(), 'folders': FOLDERS, 'phase': 'preflight', 'completed': []}

def run(args, timeout=120, check=True):
    p = subprocess.run(args, text=True, capture_output=True, timeout=timeout)
    if check and p.returncode:
        raise RuntimeError(str(args) + '\n' + p.stdout + '\n' + p.stderr)
    return p

def save():
    state['updated_at'] = time.time()
    (ROOT / 'repeat_state.json').write_text(json.dumps(state, indent=2))
    print(json.dumps(state), flush=True)

def inspect(name):
    info = json.loads(run(['docker', 'inspect', name]).stdout)[0]
    if info['Config']['Labels'].get('codex.qwen3.run') != LABEL:
        raise RuntimeError('Refusing unrelated container ' + name)
    return info

def ensure_idle():
    output = run(['npu-smi', 'info']).stdout
    idle = {int(i) for i in re.findall(r'No running processes found in NPU\s+(\d+)', output)}
    if not {0, 1, 2, 3}.issubset(idle):
        raise RuntimeError('NPU0-3 are busy; preserve workloads')
    return output

def host_snapshot(label):
    data = {'at': time.time(), 'commands': {}, 'cpu_frequency': {}}
    commands = {
        'uname': ['uname', '-a'], 'lscpu': ['lscpu'],
        'numa': ['numactl', '--hardware'], 'npu_smi': ['npu-smi', 'info'],
        'npu_topology': ['npu-smi', 'info', '-t', 'topo'],
        'npu_board': ['npu-smi', 'info', '-t', 'board', '-i', '0', '-c', '0'],
        'npu_frequency': ['npu-smi', 'info', '-t', 'freq', '-i', '0', '-c', '0'],
        'memory': ['free', '-b'], 'docker_version': ['docker', 'version', '--format', '{{json .}}'],
        'nfs': ['findmnt', '-T', str(ROOT)],
    }
    for name, args in commands.items():
        p = run(args, check=False)
        data['commands'][name] = {'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    for policy in pathlib.Path('/sys/devices/system/cpu/cpufreq').glob('policy*'):
        data['cpu_frequency'][policy.name] = {}
        for name in ['affected_cpus', 'scaling_governor', 'scaling_cur_freq', 'scaling_min_freq',
                     'scaling_max_freq', 'cpuinfo_max_freq', 'cpuinfo_min_freq']:
            path = policy / name
            if path.exists():
                data['cpu_frequency'][policy.name][name] = path.read_text().strip()
    (ROOT / (label + '_host_snapshot.json')).write_text(json.dumps(data, indent=2))

save()
try:
    before = {name:inspect(name) for name in [LATEST, CI]}
    state['initial_states'] = {name:info['State']['Status'] for name,info in before.items()}
    for folder in FOLDERS:
        if (ROOT / 'outputs' / folder).exists():
            raise RuntimeError('Refusing to overwrite existing result ' + folder)
    ensure_idle()
    host_snapshot('repeats_before')
    if before[LATEST]['State']['Running']:
        top = run(['docker', 'top', LATEST, '-eo', 'pid,comm']).stdout.splitlines()[1:]
        if any(line.split()[-1] not in ['sleep', 'bash'] for line in top if line.split()):
            raise RuntimeError('User-requested container has additional processes; preserve them')
        run(['docker', 'stop', '--timeout', '20', LATEST])
    if not before[CI]['State']['Running']:
        run(['docker', 'start', CI])
    if inspect(CI)['Image'] != 'sha256:51acbdd308d677c4add19eee604174fbc29eff784d46675968e82c8e1299b9df':
        raise RuntimeError('Pinned CI image changed')
    for folder in FOLDERS:
        ensure_idle()
        state.update({'phase':'measurement', 'current_folder':folder, 'current_started_at':time.time()})
        save()
        command = ['docker','exec',CI,'bash','-elc',
                   'python3 -u /setup/inside_runner.py --output /results/' + folder]
        with (ROOT / (folder + '_controller.log')).open('w') as log:
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
            state['pid'] = process.pid
            save()
            rc = process.wait(timeout=7500)
        output = ROOT / 'outputs' / folder
        result = json.loads((output / 'result.json').read_text())
        if not result.get('measurement_valid'):
            raise RuntimeError('Invalid measurement: ' + folder + ' ' + str(result.get('error')))
        copied = run(['docker','cp',CI + ':/vllm-workspace/vllm-ascend/output_performance.txt',
                      str(output / 'aisbench_formal_stdout.txt')], check=False)
        state['completed'].append({'folder':folder,'returncode':rc,'metrics':result['formal_metrics'],
                                   'raw_copy_returncode':copied.returncode})
        state['phase'] = 'between_measurements'
        save()
        ensure_idle()
        host_snapshot(folder + '_after')
    state['phase'] = 'restoring_container'
    save()
    run(['docker', 'stop', '--timeout', '20', CI])
    if state['initial_states'][LATEST] == 'running':
        run(['docker','start',LATEST])
        state['restored_npu_check'] = run(['docker','exec',LATEST,'bash','-elc',
                                         'python3 /setup/audit_npu.py']).stdout
    state['final_states'] = {name:inspect(name)['State']['Status'] for name in [LATEST, CI]}
    state['phase'] = 'complete'
    state['finished_at'] = time.time()
    save()
except Exception as error:
    state['phase'] = 'error'
    state['error'] = str(error)
    state['traceback'] = traceback.format_exc()
    save()
    raise
