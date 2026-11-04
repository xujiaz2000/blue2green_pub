import json,pathlib,time,traceback
from modelscope import snapshot_download
root=pathlib.Path('/results/inputs');root.mkdir(parents=True,exist_ok=True)
state={'started_at':time.time(),'model_id':'Eco-Tech/Qwen3-30B-A3B-w8a8','dataset_id':'vllm-ascend/GSM8K-in3500-bs400'}
def save():
 (root/'download_status.json').write_text(json.dumps(state,indent=2))
 print(json.dumps(state),flush=True)
try:
 state['phase']='dataset';save()
 state['dataset_path']=snapshot_download(state['dataset_id'],repo_type='dataset',cache_dir=str(root/'modelscope'),max_workers=4)
 save()
 state['phase']='model';save()
 state['model_path']=snapshot_download(state['model_id'],cache_dir=str(root/'modelscope'),max_workers=8)
 state['phase']='complete';state['finished_at']=time.time();save()
except Exception as error:
 state['phase']='error';state['error']=str(error);save();traceback.print_exc();raise
