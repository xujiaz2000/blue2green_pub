$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$target = Get-Content -LiteralPath (Join-Path $root 'target_manifest.json') -Raw | ConvertFrom-Json -AsHashtable
$latest = Get-Content -LiteralPath (Join-Path $root 'pulled_image_audit.json') -Raw | ConvertFrom-Json -AsHashtable
$ci = Get-Content -LiteralPath (Join-Path $root 'ci_pinned_image_audit.json') -Raw | ConvertFrom-Json -AsHashtable
$repeatSummary = $(if (Test-Path -LiteralPath (Join-Path $root 'repeat_summary.json')) {Get-Content -LiteralPath (Join-Path $root 'repeat_summary.json') -Raw | ConvertFrom-Json -AsHashtable} else {$null})
$repeatState = $(if (Test-Path -LiteralPath (Join-Path $root 'repeat_state.json')) {Get-Content -LiteralPath (Join-Path $root 'repeat_state.json') -Raw | ConvertFrom-Json -AsHashtable} else {$null})
$packageComparison = foreach ($name in ($latest.packages.Keys | Sort-Object)) {
    [ordered]@{package=$name; latest=$latest.packages[$name]; pinned_ci=$ci.packages[$name]; equal=($latest.packages[$name] -eq $ci.packages[$name])}
}
$measurements = foreach ($folder in (Get-ChildItem -LiteralPath $root -Directory)) {
    $path = Join-Path $folder.FullName 'result.json'
    if (Test-Path -LiteralPath $path) {
        $data = Get-Content -LiteralPath $path -Raw | ConvertFrom-Json -AsHashtable
        [ordered]@{folder=$folder.Name; result=$data}
    }
}
$summary = [ordered]@{
    updated_utc = [DateTime]::UtcNow.ToString('o')
    remote = 'ubuntu@A2_LOCAL_HOST'
    remote_root = $target.remote_experiment_root
    user_choice = $target.execution_policy
    target_ci = $target.url
    ci_formal_metrics = $target.formal_metrics
    images = [ordered]@{
        latest = [ordered]@{digest=$target.latest_image_digest; ascend=$target.latest_image_ascend_sha; vllm=$target.vllm_sha}
        pinned_ci = [ordered]@{image=$target.historical_ci_arm64_image; ascend=$target.ascend_sha; vllm=$target.vllm_sha}
    }
    image_provenance = 'Pinned arm64 image published by build run 41318495994, job 124903756474 at 2026-11-01T16:07:48Z. Its commits and core package versions match the target test. The target job logs name the rolling tag and do not log its resolved digest.'
    package_comparison = @($packageComparison)
    all_python_package_differences = @(Get-Content -LiteralPath (Join-Path $root 'package_diff_all.json') -Raw | ConvertFrom-Json -AsHashtable)
    cann = 'Both images: 9.2.1 / V100R001C12SPC002B201'
    driver = $target.host_driver_installed
    cpu_comparison = [ordered]@{
        local = $target.local_cpu_resources
        ci = $target.ci_cpu_binding_observed
        local_quota = 'cpu.max=max 100000; nr_throttled=0; cpuset.cpus.effective=0-255'
    }
    protocol = [ordered]@{
        model = 'Eco-Tech/Qwen3-30B-A3B-w8a8'
        dataset = 'vllm-ascend/GSM8K-in3500-bs400'
        warmup_requests = 18
        formal_requests = 180
        client_concurrency = 45
        max_num_seqs = 16
        output_tokens_per_request = 1500
        expected_input_tokens = 656793
        expected_output_tokens = 270000
        temperature = 0
        ignore_eos = $true
        mrv2 = 'Default selection; require all four actual worker logs'
        cpu_binding = $true
        yaml_matches_ci = $true
        path_substitutions = '/inputs/model; /inputs/dataset (read-only mounts)'
        profiling = $false
    }
    measurements = @($measurements)
    repeat_summary = $repeatSummary
    repeat_state = $repeatState
    repeat_validation_file = 'repeat_validation.json'
    ci_local_differences_file = 'ci_local_differences.json'
    actual_request_comparison_file = 'actual_request_comparison.json'
    portable_ci_diagnostic_script = 'capture_ci_environment.py'
    final_state = $(if (Test-Path -LiteralPath (Join-Path $root 'final_state.json')) {Get-Content -LiteralPath (Join-Path $root 'final_state.json') -Raw | ConvertFrom-Json -AsHashtable} else {$null})
    conclusion = 'The low CI throughput was not reproduced locally. Three local CI-image runs produced 818.2533, 820.0483 and 827.4128 tok/s, mean 821.9048, sample CV 0.590551%, range/mean 1.114423%. All exceed 802. Their mean is 7.109549% above the single target CI result 767.3497. The observed local variation does not span the cross-environment gap; CI-side variability and the actual root cause remain unmeasured. No Ascend rollback was triggered.'
    device_setup_note = 'ci_pinned01 stopped during preflight with 0 visible NPUs. Stopping the completed latest-image container released device ownership; post4 then saw four 910B3 cards without package changes. Only one test container is active on NPU0-3 at a time.'
    input_identity_limit = 'All 180 actual CI request inputs, their order, and individual input/output token counts were compared with local ci_pinned02 and match. The CI used cached ModelScope master and did not publish weight hashes; historical cached weights remain unverified. Local repetitions use the same read-only weights, model metadata and dataset hashes.'
    historical_experiment = [ordered]@{
        url = 'https://github.com/xujiaz2000/blue2green_pub/blob/main/experiments/20261009/mrv2/repeats/README.md'
        ascend_sha = 'bbb5672af80b1972c301852aa505b13374fa6355'
        vllm_sha = 'ced6857afa0ea7b2e3f0846a62e1394e90f15607'
        mrv2_w8a8_cann920_values = @(814.4012, 811.9460, 812.7597)
        mrv2_w8a8_cann920_mean = 813.0356333333333
        comparison_limit = 'Reference only: different software versions and CANN release; these are three W8A8 repetitions, not all 12 mixed-model/CANN experiments.'
    }
    attribution_limit = 'Repeated local runs estimate local run-to-run variance only. The actual GitHub CI runner was not rerun. Different hardware/runtime resources remain material confounders; CI CPU governor, CPU/memory quotas, firmware and active frequencies require capture on that runner.'
}
$out = Join-Path $root 'reproduction_summary.json'
$summary | ConvertTo-Json -Depth 22 | Set-Content -LiteralPath $out -Encoding utf8
Write-Output $out
