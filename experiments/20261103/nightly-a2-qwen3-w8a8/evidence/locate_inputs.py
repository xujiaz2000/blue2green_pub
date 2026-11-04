import json,pathlib,itertools
roots=['/mnt/share/.cache/modelscope/hub/models','/mnt/share/.cache/modelscope/hub/datasets','/mnt/share/.cache/modelscope/hub','/mnt/share/modelscope','/mnt/share/ascend-ci/models','/mnt/share/ascend-ci/ci-share','/mnt/share/models','/mnt/share/datasets','/mnt/share/z00943141/benchmark/ais_bench/datasets']
out={}
for root in roots:
 p=pathlib.Path(root);d={'exists':p.exists()}
 if p.is_dir():
  try:d['children']=[x.name for x in itertools.islice(p.iterdir(),80)]
  except OSError as e:d['error']=str(e)
 out[root]=d
print(json.dumps(out,indent=2))
