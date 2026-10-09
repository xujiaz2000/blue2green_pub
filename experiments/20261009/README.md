# 2026-10-09：CANN 版本对比

同一 A2 主机、隔离四卡、vLLM 0.30.0、vllm-ascend `bbb5672`。各目录包含该轮实际日志和配置；统计条件与限制见报告。

| 模式 | 模型 | 结果与分析 | CPU 绑核证据 |
| --- | --- | --- | --- |
| MRV1 | BF16、W8A8 | [四组 CANN 对比及完整 profiling](mrv1/README.md) | [16 个 worker 主线程](mrv1/cpu-binding.md) |
| MRV2 | BF16、W8A8 | [四组 CANN 对比及 profiling 分析](mrv2/README.md) | [BF16 的 8 个 worker 主线程](mrv2/cpu-binding.md)；W8A8 证据在服务器留存 |
