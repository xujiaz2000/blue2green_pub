# Qwen3-30B-A3B A2：历史 main 节点的 BF16 / W8A8 × CANN 9.1 / 9.2

四组均在 **vllm-ascend `bbb5672af80b1972c301852aa505b13374fa6355`、vLLM 0.30.0、MRV1** 下执行，每组正式请求 180 条，在稳定 decode 阶段采集约 1 秒 profiling，并解析全部四个 TP rank。

**结果：BF16 在 CANN 9.2 下比 9.1 低 1.63%，W8A8 低 2.09%。两组 CANN 9.1 的观测值达到各自 CI 下限，两组 CANN 9.2 未达到。** 四组均成功 180 条、失败 0 条。

## 历史 CI 依据

| 模型 | 同一历史 main 节点的 CI | CI 输出吞吐 | baseline × threshold | 达标下限 |
| --- | --- | ---: | --- | ---: |
| BF16 | [job 108372470704](https://github.com/vllm-project/vllm-ascend/actions/runs/36225208422/job/108372470704) | 783.3198 token/s | 802.4382 × 0.97 | 778.365054 token/s |
| W8A8 | [job 108372470597](https://github.com/vllm-project/vllm-ascend/actions/runs/36225208422/job/108372470597) | 784.1192 token/s | 805.872 × 0.97 | 781.695840 token/s |

参考 workflow run 为 `36225208422`，workflow HEAD 为 `eb31db4d75622a8043703d2cbb55e9df75e70f98`；CI 日志中实际执行的 vllm-ascend 为 main 历史节点 `bbb5672af80b1972c301852aa505b13374fa6355`。本次使用实际推理源码节点。历史 CI 未开启本次这种手动 profiling，本轮达标标注只表示带 profiling 的观测值超过下限。

配置来源：[BF16 YAML](https://github.com/vllm-project/vllm-ascend/blob/bbb5672af80b1972c301852aa505b13374fa6355/tests/e2e/nightly/single_node/models/configs/Qwen3-30B-A3B-BF16-A2.yaml)、[W8A8 YAML](https://github.com/vllm-project/vllm-ascend/blob/bbb5672af80b1972c301852aa505b13374fa6355/tests/e2e/nightly/single_node/models/configs/Qwen3-30B-A3B-W8A8-A2.yaml)。

## 测试配套与控制条件

| 项目 | 配置 |
| --- | --- |
| 测试日期 / 主机 | 2026-10-09；同一 192.168.9.156 宿主机 |
| 硬件 / 驱动 | Ascend 910B3，单卡 HBM 64 GB；驱动 25.5.1 |
| 隔离 | Ascend runtime 非特权容器，仅映射物理 NPU 0–3；npu-smi 只显示这四卡，torch.npu.device_count()=4 |
| vllm-ascend | bbb5672af80b1972c301852aa505b13374fa6355 |
| vLLM | ced6857afa0ea7b2e3f0846a62e1394e90f15607，v0.30.0 |
| 模型运行器 / 图模式 | MRV1；VLLM_USE_V2_MODEL_RUNNER=0；FULL_DECODE_ONLY，capture sizes=[1,2,4,8,16] |
| 并行与调度 | TP4，async scheduling，max-num-seqs=16 |
| 长度 / 显存 | max-model-len=16384，max-num-batched-tokens=16384，gpu-memory-utilization=0.9 |
| CPU 绑定 | additional-config={"enable_cpu_binding":true}；实际 worker affinity 已保留 |
| 服务端口 / 日志间隔 | 8007 / 10 秒 |
| 客户端 / 数据 | AISBench streaming chat；vllm-ascend/GSM8K-in3500-bs400 |
| 请求参数 | 正式 180 请求，batch_size=45，request_rate=0，temperature=0，ignore_eos=true，max_out_len=1500 |
| BF16 预热 | 只有 perf；客户端内部预热 1 请求，然后正式 180 请求 |
| W8A8 预热 | 先 perf-warm 18 请求，再 perf 180 请求；两次客户端调用各内部预热 1 请求 |
| Profiling | torch / torch_npu，ignore_frontend=true；稳定 decode（prompt=0、Running=16）时 start_profile → 等待约 1 秒 → stop_profile |
| 服务生命周期 | 每个环境冷启动一次；本组内部预热与正式测试使用同一服务；组后停服务，再启动下一组；各组独立 vLLM / Triton 缓存目录 |

BF16 与 W8A8 各自对齐其历史 CI 的预热流程，因此两模型间的吞吐差异不能单独归因于量化。对照重点是同一模型的 CANN 9.1 / 9.2。所有模型服务在测试结束后均已停止。

BF16 模型为 `Qwen/Qwen3-30B-A3B`，dtype=bfloat16、quantization=None；权重只读挂载来自 `/mnt/share/z00943141/qwen-a2-profiling-kit-20261008-022415/models/bf16`。W8A8 为 `Eco-Tech/Qwen3-30B-A3B-w8a8`，使用 `--quantization ascend`；权重只读挂载来自 `/mnt/share/z00943141/qwen-a2-profile-work/models/w8a8`。同一模型的两环境使用同一份权重。权重与容器镜像不包含在本目录。

服务环境变量及完整参数见 [BF16 脚本](reproduce/bf16/scripts/01_start_server.sh)、[W8A8 脚本](reproduce/w8a8/scripts/01_start_server.sh) 和各自 `profile_env.sh`；客户端配置、实际 GSM8K 测试数据、解析脚本与控制器均保存在 `reproduce/`。原始脚本保留当时的路径与容器名，复测时需适配 `experiment.json` 的目录及容器名。

### 核心版本

| 包 | 四组相同版本 |
| --- | --- |
| vllm | 0.30.0+empty |
| vllm_ascend | 0.19.1rc2.dev2433+gbbb5672af |
| torch | 2.10.0+cpu |
| torch_npu | 2.10.0.post4 |
| triton_ascend | 3.2.2 |
| transformers | 5.14.1 |
| ais_bench_benchmark | 3.1.20260609 |

四组均检查了 vllm-ascend 4280 个、vLLM 7159 个 tracked 文件的 Git blob 哈希，无差异。沿用历史节点已经分别在相应 CANN 环境中重编译的 native 扩展及选定自定义算子。两套自定义算子编译范围相同，但未覆盖完整 CI 中所有其他模型算子，不宣称整个镜像与历史 CI 完全一致。

### CANN 构建

| 组件 | CANN 9.1 | CANN 9.2 |
| --- | --- | --- |
| runtime | 9.1.0 / 20260730_231653901 | 9.2.0 / 20260930_161523958 |
| ops_transformer | 9.1.0 / 20260730_231653901 | 9.2.0 / 20260930_161523958 |
| ops_legacy | 9.1.0 / 20260730_231653901 | 9.2.0 / 20260930_161523958 |
| bisheng-compiler | 9.1.0 / 20260730_231653901 | 9.2.0 / 20260930_161523958 |

## 性能结果

| 模型 | CANN | 输出吞吐 token/s | TPOT ms | 相对本模型 9.1 | 达到 CI 下限 | 最终日志 |
| --- | --- | ---: | ---: | ---: | --- | --- |
| BF16 | 9.1 | 781.8579 | 19.1 | +0.00% | 是 | [AISBench](logs/bf16-cann910-aisbench-final-result.log) |
| BF16 | 9.2 | 769.1510 | 19.5 | -1.63% | 否 | [AISBench](logs/bf16-cann920-aisbench-final-result.log) |
| W8A8 | 9.1 | 791.6250 | 18.7 | +0.00% | 是 | [AISBench](logs/w8a8-cann910-aisbench-final-result.log) |
| W8A8 | 9.2 | 775.0892 | 19.1 | -2.09% | 否 | [AISBench](logs/w8a8-cann920-aisbench-final-result.log) |

| 指标 | BF16 9.1 | BF16 9.2 | W8A8 9.1 | W8A8 9.2 |
| --- | ---: | ---: | ---: | ---: |
| TTFT | 47887.7 ms | 48585.7 ms | 46640.3 ms | 47588.0 ms |
| E2EL | 76588.5 ms | 77741.7 ms | 74696.3 ms | 76255.8 ms |
| Benchmark Duration | 345331.3016 ms | 351036.385 ms | 341070.5729 ms | 348347.0195 ms |
| Success Requests | 180 | 180 | 180 | 180 |
| Failed Requests | 0 | 0 | 0 | 0 |
| Total Input Tokens | 656793 | 656793 | 656793 | 656793 |
| Total Generated Tokens | 270000 | 270000 | 270000 | 270000 |
| Concurrency | 39.9209 | 39.8634 | 39.421 | 39.4034 |
| Max Concurrency | 45 | 45 | 45 | 45 |
| 最终 Prefix cache hit rate | 0.5% | 0.5% | 9.9% | 9.9% |

输出吞吐取 AISBench Common Metric 中的 `Output Token Throughput`（全任务生成 tokens / benchmark duration），不是上方逐请求 `OutputTokenThroughput` 平均值。W8A8 的 18 请求 perf-warm 吞吐分别为 536.5508 / 528.5546 token/s，未混入正式 180 请求结果。

## Profiling 结果及分析

| 模型 / CANN | 采样时间（北京时间） | 开启 / 关闭 HTTP | 间隔秒数 | 四 rank trace / kernel CSV | 实际 kernel 时间轴跨度秒 |
| --- | --- | --- | ---: | --- | --- |
| bf16-cann910 | 2026-10-09 18:59:05 | 200 / 200 | 1.0010 | 4 / 4 | 1.0373, 1.0376, 1.0375, 1.0376 |
| bf16-cann920 | 2026-10-09 19:12:27 | 200 / 200 | 1.0010 | 4 / 4 | 1.0407, 1.0407, 1.0405, 1.0407 |
| w8a8-cann910 | 2026-10-09 16:11:28 | 200 / 200 | 1.0010 | 4 / 4 | 1.0285, 1.0282, 1.0283, 1.0285 |
| w8a8-cann920 | 2026-10-09 16:28:40 | 200 / 200 | 1.0004 | 4 / 4 | 1.0220, 1.0225, 1.0219, 1.0225 |

### BF16

| kernel 类型 | 9.1 平均 us / 次数 | 9.2 平均 us / 次数 | 平均耗时变化 |
| --- | ---: | ---: | ---: |
| GroupedMatmul | 89.377 / 20352 | 86.927 / 20352 | -2.74% |
| FusedInferAttentionScore | 62.395 / 10176 | 61.961 / 10176 | -0.69% |
| hcom_allReduce_ | 14.053 / 41128 | 13.998 / 41128 | -0.39% |
| MatMulV2 | 9.229 / 30740 | 9.382 / 30740 | +1.66% |
| MoeInitRoutingV3 | 16.473 / 10176 | 16.361 / 10176 | -0.69% |
| split_qkv_rmsnorm_rope_kernel | 13.872 / 10176 | 13.603 / 10176 | -1.94% |
| AddRmsNormBias | 4.953 / 20352 | 5.153 / 20352 | +4.04% |
| Cast | 3.542 / 22684 | 3.461 / 22684 | -2.28% |
| MoeGatingTopK | 7.482 / 10176 | 7.287 / 10176 | -2.60% |
| MoeTokenUnpermute | 6.409 / 10176 | 6.395 / 10176 | -0.22% |
| ScatterPaKvCache | 5.248 / 10176 | 5.472 / 10176 | +4.27% |
| SwiGlu | 4.286 / 10176 | 4.288 / 10176 | +0.03% |

BF16：9.2 的整体吞吐低 1.63%，TPOT 从 19.1 增至 19.5 ms；GroupedMatmul 平均耗时反而低 2.74%，主要相同 Input Shapes 分别快 2.78% 与 2.64%。MatMulV2、AddRmsNormBias、ScatterPaKvCache 分别慢约 1.66%、4.04%、4.27%。不能归因为 GMM 本体变慢。

每 rank 都有 55915 条 kernel 记录。将已记录 kernel 区间取并集后，CSV 时间轴没有 kernel 记录覆盖的比例，四卡均值从约 8.01% 增至 9.55%；这提示后续关注图执行、提交与同步间隔。该指标不等同于硬件完全空闲，也不能区分 host 等待、未记录设备活动与 profiler 开销。局部时间轴跨度只增加约 0.30%，未完全复现整轮 TPOT 差异。

### W8A8

| kernel 类型 | 9.1 平均 us / 次数 | 9.2 平均 us / 次数 | 平均耗时变化 |
| --- | ---: | ---: | ---: |
| GroupedMatmulSwigluQuant | 66.202 / 10560 | 68.839 / 10176 | +3.98% |
| hcom_allReduce_ | 14.718 / 42680 | 15.643 / 41128 | +6.29% |
| FusedInferAttentionScore | 58.752 / 10560 | 62.321 / 10176 | +6.08% |
| GroupedMatmul | 35.012 / 10560 | 36.581 / 10176 | +4.48% |
| Cumsum | 30.697 / 10560 | 30.037 / 10176 | -2.15% |
| QuantBatchMatmulV3 | 14.898 / 21120 | 15.148 / 20352 | +1.68% |
| MoeInitRoutingV3 | 18.220 / 10560 | 18.497 / 10176 | +1.52% |
| split_qkv_rmsnorm_rope_kernel | 16.832 / 10560 | 15.780 / 10176 | -6.25% |
| AscendQuantV2 | 11.377 / 10780 | 9.177 / 10388 | -19.34% |
| MatMulV2 | 8.763 / 10780 | 8.847 / 10388 | +0.97% |
| Cast | 3.591 / 23540 | 3.435 / 22684 | -4.37% |
| MoeGatingTopK | 7.749 / 10560 | 7.611 / 10176 | -1.78% |

W8A8：9.2 的整体吞吐低 2.09%，TPOT 从 18.7 增至 19.1 ms。采样中 GroupedMatmulSwigluQuant、GroupedMatmul、FusedInferAttentionScore 和 allReduce 的类型平均耗时分别增加约 3.98%、4.48%、6.07%、6.28%；这与整体 decode 变慢方向一致。通信耗时还可能包含等待，attention 的 KV 长度、MoE 路由与重叠也可能不同，不能据此确定某个 CANN 内部改动是唯一根因。

同一模型的两个 CANN 环境具有相同的推理源码、核心包版本、输入/输出 token 数及最终 Prefix cache 命中率。BF16 均为 0.5%，W8A8 均为 9.9%，分别与参考 CI 相同。观测到的下降不能用这些配置或最终缓存命中率差异解释。

各环境只测量一轮正式 profiling benchmark；四组顺序执行，NPU 隔离但宿主机 CPU/IO 仍共享。手动 profiler 的采样、停止和数据导出会扰动请求，因此与无 profiler 历史 CI 的比较保留该限制。类型平均耗时按四个 rank 的全部调用加权；不同调用数与不同实际 KV 长度使累计 kernel 时间不能直接代替整轮吞吐。详细原始证据及匹配形状统计保存在 [results.json](results.json) 和 `environment/`。

## 完整 profiling 下载、合并与解析

四组完整目录分别打包为 tar.gz，保留原始 `PROF_*` 数据、解析后的 `trace_view.json`、`kernel_details.csv` 及其他分析文件；没有只截取部分 trace。归档逐文件对比原目录 SHA256，再按每卷 90 MiB 保存，卷清单及校验值见 `profiling/archives.json`。发布前已实际合并全部九个分卷、解压四组数据，并逐文件验证共 2518 个文件的大小与 SHA256。

下载本目录全部内容后，使用 Python 3.12+：

```bash
# 校验各分卷以及重建后的完整归档哈希，不写解压数据
python3 restore_profiles.py profiling --verify-only
# 合并、校验、解压；再逐文件核对原始数据清单
python3 restore_profiles.py profiling --extract-to profiling/unpacked
```

解压后，每组目录为 `profiling/unpacked/<bf16|w8a8>-<cann910|cann920>/profiling/`。四个 rank 各有 `ASCEND_PROFILER_OUTPUT/trace_view.json` 与 `kernel_details.csv`。

已经解析好的 trace/CSV 可直接使用。需要重新解析时，在对应 CANN 容器加载 CANN、ATB 环境，并使用系统 Python / torch_npu：

```bash
source /usr/local/Ascend/cann/set_env.sh
source /usr/local/Ascend/nnal/atb/set_env.sh
python3 reproduce/bf16/scripts/analysis.py profiling/unpacked/bf16-cann910/profiling
# 其他三组替换上述模型和 CANN 目录名
```

### 156 上的原始路径

- bf16-cann910：`/mnt/share/z00943141/qwen-cibbb-bf16-profile-20261009-184820/cann910-bf16-profile/profiling`。
- bf16-cann920：`/mnt/share/z00943141/qwen-cibbb-bf16-profile-20261009-184820/cann920-bf16-profile/profiling`。
- w8a8-cann910：`/mnt/share/z00943141/qwen-cibbb-w8a8-profile-20261009-153616/cann910-w8a8-profile/profiling`。
- w8a8-cann920：`/mnt/share/z00943141/qwen-cibbb-w8a8-profile-20261009-153616/cann920-w8a8-profile/profiling`。

归档元数据中的文件数、大小和 SHA256 对应本次这四组实际采样，不使用之前其他节点的归档。
