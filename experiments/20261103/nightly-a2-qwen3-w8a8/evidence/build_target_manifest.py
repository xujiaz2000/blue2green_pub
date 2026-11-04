import importlib.util,json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parent
source=ROOT/'ci_job_124914290773.txt'
text=source.read_text(encoding='utf-8-sig')
spec=importlib.util.spec_from_file_location('prior_runner',ROOT.parent/'reproduction/kit/inside_runner.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
metrics=mod.parse_formal_metrics(text)
commits=re.findall(r'Z Commit hash:\s*([0-9a-f]{40})',text)
record={'source_run':41327490550,'source_job':124914290773,
 'url':'https://github.com/vllm-project/vllm-ascend/actions/runs/41327490550/job/124914290773',
 'vllm_sha':commits[0],'ascend_sha':commits[1],
 'cann_version':re.search(r'Z version=(\S+)',text).group(1),
 'cann_innerversion':re.search(r'Z innerversion=(\S+)',text).group(1),
 'torch_npu_version_observed':re.search(r"torch_npu_version': '([^']+)'",text).group(1),
 'image_requested':'swr.cn-north-12.myhuaweicloud.com/base_image/ascend-ci/vllm-ascend:nightly-ci-main-a2',
 'container_requested':'z00943141_qwen3_nightly_test','remote':'ubuntu@A2_LOCAL_HOST',
 'formal_metrics':metrics,'rollback_ascend_sha':'bbb5672af80b1972c301852aa505b13374fa6355',
 'rollback_condition':'Only if local current-CI environment reproduces the low throughput; freeze vLLM, CANN, dependencies, model, request protocol and resources',
 'mr_version':'MRV2 default; require four actual worker load paths',
 'remote_runs_started':0}
assert record['cann_version']=='9.2.1'
assert metrics['Output Token Throughput']==767.3497
(ROOT/'target_manifest.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(record,ensure_ascii=False,indent=2))
