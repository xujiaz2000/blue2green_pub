import argparse,json,pathlib,subprocess,os,time,re
ROOT=pathlib.Path('/mnt/share/z00943141/qwen3_nightly_20261103_124914290773')
SETUP=pathlib.Path('/home/ubuntu/qwen_nightly_setup')
NAME='z00943141_qwen3_nightly_test'
IMAGE='swr.cn-north-12.myhuaweicloud.com/base_image/ascend-ci/vllm-ascend:nightly-ci-main-a2'
CI_IMAGE='swr.cn-north-12.myhuaweicloud.com/base_image/ascend-ci/vllm-ascend@sha256:51acbdd308d677c4add19eee604174fbc29eff784d46675968e82c8e1299b9df'
LABEL='codex.qwen3.run=124914290773'
def run(args,check=True,timeout=120):
 p=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
 if check and p.returncode:raise RuntimeError(str(args)+'\n'+p.stdout+'\n'+p.stderr)
 return p
def save(name,data):
 ROOT.mkdir(parents=True,exist_ok=True)
 (ROOT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2))
def create(image):
 existing=run(['docker','inspect',NAME],check=False)
 if existing.returncode==0:raise RuntimeError('Named container already exists; inspect before changing it')
 info=run(['npu-smi','info']).stdout
 idle={int(x) for x in re.findall(r'No running processes found in NPU\s+(\d+)',info)}
 if not {0,1,2,3}.issubset(idle):raise RuntimeError('NPU0-3 are not all idle')
 (ROOT/'outputs').mkdir(parents=True,exist_ok=True)
 model=ROOT/'inputs/modelscope/Eco-Tech/Qwen3-30B-A3B-w8a8'
 dataset=ROOT/'inputs/modelscope/vllm-ascend/GSM8K-in3500-bs400'
 if not model.is_dir() or not dataset.is_dir():raise RuntimeError('Expected input directories are not ready')
 args=['docker','run','--detach','--name',NAME,'--label',LABEL,'--network','host','--shm-size','32g',
       '-e','ASCEND_RT_VISIBLE_DEVICES=0,1,2,3','-e','ASCEND_VISIBLE_DEVICES=0,1,2,3','-e','LANG=C.UTF-8',
       '-v',str(SETUP)+':/setup:ro','-v',str(ROOT/'outputs')+':/results',
       '-v',str(model)+':/inputs/model:ro','-v',str(dataset)+':/inputs/dataset:ro']
 for dev in ['/dev/davinci0','/dev/davinci1','/dev/davinci2','/dev/davinci3','/dev/davinci_manager','/dev/devmm_svm','/dev/hisi_hdc']:
  if not pathlib.Path(dev).exists():raise RuntimeError('Missing driver device '+dev)
  args+=['--device',dev]
 for path in ['/usr/local/Ascend/driver','/usr/local/dcmi','/usr/local/bin/npu-smi','/etc/ascend_install.info','/usr/lib64/aicpu_kernels']:
  if pathlib.Path(path).exists():args+=['-v',path+':'+path+':ro']
 args+=['--entrypoint','/bin/bash',image,'-elc','sleep infinity']
 save(NAME+'_create_command.json',args)
 result=run(args)
 print(result.stdout,flush=True)
 save(NAME+'_initial_inspect.json',json.loads(run(['docker','inspect',NAME]).stdout))
def audit(name):
 p=run(['docker','exec',name,'bash','-elc','python3 /setup/audit_image.py'])
 data=json.loads(p.stdout)
 save(name+'_audit.json',data)
 print(json.dumps({'heads':{k:v['head']['stdout'].strip() for k,v in data['repositories'].items()},'packages':data['packages'],'cann':data['cann']},indent=2))
def measure(folder, runner='inside_runner_latest.py'):
 if (ROOT/'outputs'/folder).exists():raise RuntimeError('Measurement output already exists')
 if runner not in ['inside_runner_latest.py','inside_runner.py','inside_runner_rollback.py']:raise ValueError('Unexpected runner')
 command=['docker','exec',NAME,'bash','-elc','python3 -u /setup/'+runner+' --output /results/'+folder]
 with (ROOT/(folder+'_controller.log')).open('w') as log:
  p=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
 save(folder+'_controller.json',{'pid':p.pid,'command':command,'start_time':time.time()})
 print(json.dumps({'pid':p.pid,'output':str(ROOT/'outputs'/folder)}))
parser=argparse.ArgumentParser();parser.add_argument('action',choices=['create-latest','create-ci','audit','measure']);parser.add_argument('--folder',default='baseline01');parser.add_argument('--name',default=NAME);parser.add_argument('--runner',default='inside_runner_latest.py');args=parser.parse_args()
if not re.fullmatch(r'z00943141_qwen3_nightly_[a-zA-Z0-9_]+',args.name):raise ValueError('Unexpected container name')
NAME=args.name
if args.action=='create-latest':create(IMAGE)
elif args.action=='create-ci':create(CI_IMAGE)
elif args.action=='audit':audit(NAME)
elif args.action=='measure':measure(args.folder,args.runner)
