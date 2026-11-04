import json,torch,torch_npu
print(json.dumps({'torch':torch.__version__,'torch_npu':torch_npu.__version__,
 'visible_count':torch.npu.device_count(),
 'names':[torch.npu.get_device_name(i) for i in range(torch.npu.device_count())]}))
