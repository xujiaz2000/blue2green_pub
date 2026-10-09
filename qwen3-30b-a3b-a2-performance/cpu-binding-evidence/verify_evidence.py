import hashlib,json,pathlib,re
root=pathlib.Path(__file__).resolve().parent
for line in (root/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
 digest,name=line.split('  ',1)
 assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
provenance=json.loads((root/'capture-provenance.json').read_text(encoding='utf-8'))
def expand(s):
 result=set()
 for item in s.split(','):
  a,*b=map(int,item.split('-'));result.update(range(a,(b[0] if b else a)+1))
 return result
expected={0:'194-221',1:'226-253',2:'130-157',3:'162-189'}
for model in ['bf16','w8a8']:
 script=(root/'config'/model/'01_start_server.sh').read_text(encoding='utf-8')
 assert '"enable_cpu_binding":true' in script
 assert 'export VLLM_USE_V2_MODEL_RUNNER=0' in script
 for kind in ['cann910','cann920']:
  key=model+'-'+kind;d=root/key;log=(d/'server.log').read_text(encoding='utf-8')
  assert 'gpu_model_runner.py:' in log
  raw=d/'worker-affinity-verified.json'
  assert hashlib.sha256(raw.read_bytes()).hexdigest()==provenance[key]['worker-affinity-verified.json']['sha256']
  records=json.loads(raw.read_text(encoding='utf-8'));assert len(records)==4 and {r['rank'] for r in records}=={0,1,2,3}
  for r in records:
   rank,pid=r['rank'],r['pid']
   assert f'(Worker_TP{rank} pid={pid})' in log
   assert f'mode=topo_affinity rank={rank} visible_npus=[0, 1, 2, 3]' in log
   assert int(re.search(r'^Pid:\s*(\d+)',r['status'],re.M).group(1))==pid
   actual=expand(re.search(r'^Cpus_allowed_list:\s*(.+)$',r['status'],re.M).group(1).strip())
   planned={int(s) for s in re.search(rf'NPU{rank}: main=\[([^\]]+)\]',log).group(1).split()}
   assert actual==planned==expand(expected[rank]) and len(actual)==28
  control=json.loads((d/'profile-control.json').read_text(encoding='utf-8'))
  assert provenance[key]['worker-affinity-verified.json']['mtime_epoch']<=control['start']['started']
  result=json.loads((d/'result.json').read_text(encoding='utf-8'))['metrics']
  assert result['Total Requests']==result['Success Requests']=='180' and result['Failed Requests']=='0'
  assert result['Total Generated Tokens']=='270000' and '/proc/irq is not writable' in log
  print(key, 'PASS: four worker main-thread affinity masks match the logged 28-CPU plan')
print('PASS: 16 worker records, MRV1 configuration, source snapshot SHA256 and publication manifest verified')
