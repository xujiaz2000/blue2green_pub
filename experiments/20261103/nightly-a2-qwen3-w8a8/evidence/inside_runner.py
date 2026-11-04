#!/usr/bin/env python3
"""Run the pinned CI pytest flow inside one disposable Ascend container."""

import argparse
import hashlib
import importlib.metadata
import json
import os
import pathlib
import re
import shutil
import signal
import subprocess
import sys
import threading
import time

EXPECTED_ASCEND = 'b3b82c137ee242a774c29b56325133771f5f069d'
EXPECTED_VLLM = '5df63a7203cdb9328d824a27b682e77c7b9928be'
EXPECTED_PACKAGES = {
    'vllm': '0.32.0+empty',
    'torch': '2.10.0+cpu',
    'torch-npu': '2.10.0.post4',
    'triton-ascend': '3.2.2',
    'transformers': '5.19.0',
    'ais_bench_benchmark': '3.1.20260609',
}
CONFIG_PATH = 'tests/e2e/cases/models/configs/Qwen/Qwen3-30B-A3B-W8A8-A2.yaml'
TEST_PATH = 'tests/e2e/common/single_node/test_single_node.py'
ANSI = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')


def command(args, cwd=None, timeout=120):
    try:
        result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, timeout=timeout)
        return {'args': args, 'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {'args': args, 'returncode': -1, 'error': str(error)}


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def snapshot(output, known_pids, detailed=False):
    result = {'time_ns': time.time_ns(), 'processes': {}}
    for filename in ['/proc/self/status', '/proc/self/cgroup', '/proc/loadavg', '/proc/pressure/cpu',
                     '/sys/fs/cgroup/cpu.max', '/sys/fs/cgroup/cpu.stat',
                     '/sys/fs/cgroup/cpuset.cpus.effective', '/sys/fs/cgroup/memory.current']:
        try:
            result[filename] = pathlib.Path(filename).read_text()
        except OSError as error:
            result[filename] = {'error': str(error)}
    for pid in sorted(known_pids):
        proc_root = pathlib.Path('/proc') / str(pid)
        proc = {}
        for name in ['status', 'schedstat', 'cgroup'] + (['numa_maps'] if detailed else []):
            try:
                proc[name] = (proc_root / name).read_text()
            except OSError:
                pass
        if detailed:
            proc['threads'] = {}
            for thread in (proc_root / 'task').glob('*'):
                try:
                    proc['threads'][thread.name] = {
                        'comm': (thread / 'comm').read_text().strip(),
                        'status': (thread / 'status').read_text(),
                        'schedstat': (thread / 'schedstat').read_text(),
                    }
                except OSError:
                    pass
        result['processes'][str(pid)] = proc
    with output.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(result, ensure_ascii=False) + '\n')


def parse_formal_metrics(text):
    text = ANSI.sub('', text)
    results = []
    for block in text.split('running aisbench cmd: ')[1:]:
        count = re.search(r'--num-prompts (\d+)', block)
        if not count or int(count.group(1)) != 180:
            continue
        rows = {}
        for line in block.splitlines():
            cells = [part.strip() for part in line.split('│')]
            if len(cells) >= 5 and cells[2] == 'total':
                number = re.match(r'([0-9.]+)', cells[3])
                if number:
                    rows[cells[1]] = float(number.group(1))
        if rows.get('Total Requests') == 180 and 'Output Token Throughput' in rows:
            results.append(rows)
    return results[-1] if results else None


def preflight(args, output):
    metadata = {'expected': {'ascend': EXPECTED_ASCEND, 'vllm': EXPECTED_VLLM,
                             'packages': EXPECTED_PACKAGES}, 'repositories': {}, 'packages': {},
                'commands': {}, 'cann_metadata': {}, 'native_extensions': {},
                'native_extensions_scope': 'Only .so files under the Ascend repository; '
                    'not a complete hash inventory of torch-npu, flash-attention or CANN libraries. '
                    'The immutable image digest pins the whole image.'}
    failures = []
    for name, path, expected in [('ascend', args.ascend_repo, EXPECTED_ASCEND),
                                 ('vllm', args.vllm_repo, EXPECTED_VLLM)]:
        info = command(['git', 'rev-parse', 'HEAD'], cwd=path)
        info['tracked_status'] = command(['git', 'status', '--porcelain', '--untracked-files=no'], cwd=path)
        metadata['repositories'][name] = info
        if info.get('returncode') != 0 or info.get('stdout', '').strip() != expected:
            failures.append(f'{name} git HEAD does not match expected SHA')
        info['tracked_clean'] = (info['tracked_status'].get('returncode') == 0
                                 and not info['tracked_status'].get('stdout', '').strip())
        # The immutable CI image, including its build-time patches, is the
        # authoritative artifact. Record differences without repairing them.
    for distribution, expected in EXPECTED_PACKAGES.items():
        try:
            actual = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            actual = None
        metadata['packages'][distribution] = actual
        if actual != expected:
            failures.append(f'{distribution}: expected {expected}, found {actual}')
    metadata['packages']['transformers'] = importlib.metadata.version('transformers')
    metadata['commands']['pip_list'] = command([sys.executable, '-m', 'pip', 'list', '--format=json'])
    for name, cmd in {'uname': ['uname', '-a'], 'lscpu': ['lscpu'], 'npu_smi': ['npu-smi', 'info'],
                      'numactl': ['numactl', '--hardware'], 'clang': ['clang', '--version']}.items():
        metadata['commands'][name] = command(cmd)
    candidates = list(pathlib.Path('/usr/local/Ascend').glob('**/ascend_toolkit_install.info'))
    candidates.append(pathlib.Path('/usr/local/Ascend/ascend-toolkit/latest/aarch64-linux/ascend_toolkit_install.info'))
    for path in candidates:
        try:
            metadata['cann_metadata'][str(path)] = path.read_text()
        except OSError:
            pass
    if not any('innerversion=V100R001C12SPC002B201' in value for value in metadata['cann_metadata'].values()):
        failures.append('CANN toolkit innerversion V100R001C12SPC002B201 was not found')
    for path in pathlib.Path('/usr/local/Ascend').glob('cann*/share/info/*/version.info'):
        try:
            metadata['cann_metadata'][str(path)] = path.read_text()
        except OSError:
            pass
    for path in args.ascend_repo.rglob('*.so'):
        if path.is_file():
            metadata['native_extensions'][str(path)] = {'size': path.stat().st_size, 'sha256': sha256(path)}
    for path in [args.model_path, args.dataset_path]:
        if not path.is_dir():
            failures.append(f'missing read-only input directory: {path}')
    metadata['dangling_input_links'] = [str(path) for root in [args.model_path, args.dataset_path]
                                       for path in root.rglob('*') if path.is_symlink() and not path.exists()]
    if metadata['dangling_input_links']:
        failures.append('input snapshot has symlinks whose targets are outside the read-only mounts or missing')
    if not (args.model_path / 'config.json').is_file():
        failures.append('model config.json is missing')
    if not list(args.model_path.glob('*.safetensors')) and not list(args.model_path.glob('*.bin')):
        failures.append('model has no local safetensors/bin weights')
    metadata['model_metadata'] = {str(path): sha256(path) for pattern in ['*.json', '*.py', '*.model']
                                for path in args.model_path.glob(pattern) if path.is_file()}
    metadata['dataset_files'] = {str(path.relative_to(args.dataset_path)): {'size': path.stat().st_size,
                                'sha256': sha256(path)} for path in args.dataset_path.rglob('*') if path.is_file()}
    check = command([sys.executable, '-c',
                     'import json,torch,torch_npu;print(json.dumps({"count":torch.npu.device_count(),'
                     '"names":[torch.npu.get_device_name(i) for i in range(torch.npu.device_count())]}))'])
    metadata['commands']['visible_npus'] = check
    try:
        device_info = json.loads(check['stdout'].strip().splitlines()[-1])
        if device_info['count'] != 4 or not all('910B' in name for name in device_info['names']):
            failures.append(f'expected four visible 910B devices, found {device_info}')
    except (KeyError, ValueError, IndexError):
        failures.append('could not verify exactly four visible NPU devices')
    metadata['failures'] = failures
    write_json(output / 'environment.json', metadata)
    if failures:
        raise RuntimeError('; '.join(failures))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=pathlib.Path, required=True)
    parser.add_argument('--model-path', type=pathlib.Path, default=pathlib.Path('/inputs/model'))
    parser.add_argument('--dataset-path', type=pathlib.Path, default=pathlib.Path('/inputs/dataset'))
    parser.add_argument('--ascend-repo', type=pathlib.Path, default=pathlib.Path('/vllm-workspace/vllm-ascend'))
    parser.add_argument('--vllm-repo', type=pathlib.Path, default=pathlib.Path('/vllm-workspace/vllm'))
    parser.add_argument('--timeout-seconds', type=int, default=7200)
    parser.add_argument('--preflight-only', action='store_true')
    parser.add_argument('--detailed-telemetry', action='store_true',
                        help='Opt-in diagnostic numa_maps/all-thread capture; keep off for baseline')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    result = {'source_job': 'https://github.com/vllm-project/vllm-ascend/actions/runs/41327490550/job/124914290773',
              'started_ns': time.time_ns(), 'success': False,
              'measurement_kind': 'historical_ci_image_pinned_by_arm64_digest'}
    child = None
    stop = threading.Event()
    known_pids = set()
    def stop_signal(_signum, _frame):
        raise KeyboardInterrupt('SIGTERM')
    signal.signal(signal.SIGTERM, stop_signal)
    try:
        preflight(args, args.output)
        if args.preflight_only:
            result['success'] = True
            result['preflight_only'] = True
            return 0
        import yaml

        original = args.ascend_repo / CONFIG_PATH
        config = yaml.safe_load(original.read_text())
        write_json(args.output / 'original_config.json', config)
        case = config['test_cases'][0]
        # Only paths change, so ModelScope cannot download model or data. The
        # served model name changes to this local path; record that difference.
        case['model'] = str(args.model_path)
        for benchmark in case['benchmarks'].values():
            benchmark['model_path'] = str(args.model_path)
            benchmark['dataset_path_local'] = str(args.dataset_path)
        adjusted = args.output / 'Qwen3-30B-A3B-W8A8-A2.local.yaml'
        adjusted.write_text(yaml.safe_dump(config, sort_keys=False), encoding='utf-8')
        shutil.copyfile(original, args.output / 'Qwen3-30B-A3B-W8A8-A2.original.yaml')
        env = os.environ.copy()
        env.update({'HF_HUB_OFFLINE': '1', 'HF_DATASETS_OFFLINE': '1', 'TEST_FREQUENCY': 'nightly',
                    'VLLM_USE_MODELSCOPE': 'true', 'VLLM_WORKER_MULTIPROC_METHOD': 'spawn',
                    'VLLM_ENGINE_READY_TIMEOUT_S': '1800', 'VLLM_ASCEND_BRANCH': 'main',
                    'VLLM_ASCEND_VERSION': EXPECTED_ASCEND, 'VLLM_CI_RUNNER': 'local-a2-reproduction',
                    'CONFIG_BASE_PATH': str(args.output), 'CONFIG_YAML_PATH': adjusted.name,
                    'BENCHMARK_JOB_NAME': 'reproduce-124914290773', 'PYTHONUNBUFFERED': '1',
                    'VLLM_CACHE_ROOT': str(args.output / 'cache/vllm'),
                    'TRITON_CACHE_DIR': str(args.output / 'cache/triton'),
                    'TORCHINDUCTOR_CACHE_DIR': str(args.output / 'cache/torchinductor'),
                    'ASCEND_PROFILE_ROOT': str(args.output / 'profile-disabled'),
                    'LD_LIBRARY_PATH': '/usr/local/lib:' + env.get('LD_LIBRARY_PATH', '')})
        # The CI leaves this unset and selects V2 by default. Do not accidentally
        # inherit a local manual override; retain the CI default behavior.
        for key in list(env):
            if key == 'VLLM_USE_V2_MODEL_RUNNER' or key.startswith('ASCEND_PROFILE_') and key != 'ASCEND_PROFILE_ROOT':
                env.pop(key)
        safe_env = {key: value for key, value in env.items() if key.startswith(('VLLM_', 'ASCEND_', 'HCCL_',
                   'OMP_', 'TASK_QUEUE_', 'PYTORCH_', 'TORCHINDUCTOR_', 'TRITON_', 'HF_'))}
        write_json(args.output / 'effective_test_environment.json', safe_env)
        cmd = [sys.executable, '-u', '-m', 'pytest', '-sv', TEST_PATH]
        result['command'] = cmd
        result['detailed_telemetry'] = args.detailed_telemetry
        result['path_substitution'] = {'model': str(args.model_path), 'dataset': str(args.dataset_path)}
        log_path = args.output / 'pytest.log'
        with log_path.open('w', encoding='utf-8', buffering=1) as stream:
            child = subprocess.Popen(cmd, cwd=args.ascend_repo, env=env, stdout=stream,
                                     stderr=subprocess.STDOUT, start_new_session=True)
            known_pids.add(child.pid)

            def monitor():
                elapsed = 0
                while not stop.wait(30):
                    elapsed += 30
                    try:
                        log = log_path.read_text(errors='replace')
                        known_pids.update(int(pid) for pid in re.findall(r'\bpid=(\d+)\)', log))
                        snapshot(args.output / 'runtime.jsonl', known_pids, detailed=args.detailed_telemetry)
                    except OSError:
                        pass

            thread = threading.Thread(target=monitor, daemon=True)
            thread.start()
            try:
                result['pytest_returncode'] = child.wait(timeout=args.timeout_seconds)
            except subprocess.TimeoutExpired:
                result['timed_out'] = True
                raise
            finally:
                stop.set()
                thread.join(timeout=15)
        text = ANSI.sub('', log_path.read_text(errors='replace'))
        snapshot(args.output / 'runtime.jsonl', known_pids, detailed=args.detailed_telemetry)
        metrics = parse_formal_metrics(text)
        result['formal_metrics'] = metrics
        ranks = {int(rank) for rank in re.findall(r'Worker_TP(\d+) pid=\d+\).*?\[model_runner\.py:', text)}
        result['model_runner_validation'] = {'expected': 'MRV2', 'ranks_with_v2_load': sorted(ranks),
             'v2_worker_warnings': text.count('npu model runner v2 is in developing'),
             'v1_load_detected': bool(re.search(r'\[model_runner_v1\.py:\d+\] Starting to load model', text))}
        result['binding'] = {'allocation_logs': text.count('The CPU allocation plan is as follows'),
                             'failed_logs': text.count('Bind cpus failed in rank'),
                             'irq_skipped': '/proc/irq is not writable' in text,
                             'numa_note': 'migrate logs do not establish successful physical page migration'}
        if not metrics:
            raise RuntimeError('formal 180-request AISBench result is missing')
        if metrics.get('Total Input Tokens') != 656793 or metrics.get('Total Generated Tokens') != 270000:
            raise RuntimeError('formal input/output token counts differ from CI')
        if metrics.get('Failed Requests') != 0:
            raise RuntimeError('formal requests failed')
        if ranks != {0, 1, 2, 3} or result['model_runner_validation']['v1_load_detected']:
            raise RuntimeError('the four actual MRV2 workers were not verified')
        throughput = metrics['Output Token Throughput']
        result['thresholds'] = {'temporary_ci': {'baseline': 765, 'floor': 742.05, 'pass': throughput >= 742.05},
             'original_w8a8': {'baseline': 805.872, 'floor': 781.69584, 'pass': throughput >= 781.69584},
             'user_802': {'baseline': 802, 'floor': 777.94, 'pass': throughput >= 777.94}}
        result['relative_to_ci_767_3497_pct'] = (throughput / 767.3497 - 1) * 100
        # Preserve performance data even if pytest legitimately fails its gate.
        result['measurement_valid'] = True
        result['success'] = result['pytest_returncode'] == 0
        return 0 if result['success'] else 2
    except BaseException as error:
        result['error'] = f'{type(error).__name__}: {error}'
        if child and child.poll() is None:
            try:
                os.killpg(child.pid, signal.SIGTERM)
                child.wait(timeout=20)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                if child.poll() is None:
                    os.killpg(child.pid, signal.SIGKILL)
        print(result['error'], file=sys.stderr, flush=True)
        return 1
    finally:
        stop.set()
        result['finished_ns'] = time.time_ns()
        write_json(args.output / 'result.json', result)


if __name__ == '__main__':
    raise SystemExit(main())
