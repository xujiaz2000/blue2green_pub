import json
import pathlib
import re
import shlex
import subprocess
import sys
import time
import traceback
import urllib.request

root = pathlib.Path(sys.argv[1])
state = {}
profile_mode = sys.argv[2] == 'profile' if len(sys.argv) > 2 else True
phase_suffix = '-profile' if profile_mode else ''
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def save(**changes):
    state.update(changes)
    temporary = root / 'status.tmp'
    temporary.write_text(json.dumps(state, indent=2) + '\n')
    temporary.replace(root / 'status.json')
    print(json.dumps(changes), flush=True)


def run(args, output=None):
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if output:
        pathlib.Path(output).write_text(result.stdout)
    if result.returncode:
        raise RuntimeError(str(args[:4]) + ' failed: ' + result.stdout[-3000:])
    return result.stdout


def environment(kind, path):
    return ['env', '-i', 'HOME=/root', 'USER=root', 'LANG=C.UTF-8',
            'ASCEND_VISIBLE_DEVICES=0,1,2,3', 'ASCEND_RT_VISIBLE_DEVICES=0,1,2,3',
            'VLLM_LOG_STATS_INTERVAL=10', 'TEST_CANN_KIND=' + kind, 'SERVER_PORT=8007', 'RUN_DIR=' + path,
            'VLLM_CACHE_ROOT=' + path + '/cache/vllm', 'TRITON_CACHE_DIR=' + path + '/cache/triton',
            'PATH=/usr/local/python3.12.13/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
            'LD_LIBRARY_PATH=/usr/local/python3.12.13/lib:/usr/local/Ascend/driver/lib64:/usr/local/Ascend/driver/lib64/common:/usr/local/Ascend/driver/lib64/driver',
            'bash', '--noprofile', '--norc', '-c']


initialize = 'set -e; source /usr/local/Ascend/cann/set_env.sh; source /usr/local/Ascend/nnal/atb/set_env.sh; export ASCEND_HOME_PATH="$(readlink -f "$ASCEND_HOME_PATH")"; '
metadata_code = '''import pathlib,subprocess,json,importlib.metadata as m,os,hashlib
records={}
for key,location in [('ascend','/vllm-workspace/vllm-ascend'),('vllm','/vllm-workspace/vllm')]:
    records[key]=subprocess.check_output(['git','-C',location,'rev-parse','HEAD'],text=True).strip()
records['packages']={d.metadata['Name']:d.version for d in m.distributions()}
cann=pathlib.Path(os.environ['ASCEND_HOME_PATH']);records['cann_root']=str(cann)
records['cann_metadata']={str(p):p.read_text(errors='replace') for p in cann.glob('share/info/*/version.info')}
source=pathlib.Path('/vllm-workspace/vllm-ascend');mismatches=[];checked=0
for entry in subprocess.check_output(['git','-C',str(source),'ls-tree','-rz','HEAD']).split(b'\\0'):
    if not entry:continue
    head,name=entry.split(b'\\t',1);mode,kind,expected=head.split()
    if kind!=b'blob':continue
    p=source/name.decode();raw=os.readlink(p).encode() if p.is_symlink() else p.read_bytes()
    actual=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\\0'+raw).hexdigest().encode();checked+=1
    if actual!=expected:mismatches.append(name.decode())
records['source_checked_files']=checked;records['source_mismatches']=mismatches
assert not mismatches,mismatches
print(json.dumps(records,indent=2))
'''
affinity_code = '''import pathlib,json
result=[]
for p in pathlib.Path('/proc').iterdir():
    if not p.name.isdigit():continue
    try:
        s=(p/'status').read_text()
        if 'VLLMWorker' in s.splitlines()[0]:result.append({'pid':p.name,'status':s})
    except OSError:pass
print(json.dumps(result,indent=2))
'''


def post(endpoint):
    before = time.time()
    request = urllib.request.Request('http://127.0.0.1:8007/' + endpoint, data=b'', method='POST')
    with opener.open(request, timeout=600) as response:
        return {'status': response.status, 'body': response.read().decode(), 'started': before, 'completed': time.time()}


try:
    while not (root / 'experiment.json').exists():
        save(stage='waiting_for_containers')
        time.sleep(10)
    experiment = json.loads((root / 'experiment.json').read_text())
    for kind in ['cann910', 'cann920']:
        name = experiment['containers'][kind]
        phase = root / (kind + '-bf16' + phase_suffix)
        path = '/experiment/' + phase.name
        if (phase / 'build-complete').exists():
            continue
        save(stage='building', phase=kind, container=name, started=time.time())
        run(['docker', 'start', name])
        with (phase / 'install.log').open('w') as output:
            result = subprocess.run(['docker', 'exec', name] + environment(kind, path) + [initialize + 'exec bash /experiment/install.sh ' + kind], stdout=output, stderr=subprocess.STDOUT)
        if result.returncode:
            raise RuntimeError(kind + ' install failed; see install.log')
        metadata = json.loads(run(['docker', 'exec', name] + environment(kind, path) + [initialize + 'python3 -c ' + shlex.quote(metadata_code)]))
        assert metadata['ascend'] == experiment['ascend_commit']
        assert metadata['vllm'] == experiment['vllm_commit']
        assert metadata['packages']['vllm'] == experiment['vllm_version']
        (phase / 'environment.json').write_text(json.dumps(metadata, indent=2))
        (phase / 'build-complete').touch()
        run(['docker', 'stop', '--timeout', '10', name])
        save(stage='build_complete', phase=kind)
    for kind in ['cann910', 'cann920']:
        name = experiment['containers'][kind]
        phase = root / (kind + '-bf16' + phase_suffix)
        path = '/experiment/' + phase.name
        if (phase / 'result.json').exists() and (phase / 'analysis-status.json').exists():
            continue
        save(stage='server_starting', phase=kind, container=name)
        smi = run(['npu-smi', 'info'])
        used_cards = {int(m.group(1)) for line in smi.splitlines() if (m := re.match(r'^\|\s+(\d+)\s+\d+\s+\d+\s+\S+', line))}
        if used_cards & {0, 1, 2, 3}:
            raise RuntimeError('NPU workload detected before benchmark; see npu-smi-host-before.log')
        (phase / 'npu-smi-host-before.log').write_text(smi)
        run(['docker', 'start', name])
        smi = run(['docker', 'exec', name, 'npu-smi', 'info'], phase / 'npu-smi-before.log')
        visible = sorted(set(int(x) for x in re.findall(r'^\|\s+(\d+)\s+910B', smi, re.M)))
        assert visible == [0, 1, 2, 3], visible
        run(['docker', 'exec', name] + environment(kind, path) + [initialize + "python3 -c 'import torch,torch_npu;assert torch.npu.device_count()==4;print(torch.npu.device_count())'"], phase / 'device-count.log')
        try:
            opener.open('http://127.0.0.1:8007/health', timeout=2)
            raise RuntimeError('Port 8007 already has a service')
        except urllib.error.URLError:
            pass
        run(['docker', 'exec', '-d', name] + environment(kind, path) + [initialize + 'exec bash /scripts/01_start_server.sh bf16 > ' + path + '/server-launch.log 2>&1'])
        for _ in range(240):
            text = (phase / 'server.log').read_text(errors='replace') if (phase / 'server.log').exists() else ''
            if 'Traceback (most recent call last)' in text:
                raise RuntimeError(kind + ' server startup traceback')
            try:
                with opener.open('http://127.0.0.1:8007/health', timeout=3) as response:
                    if response.status == 200:
                        break
            except urllib.error.URLError:
                pass
            time.sleep(5)
        else:
            raise RuntimeError(kind + ' server startup timeout')
        assert 'using Model Runner V2 by default' not in text, 'Unexpected Model Runner V2'
        assert '[gpu_model_runner.py:' in text or '[model_runner_v1.py:' in text, 'Runner V1 not confirmed'
        save(stage='benchmark_starting', phase=kind)
        with (phase / 'aisbench-launch.log').open('w') as output:
            benchmark = subprocess.Popen(['docker', 'exec', name] + environment(kind, path) + [initialize + 'exec bash /scripts/02_run_aisbench.sh bf16'], stdout=output, stderr=subprocess.STDOUT)
            for _ in range(600):
                if (phase / 'warmup-complete').exists():
                    break
                if benchmark.poll() is not None:
                    raise RuntimeError(kind + ' AISBench failed during warmup')
                time.sleep(2)
            else:
                raise RuntimeError(kind + ' warmup timeout')
            for _ in range(600):
                clientlog = (phase / 'aisbench-perf.log').read_text(errors='replace') if (phase / 'aisbench-perf.log').exists() else ''
                if 'Warmup finished' in clientlog:
                    break
                if benchmark.poll() is not None:
                    raise RuntimeError(kind + ' AISBench failed before internal warmup finished')
                time.sleep(1)
            else:
                raise RuntimeError(kind + ' internal warmup timeout')
            (phase / 'client-warmup-confirmed.json').write_text(json.dumps({'num_warmups': 1, 'finished': time.time()}))
            baseline = (phase / 'server.log').stat().st_size
            formal_started = time.time()
            save(stage='formal_benchmark', phase=kind)
            for _ in range(300):
                with (phase / 'server.log').open('rb') as stream:
                    stream.seek(baseline)
                    recent = stream.read().decode(errors='replace')
                metric_lines = [line for line in recent.splitlines() if 'Avg generation throughput:' in line]
                active_metric = metric_lines[-1] if metric_lines else ''
                if time.time() - formal_started >= 35 and re.search(r'Avg prompt throughput: 0\.0 tokens/s, Avg generation throughput: (?!0\.0)[0-9.]+ tokens/s, Running: 16 reqs', active_metric):
                    break
                if benchmark.poll() is not None:
                    raise RuntimeError(kind + ' formal benchmark ended before profiling')
                time.sleep(2)
            else:
                raise RuntimeError(kind + ' active decode timeout')
            run(['docker', 'exec', name, 'npu-smi', 'info'], phase / 'npu-smi-running.log')
            ranks = {int(rank):int(pid) for rank,pid in re.findall(r'\(Worker_TP(\d+) pid=(\d+)\)', (phase / 'server.log').read_text(errors='replace'))}
            assert len(ranks) == 4, ranks
            actual_affinity_code = "import pathlib,json;ranks=" + repr(ranks) + ";print(json.dumps([{'rank':r,'pid':pid,'status':pathlib.Path('/proc/'+str(pid)+'/status').read_text()} for r,pid in sorted(ranks.items())],indent=2))"
            run(['docker', 'exec', name, 'python3', '-c', actual_affinity_code], phase / 'worker-affinity-verified.json')
            run(['uptime'], phase / 'host-load.log')
            capture = None
            if profile_mode:
                save(stage='profiling', phase=kind)
                capture = {'server_metric_before_start': active_metric, 'start': post('start_profile')}
                time.sleep(1)
                capture['stop'] = post('stop_profile')
                capture['hold_seconds'] = capture['stop']['started'] - capture['start']['completed']
                (phase / 'profile-control.json').write_text(json.dumps(capture, indent=2))
            save(stage='benchmark_finishing', phase=kind)
            code = benchmark.wait(timeout=3600)
            if code:
                raise RuntimeError(kind + ' AISBench failed')
        text = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', (phase / 'aisbench-perf.log').read_text())
        summary = text[text.rfind('Performance Results of task'):]
        metrics = {}
        for line in summary.splitlines():
            if line.startswith('│'):
                values = [x.strip() for x in line.split('│')[1:-1]]
                if len(values) >= 3 and values[1] == 'total':
                    metrics[values[0]] = values[2]
        assert metrics['Success Requests'] == '180' and metrics['Failed Requests'] == '0', metrics
        assert metrics['Total Generated Tokens'] == '270000', metrics
        (phase / 'aisbench-final-result.log').write_text(summary)
        (phase / 'result.json').write_text(json.dumps({'metrics': metrics, 'profile': capture, 'ascend_commit': experiment['ascend_commit'], 'vllm_commit': experiment['vllm_commit']}, indent=2))
        # Stop the service before offline parsing to free NPU memory and isolate the next group.
        run(['docker', 'stop', '--timeout', '30', name])
        if profile_mode:
            run(['docker', 'start', name])
            save(stage='analysing', phase=kind)
            run(['docker', 'exec', name] + environment(kind, path) + [initialize + 'python3 /scripts/analysis.py ' + path + '/profiling'], phase / 'analysis.log')
            traces = list((phase / 'profiling').rglob('trace_view.json'))
            kernels = list((phase / 'profiling').rglob('kernel_details.csv'))
            assert len(traces) >= 4 and len(kernels) >= 4, (len(traces), len(kernels))
            (phase / 'analysis-status.json').write_text(json.dumps({'trace_count': len(traces), 'kernel_count': len(kernels)}, indent=2))
            run(['docker', 'stop', '--timeout', '10', name])
        else:
            (phase / 'analysis-status.json').write_text(json.dumps({'mode':'performance_only','trace_count':0,'kernel_count':0}))
        save(stage='phase_complete', phase=kind, metrics=metrics)
    save(stage='complete')
except Exception as error:
    save(stage='failed', error=str(error))
    traceback.print_exc()
    if 'experiment' in globals():
        for name in experiment['containers'].values():
            subprocess.run(['docker', 'stop', '--timeout', '20', name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sys.exit(1)
