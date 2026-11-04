import grp,json,pathlib,pwd,subprocess,os
base=pathlib.Path('/home/ubuntu/qwen_nightly_setup')
if os.geteuid()!=0:raise SystemExit('root required')
if pathlib.Path('/usr/local/Ascend/driver').exists():raise SystemExit('driver already exists; inspect before changing it')
try:grp.getgrnam('HwHiAiUser')
except KeyError:subprocess.run(['groupadd','HwHiAiUser'],check=True)
try:pwd.getpwnam('HwHiAiUser')
except KeyError:subprocess.run(['useradd','-g','HwHiAiUser','-d','/home/HwHiAiUser','-m','-s','/bin/bash','HwHiAiUser'],check=True)
log=base/'driver_install.log'
cmd=['bash',str(base/'Ascend-hdk-910-npu-driver_25.5.2_linux-aarch64.run'),'--quiet','--full','--install-for-all','--install-username=HwHiAiUser','--install-usergroup=HwHiAiUser']
with log.open('w') as out:
 p=subprocess.Popen(cmd,stdout=out,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True,cwd=base)
(base/'driver_install.pid').write_text(str(p.pid))
print(json.dumps({'pid':p.pid,'log':str(log),'command':cmd}))
