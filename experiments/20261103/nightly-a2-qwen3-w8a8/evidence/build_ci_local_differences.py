import json
import pathlib
import re

root = pathlib.Path(__file__).parent
ci_log = (root / 'ci_job_124914290773.txt').read_text(encoding='utf-8-sig')
local = json.loads((root / 'ci_pinned02/environment.json').read_text(encoding='utf-8-sig'))
host = json.loads((root / 'repeats_before_host_snapshot.json').read_text(encoding='utf-8-sig'))
requests = json.loads((root / 'actual_request_comparison.json').read_text(encoding='utf-8-sig'))

def temperatures(text):
    result = {}
    for line in text.splitlines():
        match = re.search(r'\|\s*([0-3])\s+910B3\s*\|\s*OK\s*\|\s*[\d.]+\s+(\d+)\s+', line)
        if match and match[1] not in result:
            result[match[1]] = int(match[2])
    return result

comparison = {
    'comparison_scope':'Actual target CI job 124914290773 versus local CI-version pinned image run ci_pinned02 and its repetitions. The separate latest-tag run has additional software-version differences.',
    'ci_source':'https://github.com/vllm-project/vllm-ascend/actions/runs/41327490550/job/124914290773',
    'confirmed_differences':[
        {'item':'Worker CPU affinity', 'ci':'20 main CPUs per rank', 'local':'28 main CPUs per rank',
         'evidence':'Four cpu_binding.py allocation records in both pytest logs; local /proc snapshots verify applied affinities'},
        {'item':'Container orchestration', 'ci':'GitHub Actions job container via /home/runner/k8s/index.js hooks',
         'local':'Docker 29.1.3 standalone container, host networking, non-privileged, explicit device/driver mounts',
         'impact':'CI Pod resource limits, CPU weight, seccomp/capabilities and neighboring workloads are not captured by the CI log'},
        {'item':'Driver device exposure', 'ci':'npu-smi initially lists 8 physical 910B3 cards',
         'local':'Measurement container exposes only physical cards 0-3 plus manager/SVM/HDC devices',
         'same':'Both serve with ASCEND_RT_VISIBLE_DEVICES=0,1,2,3 and TP=4'},
        {'item':'Pre-test NPU temperature in Celsius', 'ci':temperatures(ci_log),
         'local':temperatures(local['commands']['npu_smi']['stdout']),
         'impact':'These are pre-test snapshots; they do not establish active frequencies or thermal throttling'},
        {'item':'Model and data storage', 'ci':'Existing ModelScope master cache under /root/.cache/modelscope',
         'local':'Freshly downloaded snapshot in experiment-specific NFS directory, mounted read-only under /inputs',
         'same':'All 180 actual input messages, order, per-request input/output token counts match',
         'unverified':'CI did not publish weight-file hashes; historical cached weights are not byte-verified'},
        {'item':'Compile-cache placement', 'ci':'Default image cache under /root/.cache/vllm and default Triton/Inductor settings',
         'local':'A separate /results/<run>/cache directory per round for vLLM, Triton and TorchInductor',
         'same':'Each round starts a fresh service, captures the same decode graph sizes, and executes 18-request warmup before 180 formal requests',
         'unverified':'Global CANN and filesystem cache contents are not made byte-identical'},
        {'item':'Runtime preparation and metadata', 'ci':'Installs uv 0.13.6, MAX_JOBS=184, CI runner/job labels, proxy and CA bundle environment',
         'local':'uv absent from original pinned image; local runner/job labels, no CI proxy setup',
         'same':'Core inference package versions match. Actual AISBench request target is localhost in both cases'},
        {'item':'Logging and outputs', 'ci':'pytest stdout is piped through tee and GitHub Actions log collection',
         'local':'pytest stdout is redirected to an experiment log file; local AISBench artifacts remain in the container'},
        {'item':'Run identifiers and paths', 'details':requests['configuration_differences'],
         'same':'No unexpected AISBench configuration difference after excluding timestamps, paths, served model name and port'},
        {'item':'Generated text', 'identical_full_predictions':requests['identical_prediction_count'], 'n':180,
         'common_prefix_chars':requests['prediction_common_prefix_chars'],
         'same':'Each response still contains 1500 generated tokens',
         'unverified':'Batch composition, numerical nondeterminism and cached weight identity remain possible explanations; output text alone does not identify which applies',
         'local_control':'Two local rounds with the same read-only weights and identical package/native-extension hashes also have 0/180 byte-identical full predictions; their throughput differs by about 0.22%'},
    ],
    'confirmed_matching_conditions':{
        'vllm':'5df63a7203cdb9328d824a27b682e77c7b9928be / 0.32.0+empty',
        'ascend':'b3b82c137ee242a774c29b56325133771f5f069d',
        'cann':'9.2.1 / V100R001C12SPC002B201','driver_version':'25.5.2','npu_model':'910B3',
        'torch':'2.10.0+cpu','torch_npu':'2.10.0.post4','triton_ascend':'3.2.2',
        'model_runner':'Actual MRV2 on all four worker ranks','tensor_parallel':4,'max_num_seqs':16,
        'max_model_len':16384,'max_batched_tokens':16384,'cpu_binding':True,
        'decode_graph_sizes':[1,2,4,8,16],'decode_graph_mode':'FULL_DECODE_ONLY',
        'client_concurrency':45,'formal_requests':180,'temperature':0,'ignore_eos':True,
        'total_input_tokens':656793,'total_output_tokens':270000,'profiling_enabled':False,
        'actual_request_input_mismatches':len(requests['input_mismatch_ids'])},
    'unknown_ci_fields_and_local_observations':{
        'host_kernel':{'ci':'not logged','local':host['commands']['uname']['stdout'].strip()},
        'cpu_model_and_memory':{'ci':'not logged','local':'Kunpeng-920, 4 sockets x 64 cores, 8 NUMA nodes; about 2 TiB memory'},
        'cpu_governor':{'ci':'not logged','local':'ondemand, 200000-3000000 kHz permitted; no manual frequency lock'},
        'npu_firmware':{'ci':'not logged','local':'7.8.0.6.201'},
        'cpu_quota_and_throttling':{'ci':'not logged','local':'cpu.max=max 100000, 0-255 effective cpuset, no throttling observed'},
        'numa_physical_page_placement':{'ci':'not captured','local':'Affinity verified; physical page migration not verified'},
        'active_npu_frequency_power_limits':{'ci':'not logged','local':'Not sampled during timed formal runs'},
        'host_workload_contention':{'ci':'NPU idle at initial snapshot; host CPU and memory competition unmeasured',
                                    'local':'NPU0-3 idle before each round; no CPU quota throttling observed'}},
    'separate_latest_image_comparison':json.loads((root / 'package_diff_all.json').read_text(encoding='utf-8-sig')),
    'conclusion_limit':'Confirmed differences are not established root causes. Repeated local tests estimate local variance only; the actual CI runner needs the same read-only capture to close the remaining gaps.'}
(root / 'ci_local_differences.json').write_text(json.dumps(comparison, ensure_ascii=False, indent=2))
print(json.dumps({'confirmed_difference_categories':len(comparison['confirmed_differences']),
                  'request_input_mismatches':len(requests['input_mismatch_ids']),
                  'ci_initial_temperatures':temperatures(ci_log),
                  'local_initial_temperatures':temperatures(local['commands']['npu_smi']['stdout'])}, indent=2))
