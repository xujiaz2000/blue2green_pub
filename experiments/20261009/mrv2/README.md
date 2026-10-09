# Qwen3-30B-A3B A2：MRV2 下 BF16 / W8A8 × CANN 9.1 / 9.2

四组使用相同 main 历史节点 `bbb5672af80b1972c301852aa505b13374fa6355`、vLLM `0.30.0+empty`（`ced6857afa0ea7b2e3f0846a62e1394e90f15607`），均开启 MRV2。同一 192.168.9.156 机器，容器仅可见物理 NPU 0–3，TP4、FULL_DECODE_ONLY；各组冷启动并顺序运行，结束后停止模型服务。

每组完成 180 / 180 正式请求，失败 0 条，输入 656793、输出 270000 tokens；稳定 decode 阶段采约 1 秒 profiling，四个 TP rank 均完成解析。BF16 只有客户端内部 1 请求预热；W8A8 按 CI 先运行 18 请求 perf-warm，两个客户端调用各内部预热 1 请求。两种模型的预热协议不同，因此重点比较同一模型的 CANN 版本差异。

## 性能结果

| 模型 | CANN | 输出吞吐 token/s | TPOT ms | 相对本模型 9.1 | 达到 CI 下限 | 最终日志 |
| --- | --- | ---: | ---: | ---: | --- | --- |
| BF16 | 9.1 | 800.3532 | 18.6 | +0.00% | 是 | [AISBench](logs/bf16-cann910-aisbench-final-result.log) |
| BF16 | 9.2 | 799.0187 | 18.6 | -0.17% | 是 | [AISBench](logs/bf16-cann920-aisbench-final-result.log) |
| W8A8 | 9.1 | 824.7901 | 17.9 | +0.00% | 是 | [AISBench](logs/w8a8-cann910-aisbench-final-result.log) |
| W8A8 | 9.2 | 813.6934 | 18.2 | -1.35% | 是 | [AISBench](logs/w8a8-cann920-aisbench-final-result.log) |

BF16 CI 下限为 **778.365054 token/s**，W8A8 为 **781.695840 token/s**。历史 CI 使用 MRV1；本轮达标标注仅表示带 profiling 的 MRV2 观测值超过同一 YAML 下限。每环境一次测量，差距是否稳定仍需重复实验。

## 与同节点 MRV1 比较

| 模型 | CANN | MRV1 token/s | MRV2 token/s | 变化 |
| --- | --- | ---: | ---: | ---: |
| BF16 | 9.1 | 781.8579 | 800.3532 | +2.37% |
| BF16 | 9.2 | 769.1510 | 799.0187 | +3.88% |
| W8A8 | 9.1 | 791.6250 | 824.7901 | +4.19% |
| W8A8 | 9.2 | 775.0892 | 813.6934 | +4.98% |

[MRV1 四组报告](../mrv1/README.md)。各轮使用相同模型、源码、卡和对应请求协议，按顺序完成，没有交错重复；不能排除时间及宿主机负载波动。

## CPU 绑核证据范围

[已上传的绑核证据与校验脚本](cpu-binding.md)覆盖 BF16 两组共 8 个 worker 主线程。W8A8 的环境、worker 亲和性与运行日志保留在下文服务器实验目录；本次新增上传为两份 W8A8 最终 AISBench 日志及本合并报告。

## BF16：CANN 9.1 / 9.2

CANN 9.1 输出吞吐 **800.3532 token/s**，CANN 9.2 **799.0187 token/s**，9.2 相对 9.1 **-0.17%**。两组均为 180 请求全部成功、失败 0、输出 270000 tokens。每组采 1 秒 profiling，四个 TP rank 均完成解析。

### CPU 绑核验证

两组实际 worker 主线程亲和性均与 topo_affinity 计划一致；[完整证据链与校验方法](cpu-binding.md)。IRQ 亲和性调整未执行。

### 唯一的配置变化

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

### 结果

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

### 与同节点上一轮 MRV1 比较

上一轮在相同机器、代码、权重、卡、180 请求协议和 1 秒 profiling 下完成；两次实验顺序进行，未重复交错测量，因此下表描述实际观测变化，不排除时间与宿主机负载波动。

| 环境 | MRV1 输出吞吐 | 本轮 MRV2 | 变化 |
| --- | ---: | ---: | ---: |
| CANN 9.1 | 781.8579 | 800.3532 | +2.37% |
| CANN 9.2 | 769.1510 | 799.0187 | +3.88% |

[上一轮 MRV1 报告](../mrv1/README.md)。上述下限来自 bbb5672 的 BF16 YAML：baseline=802.4382、threshold=0.97。历史 BF16 CI 实际使用 MRV1；MRV2 是否超过同一下限只表示本次观测结果，不等于原 MRV1 CI 配置的验证。

### 版本与 CANN 构建

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

### Profiling 与算子统计

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

### 分析与限制

本轮仅打开 MRV2 后，CANN 9.1 / 9.2 分别达到 800.3532 / 799.0187 token/s，都高于原 BF16 YAML 的下限 778.365054。相对上一轮 MRV1 各提升 2.37% / 3.88%。两种 CANN 的观测差距从 MRV1 的 -1.63% 缩小至本轮 -0.17%，TPOT 两组均为 18.6 ms（日志精度 0.1 ms）。这支持该节点 BF16 在本轮切换 MRV2 后两套 CANN 均能达到同一吞吐下限；不能据此认定 CANN 9.2 的内部性能问题已修复。微小版本差距是否稳定仍需重复测量。

采样中 CANN 9.2 的 GroupedMatmul 类型平均耗时比 9.1 高约 0.77%，FusedInferAttentionScore 高约 8.56%，allReduce 低约 3.10%。两窗口调用数不同（例如 GroupedMatmul 为 21504 / 21120），真实 KV 长度并未严格匹配；这些局部统计不能单独证明 attention 导致整体版本劣化，尤其整轮吞吐差距只有 0.17%。两组最终 Prefix cache hit rate 都为 0.5%。

两套代码和核心包一致、只读模型一致、输入/输出 token 数一致，因此比较的是本轮对应 CANN 软件栈下的整体表现。采样在 Running=16、prompt 吞吐为 0 的 decode 阶段；即使 Input Shapes 相同，真实 KV 长度、专家路由和通信重叠仍可能不同。一次 1 秒采样不能单独定位 CANN 内部改动的因果，也不能简单累计算子平均耗时来解释整轮吞吐。

每环境只进行一次正式性能测量，整轮结果包含 profiler 开关与导出开销，不能代替多次无 profiler 测量。模型服务在下一组前已停止，避免跨组 Prefix cache 命中；组内内部预热带来的缓存保留。

首轮 CANN 9.1 的服务预检正常加载了 MRV2，但控制脚本用 /proc/environ 读取 worker 配置未通过；当时未运行 AISBench。随后保留预检日志、重建空缓存目录并冷启动，改用四个 worker 实际执行 MRV2 的专用日志核对。上面的数据仅包含正式成功的一轮；这项调整没有改模型源码或服务参数。

### Profiling 路径（192.168.9.156）

- cann910：`/mnt/share/z00943141/qwen-cibbb-bf16-mrv2-profile-20261009-202845/cann910-bf16-profile/profiling`；四 rank 窗口 1.0342, 1.0342, 1.0340, 1.0340s；最终 Prefix hit 0.5%。
- cann920：`/mnt/share/z00943141/qwen-cibbb-bf16-mrv2-profile-20261009-202845/cann920-bf16-profile/profiling`；四 rank 窗口 1.0282, 1.0283, 1.0288, 1.0288s；最终 Prefix hit 0.5%。

原始 profiling、trace_view.json、kernel_details.csv、服务/客户端日志和源码验证均保留在 `/mnt/share/z00943141/qwen-cibbb-bf16-mrv2-profile-20261009-202845`。两套模型服务已停止。本目录 BF16 部分包含两份 AISBench 最终日志及 CPU 绑核证据；原始 profiling 保留在上述本机路径。

- [CANN 9.1 最终日志](logs/bf16-cann910-aisbench-final-result.log)
- [CANN 9.2 最终日志](logs/bf16-cann920-aisbench-final-result.log)


## W8A8：CANN 9.1 / 9.2

两组各完成 **180 / 180 正式请求，失败 0 条**，每条输出 1500 tokens。CANN 9.1 输出吞吐 **824.7901 token/s**，CANN 9.2 **813.6934 token/s**，9.2 相对 9.1 **-1.35%**。每组在稳定 decode 阶段采 1 秒 profiling，四个 TP rank 均解析完成。

历史 MRV1 参考 CI 为 [run 36225208422 / job 108372470597](https://github.com/vllm-project/vllm-ascend/actions/runs/36225208422/job/108372470597)，其正式输出吞吐为 **784.1192 token/s**。源码 YAML 的 baseline 为 805.872，threshold=0.97，达标下限 **781.695840 token/s**。本轮带有一次 profiling，因此下面的达标标注只表示观测值是否达到该下限，不能替代完全无 profiler 的 CI 验证。

### 结果

| 指标 | CANN 9.1 | CANN 9.2 |
| --- | ---: | ---: |
| Output Token Throughput | 824.7901 token/s | 813.6934 token/s |
| TPOT | 17.9 ms | 18.2 ms |
| TTFT | 44790.1 ms | 45417.5 ms |
| E2EL | 71679.3 ms | 72702.6 ms |
| Benchmark Duration | 327356.0314 ms | 331820.3049 ms |
| Total Requests | 180 | 180 |
| Success Requests | 180 | 180 |
| Failed Requests | 0 | 0 |
| Total Input Tokens | 656793 | 656793 |
| Total Generated Tokens | 270000 | 270000 |
| Concurrency | 39.4136 | 39.4384 |
| Max Concurrency | 45 | 45 |
| 达到 CI 下限 | 是 | 是 |
| 相对参考 CI 784.1192 | +5.19% | +3.77% |

### 一致的代码、模型与流程

- vllm-ascend 实际 HEAD：`bbb5672af80b1972c301852aa505b13374fa6355`。参考 CI 日志记录 Branch=main；Git 历史确认该节点属于 main。workflow 的 head eb31db4d7562 与容器实际执行的 bbb5672 不同，本次使用后者。
- vLLM 实际 HEAD：`ced6857afa0ea7b2e3f0846a62e1394e90f15607`，包版本 `0.30.0+empty`。两套源码全部 tracked 文件与各自 HEAD 的 blob 哈希逐一核对，均无差异。
- 两套环境从已验证 BF16 MRV2 的同一 CANN 9.1 / 9.2 软件镜像创建独立容器，保留原容器。沿用分别针对 bbb5672 用各自 CANN 编译的 C++ 扩展和选定自定义算子，本轮没有改源码、重装 Python 包或重新编译。W8A8 服务脚本相对之前的 W8A8 MRV1 仅把 VLLM_USE_V2_MODEL_RUNNER 从 0 改为 1；/scripts 内其他文件按 SHA256 核对一致。
- 同一 192.168.9.156 宿主机，Ascend 910B3、驱动 25.5.1；Ascend runtime 非特权容器仅映射物理卡 0–3。npu-smi 与 torch.npu.device_count 均确认仅四卡。两轮顺序执行。
- 两套容器使用同一个只读权重挂载 `/mnt/share/z00943141/qwen-a2-profile-work/models/w8a8`；模型 Eco-Tech/Qwen3-30B-A3B-w8a8，w8a8_dynamic，--quantization ascend。
- MRV2，VLLM_USE_V2_MODEL_RUNNER=1；非 eager，FULL_DECODE_ONLY，capture sizes=[1,2,4,8,16]。TP4、async scheduling、max-num-seqs=16、max-model-len/max-num-batched-tokens=16384、GPU memory utilization=0.9、CPU binding=true。其余 HCCL、NZ、OMP 等服务参数沿用参考 CI。
- 使用相同 GSM8K-in3500-bs400 数据及 streaming chat 客户端。request_rate=0、batch_size=45、temperature=0、ignore_eos=true、max_out_len=1500。每组先执行 CI perf-warm 的 18 请求，再执行 perf 的 180 请求；各 AISBench 调用内部预热 1 请求。
- 每个 CANN 环境各冷启动一次服务；18 请求预热与其后 180 请求正式测试共用该服务，与 CI 流程一致。上一组测试完即停服务再启动下一组，避免跨组 Prefix cache 命中。组内 Prefix caching 按 CI 开启，保留预热带来的缓存影响。
- 每组仅跑一轮正式 profiling 测试，没有额外无 profiling 性能轮。统计日志间隔恢复为参考 CI 的 10 秒；服务端口 8007。

### 核心包版本

| 包 | 两套环境 |
| --- | --- |
| vllm | 0.30.0+empty |
| vllm_ascend | 0.19.1rc2.dev2433+gbbb5672af |
| torch | 2.10.0+cpu |
| torch_npu | 2.10.0.post4 |
| triton_ascend | 3.2.2 |
| transformers | 5.14.1 |
| ais_bench_benchmark | 3.1.20260609 |

### CANN 实际构建

| 组件 | CANN 9.1 | CANN 9.2 |
| --- | --- | --- |
| runtime | 9.1.0 / 20260730_231653901 | 9.2.0 / 20260930_161523958 |
| ops_transformer | 9.1.0 / 20260730_231653901 | 9.2.0 / 20260930_161523958 |
| ops_legacy | 9.1.0 / 20260730_231653901 | 9.2.0 / 20260930_161523958 |
| bisheng-compiler | 9.1.0 / 20260730_231653901 | 9.2.0 / 20260930_161523958 |

自定义算子构建范围为 scatter_nd_update_sk、moe_gating_top_k、moe_gating_top_k_hash、add_rms_norm_bias、rms_norm_cast、transpose_kv_cache_by_block、copy_and_expand_eagle_inputs、inplace_partial_rotary_mul、grouped_matmul_swiglu_quant_weight_nz_tensor_list、dequant_swiglu_quant；两套范围相同。标准量化 GMM 接口使用对应 CANN 原生库。编译时临时限制算子选择，编译后恢复源码；运行源码无修改。该范围未覆盖完整 CI 中的所有其他模型算子，本次不宣称完整镜像与 CI 所有编译产物完全相同。

### Profiling 采样

| 环境 | start / stop HTTP | 等待秒数 | 采样前服务状态 |
| --- | --- | ---: | --- |
| cann910 | 200 / 200 | 1.0007 | Avg prompt throughput: 0.0 tokens/s, Avg generation throughput: 935.7 tokens/s, Running: 16 reqs, Waiting: 29 reqs, NPU KV cache usage: 3.6%, Prefix cache hit rate: 37.6% |
| cann920 | 200 / 200 | 1.0011 | Avg prompt throughput: 0.0 tokens/s, Avg generation throughput: 907.0 tokens/s, Running: 16 reqs, Waiting: 29 reqs, NPU KV cache usage: 3.9%, Prefix cache hit rate: 37.6% |

四个 rank 合并统计；主要 kernel 类型平均耗时如下。

| 类型 | 9.1 us / 次数 | 9.2 us / 次数 | 平均耗时变化 |
| --- | ---: | ---: | ---: |
| GroupedMatmulSwigluQuant | 67.077 / 10944 | 66.317 / 10752 | -1.13% |
| FusedInferAttentionScore | 59.869 / 10944 | 66.278 / 10752 | +10.71% |
| hcom_allReduce_ | 14.106 / 44232 | 14.586 / 43456 | +3.40% |
| GroupedMatmul | 35.183 / 10944 | 37.170 / 10752 | +5.65% |
| Cumsum | 30.284 / 10944 | 30.481 / 10752 | +0.65% |
| QuantBatchMatmulV3 | 14.868 / 21888 | 14.971 / 21504 | +0.69% |
| MoeInitRoutingV3 | 18.114 / 10944 | 17.989 / 10752 | -0.69% |
| split_qkv_rmsnorm_rope_kernel | 15.083 / 10944 | 15.143 / 10752 | +0.40% |
| AscendQuantV2 | 11.034 / 11172 | 9.057 / 10976 | -17.92% |
| MatMulV2 | 8.672 / 11172 | 8.689 / 10976 | +0.20% |
| Cast | 3.535 / 23484 | 3.679 / 23072 | +4.07% |
| MoeGatingTopK | 7.515 / 10944 | 7.937 / 10752 | +5.62% |
| AddRmsNormQuant | 6.681 / 10716 | 7.468 / 10528 | +11.79% |
| MoeTokenUnpermute | 6.213 / 10944 | 6.383 / 10752 | +2.73% |
| ScatterPaKvCache | 5.365 / 10944 | 5.539 / 10752 | +3.24% |
| AddRmsNormBias | 5.151 / 11172 | 5.155 / 10976 | +0.08% |
| hcom_allGather_ | 84.439 / 456 | 86.293 / 448 | +2.20% |
| Abs | 1.380 / 10944 | 1.373 / 10752 | -0.52% |

匹配类型与 Input Shapes 的主要 kernel：

| 类型 / Input Shapes | 9.1 us | 9.2 us | 变化 |
| --- | ---: | ---: | ---: |
| GroupedMatmulSwigluQuant / `"128,2048;128,12,128,16,32;128,384;128;128"` | 67.077 | 66.317 | -1.13% |
| hcom_allReduce_ / `N/A` | 14.106 | 14.586 | +3.40% |
| GroupedMatmul / `"128,192;128,192,2048;;128,2048;;;;128;128"` | 35.183 | 37.170 | +5.65% |
| Cumsum / `N/A` | 30.284 | 30.481 | +0.65% |
| QuantBatchMatmulV3 / `"16,2048;40,128,16,32;1280;1280"` | 18.359 | 18.663 | +1.66% |
| MoeInitRoutingV3 / `"16,2048;16,8"` | 18.114 | 17.989 | -0.69% |
| split_qkv_rmsnorm_rope_kernel / `N/A` | 15.083 | 15.143 | +0.40% |
| AscendQuantV2 / `"16,1024;1024;1024"` | 11.031 | 9.010 | -18.32% |
| QuantBatchMatmulV3 / `"16,1024;64,64,16,32;2048"` | 11.448 | 11.258 | -1.66% |
| MoeGatingTopK / `"16,128;"` | 7.515 | 7.937 | +5.62% |
| AddRmsNormQuant / `"16,2048;16,2048;2048;2048;2048;2048"` | 6.681 | 7.468 | +11.79% |
| MatMulV2 / `"16,2048;128,2048"` | 6.247 | 6.273 | +0.42% |
| MoeTokenUnpermute / `"128,2048;128;16,8"` | 6.213 | 6.383 | +2.73% |
| Cast / `"16,2048"` | 6.114 | 6.430 | +5.17% |

### 与同节点之前的 W8A8 MRV1 比较

| 环境 | MRV1 token/s | MRV2 token/s | 变化 |
| --- | ---: | ---: | ---: |
| CANN 9.1 | 791.6250 | 824.7901 | +4.19% |
| CANN 9.2 | 775.0892 | 813.6934 | +4.98% |

之前 MRV1 数据保留在 `/mnt/share/z00943141/qwen-cibbb-w8a8-profile-20261009-153616`；两次测试使用同节点、模型、物理卡 0–3、18+180 请求协议和 1 秒 profiling。各轮冷启动，但两轮没有交错重复，因此不能排除时间与宿主机负载波动。原始 CI 使用 MRV1；本次达标标注只表示 MRV2 的观测吞吐达到同一 YAML 下限。

本轮两个 CANN 环境各四个 Worker_TP 均出现 upstream V2 专用 model_runner.py:428 的模型加载日志，没有 MRV1 的 gpu_model_runner.py / model_runner_v1.py 执行日志。服务配置开关为 1，历史 Ascend 源码的 runner 选择逻辑直接由此开关控制。

本轮 KV cache layout：CANN 9.1 为 LBNHC，CANN 9.2 为 LBNHC。四个实际 worker 主线程 CPU masks 分别为 194–221、226–253、130–157、162–189；两套一致，原始 /proc 状态快照保留在各组 worker-affinity-verified.json。

本轮 CANN 9.2 相对 9.1 的吞吐变化为 -1.35%；MRV2 相对此前同节点 MRV1，在 CANN 9.1 / 9.2 上分别变化 +4.19% / +4.98%。这些是各轮实际观测值，尚未进行重复测量。

局部 decode 采样中，CANN 9.2 的 FusedInferAttentionScore / GroupedMatmul / allReduce 平均耗时相对 9.1 分别变化 +10.71% / +5.65% / +3.40%，而 GroupedMatmulSwigluQuant 为 -1.13%。部分热点耗时增加与整轮吞吐较低方向一致，但不同窗口的真实 KV 长度、路由及重叠并未严格配对，不能据此确认单一算子是原因。


### 分析边界

本次对照保持模型、两套推理源码与核心 Python 包一致，改变 CANN 软件栈及使用它编译的产物，因此可观察这一套 CANN 版本变更对应的整体性能差异。只有每环境一次正式测量，尚不能排除宿主机 CPU/IO 与运行间波动，也不能由一次结果或单个 kernel 均值确定 CANN 内部某项改动的因果。

采样均在 prompt 吞吐为 0、Running=16 的 decode 阶段。即使 Input Shapes 相同，实际 KV 长度、专家路由和通信重叠仍可能不同。1 秒 profiling 是局部窗口，不能简单累计各 kernel 均值来解释整轮吞吐。两组均包含 profiling 暂停及导出开销；与历史完全无 profiler 的 CI 比较时应保留这一限制。

参考 CI 最终 Prefix cache hit rate=9.9%；本次各组最终值及采样窗口见下。缓存命中率只是服务累计统计，不能仅凭非零命中就认定结果可比，或凭命中差异直接归因。

### Profiling 本地路径（192.168.9.156）

- cann910：`/mnt/share/z00943141/qwen-cibbb-w8a8-mrv2-profile-20261009-213915/cann910-w8a8-profile/profiling`。四 rank 窗口 1.0216, 1.0213, 1.0216, 1.0214s；最终 Prefix hit 9.9%。
- cann920：`/mnt/share/z00943141/qwen-cibbb-w8a8-mrv2-profile-20261009-213915/cann920-w8a8-profile/profiling`。四 rank 窗口 1.0272, 1.0271, 1.0274, 1.0274s；最终 Prefix hit 9.9%。

原始 profiling、trace_view.json 与 kernel_details.csv 均在上述目录。服务/客户端日志、环境验证及复现脚本保留在 `/mnt/share/z00943141/qwen-cibbb-w8a8-mrv2-profile-20261009-213915`。两套模型服务均已停止。本轮新增上传两份 W8A8 AISBench 最终结果日志，分析合并在本 README。

### 最终结果日志

- [CANN 9.1](logs/w8a8-cann910-aisbench-final-result.log)
- [CANN 9.2](logs/w8a8-cann920-aisbench-final-result.log)
