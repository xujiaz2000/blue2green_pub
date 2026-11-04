import json
import pathlib
import re
import subprocess
import time

root = pathlib.Path('/mnt/share/z00943141/qwen3_nightly_20261103_124914290773')
runs = {'latest_baseline01': 'z00943141_qwen3_nightly_test',
        'ci_pinned02': 'z00943141_qwen3_nightly_ci_pinned'}

def run(args, check=True, timeout=120):
    result = subprocess.run(args, text=True, capture_output=True, timeout=timeout)
    if check and result.returncode:
        raise RuntimeError(str(args) + '\n' + result.stdout + '\n' + result.stderr)
    return result

record = {'started_at': time.time(), 'results': {}, 'containers': {}, 'raw_artifact_copy': {}}
for folder, name in runs.items():
    output = root / 'outputs' / folder
    result = json.loads((output / 'result.json').read_text())
    if not result.get('measurement_valid') or result['formal_metrics']['Output Token Throughput'] < 802:
        raise RuntimeError('Do not finalize: performance comparison is incomplete or requires rollback investigation')
    record['results'][folder] = result['formal_metrics']['Output Token Throughput']
    info = json.loads(run(['docker', 'inspect', name]).stdout)[0]
    if info['Config']['Labels'].get('codex.qwen3.run') != '124914290773':
        raise RuntimeError('Refusing to operate an unrelated container')
    for source, destination in [('output_performance.txt', 'aisbench_formal_stdout.txt')]:
        copied = run(['docker', 'cp', name + ':/vllm-workspace/vllm-ascend/' + source,
                      str(output / destination)], check=False)
        record['raw_artifact_copy'][folder + '/' + destination] = {
            'returncode': copied.returncode, 'stderr': copied.stderr}

health = run(['npu-smi', 'info']).stdout
(root / 'npu_smi_after_measurements.txt').write_text(health)
idle = {int(value) for value in re.findall(r'No running processes found in NPU\s+(\d+)', health)}
if not {0, 1, 2, 3}.issubset(idle):
    raise RuntimeError('Measurement devices are still busy; preserve state for inspection')

print('Stopping completed CI comparison container', flush=True)
run(['docker', 'stop', '--timeout', '20', runs['ci_pinned02']], timeout=100)
print('Restoring user-requested latest-image container', flush=True)
run(['docker', 'start', runs['latest_baseline01']])
visible = run(['docker', 'exec', runs['latest_baseline01'], 'bash', '-elc',
               'python3 /setup/audit_npu.py'])
record['latest_npu_validation'] = visible.stdout
for name in runs.values():
    info = json.loads(run(['docker', 'inspect', name]).stdout)[0]
    record['containers'][name] = {'status': info['State']['Status'], 'image': info['Image'],
                                 'configured_image': info['Config']['Image']}
record['rollback_performed'] = False
record['rollback_reason'] = 'Both local valid formal measurements exceed 802; user condition for rollback was not met'
record['finished_at'] = time.time()
(root / 'final_state.json').write_text(json.dumps(record, indent=2))
print(json.dumps(record, indent=2), flush=True)
