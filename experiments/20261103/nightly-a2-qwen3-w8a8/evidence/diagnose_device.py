import ctypes
import glob
import importlib.metadata
import importlib.util
import json
import os
import pathlib
import subprocess

result = {'torch_npu': importlib.metadata.version('torch-npu'),
          'environment': {k:v for k,v in os.environ.items() if k.startswith(('ASCEND_', 'LD_', 'PATH', 'DLSMI_'))},
          'devices': glob.glob('/dev/davinci*') + glob.glob('/dev/devmm*') + glob.glob('/dev/hisi*'),
          'libraries': {}, 'commands': {}}
for name, args in {'smi': ['npu-smi', 'info'], 'smi-list': ['npu-smi', 'info', '-l'],
                   'ldconfig': ['bash', '-c', 'ldconfig -p | grep -E "ascend_hal|drvdsmi|dcmi"']}.items():
    p = subprocess.run(args, text=True, capture_output=True)
    result['commands'][name] = {'rc':p.returncode, 'out':p.stdout, 'err':p.stderr}
for path in ['libascend_hal.so', '/usr/local/Ascend/driver/lib64/driver/libascend_hal.so',
             '/usr/local/Ascend/driver/lib64/libascend_hal.so']:
    try:
        lib = ctypes.CDLL(path)
        count = ctypes.c_uint32()
        rc = lib.halGetDeviceCount(ctypes.byref(count))
        result['libraries'][path] = {'count_rc':rc,'count':count.value}
    except Exception as error:
        result['libraries'][path] = {'error':str(error)}
spec = importlib.util.find_spec('torch_npu')
if spec and spec.origin:
    path = pathlib.Path(spec.origin).parent / 'npu/__init__.py'
    lines = path.read_text().splitlines()
    for index, line in enumerate(lines):
        if line.startswith('def _device_count_ascend_hal'):
            result['device_count_implementation'] = '\n'.join(lines[index:index+95])
            break
print(json.dumps(result, indent=2))
