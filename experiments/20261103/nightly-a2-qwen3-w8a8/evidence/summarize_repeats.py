import json
import pathlib
import statistics

root = pathlib.Path(__file__).parent
folders = ['ci_pinned02','ci_pinned03','ci_pinned04']
rows = []
for folder in folders:
    result_path = root / folder / 'result.json'
    if not result_path.exists():
        continue
    result = json.loads(result_path.read_text(encoding='utf-8-sig'))
    if not result.get('measurement_valid'):
        raise ValueError('Invalid formal measurement ' + folder)
    metrics = result['formal_metrics']
    rows.append({'folder':folder, 'output_token_throughput':metrics['Output Token Throughput'],
                 'duration_ms':metrics['Benchmark Duration'],'mean_tpot_ms':metrics['TPOT'],
                 'mean_ttft_ms':metrics['TTFT'],'mean_e2el_ms':metrics['E2EL'],
                 'success_requests':metrics['Success Requests'],'failed_requests':metrics['Failed Requests'],
                 'input_tokens':metrics['Total Input Tokens'],'output_tokens':metrics['Total Generated Tokens'],
                 'verified_mrv2_ranks':result['model_runner_validation']['ranks_with_v2_load'],
                 'binding_failures':result['binding']['failed_logs']})
values = [row['output_token_throughput'] for row in rows]
mean = statistics.mean(values)
sd = statistics.stdev(values) if len(values) > 1 else None
summary = {'image':'sha256:51acbdd308d677c4add19eee604174fbc29eff784d46675968e82c8e1299b9df',
           'scope':'Local A2 only; the actual GitHub CI runner was not rerun',
           'cpu_policy':'Same 256-CPU host, 28 main CPUs per rank, unchanged ondemand governor; no manual clock lock',
           'n':len(values),'expected_n':3,'rows':rows,
           'statistics':{'mean':mean,'median':statistics.median(values),'min':min(values),'max':max(values),
                         'sample_sd':sd,'cv_percent':100 * sd / mean if sd is not None else None,
                         'range_percent_of_mean':100 * (max(values) - min(values)) / mean},
           'ci_single_reference':767.3497,'local_mean_above_ci_percent':100 * (mean / 767.3497 - 1),
           'target_802_passes':sum(value >= 802 for value in values),
           'original_user_gate_777_94_passes':sum(value >= 777.94 for value in values),
           'inference_limit':'Three local runs characterize local variability only. CI variability and the source of the cross-host gap remain unmeasured.'}
(root / 'repeat_summary.json').write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
