#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

source "$SCRIPT_DIR/profile_env.sh" "${1:-w8a8}"
test -x "$AISBENCH"
CONFIG_DIR="$SCRIPT_DIR/configs"
MODEL_CONF=vllm_api_stream_chat_${MODEL_KIND}_simple
DATASET_CONF=gsm8k_gen_0_shot_cot_str_perf_simple
mkdir -p "$RUN_DIR"
curl --noproxy '*' -fsS --max-time 10 "http://127.0.0.1:${SERVER_PORT:-8007}/health" > /dev/null

touch "$RUN_DIR/warmup-complete"

echo 'Formal benchmark: 180 requests. Start profiling after actual generation begins.'
"$AISBENCH" --config-dir "$CONFIG_DIR" \
  --models "$MODEL_CONF" --datasets "$DATASET_CONF" \
  --mode perf --num-prompts 180 --num-warmups 1 --debug --work-dir "$RUN_DIR/aisbench-perf" \
  2>&1 | tee "$RUN_DIR/aisbench-perf.log"
