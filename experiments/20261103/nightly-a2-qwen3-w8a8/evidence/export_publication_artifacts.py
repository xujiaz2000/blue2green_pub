"""Export existing records only; this script does not start/stop containers or inference."""
import json
import pathlib
import re
import subprocess
import tarfile

root = pathlib.Path('/mnt/share/z00943141/qwen3_nightly_20261103_124914290773')
runs = {'latest_baseline01':'z00943141_qwen3_nightly_test',
        'ci_pinned02':'z00943141_qwen3_nightly_ci_pinned',
        'ci_pinned03':'z00943141_qwen3_nightly_ci_pinned',
        'ci_pinned04':'z00943141_qwen3_nightly_ci_pinned'}
for folder, container in runs.items():
    output = root / 'outputs' / folder
    result = json.loads((output / 'result.json').read_text())
    if not result.get('measurement_valid'):
        raise RuntimeError('Expected a completed formal result: ' + folder)
    info = json.loads(subprocess.check_output(['docker','inspect',container], text=True))[0]
    if info['Config']['Labels'].get('codex.qwen3.run') != '124914290773':
        raise RuntimeError('Unexpected container')
    paths = re.findall(r'Current exp folder:\s*(outputs/default/\d{8}_\d{6})',
                       (output / 'pytest.log').read_text(errors='replace'))
    if not paths:
        raise RuntimeError('Formal AISBench artifact path missing: ' + folder)
    source = '/vllm-workspace/vllm-ascend/' + paths[-1]
    for suffix, name in [('configs','aisbench_configs'),
                         ('performances/vllm-api-stream-chat/gsm8k_details.jsonl','aisbench_details.jsonl'),
                         ('performances/vllm-api-stream-chat/db_data','aisbench_db_data'),
                         ('performances/vllm-api-stream-chat/gsm8k.json','aisbench_metrics.json'),
                         ('performances/vllm-api-stream-chat/gsm8k.csv','aisbench_metrics.csv')]:
        target = output / name
        if not target.exists():
            subprocess.run(['docker','cp',container + ':' + source + '/' + suffix,str(target)],
                           check=True,capture_output=True)

archive = root / 'publication_records_20261104.tar.gz'
with tarfile.open(archive, 'w:gz') as tar:
    for folder in [*runs, 'ci_pinned01']:
        output = root / 'outputs' / folder
        for path in sorted(output.rglob('*')):
            if 'cache' in path.relative_to(output).parts or not path.is_file():
                continue
            tar.add(path, arcname=folder + '/' + str(path.relative_to(output)), recursive=False)
    for pattern in ['*_controller.json','*_controller.log','*driver*status*.json','*driver*install*.log',
                    '*_create_command.json','*_initial_inspect.json','*_audit.json']:
        for path in sorted(root.glob(pattern)):
            if path.is_file():
                tar.add(path, arcname='remote_metadata/' + path.name, recursive=False)
    setup = pathlib.Path('/home/ubuntu/qwen_nightly_setup')
    for pattern in ['*driver*status*.json','*driver*install*.log','*driver*.log']:
        for path in sorted(setup.glob(pattern)):
            if path.is_file():
                tar.add(path, arcname='remote_setup/' + path.name, recursive=False)
archive.chmod(0o644)
print(json.dumps({'archive':str(archive),'bytes':archive.stat().st_size}),flush=True)
