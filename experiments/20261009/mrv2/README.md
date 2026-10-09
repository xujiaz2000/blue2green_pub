# BF16：仅打开 MRV2，bbb5672 / vLLM 0.30.0 的 CANN 9.1 与 9.2 对比

CANN 9.1 输出吞吐 **800.3532 token/s**，CANN 9.2 **799.0187 token/s**，9.2 相对 9.1 **-0.17%**。两组均为 180 请求全部成功、失败 0、输出 270000 tokens。每组采 1 秒 profiling，四个 TP rank 均完成解析。

## CPU 绑核验证

两组实际 worker 主线程亲和性均与 topo_affinity 计划一致；[完整证据链与校验方法](cpu-binding.md)。IRQ 亲和性调整未执行。

## 唯一的配置变化

从上一轮 BF16 MRV1 使用的同一 CANN 镜像创建独立容器。没有改推理源码、重新安装 Python 包或重新编译。服务脚本仅作以下变化：

```diff
-export VLLM_USE_V2_MODEL_RUNNER=0
+export VLLM_USE_V2_MODEL_RUNNER=1
```

/scripts 内其他脚本和客户端配置按文件 SHA256 核对无变化。容器和结果目录使用新名称，VLLM_CACHE_ROOT / TRITON_CACHE_DIR 指向本轮独立缓存目录。服务启动后确认 MRV2 专用 model_runner.py 加载日志，四个实际 Worker_TP 均有 upstream V2 专用 model_runner.py:428 模型加载日志，没有 MRV1 的 gpu_model_runner.py / model_runner_v1.py 执行日志；历史源码的 Ascend runner 选择逻辑直接使用这个环境变量。

- vllm-ascend：`bbb5672af80b1972c301852aa505b13374fa6355`。vLLM：`ced6857afa0ea7b2e3f0846a62e1394e90f15607`，包版本 `0.30.0+empty`。两套 tracked 源码分别与 HEAD 的所有 blob 哈希匹配。
- 同一 192.168.9.156 / Ascend 910B3 / driver 25.5.1；非特权 Ascend runtime 容器仅映射物理卡 0–3，npu-smi 与 torch.npu.device_count 确认仅四卡。两轮顺序执行，各轮后停止模型服务。
- 同一只读 BF16 权重：`/mnt/share/z00943141/qwen-a2-profiling-kit-20261008-022415/models/bf16`；Qwen/Qwen3-30B-A3B，dtype=bfloat16，无量化。
- MRV2，TP4，async scheduling，max-num-seqs=16，max-model-len/max-num-batched-tokens=16384，GPU memory utilization=0.9，CPU binding=true。非 eager，FULL_DECODE_ONLY，capture sizes=[1,2,4,8,16]。
- 与上一轮相同的 GSM8K-in3500-bs400 数据和 streaming chat 客户端；180 正式请求，AISBench 内部预热 1 请求，没有 W8A8 的额外 18 请求 perf-warm。batch_size=45、request_rate=0、temperature=0、ignore_eos=true、max_out_len=1500。Prefix caching 保持开启，跨组停止服务后冷启动。
- 当前 MRV2 与上一轮 MRV1 的 BF16 日志均为 LBNHC KV cache layout；本次没有单独更改布局，不把性能变化直接归因于布局切换。
- 端口 8007，日志统计间隔 10 秒，HCCL / NZ / OMP 等设置不变。每组只跑本次 profiling 轮，无额外无 profiler 轮。

## 结果

| 指标 | CANN 9.1 MRV2 | CANN 9.2 MRV2 |
| --- | ---: | ---: |
| Output Token Throughput | 800.3532 token/s | 799.0187 token/s |
| TPOT | 18.6 ms | 18.6 ms |
| TTFT | 46482.5 ms | 46533.3 ms |
| E2EL | 74355.4 ms | 74435.9 ms |
| Benchmark Duration | 337351.0656 ms | 337914.4863 ms |
| Total Requests | 180 | 180 |
| Success Requests | 180 | 180 |
| Failed Requests | 0 | 0 |
| Total Input Tokens | 656793 | 656793 |
| Total Generated Tokens | 270000 | 270000 |
| Concurrency | 39.6737 | 39.6504 |
| Max Concurrency | 45 | 45 |
| 达到原 BF16 CI 下限 778.365054 token/s | 是 | 是 |

## 与同节点上一轮 MRV1 比较

上一轮在相同机器、代码、权重、卡、180 请求协议和 1 秒 profiling 下完成；两次实验顺序进行，未重复交错测量，因此下表描述实际观测变化，不排除时间与宿主机负载波动。

| 环境 | MRV1 输出吞吐 | 本轮 MRV2 | 变化 |
| --- | ---: | ---: | ---: |
| CANN 9.1 | 781.8579 | 800.3532 | +2.37% |
| CANN 9.2 | 769.1510 | 799.0187 | +3.88% |

[上一轮 MRV1 报告](../mrv1/README.md)。上述下限来自 bbb5672 的 BF16 YAML：baseline=802.4382、threshold=0.97。历史 BF16 CI 实际使用 MRV1；MRV2 是否超过同一下限只表示本次观测结果，不等于原 MRV1 CI 配置的验证。

## 版本与 CANN 构建

| 核心包 | 两套环境 |
| --- | --- |
| vllm | 0.30.0+empty |
| vllm_ascend | 0.19.1rc2.dev2433+gbbb5672af |
| torch | 2.10.0+cpu |
| torch_npu | 2.10.0.post4 |
| triton_ascend | 3.2.2 |
| transformers | 5.14.1 |
| ais_bench_benchmark | 3.1.20260609 |

| CANN 组件 | 9.1 | 9.2 |
| --- | --- | --- |
| runtime | 9.1.0 / 20260730_231653901 | 9.2.0 / 20260930_161523958 |
| ops_transformer | 9.1.0 / 20260730_231653901 | 9.2.0 / 20260930_161523958 |
| ops_legacy | 9.1.0 / 20260730_231653901 | 9.2.0 / 20260930_161523958 |
| bisheng-compiler | 9.1.0 / 20260730_231653901 | 9.2.0 / 20260930_161523958 |

沿用父容器分别用对应 CANN 为 bbb5672 编译的 C++ 扩展及相同范围的自定义算子。两组标准 BF16 GMM 使用各自 CANN 原生库；并非完全复制历史 CI 的所有模型算子编译产物。

## Profiling 与算子统计

| 环境 | HTTP start / stop | 采集间隔 | 采样前状态 |
| --- | --- | ---: | --- |
| cann910 | 200 / 200 | 1.0010s | Avg prompt throughput: 0.0 tokens/s, Avg generation throughput: 926.2 tokens/s, Running: 16 reqs, Waiting: 29 reqs, NPU KV cache usage: 4.2%, Prefix cache hit rate: 2.8% |
| cann920 | 200 / 200 | 1.0011s | Avg prompt throughput: 0.0 tokens/s, Avg generation throughput: 881.3 tokens/s, Running: 16 reqs, Waiting: 29 reqs, NPU KV cache usage: 4.6%, Prefix cache hit rate: 2.8% |

四个 rank 合并统计。按 kernel 类型比较主要平均耗时；调用数量与具体输入形状一并列出，避免用总耗时代替单次耗时。

| 类型 | 9.1 us / 次数 | 9.2 us / 次数 | 平均耗时变化 |
| --- | ---: | ---: | ---: |
| GroupedMatmul | 85.196 / 21504 | 85.851 / 21120 | +0.77% |
| FusedInferAttentionScore | 59.693 / 10752 | 64.802 / 10560 | +8.56% |
| hcom_allReduce_ | 13.519 / 43456 | 13.101 / 42680 | -3.10% |
| MatMulV2 | 9.422 / 32480 | 9.444 / 31900 | +0.23% |
| MoeInitRoutingV3 | 15.752 / 10752 | 15.803 / 10560 | +0.32% |
| split_qkv_rmsnorm_rope_kernel | 14.912 / 10752 | 14.405 / 10560 | -3.40% |
| AddRmsNormBias | 5.079 / 21504 | 5.017 / 21120 | -1.23% |
| Cast | 3.525 / 23072 | 3.641 / 22660 | +3.30% |
| MoeGatingTopK | 7.330 / 10752 | 7.273 / 10560 | -0.77% |
| MoeTokenUnpermute | 6.611 / 10752 | 6.448 / 10560 | -2.47% |
| ScatterPaKvCache | 5.301 / 10752 | 5.313 / 10560 | +0.23% |
| SwiGlu | 4.289 / 10752 | 4.298 / 10560 | +0.22% |
| hcom_allGather_ | 90.426 / 448 | 87.437 / 440 | -3.31% |
| Abs | 1.370 / 10752 | 1.350 / 10560 | -1.47% |
| _categorical_prepare_mass_kernel | 30.230 / 224 | 32.485 / 220 | +7.46% |
| Index | 10.006 / 672 | 10.063 / 660 | +0.57% |
| _categorical_sample_kernel | 26.241 / 224 | 26.295 / 220 | +0.20% |
| Transpose | 14.471 / 224 | 14.978 / 220 | +3.51% |

主要相同 kernel 类型与 Input Shapes 的统计：

| 类型 / Input Shapes | 9.1 us | 9.2 us | 变化 |
| --- | ---: | ---: | ---: |
| GroupedMatmul / `"128,2048;128,2048,384;;;;;;128"` | 121.316 | 122.199 | +0.73% |
| hcom_allReduce_ / `N/A` | 13.519 | 13.101 | -3.10% |
| GroupedMatmul / `"128,192;128,192,2048;;;;;;128"` | 49.076 | 49.502 | +0.87% |
| MoeInitRoutingV3 / `"16,2048;16,8"` | 15.752 | 15.803 | +0.32% |
| split_qkv_rmsnorm_rope_kernel / `N/A` | 14.912 | 14.405 | -3.40% |
| AddRmsNormBias / `"16,2048;16,2048;2048;"` | 5.079 | 5.017 | -1.23% |
| MatMulV2 / `"16,2048;1280,2048"` | 9.971 | 10.050 | +0.79% |
| MatMulV2 / `"16,1024;2048,1024"` | 9.570 | 9.498 | -0.75% |
| MoeGatingTopK / `"16,128;"` | 7.330 | 7.273 | -0.77% |
| MoeTokenUnpermute / `"128,2048;128;16,8"` | 6.611 | 6.448 | -2.47% |
| MatMulV2 / `"16,2048;128,2048"` | 6.335 | 6.380 | +0.72% |
| Cast / `"16,2048"` | 6.096 | 6.372 | +4.52% |
| ScatterPaKvCache / `"16,1,128;13261,128,1,128;16;16,1,128;13261,128,1,128;;;"` | 5.301 | 5.313 | +0.23% |
| SwiGlu / `"128,384"` | 4.289 | 4.298 | +0.22% |

## 分析与限制

本轮仅打开 MRV2 后，CANN 9.1 / 9.2 分别达到 800.3532 / 799.0187 token/s，都高于原 BF16 YAML 的下限 778.365054。相对上一轮 MRV1 各提升 2.37% / 3.88%。两种 CANN 的观测差距从 MRV1 的 -1.63% 缩小至本轮 -0.17%，TPOT 两组均为 18.6 ms（日志精度 0.1 ms）。这支持该节点 BF16 在本轮切换 MRV2 后两套 CANN 均能达到同一吞吐下限；不能据此认定 CANN 9.2 的内部性能问题已修复。微小版本差距是否稳定仍需重复测量。

采样中 CANN 9.2 的 GroupedMatmul 类型平均耗时比 9.1 高约 0.77%，FusedInferAttentionScore 高约 8.56%，allReduce 低约 3.10%。两窗口调用数不同（例如 GroupedMatmul 为 21504 / 21120），真实 KV 长度并未严格匹配；这些局部统计不能单独证明 attention 导致整体版本劣化，尤其整轮吞吐差距只有 0.17%。两组最终 Prefix cache hit rate 都为 0.5%。

两套代码和核心包一致、只读模型一致、输入/输出 token 数一致，因此比较的是本轮对应 CANN 软件栈下的整体表现。采样在 Running=16、prompt 吞吐为 0 的 decode 阶段；即使 Input Shapes 相同，真实 KV 长度、专家路由和通信重叠仍可能不同。一次 1 秒采样不能单独定位 CANN 内部改动的因果，也不能简单累计算子平均耗时来解释整轮吞吐。

每环境只进行一次正式性能测量，整轮结果包含 profiler 开关与导出开销，不能代替多次无 profiler 测量。模型服务在下一组前已停止，避免跨组 Prefix cache 命中；组内内部预热带来的缓存保留。

首轮 CANN 9.1 的服务预检正常加载了 MRV2，但控制脚本用 /proc/environ 读取 worker 配置未通过；当时未运行 AISBench。随后保留预检日志、重建空缓存目录并冷启动，改用四个 worker 实际执行 MRV2 的专用日志核对。上面的数据仅包含正式成功的一轮；这项调整没有改模型源码或服务参数。

## Profiling 路径（192.168.9.156）

- cann910：`/mnt/share/z00943141/qwen-cibbb-bf16-mrv2-profile-20261009-202845/cann910-bf16-profile/profiling`；四 rank 窗口 1.0342, 1.0342, 1.0340, 1.0340s；最终 Prefix hit 0.5%。
- cann920：`/mnt/share/z00943141/qwen-cibbb-bf16-mrv2-profile-20261009-202845/cann920-bf16-profile/profiling`；四 rank 窗口 1.0282, 1.0283, 1.0288, 1.0288s；最终 Prefix hit 0.5%。

原始 profiling、trace_view.json、kernel_details.csv、服务/客户端日志和源码验证均保留在 `/mnt/share/z00943141/qwen-cibbb-bf16-mrv2-profile-20261009-202845`。两套模型服务已停止。本公开目录包含两份 AISBench 最终日志、本报告及 CPU 绑核证据；原始 profiling 保留在上述本机路径。

- [CANN 9.1 最终日志](cann910-aisbench-final-result.log)
- [CANN 9.2 最终日志](cann920-aisbench-final-result.log)
