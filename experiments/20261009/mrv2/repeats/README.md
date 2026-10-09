# MRV2 三轮重复：BF16 / W8A8 × CANN 9.1 / 9.2

新增三轮、每轮四组，共 12 组。统计仅包含本目录三轮，之前的单轮 MRV2 留作参考，未混入均值。每组均为冷启动、独立 vLLM/Triton 缓存、180 正式请求和约 1 秒 profiling。

## 吞吐稳定性统计

| 模型 | CANN | 第 1 轮 | 第 2 轮 | 第 3 轮 | 均值 token/s | 样本标准差 | CV | 最小 | 最大 | 达标次数 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| BF16 | cann910 | 806.9349 | 808.3401 | 806.1744 | 807.1498 | 1.0987 | 0.14% | 806.1744 | 808.3401 | 3/3 |
| BF16 | cann920 | 799.3618 | 801.9841 | 802.3243 | 801.2234 | 1.6211 | 0.20% | 799.3618 | 802.3243 | 3/3 |
| W8A8 | cann910 | 826.4111 | 818.0495 | 817.3749 | 820.6118 | 5.0336 | 0.61% | 817.3749 | 826.4111 | 3/3 |
| W8A8 | cann920 | 814.4012 | 811.9460 | 812.7597 | 813.0356 | 1.2506 | 0.15% | 811.9460 | 814.4012 | 3/3 |

样本标准差使用 n−1；CV=样本标准差/均值。BF16 CI 下限 778.365054 token/s，W8A8 为 781.695840 token/s。每组合只有三次，CV 描述本次离散程度，不代表长期稳定性；结果均包含 profiler 开关和导出开销。

## 同轮 CANN 差异

| 模型 | 第 1 轮：9.2/9.1−1 | 第 2 轮 | 第 3 轮 | 三轮配对差异均值 | 均值吞吐之比：9.2/9.1−1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| BF16 | -0.94% | -0.79% | -0.48% | -0.73% | -0.73% |
| W8A8 | -1.45% | -0.75% | -0.56% | -0.92% | -0.92% |

配对差异先计算每轮比例再求均值，与两组均值之比略有不同。本实验每个 CANN 组合按轮次先后执行，没有并发占用四卡；不同轮次调整顺序，减少固定先后顺序带来的偏差。

## 三轮观测结论

BF16：三轮 CANN 9.2 吞吐均低于 9.1；同轮差异范围 -0.94% 至 -0.48%。CANN 9.1 / 9.2 的 CV 为 0.14% / 0.20%，达到 CI 下限次数为 3/3 与 3/3。这里只描述三次观测，不据此保证长期稳定。

W8A8：三轮 CANN 9.2 吞吐均低于 9.1；同轮差异范围 -1.45% 至 -0.56%。CANN 9.1 / 9.2 的 CV 为 0.61% / 0.15%，达到 CI 下限次数为 3/3 与 3/3。这里只描述三次观测，不据此保证长期稳定。

## 实验表与完整结果

| 顺序 | 轮次 | 模型 | CANN | 吞吐 token/s | TPOT | TTFT | E2EL | Duration | 成功/失败 | 日志 |
| ---: | ---: | --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| 1 | 1 | BF16 | cann910 | 806.9349 | 18.5 ms | 46174.9 ms | 73835.4 ms | 334599.4793 ms | 180 / 0 | [AISBench](round-01/logs/bf16-cann910-aisbench-final-result.log) |
| 2 | 1 | BF16 | cann920 | 799.3618 | 18.6 ms | 46578.5 ms | 74498.2 ms | 337769.4393 ms | 180 / 0 | [AISBench](round-01/logs/bf16-cann920-aisbench-final-result.log) |
| 3 | 1 | W8A8 | cann910 | 826.4111 | 17.9 ms | 44705.3 ms | 71543.6 ms | 326713.9156 ms | 180 / 0 | [AISBench](round-01/logs/w8a8-cann910-aisbench-final-result.log) |
| 4 | 1 | W8A8 | cann920 | 814.4012 | 18.2 ms | 45420.8 ms | 72700.3 ms | 331531.9189 ms | 180 / 0 | [AISBench](round-01/logs/w8a8-cann920-aisbench-final-result.log) |
| 5 | 2 | W8A8 | cann920 | 811.9460 | 18.3 ms | 45539.6 ms | 72903.5 ms | 332534.4289 ms | 180 / 0 | [AISBench](round-02/logs/w8a8-cann920-aisbench-final-result.log) |
| 6 | 2 | W8A8 | cann910 | 818.0495 | 18.1 ms | 45198.8 ms | 72338.5 ms | 330053.3718 ms | 180 / 0 | [AISBench](round-02/logs/w8a8-cann910-aisbench-final-result.log) |
| 7 | 2 | BF16 | cann920 | 801.9841 | 18.6 ms | 46398.0 ms | 74211.2 ms | 336665.0292 ms | 180 / 0 | [AISBench](round-02/logs/bf16-cann920-aisbench-final-result.log) |
| 8 | 2 | BF16 | cann910 | 808.3401 | 18.4 ms | 46019.1 ms | 73590.9 ms | 334017.825 ms | 180 / 0 | [AISBench](round-02/logs/bf16-cann910-aisbench-final-result.log) |
| 9 | 3 | BF16 | cann920 | 802.3243 | 18.6 ms | 46402.9 ms | 74213.6 ms | 336522.2573 ms | 180 / 0 | [AISBench](round-03/logs/bf16-cann920-aisbench-final-result.log) |
| 10 | 3 | BF16 | cann910 | 806.1744 | 18.4 ms | 46092.5 ms | 73721.8 ms | 334915.1316 ms | 180 / 0 | [AISBench](round-03/logs/bf16-cann910-aisbench-final-result.log) |
| 11 | 3 | W8A8 | cann910 | 817.3749 | 18.1 ms | 45217.3 ms | 72373.8 ms | 330325.7652 ms | 180 / 0 | [AISBench](round-03/logs/w8a8-cann910-aisbench-final-result.log) |
| 12 | 3 | W8A8 | cann920 | 812.7597 | 18.2 ms | 45502.0 ms | 72839.1 ms | 332201.5059 ms | 180 / 0 | [AISBench](round-03/logs/w8a8-cann920-aisbench-final-result.log) |

所有组输入 656793、输出 270000 tokens；180 正式请求、batch_size=45、request_rate=0、temperature=0、ignore_eos=true、max_out_len=1500。BF16 内部预热 1 请求；W8A8 先 18 请求 perf-warm，两次 AISBench 调用各内部预热 1 请求。

## 一致的代码、配置与隔离

- MRV2；vllm-ascend bbb5672af80b1972c301852aa505b13374fa6355；vLLM ced6857afa0ea7b2e3f0846a62e1394e90f15607、0.30.0+empty。每组分别验证 tracked 源码哈希及实际四个 worker 的 MRV2 加载日志。
- 同一 192.168.9.156 / Ascend 910B3 / driver 25.5.1；非特权 Ascend runtime，仅可见物理卡 0–3，每组开始前检查无其他 NPU 进程。
- 沿用之前对应 CANN 的同一已编译镜像；同模型使用同一份只读权重和相同脚本。仅结果、容器和缓存目录随组次变化，没有源码或 Python 包变更。
- TP4、async scheduling、max-num-seqs=16、max-model-len/max-num-batched-tokens=16384、GPU memory utilization=0.9、CPU binding=true；FULL_DECODE_ONLY，[1,2,4,8,16]，非 eager。
- 稳定 decode（prompt=0、Running=16）时 start_profile → 等待约 1 秒 → stop_profile；两接口均 200，四 rank trace / kernel CSV 均解析完成；组后停模型服务再解析和启动下一组。

批次开始时间：2026-10-09T22:39:03.285038+08:00；完成时间：2026-10-10T02:02:51.254109+08:00。按任务开始日期归档到 20261009，实际运行可能跨午夜。

## Profiling 路径（192.168.9.156）

| 轮次 | 模型 | CANN | 间隔秒 | 本地 profiling |
| --- | --- | --- | ---: | --- |
| 1 | BF16 | cann910 | 1.0001 | `/mnt/share/z00943141/qwen-cibbb-mrv2-repeats-20261009-223525/round-01/bf16/cann910-bf16-profile/profiling` |
| 1 | BF16 | cann920 | 1.0007 | `/mnt/share/z00943141/qwen-cibbb-mrv2-repeats-20261009-223525/round-01/bf16/cann920-bf16-profile/profiling` |
| 1 | W8A8 | cann910 | 1.0010 | `/mnt/share/z00943141/qwen-cibbb-mrv2-repeats-20261009-223525/round-01/w8a8/cann910-w8a8-profile/profiling` |
| 1 | W8A8 | cann920 | 1.0011 | `/mnt/share/z00943141/qwen-cibbb-mrv2-repeats-20261009-223525/round-01/w8a8/cann920-w8a8-profile/profiling` |
| 2 | W8A8 | cann920 | 1.0011 | `/mnt/share/z00943141/qwen-cibbb-mrv2-repeats-20261009-223525/round-02/w8a8/cann920-w8a8-profile/profiling` |
| 2 | W8A8 | cann910 | 1.0011 | `/mnt/share/z00943141/qwen-cibbb-mrv2-repeats-20261009-223525/round-02/w8a8/cann910-w8a8-profile/profiling` |
| 2 | BF16 | cann920 | 1.0011 | `/mnt/share/z00943141/qwen-cibbb-mrv2-repeats-20261009-223525/round-02/bf16/cann920-bf16-profile/profiling` |
| 2 | BF16 | cann910 | 1.0011 | `/mnt/share/z00943141/qwen-cibbb-mrv2-repeats-20261009-223525/round-02/bf16/cann910-bf16-profile/profiling` |
| 3 | BF16 | cann920 | 1.0011 | `/mnt/share/z00943141/qwen-cibbb-mrv2-repeats-20261009-223525/round-03/bf16/cann920-bf16-profile/profiling` |
| 3 | BF16 | cann910 | 1.0011 | `/mnt/share/z00943141/qwen-cibbb-mrv2-repeats-20261009-223525/round-03/bf16/cann910-bf16-profile/profiling` |
| 3 | W8A8 | cann910 | 1.0010 | `/mnt/share/z00943141/qwen-cibbb-mrv2-repeats-20261009-223525/round-03/w8a8/cann910-w8a8-profile/profiling` |
| 3 | W8A8 | cann920 | 1.0008 | `/mnt/share/z00943141/qwen-cibbb-mrv2-repeats-20261009-223525/round-03/w8a8/cann920-w8a8-profile/profiling` |

原始 profiling、解析产物、环境元数据、亲和性快照、启动日志及脚本位于 `/mnt/share/z00943141/qwen-cibbb-mrv2-repeats-20261009-223525`。仓库上传 12 份最终 AISBench 日志、本报告和 results.json；原始 profiling 保留服务器。所有模型服务已停止。

## 与原单轮结果对照及解释范围

| 模型 | CANN | 原单轮 MRV2 token/s | 新三轮均值 | 均值相对原单轮 |
| --- | --- | ---: | ---: | ---: |
| BF16 | cann910 | 800.3532 | 807.1498 | +0.85% |
| BF16 | cann920 | 799.0187 | 801.2234 | +0.28% |
| W8A8 | cann910 | 824.7901 | 820.6118 | -0.51% |
| W8A8 | cann920 | 813.6934 | 813.0356 | -0.08% |

[原 MRV2 单轮报告](../README.md)、[MRV1/MRV2 八组对比](../../README.md)。这些重复仍带 profiling，未增加无 profiler 的对照；宿主机 CPU/IO 共享，三次样本不能单独定位 CANN 内部改动的因果。是否稳定劣化应结合每轮版本差异方向、离散程度和达标次数判断。
