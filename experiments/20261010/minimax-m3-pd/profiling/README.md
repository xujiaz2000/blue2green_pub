# MiniMax M3 MRV1 / MRV2 Decode profiling

Captured on 2026-10-10 (Asia/Shanghai). Full archives contain all four Decode instances (DP0-DP3), with four TP workers per instance: **16 workers per runner, 32 in total**. Both original profiling data and parsed outputs are included.

## Download

[Release and SHA256SUMS](https://github.com/xujiaz2000/blue2green_pub/releases/tag/minimax-m3-decode-profiling-20261010)

| Runner | Instances | Workers | Archive |
| --- | --- | --- | --- |
| MRV1 | DP0-DP3 | 16 | [All Decode instances, about 731 MiB](https://github.com/xujiaz2000/blue2green_pub/releases/download/minimax-m3-decode-profiling-20261010/minimax-m3-mrv1-decode-profiling.tar.gz) |
| MRV2 | DP0-DP3 | 16 | [All Decode instances, about 642 MiB](https://github.com/xujiaz2000/blue2green_pub/releases/download/minimax-m3-decode-profiling-20261010/minimax-m3-mrv2-decode-profiling.tar.gz) |
| MRV1 | DP0 only | 4 | [Previously uploaded DP0 archive](https://github.com/xujiaz2000/blue2green_pub/releases/download/minimax-m3-decode-profiling-20261010/minimax-m3-mrv1-decode-dp0-profiling.tar.gz) |
| MRV2 | DP0 only | 4 | [Previously uploaded DP0 archive](https://github.com/xujiaz2000/blue2green_pub/releases/download/minimax-m3-decode-profiling-20261010/minimax-m3-mrv2-decode-dp0-profiling.tar.gz) |

These archives exceed GitHub's normal Git file size limit and are stored as Release assets. The DP0-only archives are subsets of the full archives, not additional captures.

## Capture

| Runner | Capture trigger (Asia/Shanghai) | Running requests at trigger, DP0/1/2/3 |
| --- | --- | --- |
| MRV1 | 2026-10-10 17:57:16 | 9 / 8 / 8 / 8 |
| MRV2 | 2026-10-10 18:15:36 | 9 / 9 / 8 / 8 |

The service uses P DP2/TP4/PP2 and D DP4/TP4/PP1. Both rounds use the experiment environment documented in the [parent README](../README.md). Only the runner flag changed. Both dedicated containers were stopped before restarting MRV2.

AISBench was configured for concurrency 144, input length 131072, output length 1024 and prefix caching. Capture started after service warmup and prefix-cache warmup, during the formal benchmark stage. It waited until all four D APIs had at least eight running requests, invoked start_profile in parallel, waited one second after those calls succeeded, then invoked stop_profile in parallel.

The workload was still ramping up at capture time; this was not a verified steady 144-concurrency interval. Actual worker trace spans can exceed one second due to API, worker and device timing. These captures can diagnose the observed execution paths, but should not alone establish a steady-state performance comparison.

Each benchmark was intentionally stopped after successful capture. No final performance result is expected; these runs are separate from the earlier complete AISBench baselines.

## Extract and inspect

Download the two full archives and SHA256SUMS from the Release. Verify each downloaded archive:

~~~bash
grep '  minimax-m3-mrv1-decode-profiling.tar.gz$' SHA256SUMS | sha256sum -c -
grep '  minimax-m3-mrv2-decode-profiling.tar.gz$' SHA256SUMS | sha256sum -c -
tar -xzf minimax-m3-mrv1-decode-profiling.tar.gz
tar -xzf minimax-m3-mrv2-decode-profiling.tar.gz
~~~

Parsed files are under:

~~~text
mrv1/decode-dp{0,1,2,3}/*_ascend_pt/ASCEND_PROFILER_OUTPUT/
mrv2/decode-dp{0,1,2,3}/*_ascend_pt/ASCEND_PROFILER_OUTPUT/
~~~

All 32 worker traces were validated: trace_view.json is readable and contains complete events; kernel_details.csv contains actual NPU operator records. Import the worker trace_view.json files into a trace viewer to inspect timelines.

Per-run directories contain all-workers.json (all 16 workers), validated_workers.json (the original DP0 subset), the capture trigger state, effective Decode service script and profiling/analysis scripts.
