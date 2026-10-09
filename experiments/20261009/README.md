# 2026-10-09：MRV1 / MRV2 × BF16 / W8A8 × CANN 9.1 / 9.2 完整对比

## MRV2 三轮重复稳定性复测

新增 12 组正式 profiling 实验，以下统计只包含新三轮；原八组单轮结果保留在后文。完整每轮指标、同轮 CANN 差异和 12 份日志见 [重复实验报告](mrv2/repeats/README.md)。

| 模型 | CANN | 三轮均值 token/s | 样本标准差 | CV | 最小 / 最大 | 达标次数 |
| --- | --- | ---: | ---: | ---: | --- | ---: |
| BF16 | cann910 | 807.1498 | 1.0987 | 0.14% | 806.1744 / 808.3401 | 3/3 |
| BF16 | cann920 | 801.2234 | 1.6211 | 0.20% | 799.3618 / 802.3243 | 3/3 |
| W8A8 | cann910 | 820.6118 | 5.0336 | 0.61% | 817.3749 / 826.4111 | 3/3 |
| W8A8 | cann920 | 813.0356 | 1.2506 | 0.15% | 811.9460 / 814.4012 | 3/3 |

每组合仅三次、均包含 1 秒 profiling；标准差使用 n−1，CV 描述本批次离散程度，不能代表长期稳定性。

同一 Ascend A2 主机、隔离物理卡 0–3、同一历史 main 节点和 vLLM 0.30.0，共八组正式 profiling 测试。每组 180 请求全部成功、失败 0，生成 270000 tokens；每组稳定 decode 阶段采约 1 秒 profiling，四个 TP rank 均已解析。

**观测结果：MRV2 的四组吞吐均高于同模型、同 CANN 的 MRV1；CANN 9.2 相对 9.1 的差距在 BF16 中从 -1.63% 缩小为 -0.17%，在 W8A8 中从 -2.09% 缩小为 -1.35%。MRV1 的两个 CANN 9.2 观测值低于原 CI 下限，MRV2 四组均超过。**

## 八组输出吞吐与达标情况

| 运行器 | 模型 | CANN | 输出吞吐 token/s | TPOT ms | 相对本模型同运行器 9.1 | 达到 CI 下限 | 最终结果日志 |
| --- | --- | --- | ---: | ---: | ---: | --- | --- |
| MRV1 | BF16 | 9.1 | 781.8579 | 19.1 | +0.00% | 是 | [AISBench](mrv1/logs/bf16-cann910-aisbench-final-result.log) |
| MRV1 | BF16 | 9.2 | 769.1510 | 19.5 | -1.63% | 否 | [AISBench](mrv1/logs/bf16-cann920-aisbench-final-result.log) |
| MRV1 | W8A8 | 9.1 | 791.6250 | 18.7 | +0.00% | 是 | [AISBench](mrv1/logs/w8a8-cann910-aisbench-final-result.log) |
| MRV1 | W8A8 | 9.2 | 775.0892 | 19.1 | -2.09% | 否 | [AISBench](mrv1/logs/w8a8-cann920-aisbench-final-result.log) |
| MRV2 | BF16 | 9.1 | 800.3532 | 18.6 | +0.00% | 是 | [AISBench](mrv2/logs/bf16-cann910-aisbench-final-result.log) |
| MRV2 | BF16 | 9.2 | 799.0187 | 18.6 | -0.17% | 是 | [AISBench](mrv2/logs/bf16-cann920-aisbench-final-result.log) |
| MRV2 | W8A8 | 9.1 | 824.7901 | 17.9 | +0.00% | 是 | [AISBench](mrv2/logs/w8a8-cann910-aisbench-final-result.log) |
| MRV2 | W8A8 | 9.2 | 813.6934 | 18.2 | -1.35% | 是 | [AISBench](mrv2/logs/w8a8-cann920-aisbench-final-result.log) |

输出吞吐取 AISBench Common Metric 中的 **Output Token Throughput = Total Generated Tokens / Benchmark Duration（秒）**，不是逐请求 OutputTokenThroughput 的平均值。性能轮包含 profiler 开关和导出开销，达标标注仅表示观测值达到相同 YAML 下限，不等价于无 profiler CI 的复验。

## MRV2 相对 MRV1 的变化

| 模型 | CANN | MRV1 token/s | MRV2 token/s | 吞吐变化 | TPOT：MRV1 → MRV2 |
| --- | --- | ---: | ---: | ---: | --- |
| BF16 | 9.1 | 781.8579 | 800.3532 | +2.37% | 19.1 ms → 18.6 ms |
| BF16 | 9.2 | 769.1510 | 799.0187 | +3.88% | 19.5 ms → 18.6 ms |
| W8A8 | 9.1 | 791.6250 | 824.7901 | +4.19% | 18.7 ms → 17.9 ms |
| W8A8 | 9.2 | 775.0892 | 813.6934 | +4.98% | 19.1 ms → 18.2 ms |

| 模型 | MRV1：9.2 相对 9.1 | MRV2：9.2 相对 9.1 | 版本差距缩小 |
| --- | ---: | ---: | ---: |
| BF16 | -1.63% | -0.17% | 1.46 个百分点 |
| W8A8 | -2.09% | -1.35% | 0.74 个百分点 |

这里记录的是顺序执行、每环境一次的实际观测差异。源码、权重和对应请求协议保持一致；未做交错重复测量，不能排除时间与宿主机 CPU/IO 负载波动。

## 历史 CI 依据

| 模型 | 原始 MRV1 CI | CI 吞吐 token/s | baseline × threshold | 达标下限 token/s |
| --- | --- | ---: | --- | ---: |
| BF16 | [job 108372470704](https://github.com/vllm-project/vllm-ascend/actions/runs/36225208422/job/108372470704) | 783.3198 | 802.4382 × 0.97 | 778.365054 |
| W8A8 | [job 108372470597](https://github.com/vllm-project/vllm-ascend/actions/runs/36225208422/job/108372470597) | 784.1192 | 805.872 × 0.97 | 781.695840 |

CI 日志实际执行的 vllm-ascend 为 `bbb5672af80b1972c301852aa505b13374fa6355`，属于 main 历史节点；workflow HEAD `eb31db4d75622a8043703d2cbb55e9df75e70f98` 与实际推理源码不同。本轮使用实际推理源码节点。历史 CI 使用 MRV1，未开启本轮这种手动 profiling。

## 控制条件与运行器差异

| 项目 | 八组共同配置 / 按模型配置 |
| --- | --- |
| 主机 / 硬件 / 驱动 | 192.168.9.156；Ascend 910B3、单卡 HBM 64 GB；驱动 25.5.1 |
| 隔离 | 非特权 Ascend runtime 容器仅可见物理 NPU 0–3；npu-smi 只显示四卡，torch.npu.device_count()=4 |
| vllm-ascend | bbb5672af80b1972c301852aa505b13374fa6355 |
| vLLM | ced6857afa0ea7b2e3f0846a62e1394e90f15607，0.30.0+empty |
| 运行器开关 | MRV1：VLLM_USE_V2_MODEL_RUNNER=0；MRV2：=1，实际四个 worker 的 V2 专用加载日志已确认 |
| 图模式 | 非 eager；FULL_DECODE_ONLY，capture sizes=[1,2,4,8,16] |
| 并行与调度 | TP4，async scheduling，max-num-seqs=16 |
| 长度 / 显存 | max-model-len=max-num-batched-tokens=16384，gpu-memory-utilization=0.9 |
| CPU / 环境变量 | enable_cpu_binding=true；HCCL、NZ、OMP 等参数沿用相同模型 CI 配置 |
| 服务端口 / 日志间隔 | 8007 / 10 秒 |
| 数据 / 客户端 | GSM8K-in3500-bs400，AISBench streaming chat |
| 正式请求 | 180；batch_size=45、request_rate=0、temperature=0、ignore_eos=true、max_out_len=1500 |
| BF16 预热 | 只有 perf：内部预热 1 请求后，正式 180 请求 |
| W8A8 预热 | 先 perf-warm 18 请求，再 perf 180 请求；两次 AISBench 调用各内部预热 1 请求 |
| Profiling | torch / torch_npu，ignore_frontend=true；稳定 decode（prompt=0、Running=16）时 start → 等待约 1 秒 → stop |
| 服务与缓存 | 每组冷启动、独立 vLLM/Triton 缓存目录；组内预热与正式轮共用服务；组后停服务，再启动下一组 |

BF16 为 Qwen/Qwen3-30B-A3B，dtype=bfloat16、无量化，权重位于 `/mnt/share/z00943141/qwen-a2-profiling-kit-20261008-022415/models/bf16`。W8A8 为 Eco-Tech/Qwen3-30B-A3B-w8a8，w8a8_dynamic、`--quantization ascend`，权重位于 `/mnt/share/z00943141/qwen-a2-profile-work/models/w8a8`。同一模型的四组实验共用只读权重。BF16 和 W8A8 的预热协议不同，两模型间差异不能单独归因于量化。

MRV2 使用对应 CANN 的已编译镜像，沿用相同历史节点的 native 扩展及同范围自定义算子；服务脚本相对对应 MRV1 仅把运行器开关从 0 改为 1，其他脚本与客户端配置按 SHA256 核对。推理源码、核心 Python 包未改变；各组 Ascend 4280 个、vLLM 7159 个 tracked 文件与 HEAD blob 哈希均一致。两套 native 产物分别使用各自 CANN 构建，未覆盖完整历史 CI 所有模型算子，不宣称镜像所有编译产物与 CI 完全相同。

| 包 | 八组版本 |
| --- | --- |
| vllm | 0.30.0+empty |
| vllm_ascend | 0.19.1rc2.dev2433+gbbb5672af |
| torch | 2.10.0+cpu |
| torch_npu | 2.10.0.post4 |
| triton_ascend | 3.2.2 |
| transformers | 5.14.1 |
| ais_bench_benchmark | 3.1.20260609 |

| CANN 组件 | 9.1 版本 / 构建标记 | 9.2 版本 / 构建标记 |
| --- | --- | --- |
| runtime | 9.1.0 / 20260730_231653901 | 9.2.0 / 20260930_161523958 |
| ops_transformer | 9.1.0 / 20260730_231653901 | 9.2.0 / 20260930_161523958 |
| ops_legacy | 9.1.0 / 20260730_231653901 | 9.2.0 / 20260930_161523958 |
| bisheng-compiler | 9.1.0 / 20260730_231653901 | 9.2.0 / 20260930_161523958 |

## 完整 AISBench 指标

逐请求指标以下列均值对比；完整 min/max/median/P75/P90/P99 见文末。所有值直接取各组最终 AISBench 日志。

### BF16

| 指标 | MRV1 / 9.1 | MRV1 / 9.2 | MRV2 / 9.1 | MRV2 / 9.2 |
| --- | ---: | ---: | ---: | ---: |
| E2EL | 76588.5 ms | 77741.7 ms | 74355.4 ms | 74435.9 ms |
| TTFT | 47887.7 ms | 48585.7 ms | 46482.5 ms | 46533.3 ms |
| TPOT | 19.1 ms | 19.5 ms | 18.6 ms | 18.6 ms |
| ITL | 19.1 ms | 19.4 ms | 18.6 ms | 18.6 ms |
| InputTokens | 3648.85 | 3648.85 | 3648.85 | 3648.85 |
| OutputTokens | 1500.0 | 1500.0 | 1500.0 | 1500.0 |
| OutputTokenThroughput | 21.7709 token/s | 21.4668 token/s | 22.4297 token/s | 22.4063 token/s |
| Benchmark Duration | 345331.3016 ms | 351036.385 ms | 337351.0656 ms | 337914.4863 ms |
| Total Requests | 180 | 180 | 180 | 180 |
| Failed Requests | 0 | 0 | 0 | 0 |
| Success Requests | 180 | 180 | 180 | 180 |
| Concurrency | 39.9209 | 39.8634 | 39.6737 | 39.6504 |
| Max Concurrency | 45 | 45 | 45 | 45 |
| Request Throughput | 0.5212 req/s | 0.5128 req/s | 0.5336 req/s | 0.5327 req/s |
| Total Input Tokens | 656793 | 656793 | 656793 | 656793 |
| Prefill Token Throughput | 76.1959 token/s | 75.1014 token/s | 78.4994 token/s | 78.4137 token/s |
| Total Generated Tokens | 270000 | 270000 | 270000 | 270000 |
| Input Token Throughput | 1901.9214 token/s | 1871.0112 token/s | 1946.9125 token/s | 1943.6663 token/s |
| Output Token Throughput | 781.8579 token/s | 769.151 token/s | 800.3532 token/s | 799.0187 token/s |
| Total Token Throughput | 2683.7793 token/s | 2640.1622 token/s | 2747.2657 token/s | 2742.685 token/s |
| 最终 Prefix cache hit rate | 0.5% | 0.5% | 0.5% | 0.5% |

### W8A8

| 指标 | MRV1 / 9.1 | MRV1 / 9.2 | MRV2 / 9.1 | MRV2 / 9.2 |
| --- | ---: | ---: | ---: | ---: |
| E2EL | 74696.3 ms | 76255.8 ms | 71679.3 ms | 72702.6 ms |
| TTFT | 46640.3 ms | 47588.0 ms | 44790.1 ms | 45417.5 ms |
| TPOT | 18.7 ms | 19.1 ms | 17.9 ms | 18.2 ms |
| ITL | 18.7 ms | 19.1 ms | 17.9 ms | 18.2 ms |
| InputTokens | 3648.85 | 3648.85 | 3648.85 | 3648.85 |
| OutputTokens | 1500.0 | 1500.0 | 1500.0 | 1500.0 |
| OutputTokenThroughput | 22.585 token/s | 22.128 token/s | 23.5517 token/s | 23.2061 token/s |
| Benchmark Duration | 341070.5729 ms | 348347.0195 ms | 327356.0314 ms | 331820.3049 ms |
| Total Requests | 180 | 180 | 180 | 180 |
| Failed Requests | 0 | 0 | 0 | 0 |
| Success Requests | 180 | 180 | 180 | 180 |
| Concurrency | 39.421 | 39.4034 | 39.4136 | 39.4384 |
| Max Concurrency | 45 | 45 | 45 | 45 |
| Request Throughput | 0.5278 req/s | 0.5167 req/s | 0.5499 req/s | 0.5425 req/s |
| Total Input Tokens | 656793 | 656793 | 656793 | 656793 |
| Prefill Token Throughput | 78.2339 token/s | 76.6758 token/s | 81.4655 token/s | 80.3402 token/s |
| Total Generated Tokens | 270000 | 270000 | 270000 | 270000 |
| Input Token Throughput | 1925.6806 token/s | 1885.4561 token/s | 2006.3568 token/s | 1979.3635 token/s |
| Output Token Throughput | 791.625 token/s | 775.0892 token/s | 824.7901 token/s | 813.6934 token/s |
| Total Token Throughput | 2717.3057 token/s | 2660.5452 token/s | 2831.1469 token/s | 2793.0569 token/s |
| 最终 Prefix cache hit rate | 9.9% | 9.9% | 9.9% | 9.9% |

## Profiling 窗口与 kernel 对比

| 运行器 / 模型 / CANN | 采样时间（北京时间） | start / stop HTTP | 间隔秒 | trace / kernel CSV | 四 rank 时间轴跨度秒 |
| --- | --- | --- | ---: | --- | --- |
| MRV1 / BF16 / cann910 | 18:59:05 | 200 / 200 | 1.0010 | 4 / 4 | 1.0373, 1.0376, 1.0375, 1.0376 |
| MRV1 / BF16 / cann920 | 19:12:27 | 200 / 200 | 1.0010 | 4 / 4 | 1.0407, 1.0407, 1.0405, 1.0407 |
| MRV1 / W8A8 / cann910 | 16:11:28 | 200 / 200 | 1.0010 | 4 / 4 | 1.0285, 1.0282, 1.0283, 1.0285 |
| MRV1 / W8A8 / cann920 | 16:28:40 | 200 / 200 | 1.0004 | 4 / 4 | 1.0220, 1.0225, 1.0219, 1.0225 |
| MRV2 / BF16 / cann910 | 20:47:24 | 200 / 200 | 1.0010 | 4 / 4 | 1.0342, 1.0342, 1.0340, 1.0340 |
| MRV2 / BF16 / cann920 | 21:01:49 | 200 / 200 | 1.0011 | 4 / 4 | 1.0282, 1.0283, 1.0288, 1.0288 |
| MRV2 / W8A8 / cann910 | 21:53:50 | 200 / 200 | 1.0007 | 4 / 4 | 1.0216, 1.0213, 1.0216, 1.0214 |
| MRV2 / W8A8 / cann920 | 22:11:18 | 200 / 200 | 1.0011 | 4 / 4 | 1.0272, 1.0271, 1.0274, 1.0274 |

下表为四个 rank 合并、按调用数加权的 kernel 类型平均耗时（us），并分别比较运行器内部 CANN 9.2 相对 9.1 的变化。类型平均值未严格配对实际 KV 长度、专家路由与通信重叠，不能当作相同工作负载的因果结论。

### BF16 kernels

| 类型 | MRV1 / 9.1 us | MRV1 / 9.2 us | MRV1 变化 | MRV2 / 9.1 us | MRV2 / 9.2 us | MRV2 变化 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GroupedMatmul | 89.377 | 86.927 | -2.74% | 85.196 | 85.851 | +0.77% |
| FusedInferAttentionScore | 62.395 | 61.961 | -0.69% | 59.693 | 64.802 | +8.56% |
| hcom_allReduce_ | 14.053 | 13.998 | -0.39% | 13.519 | 13.101 | -3.10% |
| MatMulV2 | 9.229 | 9.382 | +1.66% | 9.422 | 9.444 | +0.23% |
| MoeInitRoutingV3 | 16.473 | 16.361 | -0.69% | 15.752 | 15.803 | +0.32% |
| split_qkv_rmsnorm_rope_kernel | 13.872 | 13.603 | -1.94% | 14.912 | 14.405 | -3.40% |
| AddRmsNormBias | 4.953 | 5.153 | +4.04% | 5.079 | 5.017 | -1.23% |
| Cast | 3.542 | 3.461 | -2.28% | 3.525 | 3.641 | +3.30% |
| MoeGatingTopK | 7.482 | 7.287 | -2.60% | 7.330 | 7.273 | -0.77% |
| MoeTokenUnpermute | 6.409 | 6.395 | -0.22% | 6.611 | 6.448 | -2.47% |
| ScatterPaKvCache | 5.248 | 5.472 | +4.27% | 5.301 | 5.313 | +0.23% |
| SwiGlu | 4.286 | 4.288 | +0.03% | 4.289 | 4.298 | +0.22% |

### W8A8 kernels

| 类型 | MRV1 / 9.1 us | MRV1 / 9.2 us | MRV1 变化 | MRV2 / 9.1 us | MRV2 / 9.2 us | MRV2 变化 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GroupedMatmulSwigluQuant | 66.202 | 68.839 | +3.98% | 67.077 | 66.317 | -1.13% |
| hcom_allReduce_ | 14.718 | 15.643 | +6.29% | 14.106 | 14.586 | +3.40% |
| FusedInferAttentionScore | 58.752 | 62.321 | +6.08% | 59.869 | 66.278 | +10.71% |
| GroupedMatmul | 35.012 | 36.581 | +4.48% | 35.183 | 37.170 | +5.65% |
| Cumsum | 30.697 | 30.037 | -2.15% | 30.284 | 30.481 | +0.65% |
| QuantBatchMatmulV3 | 14.898 | 15.148 | +1.68% | 14.868 | 14.971 | +0.69% |
| MoeInitRoutingV3 | 18.220 | 18.497 | +1.52% | 18.114 | 17.989 | -0.69% |
| split_qkv_rmsnorm_rope_kernel | 16.832 | 15.780 | -6.25% | 15.083 | 15.143 | +0.40% |
| AscendQuantV2 | 11.377 | 9.177 | -19.34% | 11.034 | 9.057 | -17.92% |
| MatMulV2 | 8.763 | 8.847 | +0.97% | 8.672 | 8.689 | +0.20% |
| Cast | 3.591 | 3.435 | -4.37% | 3.535 | 3.679 | +4.07% |
| MoeGatingTopK | 7.749 | 7.611 | -1.78% | 7.515 | 7.937 | +5.62% |

## 对比分析与限制

BF16 切换 MRV2 后，9.1 / 9.2 吞吐分别提高 2.37% / 3.88%，CANN 版本差距从 -1.63% 缩小到 -0.17%。MRV1 的 9.2 采样中 GMM 均值反而较低，不能把整体下降直接归因为 GMM 本体变慢；已记录 kernel 时间轴未覆盖的比例从约 8.01% 升至 9.55%，提示进一步检查图提交、同步与间隔。该比例不等同于硬件完全空闲。MRV2 的 9.2 attention 均值高约 8.56%，但整轮吞吐差距很小，局部均值不能单独解释总体差异。

W8A8 切换 MRV2 后，9.1 / 9.2 吞吐分别提高 4.19% / 4.98%，CANN 版本差距从 -2.09% 缩小到 -1.35%。MRV1 的 9.2 融合量化 GMM、GMM、attention 与 allReduce 类型均值更高；MRV2 的融合量化 GMM 均值低约 1.13%，但 GMM、attention、allReduce 分别高约 5.65%、10.71%、3.40%。这表明热点变化并不一致，不能认定一个算子解释全部版本劣化。

同一模型各组的输入/输出 token 数和最终 Prefix cache 命中率一致：BF16 为 0.5%，W8A8 为 9.9%，与对应参考 CI 一致。MRV2 两模型的两套 CANN 均记录 LBNHC KV cache layout；BF16 MRV1 也记录相同布局，没有单独修改 KV 布局。最终缓存命中率一致仍不能保证整个调度时间线相同。

八组顺序执行、每环境仅一次正式性能轮，NPU 隔离而宿主机 CPU/IO 共享；没有无 profiler 的重复或交错实验。1 秒 profiling 为局部 decode 窗口，调用数和真实 KV 长度不同，通信 kernel 也可能包含等待；不能累计 kernel 均值来代替整轮吞吐，或凭这些数据确认 CANN 内部改动的唯一根因。MRV2 本轮超过 CI 下限，不表示原 MRV1 CI 已复现，也不能判定 CANN 9.2 的问题已修复。

BF16 MRV2 第一轮服务预检曾因控制脚本读取 /proc/environ 的方法未通过校验，当时没有运行 AISBench；改为实际四个 worker 的 MRV2 加载日志核对后重建空缓存并冷启动。这里只统计最终成功的正式轮，未改模型源码或服务参数。

## CPU 绑核、日志和 profiling 证据

| 范围 | 报告 / 证据 |
| --- | --- |
| MRV1 四组 | [分组完整报告](mrv1/README.md)、[16 个 worker 主线程绑核证据](mrv1/cpu-binding.md)、[结构化结果](mrv1/results.json) |
| MRV2 四组 | [分组完整报告](mrv2/README.md)；[BF16 的 8 个 worker 主线程绑核证据](mrv2/cpu-binding.md)，W8A8 原始证据在服务器实验目录 |

实际 worker 主线程亲和性与 topo_affinity 计划一致；MRV2 W8A8 的四个主线程 masks 为 194–221、226–253、130–157、162–189，两套相同。IRQ 调整未执行。仓库中的 MRV2 verify_evidence.py 校验 BF16 绑核证据及该目录 SHA256SUMS，不宣称其同时校验了服务器上的 W8A8 绑核快照。

MRV1 四组完整 profiling 已按分卷归档到 [mrv1/profiling/](mrv1/profiling/)，下载、合并与解析命令见 [原始报告](mrv1/README.md#完整-profiling-下载合并与解析)。MRV2 原始 profiling 保留在 192.168.9.156，各组路径如下；已包含四个 rank 的 trace_view.json、kernel_details.csv 和原始 PROF_* 数据。

| 运行器 | 模型 | CANN | 192.168.9.156 上的 profiling 路径 |
| --- | --- | --- | --- |
| MRV1 | BF16 | cann910 | `/mnt/share/z00943141/qwen-cibbb-bf16-profile-20261009-184820/cann910-bf16-profile/profiling` |
| MRV1 | BF16 | cann920 | `/mnt/share/z00943141/qwen-cibbb-bf16-profile-20261009-184820/cann920-bf16-profile/profiling` |
| MRV1 | W8A8 | cann910 | `/mnt/share/z00943141/qwen-cibbb-w8a8-profile-20261009-153616/cann910-w8a8-profile/profiling` |
| MRV1 | W8A8 | cann920 | `/mnt/share/z00943141/qwen-cibbb-w8a8-profile-20261009-153616/cann920-w8a8-profile/profiling` |
| MRV2 | BF16 | cann910 | `/mnt/share/z00943141/qwen-cibbb-bf16-mrv2-profile-20261009-202845/cann910-bf16-profile/profiling` |
| MRV2 | BF16 | cann920 | `/mnt/share/z00943141/qwen-cibbb-bf16-mrv2-profile-20261009-202845/cann920-bf16-profile/profiling` |
| MRV2 | W8A8 | cann910 | `/mnt/share/z00943141/qwen-cibbb-w8a8-mrv2-profile-20261009-213915/cann910-w8a8-profile/profiling` |
| MRV2 | W8A8 | cann920 | `/mnt/share/z00943141/qwen-cibbb-w8a8-mrv2-profile-20261009-213915/cann920-w8a8-profile/profiling` |

所有模型服务已停止。复现脚本、请求配置与各组环境记录见分组报告；MRV1 文件位于 reproduce/、environment/，MRV2 BF16 已发布 evidence/，MRV2 W8A8 的完整运行脚本和 comparison-evidence.json 在其服务器实验根目录。

## 逐请求指标完整分布

保留 AISBench 原始 min/max/median/P75/P90/P99；每组日志链接见上面的总表。

<details>
<summary>MRV1 / BF16 / cann910</summary>

| 指标 | Average | Min | Max | Median | P75 | P90 | P99 | N |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| E2EL | 76588.5 ms | 29673.7 ms | 90186.3 ms | 88467.6 ms | 88923.4 ms | 89559.9 ms | 90110.2 ms | 180 |
| TTFT | 47887.7 ms | 171.6 ms | 61559.7 ms | 59677.0 ms | 59869.6 ms | 60555.3 ms | 61482.1 ms | 180 |
| TPOT | 19.1 ms | 12.0 ms | 20.3 ms | 19.2 ms | 19.4 ms | 19.7 ms | 20.1 ms | 180 |
| ITL | 19.1 ms | 0.0 ms | 861.5 ms | 18.6 ms | 19.0 ms | 19.3 ms | 21.4 ms | 180 |
| InputTokens | 3648.85 | 3285.0 | 4079.0 | 3629.0 | 3709.75 | 3816.3 | 4022.57 | 180 |
| OutputTokens | 1500.0 | 1500.0 | 1500.0 | 1500.0 | 1500.0 | 1500.0 | 1500.0 | 180 |
| OutputTokenThroughput | 21.7709 token/s | 16.6322 token/s | 50.5498 token/s | 16.9554 token/s | 24.8359 token/s | 25.1482 token/s | 50.3028 token/s | 180 |

</details>

<details>
<summary>MRV1 / BF16 / cann920</summary>

| 指标 | Average | Min | Max | Median | P75 | P90 | P99 | N |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| E2EL | 77741.7 ms | 29978.1 ms | 91550.3 ms | 89777.9 ms | 90214.1 ms | 91096.0 ms | 91482.1 ms | 180 |
| TTFT | 48585.7 ms | 173.7 ms | 62382.1 ms | 60532.2 ms | 60743.5 ms | 61583.1 ms | 62312.2 ms | 180 |
| TPOT | 19.5 ms | 12.6 ms | 20.6 ms | 19.5 ms | 19.7 ms | 20.0 ms | 20.4 ms | 180 |
| ITL | 19.4 ms | 0.0 ms | 898.6 ms | 18.9 ms | 19.3 ms | 19.6 ms | 21.6 ms | 180 |
| InputTokens | 3648.85 | 3285.0 | 4079.0 | 3629.0 | 3709.75 | 3816.3 | 4022.57 | 180 |
| OutputTokens | 1500.0 | 1500.0 | 1500.0 | 1500.0 | 1500.0 | 1500.0 | 1500.0 | 180 |
| OutputTokenThroughput | 21.4668 token/s | 16.3844 token/s | 50.0366 token/s | 16.7079 token/s | 24.4861 token/s | 24.7499 token/s | 49.7807 token/s | 180 |

</details>

<details>
<summary>MRV1 / W8A8 / cann910</summary>

| 指标 | Average | Min | Max | Median | P75 | P90 | P99 | N |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| E2EL | 74696.3 ms | 27473.4 ms | 88476.7 ms | 86465.9 ms | 86926.6 ms | 87039.7 ms | 88475.4 ms | 180 |
| TTFT | 46640.3 ms | 204.3 ms | 60525.0 ms | 58408.3 ms | 58538.5 ms | 58964.6 ms | 60523.7 ms | 180 |
| TPOT | 18.7 ms | 14.8 ms | 19.8 ms | 18.7 ms | 19.0 ms | 19.2 ms | 19.6 ms | 180 |
| ITL | 18.7 ms | 0.0 ms | 835.1 ms | 18.1 ms | 18.3 ms | 18.4 ms | 21.0 ms | 180 |
| InputTokens | 3648.85 | 3285.0 | 4079.0 | 3629.0 | 3709.75 | 3816.3 | 4022.57 | 180 |
| OutputTokens | 1500.0 | 1500.0 | 1500.0 | 1500.0 | 1500.0 | 1500.0 | 1500.0 | 180 |
| OutputTokenThroughput | 22.585 token/s | 16.9536 token/s | 54.5983 token/s | 17.3479 token/s | 25.4119 token/s | 26.0979 token/s | 54.3197 token/s | 180 |

</details>

<details>
<summary>MRV1 / W8A8 / cann920</summary>

| 指标 | Average | Min | Max | Median | P75 | P90 | P99 | N |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| E2EL | 76255.8 ms | 28040.5 ms | 90173.6 ms | 88335.7 ms | 88788.8 ms | 88852.7 ms | 90171.6 ms | 180 |
| TTFT | 47588.0 ms | 203.2 ms | 61651.6 ms | 59656.6 ms | 59731.8 ms | 60161.1 ms | 61649.6 ms | 180 |
| TPOT | 19.1 ms | 15.2 ms | 20.2 ms | 19.2 ms | 19.4 ms | 19.6 ms | 20.0 ms | 180 |
| ITL | 19.1 ms | 0.0 ms | 846.7 ms | 18.5 ms | 18.7 ms | 18.9 ms | 20.9 ms | 180 |
| InputTokens | 3648.85 | 3285.0 | 4079.0 | 3629.0 | 3709.75 | 3816.3 | 4022.57 | 180 |
| OutputTokens | 1500.0 | 1500.0 | 1500.0 | 1500.0 | 1500.0 | 1500.0 | 1500.0 | 180 |
| OutputTokenThroughput | 22.128 token/s | 16.6346 token/s | 53.4941 token/s | 16.9807 token/s | 24.9078 token/s | 25.5904 token/s | 53.2474 token/s | 180 |

</details>

<details>
<summary>MRV2 / BF16 / cann910</summary>

| 指标 | Average | Min | Max | Median | P75 | P90 | P99 | N |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| E2EL | 74355.4 ms | 28733.7 ms | 87600.7 ms | 85759.2 ms | 86201.3 ms | 87058.5 ms | 87522.3 ms | 180 |
| TTFT | 46482.5 ms | 198.9 ms | 59669.8 ms | 57898.5 ms | 58047.8 ms | 58860.6 ms | 59589.7 ms | 180 |
| TPOT | 18.6 ms | 13.1 ms | 19.6 ms | 18.6 ms | 18.8 ms | 19.1 ms | 19.4 ms | 180 |
| ITL | 18.6 ms | 0.0 ms | 853.8 ms | 18.1 ms | 18.5 ms | 18.7 ms | 19.1 ms | 180 |
| InputTokens | 3648.85 | 3285.0 | 4079.0 | 3629.0 | 3709.75 | 3816.3 | 4022.57 | 180 |
| OutputTokens | 1500.0 | 1500.0 | 1500.0 | 1500.0 | 1500.0 | 1500.0 | 1500.0 | 180 |
| OutputTokenThroughput | 22.4297 token/s | 17.1232 token/s | 52.2035 token/s | 17.4908 token/s | 25.5886 token/s | 25.863 token/s | 51.903 token/s | 180 |

</details>

<details>
<summary>MRV2 / BF16 / cann920</summary>

| 指标 | Average | Min | Max | Median | P75 | P90 | P99 | N |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| E2EL | 74435.9 ms | 28755.6 ms | 87809.9 ms | 85919.2 ms | 86304.9 ms | 87143.9 ms | 87751.3 ms | 180 |
| TTFT | 46533.3 ms | 204.5 ms | 59821.1 ms | 57926.8 ms | 58158.4 ms | 59054.7 ms | 59760.4 ms | 180 |
| TPOT | 18.6 ms | 13.3 ms | 19.7 ms | 18.7 ms | 18.9 ms | 19.1 ms | 19.5 ms | 180 |
| ITL | 18.6 ms | 0.0 ms | 873.5 ms | 18.1 ms | 18.5 ms | 18.7 ms | 19.5 ms | 180 |
| InputTokens | 3648.85 | 3285.0 | 4079.0 | 3629.0 | 3709.75 | 3816.3 | 4022.57 | 180 |
| OutputTokens | 1500.0 | 1500.0 | 1500.0 | 1500.0 | 1500.0 | 1500.0 | 1500.0 | 180 |
| OutputTokenThroughput | 22.4063 token/s | 17.0824 token/s | 52.1638 token/s | 17.4583 token/s | 25.5757 token/s | 25.8909 token/s | 51.868 token/s | 180 |

</details>

<details>
<summary>MRV2 / W8A8 / cann910</summary>

| 指标 | Average | Min | Max | Median | P75 | P90 | P99 | N |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| E2EL | 71679.3 ms | 26264.2 ms | 84967.6 ms | 82960.0 ms | 83432.0 ms | 83515.1 ms | 84967.0 ms | 180 |
| TTFT | 44790.1 ms | 214.4 ms | 58174.0 ms | 56076.2 ms | 56158.1 ms | 56620.4 ms | 58173.4 ms | 180 |
| TPOT | 17.9 ms | 14.2 ms | 19.0 ms | 17.9 ms | 18.2 ms | 18.4 ms | 18.8 ms | 180 |
| ITL | 17.9 ms | 0.0 ms | 830.4 ms | 17.3 ms | 17.5 ms | 17.7 ms | 19.0 ms | 180 |
| InputTokens | 3648.85 | 3285.0 | 4079.0 | 3629.0 | 3709.75 | 3816.3 | 4022.57 | 180 |
| OutputTokens | 1500.0 | 1500.0 | 1500.0 | 1500.0 | 1500.0 | 1500.0 | 1500.0 | 180 |
| OutputTokenThroughput | 23.5517 token/s | 17.6538 token/s | 57.112 token/s | 18.081 token/s | 26.4779 token/s | 27.2276 token/s | 56.8198 token/s | 180 |

</details>

<details>
<summary>MRV2 / W8A8 / cann920</summary>

| 指标 | Average | Min | Max | Median | P75 | P90 | P99 | N |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| E2EL | 72702.6 ms | 26724.5 ms | 86084.8 ms | 84163.1 ms | 84620.9 ms | 84708.2 ms | 86084.4 ms | 180 |
| TTFT | 45417.5 ms | 215.8 ms | 58912.5 ms | 56869.6 ms | 56973.8 ms | 57416.1 ms | 58910.7 ms | 180 |
| TPOT | 18.2 ms | 14.3 ms | 19.3 ms | 18.2 ms | 18.5 ms | 18.7 ms | 19.1 ms | 180 |
| ITL | 18.2 ms | 0.0 ms | 865.3 ms | 17.6 ms | 17.8 ms | 17.9 ms | 18.6 ms | 180 |
| InputTokens | 3648.85 | 3285.0 | 4079.0 | 3629.0 | 3709.75 | 3816.3 | 4022.57 | 180 |
| OutputTokens | 1500.0 | 1500.0 | 1500.0 | 1500.0 | 1500.0 | 1500.0 | 1500.0 | 180 |
| OutputTokenThroughput | 23.2061 token/s | 17.4247 token/s | 56.1283 token/s | 17.8225 token/s | 26.1036 token/s | 26.7997 token/s | 55.8538 token/s | 180 |

</details>
