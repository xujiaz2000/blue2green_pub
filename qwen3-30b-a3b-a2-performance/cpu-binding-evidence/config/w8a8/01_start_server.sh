#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

source "$SCRIPT_DIR/profile_env.sh" "${1:-w8a8}" start

export ASCEND_RT_VISIBLE_DEVICES=${ASCEND_RT_VISIBLE_DEVICES:-0,1,2,3}
export HCCL_BUFFSIZE=512
export HCCL_OP_EXPANSION_MODE=AIV
export LD_PRELOAD=/usr/lib/aarch64-linux-gnu/libjemalloc.so.2
export NPU_MEMORY_FRACTION=0.95
export OMP_NUM_THREADS=1
export OMP_PROC_BIND=false
export PYTORCH_NPU_ALLOC_CONF=expandable_segments:True
export TASK_QUEUE_ENABLE=1
export VLLM_ASCEND_ENABLE_NZ=2
export VLLM_USE_V1=1
export VLLM_USE_V2_MODEL_RUNNER=0
export VLLM_LOG_STATS_INTERVAL=10
vllm serve "$MODEL_PATH" \
  --served-model-name "$SERVED_MODEL_NAME" \
  --host 127.0.0.1 --port "$SERVER_PORT" \
  --async-scheduling --tensor-parallel-size 4 \
  --max-num-seqs 16 --max-model-len 16384 \
  --max-num-batched-tokens 16384 --gpu-memory-utilization 0.9 \
  --trust-remote-code "${QUANT_ARGS[@]}" \
  --additional-config '{"enable_cpu_binding":true}' \
  --compilation-config '{"cudagraph_mode":"FULL_DECODE_ONLY","cudagraph_capture_sizes":[1,2,4,8,16]}' \
  --profiler-config "{\"profiler\":\"torch\",\"torch_profiler_dir\":\"${RUN_DIR}/profiling\",\"torch_profiler_with_stack\":false,\"torch_profiler_with_memory\":false,\"ignore_frontend\":true,\"delay_iterations\":0,\"max_iterations\":0}" \
  2>&1 | tee "$RUN_DIR/server.log"
