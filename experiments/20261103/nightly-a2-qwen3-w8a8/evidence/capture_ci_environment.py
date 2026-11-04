"""Read-only, stdlib-only environment capture; run before/after a CI benchmark."""
import argparse
import importlib.metadata
import json
import os
import pathlib
import subprocess
import time

parser = argparse.ArgumentParser()
parser.add_argument('--output', type=pathlib.Path, default=pathlib.Path('perf_environment.json'))
args = parser.parse_args()
data = {'captured_at_ns':time.time_ns(), 'commands':{}, 'files':{}, 'packages':{},
        'cpu_frequency':{}, 'environment':{}}
commands = {'uname':['uname','-a'], 'cpu':['lscpu'], 'numa':['numactl','--hardware'],
            'npu':['npu-smi','info'], 'npu_topology':['npu-smi','info','-t','topo'],
            'compiler':['clang','--version']}
for device in range(4):
    commands['npu_board_' + str(device)] = ['npu-smi','info','-t','board','-i',str(device),'-c','0']
    commands['npu_sensors_' + str(device)] = ['npu-smi','info','-t','sensors','-i',str(device),'-c','0']
    commands['npu_common_' + str(device)] = ['npu-smi','info','-t','common','-i',str(device),'-c','0']
    commands['npu_power_' + str(device)] = ['npu-smi','info','-t','power','-i',str(device),'-c','0']
for name, command in commands.items():
    try:
        p = subprocess.run(command, text=True, capture_output=True, timeout=20)
        data['commands'][name] = {'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    except (OSError, subprocess.TimeoutExpired) as error:
        data['commands'][name] = {'error':str(error)}
paths = ['/proc/self/status','/proc/self/cgroup','/proc/self/mountinfo','/proc/loadavg',
         '/proc/pressure/cpu','/proc/pressure/memory','/proc/meminfo','/etc/os-release',
         '/sys/fs/cgroup/cpu.max','/sys/fs/cgroup/cpu.stat','/sys/fs/cgroup/cpu.weight',
         '/sys/fs/cgroup/cpuset.cpus.effective','/sys/fs/cgroup/cpuset.mems.effective',
         '/sys/fs/cgroup/memory.max','/sys/fs/cgroup/memory.current','/sys/fs/cgroup/memory.events',
         '/sys/fs/cgroup/cpu/cpu.cfs_quota_us','/sys/fs/cgroup/cpu/cpu.cfs_period_us',
         '/sys/fs/cgroup/cpu/cpu.stat','/sys/fs/cgroup/cpuset/cpuset.cpus',
         '/sys/fs/cgroup/cpuset/cpuset.mems','/sys/fs/cgroup/memory/memory.limit_in_bytes']
for path in paths:
    try:
        data['files'][path] = pathlib.Path(path).read_text()
    except OSError:
        pass
for policy in pathlib.Path('/sys/devices/system/cpu/cpufreq').glob('policy*'):
    data['cpu_frequency'][policy.name] = {}
    for name in ['affected_cpus','scaling_governor','scaling_cur_freq','scaling_min_freq',
                 'scaling_max_freq','cpuinfo_max_freq','cpuinfo_min_freq']:
        try:
            data['cpu_frequency'][policy.name][name] = (policy / name).read_text().strip()
        except OSError:
            pass
for name in ['vllm','vllm-ascend','torch','torch-npu','triton','triton-ascend','transformers',
             'ais_bench_benchmark','numpy','uv']:
    try:
        data['packages'][name] = importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        data['packages'][name] = None
for key in ['ASCEND_RT_VISIBLE_DEVICES','ASCEND_VISIBLE_DEVICES','OMP_NUM_THREADS','OMP_PROC_BIND',
            'HCCL_BUFFSIZE','HCCL_OP_EXPANSION_MODE','TASK_QUEUE_ENABLE','VLLM_ASCEND_ENABLE_NZ',
            'VLLM_USE_V2_MODEL_RUNNER','VLLM_WORKER_MULTIPROC_METHOD','MAX_JOBS',
            'ASCEND_HOME_PATH','ASCEND_OPP_PATH','LD_LIBRARY_PATH','VLLM_CACHE_ROOT',
            'TRITON_CACHE_DIR','TORCHINDUCTOR_CACHE_DIR']:
    data['environment'][key] = os.environ.get(key)
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(data, indent=2))
print(args.output)
