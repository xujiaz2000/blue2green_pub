#!/usr/bin/env python3
"""Run inside the Decode container, after stop_profile returns."""
import sys
from pathlib import Path

try:
    from torch_npu.profiler import analyse
except ImportError:
    from torch_npu.profiler.profiler import analyse

root = Path(sys.argv[1] if len(sys.argv) > 1 else
            "/mnt/share/z00943141/minimax_m3_performance_mrv2/profiling").resolve()
traces = [root] if root.name.endswith("_ascend_pt") else sorted(root.rglob("*_ascend_pt"))
traces = [path for path in traces if path.is_dir()]
if not traces:
    raise SystemExit(f"No *_ascend_pt directories found: {root}")
for trace in traces:
    print(f"Analyse: {trace}", flush=True)
    analyse(str(trace))
    output = trace / "ASCEND_PROFILER_OUTPUT"
    if not output.is_dir() or not any(output.iterdir()):
        raise SystemExit(f"No parsed output: {output}; check the analyser log.")
    print(f"Output: {output}", flush=True)
