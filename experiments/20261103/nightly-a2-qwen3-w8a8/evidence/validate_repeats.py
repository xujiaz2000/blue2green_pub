import hashlib
import json
import os
import pathlib
import re
import statistics

root = pathlib.Path(__file__).parent
base = json.loads((root / 'ci_pinned02/environment.json').read_text(encoding='utf-8-sig'))
checks = []
def affinities(folder):
    text = (root / folder / 'pytest.log').read_text(encoding='utf-8-sig')
    return {rank:[int(value) for value in cpus.split()]
            for rank,cpus in re.findall(r'NPU(\d+): main=\[([0-9 ]+)\]', text)}

base_affinities = affinities('ci_pinned02')
for name in ['ci_pinned02','ci_pinned03','ci_pinned04']:
    path = root / name / 'environment.json'
    if not path.exists():
        continue
    environment = json.loads(path.read_text(encoding='utf-8-sig'))
    packages = json.loads(environment['commands']['pip_list']['stdout'])
    baseline_packages = json.loads(base['commands']['pip_list']['stdout'])
    package_versions = {entry['name']:entry['version'] for entry in packages}
    baseline_versions = {entry['name']:entry['version'] for entry in baseline_packages}
    result = json.loads((root / name / 'result.json').read_text(encoding='utf-8-sig'))
    checks.append({'folder':name,'package_versions_equal':package_versions == baseline_versions,
                   'native_extension_hashes_equal':environment['native_extensions'] == base['native_extensions'],
                   'model_config_metadata_hashes_equal':environment['model_metadata'] == base['model_metadata'],
                   'dataset_file_hashes_equal':environment['dataset_files'] == base['dataset_files'],
                   'vllm_sha_equal':environment['repositories']['vllm']['stdout'] == base['repositories']['vllm']['stdout'],
                   'ascend_sha_equal':environment['repositories']['ascend']['stdout'] == base['repositories']['ascend']['stdout'],
                   'tracked_sources_clean':all(item['tracked_clean'] for item in environment['repositories'].values()),
                   'measurement_valid':result['measurement_valid'],
                   'all_requests_succeeded':result['formal_metrics']['Success Requests'] == 180 and result['formal_metrics']['Failed Requests'] == 0,
                   'four_mrv2_workers':result['model_runner_validation']['ranks_with_v2_load'] == [0,1,2,3],
                   'cpu_allocation_equal':affinities(name) == base_affinities,
                   'binding_failure_count':result['binding']['failed_logs']})

def records(folder):
    path = root / folder / 'aisbench_details.jsonl'
    return {item['id']:item for line in path.read_text(encoding='utf-8-sig').splitlines()
            if line.strip() for item in [json.loads(line)]}

comparisons = []
left = records('ci_pinned02')
for name in ['ci_pinned03','ci_pinned04']:
    if not (root / name / 'aisbench_details.jsonl').exists():
        continue
    right = records(name)
    mismatches = [key for key, row in left.items() if row['input'] != right[key]['input']]
    identical = sum(row['prediction'] == right[key]['prediction'] for key,row in left.items())
    prefixes = [len(os.path.commonprefix([row['prediction'],right[key]['prediction']])) for key,row in left.items()]
    comparisons.append({'against':name,'n':len(left),'input_mismatch_ids':mismatches,
                        'identical_full_predictions':identical,
                        'median_common_prediction_prefix_chars':statistics.median(prefixes)})
policy_checks = []
before_host = json.loads((root / 'repeats_before_host_snapshot.json').read_text(encoding='utf-8-sig'))
def policies(data):
    return {name:{key:value for key,value in info.items() if key != 'scaling_cur_freq'}
            for name,info in data['cpu_frequency'].items()}
for path in sorted(root.glob('ci_pinned0*_after_host_snapshot.json')):
    snapshot = json.loads(path.read_text(encoding='utf-8-sig'))
    policy_checks.append({'snapshot':path.name,'governor_and_frequency_limits_unchanged':policies(snapshot) == policies(before_host)})
report = {'environment_checks':checks,'cpu_policy_checks':policy_checks,'local_generation_comparison':comparisons,
          'last_run_shutdown_note':'ci_pinned04 formal results saved at 11:25:43.641 UTC and benchmark finished before 11:25:46 UTC. The test then triggered mode=abort shutdown and killed EngineCore; the output-handler EngineDeadError was logged during that teardown. All 180 requests had completed successfully.',
          'note':'Package/native extension hashes, model configuration metadata and dataset contents were checked. Historical CI weight bytes remain unverified; local rounds use the same read-only model files.'}
(root / 'repeat_validation.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
