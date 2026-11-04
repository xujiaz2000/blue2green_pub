import glob,json,os,pathlib,subprocess,shutil
result={'root':os.geteuid()==0,'paths':{},'commands':{}}
paths=['/mnt/share/public','/mnt/share/cann','/mnt/share/ascend-ci','/mnt/share/z00943141','/mnt/share/host-image-backups','/usr/src','/lib/modules/'+os.uname().release+'/build','/var/lib/dkms','/etc/apt/sources.list','/usr/local/sbin','/usr/local/bin','/run/user/1000']
for path in paths:
 p=pathlib.Path(path);result['paths'][path]={'exists':p.exists()}
 if p.is_dir():
  try:result['paths'][path]['children']=[x.name for x in p.iterdir()][:180]
  except OSError as e:result['paths'][path]['error']=str(e)
for name,args in {'sudo':['sudo','-l','-U','ubuntu'],'modules':['lsmod'],'docker_policy':['apt-cache','policy','docker.io','containerd','dkms','linux-headers-'+os.uname().release],'runtime_packages':['dpkg-query','-W','*ascend*','*docker*','*containerd*','*npu*'],'disk':['df','-h','/','/mnt/share'],'secureboot':['mokutil','--sb-state']}.items():
 try:
  p=subprocess.run(args,capture_output=True,text=True,timeout=20)
  stdout=p.stdout
  if name=='modules':stdout='\n'.join(l for l in stdout.splitlines() if any(k in l.lower() for k in ['npu','devmm','hisi','ascend','drv','module']))
  result['commands'][name]={'returncode':p.returncode,'stdout':stdout,'stderr':p.stderr}
 except Exception as e:result['commands'][name]={'error':str(e)}
print(json.dumps(result,ensure_ascii=False,indent=2))
