#!/usr/bin/env bash
set -euo pipefail
[[ $# == 8 ]] || { echo "Expected 8 args: devices port dp rank ip rpc tp pp" >&2; exit 2; }
unset http_proxy https_proxy ftp_proxy
export VLLM_USE_V2_MODEL_RUNNER=0
profiling_dir="/mnt/share/z00943141/minimax_m3_performance_mrv2/profiling/mrv$((VLLM_USE_V2_MODEL_RUNNER + 1))/decode-dp$4"
mkdir -p "$profiling_dir"

nic_name="enp209s0f0"                                               # NIC corresponding to local_ip
local_ip="192.168.13.198"                                           # Decode node IP
model_path="/mnt/weight/MiniMax/Eco-Tech_MiniMax-M3-w8a8-0626"      # MiniMax-M3 model path
EAGLE3_WEIGHT_PATH="/mnt/share/weight/MiniMax-M3-EAGLE3-GQA"       # MiniMax-M3-EAGLE3-GQA path

export VLLM_SERVER_DEV_MODE=1

export HCCL_BUFFSIZE=2048
export HCCL_IF_IP=$local_ip
export HCCL_OP_EXPANSION_MODE="AIV"
export ASCEND_RT_VISIBLE_DEVICES=$1
export HCCL_SOCKET_IFNAME=$nic_name
export GLOO_SOCKET_IFNAME=$nic_name
export PYTORCH_NPU_ALLOC_CONF=expandable_segments:True

# If Mooncake is installed in a non-standard path, set this before startup.
if [ -n "${MOONCAKE_LIB_DIRS:-}" ]; then
    export LD_LIBRARY_PATH="${MOONCAKE_LIB_DIRS}:${LD_LIBRARY_PATH:-}"
fi

exec vllm serve "$model_path" \
    --host 0.0.0.0 \
    --port $2 \
    --profiler-config "{\"profiler\":\"torch\",\"torch_profiler_dir\":\"$profiling_dir\",\"torch_profiler_with_stack\":false,\"ignore_frontend\":true}" \
    --data-parallel-size $3 \
    --data-parallel-rank $4 \
    --data-parallel-address $5 \
    --data-parallel-rpc-port $6 \
    --tensor-parallel-size $7 \
    --pipeline-parallel-size $8 \
    --enable-expert-parallel \
    --seed 1024 \
    --served-model-name minimax-m3 \
    --reasoning-parser minimax_m3 \
    --distributed-executor-backend mp \
    --max-model-len 263000 \
    --max-num-batched-tokens 32768 \
    --trust-remote-code \
    --quantization ascend \
    --max-num-seqs 128 \
    --compilation-config '{"cudagraph_mode":"FULL_DECODE_ONLY"}' \
    --gpu-memory-utilization 0.92 \
    --limit-mm-per-prompt '{"image":1,"video":0}' \
    --language-model-only  \
    --additional-config '{"enable_cpu_binding":true,"ascend_compilation_config":{"fuse_norm_quant":false},"multistream_overlap_shared_expert":true,"weight_nz_mode":2,"enable_shared_expert_dp":true}' \
    --speculative-config '{"method":"eagle3","model":"/mnt/share/weight/MiniMax-M3-EAGLE3-GQA","num_speculative_tokens":3,"enforce_eager":false}' \
    --kv-transfer-config \
    '{
        "kv_connector":"MooncakeConnectorV1",
        "kv_role":"kv_consumer",
        "kv_port":"26100",
        "engine_id":"1",
        "kv_connector_extra_config":{
            "use_ascend_direct":true,
            "prefill":{"dp_size":2,"tp_size":4,"pp_size":2,"pp_layer_partition":"30,30"},
            "decode":{"dp_size":4,"tp_size":4,"pp_size":1}
        }
    }'
