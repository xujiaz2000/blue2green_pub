#!/usr/bin/env bash
# Shared setup. Default model: w8a8. AISBench internal warmup: 1; no extra warmup benchmark.
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
export MODEL_KIND=${1:-w8a8}
case "$MODEL_KIND" in
  w8a8)
    export MODEL_PATH=${MODEL_PATH:-/workspace/models/w8a8}
    SERVED_MODEL_NAME=Eco-Tech/Qwen3-30B-A3B-w8a8
    QUANT_ARGS=(--quantization ascend)
    ;;
  bf16)
    export MODEL_PATH=${MODEL_PATH:-/root/.cache/modelscope/hub/models/Qwen/Qwen3-30B-A3B}
    SERVED_MODEL_NAME=Qwen/Qwen3-30B-A3B
    QUANT_ARGS=()
    ;;
  *) echo 'Choose w8a8 or bf16' >&2; return 1 ;;
esac
case "${ASCEND_HOME_PATH:-}" in
  *cann-9.1.0*) CANN_TAG=910 ;;
  *cann-9.2.0*) CANN_TAG=920 ;;
  *) echo 'Cannot identify CANN 9.1/9.2 from ASCEND_HOME_PATH' >&2; return 1 ;;
esac
export SERVER_PORT=${SERVER_PORT:-8007}
export NO_PROXY="localhost,127.0.0.1${NO_PROXY:+,$NO_PROXY}"
export no_proxy="$NO_PROXY"
AISBENCH=${AISBENCH:-/usr/local/python3.12.13/bin/ais_bench}
if [ ! -x "$AISBENCH" ]; then AISBENCH=$(command -v ais_bench || true); fi
STATE_DIR="$SCRIPT_DIR/.profile-runs"
STATE_FILE="$STATE_DIR/cann${CANN_TAG}-${MODEL_KIND}.current"
if [ "${2:-}" = start ]; then
  export RUN_DIR=${RUN_DIR:-$SCRIPT_DIR/results/${MODEL_KIND}-cann${CANN_TAG}-$(date +%Y%m%d-%H%M%S)}
  test -f "$MODEL_PATH/config.json"
  mkdir -p "$RUN_DIR/profiling" "$STATE_DIR"
  printf '%s\n' "$RUN_DIR" > "$STATE_FILE.tmp"
  mv "$STATE_FILE.tmp" "$STATE_FILE"
else
  if [ -z "${RUN_DIR:-}" ]; then
    if [ ! -f "$STATE_FILE" ]; then echo 'Run 01_start_server.sh for this model first' >&2; return 1; fi
    export RUN_DIR=$(cat "$STATE_FILE")
  fi
fi
printf 'MODEL=%s CANN=%s\nMODEL_PATH=%s\nRUN_DIR=%s\n' "$MODEL_KIND" "$CANN_TAG" "$MODEL_PATH" "$RUN_DIR"
