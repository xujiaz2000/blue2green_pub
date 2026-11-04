import argparse
import json
import pathlib
import re
import time

root = pathlib.Path('/mnt/share/z00943141/qwen3_nightly_20261103_124914290773')
parser = argparse.ArgumentParser()
parser.add_argument('folder', nargs='?', default='latest_baseline01')
args = parser.parse_args()
folder = root / 'outputs' / args.folder
result = folder / 'result.json'
print('UTC', time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
if result.is_file():
    print(result.read_text())
log = folder / 'pytest.log'
if log.is_file():
    text = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', log.read_text(errors='replace'))
    text = text.replace('\r', '\n')
    lines = text.splitlines()
    key = [line for line in lines if any(term in line for term in [
        'Starting to load model', 'CPU allocation plan', 'Bind cpus failed',
        'running aisbench cmd:', 'Output Token Throughput', 'Failed Requests',
        'Total Requests', 'Total Generated Tokens', 'Total Input Tokens',
        'Benchmark Duration', 'ERROR', 'Traceback', 'passed in', 'failed in',
        'Waiting for application startup', 'Application startup complete',
    ])]
    print('KEY_EVENTS')
    print('\n'.join(line[:650] for line in key[-20:]))
    print('TAIL')
    print('\n'.join(line[:450] for line in lines[-10:]))
else:
    print('NO_LOG_YET')
