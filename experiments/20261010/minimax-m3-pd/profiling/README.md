# MiniMax M3 MRV1 / MRV2 Decode profiling

Captured on 2026-10-10 (Asia/Shanghai). Each archive contains **one Decode instance, decode-dp0**, with all four TP workers: original profiling data and parsed outputs.

| Runner | Capture start (Asia/Shanghai) | Workers | Download |
| --- | --- | --- | --- |
| MRV1 | 17:57:16 | 4 | [MRV1 DP0 archive](https://github.com/xujiaz2000/blue2green_pub/releases/download/minimax-m3-decode-profiling-20261010/minimax-m3-mrv1-decode-dp0-profiling.tar.gz) |
| MRV2 | 18:15:36 | 4 | [MRV2 DP0 archive](https://github.com/xujiaz2000/blue2green_pub/releases/download/minimax-m3-decode-profiling-20261010/minimax-m3-mrv2-decode-dp0-profiling.tar.gz) |

[Release](https://github.com/xujiaz2000/blue2green_pub/releases/tag/minimax-m3-decode-profiling-20261010) includes both archives and SHA256SUMS. Archives exceed GitHub's normal Git file size limit and are stored as Release assets.

## Capture

The service uses P DP2/TP4/PP2 and D DP4/TP4/PP1. Both rounds use the experiment environment documented in the [parent README](../README.md). Only the runner flag changed. Both dedicated containers were stopped before restarting MRV2.

AISBench generated load with concurrency 144, input length 131072, output length 1024 and prefix caching. Capture waited until all four D APIs had at least eight running requests, then invoked their start_profile endpoints in parallel, waited one second, and invoked stop_profile in parallel. The uploaded subset is DP0 only; capture-state.json records the full-service trigger state.

Each benchmark was intentionally stopped immediately after successful capture. No final performance result is expected, and these runs are separate from the earlier complete AISBench baselines.

## Open the data

~~~bash
sha256sum -c SHA256SUMS
tar -xzf minimax-m3-mrv1-decode-dp0-profiling.tar.gz
tar -xzf minimax-m3-mrv2-decode-dp0-profiling.tar.gz
~~~

Parsed files are under:

~~~text
mrv1/decode-dp0/*_ascend_pt/ASCEND_PROFILER_OUTPUT/
mrv2/decode-dp0/*_ascend_pt/ASCEND_PROFILER_OUTPUT/
~~~

All eight uploaded worker traces were validated: trace_view.json is readable and contains complete events; kernel_details.csv contains actual NPU operator records. Import trace_view.json into a trace viewer to inspect the timeline.

Per-run directories contain the capture trigger state, uploaded-worker validation records, effective Decode service script and profiling/analysis scripts.
