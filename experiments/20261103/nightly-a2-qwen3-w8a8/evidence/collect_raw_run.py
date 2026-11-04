import argparse
import json
import pathlib
import re
import subprocess

root = pathlib.Path('/mnt/share/z00943141/qwen3_nightly_20261103_124914290773/outputs')
container = 'z00943141_qwen3_nightly_ci_pinned'
parser = argparse.ArgumentParser()
parser.add_argument('folders', nargs='+', choices=['ci_pinned02','ci_pinned03','ci_pinned04'])
args = parser.parse_args()
info = json.loads(subprocess.check_output(['docker','inspect',container], text=True))[0]
if info['Config']['Labels'].get('codex.qwen3.run') != '124914290773':
    raise RuntimeError('Unexpected container')
for folder in args.folders:
    output = root / folder
    result = json.loads((output / 'result.json').read_text())
    if not result.get('measurement_valid'):
        raise RuntimeError('Not a valid formal run: ' + folder)
    log = (output / 'pytest.log').read_text(errors='replace')
    paths = re.findall(r'Current exp folder:\s*(outputs/default/\d{8}_\d{6})', log)
    if not paths:
        raise RuntimeError('AISBench formal experiment path missing')
    experiment = '/vllm-workspace/vllm-ascend/' + paths[-1]
    evidence = {'source_experiment':experiment,'files':{}}
    for suffix, name in [('configs','aisbench_configs'),
                         ('performances/vllm-api-stream-chat/gsm8k_details.jsonl','aisbench_details.jsonl'),
                         ('performances/vllm-api-stream-chat/db_data','aisbench_db_data')]:
        destination = output / name
        if not destination.exists():
            subprocess.run(['docker','cp',container + ':' + experiment + '/' + suffix,
                            str(destination)], check=True, capture_output=True)
        evidence['files'][name] = str(destination)
    (output / 'raw_artifacts.json').write_text(json.dumps(evidence, indent=2))
    print(json.dumps({'folder':folder, **evidence}), flush=True)
