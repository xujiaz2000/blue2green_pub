# 2026-10-14：MRV2 关闭 CPU 绑核性能对比

[156 上 BF16 / W8A8 × CANN 9.1 / 9.2 四组结果与分析](mrv2/cpu-binding-off-156/README.md)

沿用 vLLM 0.30.0 和 bbb5672af 节点，仅将 enable_cpu_binding 改为 false；每组 180 请求和 1 秒 profiling。历史开启绑核数据来自同一 156 的 0–3 卡，跨日期及单次采样的限制详见报告。
