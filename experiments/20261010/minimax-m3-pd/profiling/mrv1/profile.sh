#!/usr/bin/env bash
# Run on the Decode node while benchmark requests are in flight.
set -euo pipefail
BASE=/mnt/share/z00943141/minimax_m3_performance_mrv2
ports=("$@")
[[ $# != 0 ]] || ports=(31060 31061 31062 31063)
for port in "${ports[@]}"; do
    [[ "$port" =~ ^3106[0-3]$ ]] || { echo 'Use Decode ports 31060..31063.' >&2; exit 2; }
done
v2=$(sed -n 's/^export VLLM_USE_V2_MODEL_RUNNER=\([01]\)$/\1/p' "$BASE/serve_d.sh")
[[ "$v2" =~ ^[01]$ ]] || exit 2
runner=mrv$((v2 + 1))
mkdir -p "$BASE/logs/profiling/$runner"
log=$(mktemp "$BASE/logs/profiling/$runner/$(TZ=Asia/Shanghai date +%Y%m%d_%H%M%S)_XXXXXX.log")
exec > >(tee "$log") 2>&1

post() {
    local action=$1 pid failed=0
    local pids=()
    for port in "${ports[@]}"; do
        (curl --noproxy '*' -fsS --max-time 600 -X POST "http://localhost:$port/$action" &&
         echo "$port $action OK") &
        pids+=("$!")
    done
    for pid in "${pids[@]}"; do wait "$pid" || failed=1; done
    return "$failed"
}
trap 'post stop_profile || true' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
post start_profile
sleep 1
post stop_profile
trap - EXIT
echo "Profiling: $BASE/profiling/$runner; request log: $log"
