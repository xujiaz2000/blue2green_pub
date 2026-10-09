import hashlib
import json
import pathlib
import re

root=pathlib.Path(__file__).resolve().parent
for line in (root/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
    digest,name=line.split('  ',1)
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name

provenance=json.loads((root/'evidence/capture-provenance.json').read_text(encoding='utf-8'))
script=(root/'evidence/01_start_server.sh').read_text(encoding='utf-8')
assert '"enable_cpu_binding":true' in script
assert 'export VLLM_USE_V2_MODEL_RUNNER=1' in script
expected={0:'194-221',1:'226-253',2:'130-157',3:'162-189'}

def expand(value):
    cpus=set()
    for piece in value.split(','):
        if '-' in piece:
            a,b=map(int,piece.split('-'));cpus.update(range(a,b+1))
        else:cpus.add(int(piece))
    return cpus

for kind in ['cann910','cann920']:
    directory=root/'evidence'/kind
    server=(directory/'server.log').read_text(encoding='utf-8')
    raw=directory/'worker-affinity-verified.json'
    assert hashlib.sha256(raw.read_bytes()).hexdigest()==provenance[kind]['source_sha256']
    records=json.loads(raw.read_text(encoding='utf-8'))
    assert {x['rank'] for x in records}=={0,1,2,3} and len(records)==4
    for record in records:
        rank,pid=record['rank'],record['pid']
        assert f'(Worker_TP{rank} pid={pid})' in server
        assert f'mode=topo_affinity rank={rank} visible_npus=[0, 1, 2, 3]' in server
        actual=re.search(r'^Cpus_allowed_list:\s*(.+)$',record['status'],re.M).group(1).strip()
        planned=re.search(rf'NPU{rank}: main=\[([^\]]+)\]',server).group(1)
        planned_set={int(n) for n in planned.split()}
        assert expand(actual)==planned_set==expand(expected[rank])
        assert len(planned_set)==28
        assert int(re.search(r'^Pid:\s*(\d+)',record['status'],re.M).group(1))==pid
    control=json.loads((directory/'profile-control.json').read_text(encoding='utf-8'))
    assert provenance[kind]['saved_epoch']<=control['start']['started']
    result=json.loads((directory/'result.json').read_text(encoding='utf-8'))['metrics']
    assert result['Total Requests']==result['Success Requests']=='180'
    assert result['Failed Requests']=='0' and result['Total Generated Tokens']=='270000'
    assert '/proc/irq is not writable' in server
    print(kind,'PASS: four worker main-thread affinity masks match topo_affinity plan; IRQ adjustment unavailable')
print('PASS: SHA256SUMS and original snapshot hashes verified')
