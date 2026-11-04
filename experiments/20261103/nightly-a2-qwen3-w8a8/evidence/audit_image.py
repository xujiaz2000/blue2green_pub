import importlib.metadata,json,pathlib,subprocess,sys,os
def run(args,cwd=None):
 p=subprocess.run(args,cwd=cwd,text=True,capture_output=True)
 return {'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
out={'python':sys.version,'repositories':{},'packages':{},'cann':{},'paths':{},'environment':{}}
for name,path in [('vllm','/vllm-workspace/vllm'),('ascend','/vllm-workspace/vllm-ascend')]:
 out['repositories'][name]={'path':path,'head':run(['git','rev-parse','HEAD'],path),'status':run(['git','status','--porcelain','--untracked-files=no'],path)}
for name in ['vllm','vllm-ascend','torch','torch-npu','triton','triton-ascend','transformers','ais_bench_benchmark','numpy','datasets']:
 try:out['packages'][name]=importlib.metadata.version(name)
 except importlib.metadata.PackageNotFoundError:out['packages'][name]=None
for p in pathlib.Path('/usr/local/Ascend').glob('**/ascend_toolkit_install.info'):
 try:out['cann'][str(p)]=p.read_text()
 except OSError:pass
for key in ['PATH','LD_LIBRARY_PATH','ASCEND_HOME_PATH','ASCEND_OPP_PATH','VLLM_USE_V2_MODEL_RUNNER','ASCEND_RT_VISIBLE_DEVICES']:
 out['environment'][key]=os.environ.get(key)
out['package_list']=run([sys.executable,'-m','pip','list','--format=json'])
for p in ['/usr/local/Ascend/driver','/usr/local/bin/npu-smi','/usr/local/dcmi','/usr/lib64/aicpu_kernels']:
 out['paths'][p]=pathlib.Path(p).exists()
print(json.dumps(out,ensure_ascii=False,indent=2))
