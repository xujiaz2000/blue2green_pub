import glob,json,os,pathlib,shutil,subprocess
result={'paths':{},'commands':{}}
for path in ['/usr/local/Ascend','/usr/local/Ascend/driver/tools/npu-smi','/usr/bin/docker','/usr/local/bin/docker','/snap/bin/docker','/var/run/docker.sock','/mnt/share','/opt','/dev/davinci0','/dev/davinci_manager','/home/ubuntu']:
 p=pathlib.Path(path)
 result['paths'][path]={'exists':p.exists(),'is_dir':p.is_dir()}
 if p.is_dir():
  try:result['paths'][path]['children']=[x.name for x in p.iterdir()][:100]
  except OSError as e:result['paths'][path]['error']=str(e)
result['devices']=glob.glob('/dev/davinci*')+glob.glob('/dev/devmm*')+glob.glob('/dev/hisi_hdc*')
for name,args in {'id':['id'],'sudo':['sudo','-n','true'],'pci':['lspci','-nn'],'docker_service':['systemctl','status','docker','--no-pager'],'os':['cat','/etc/os-release'],'mounts':['findmnt','-T','/mnt/share']}.items():
 try:
  p=subprocess.run(args,capture_output=True,text=True,timeout=20)
  result['commands'][name]={'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
 except Exception as e:result['commands'][name]={'error':str(e)}
print(json.dumps(result,ensure_ascii=False,indent=2))
