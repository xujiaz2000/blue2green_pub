import hashlib,json,os,pathlib,subprocess,urllib.request,time
base=pathlib.Path('/home/ubuntu/qwen_nightly_setup')
url='https://ascend-repo.obs.cn-east-2.myhuaweicloud.com/Ascend%20HDK/Ascend%20HDK%2025.5.2/Ascend-hdk-910b-npu-driver_25.5.2_linux-aarch64.run'
status={}
def save(phase,**extra):
 status.update(phase=phase,time_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),**extra)
 (base/'driver_910b_status.json').write_text(json.dumps(status,indent=2))
 print(json.dumps(status),flush=True)
if os.geteuid()!=0:raise SystemExit('root required')
if pathlib.Path('/usr/local/Ascend/driver').exists():raise SystemExit('driver directory exists; inspect before installing')
package=base/'Ascend-hdk-910b-npu-driver_25.5.2_linux-aarch64.run'
try:
 save('download',url=url)
 if not package.exists() or package.stat().st_size!=120936131:
  with urllib.request.urlopen(url,timeout=60) as response,package.open('wb') as stream:
   count=0
   while True:
    chunk=response.read(1024*1024)
    if not chunk:break
    stream.write(chunk);count+=len(chunk)
    if count%(20*1024*1024)==0:print('download_bytes',count,flush=True)
 sha=hashlib.sha256(package.read_bytes()).hexdigest()
 save('verify',bytes=package.stat().st_size,sha256=sha)
 subprocess.run(['bash',str(package),'--check'],check=True,cwd=base)
 save('install')
 cmd=['bash',str(package),'--quiet','--full','--install-for-all','--install-username=HwHiAiUser','--install-usergroup=HwHiAiUser']
 result=subprocess.run(cmd,cwd=base)
 save('finished',returncode=result.returncode)
except Exception as e:
 save('error',error=str(e));raise
