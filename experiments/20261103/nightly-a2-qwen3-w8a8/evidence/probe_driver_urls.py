import concurrent.futures,json,urllib.request,urllib.error
base='https://ascend-repo.obs.cn-east-2.myhuaweicloud.com/'
paths=[
 'Ascend%20HDK/Ascend%20HDK%2025.5.2/Ascend-hdk-910b-npu-driver_25.5.2_linux-aarch64.run',
 'Ascend%20HDK/Ascend%20HDK%2025.5.2/Ascend-hdk-910b-npu-driver_25.5.2_linux-aarch64.run?response-content-type=application/octet-stream',
 'Ascend%20HDK/Ascend%20HDK%2025.5.2/Ascend-hdk-910b-npu-driver_25.5.2_linux-aarch64.run.asc',
 'Ascend%20HDK/Ascend%20HDK%2025.5.1/Ascend-hdk-910b-npu-driver_25.5.1_linux-aarch64.run',
]
def check(path):
 url=base+path
 try:
  with urllib.request.urlopen(urllib.request.Request(url,method='HEAD'),timeout=15) as response:
   return {'url':url,'status':response.status,'bytes':response.headers.get('Content-Length')}
 except urllib.error.HTTPError as e:return {'url':url,'status':e.code}
 except Exception as e:return {'url':url,'error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 print(json.dumps(list(pool.map(check,paths)),indent=2))
