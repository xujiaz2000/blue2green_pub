# MRV2 关闭 CPU 绑核：156 上 BF16 / W8A8 × CANN 9.1 / 9.2

按用户要求先跑一轮、共四组。服务配置仅将 `enable_cpu_binding=true` 改为 JSON 布尔值 `false`；沿用原已编译镜像、vLLM 0.30.0、历史 main vllm-ascend 节点、模型权重、AISBench 参数和 profiling 流程。没有修改模型源码、安装或升级 Python 包。

## 四组正式结果

| 模型 | CANN | 输出吞吐 token/s | TPOT | TTFT | E2EL | 成功 / 失败 | 达到原 CI 下限 | 最终日志 |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| BF16 | 9.1.0 | 805.5155 | 18.4 ms | 46053.5 ms | 73662.2 ms | 180 / 0 | 是 | [AISBench](logs/bf16-cann910-aisbench-final-result.log) |
| BF16 | 9.2.0 | 795.8386 | 18.7 ms | 46732.6 ms | 74752.2 ms | 180 / 0 | 是 | [AISBench](logs/bf16-cann920-aisbench-final-result.log) |
| W8A8 | 9.1.0 | 803.6051 | 18.4 ms | 45760.1 ms | 73283.5 ms | 180 / 0 | 是 | [AISBench](logs/w8a8-cann910-aisbench-final-result.log) |
| W8A8 | 9.2.0 | 813.5922 | 18.2 ms | 45409.8 ms | 72678.9 ms | 180 / 0 | 是 | [AISBench](logs/w8a8-cann920-aisbench-final-result.log) |

同一台 156、关闭绑核条件下，CANN 9.2 相对 9.1：BF16 **-1.20%**，W8A8 **+1.24%**。每组合仅一次，尚不能判断长期稳定性。

BF16 CI 下限为 778.365054 token/s，W8A8 为 781.695840 token/s。原 CI 使用开启 CPU binding 的 A2 环境，这里只作为性能指标参考。

## 与之前开启绑核的历史数据比较

| 模型 | CANN | 156 开启绑核三轮均值 token/s | 156 关闭绑核本轮 | 变化 |
| --- | --- | ---: | ---: | ---: |
| BF16 | 9.1.0 | 807.1498 | 805.5155 | -0.20% |
| BF16 | 9.2.0 | 801.2234 | 795.8386 | -0.67% |
| W8A8 | 9.1.0 | 820.6118 | 803.6051 | -2.07% |
| W8A8 | 9.2.0 | 813.0356 | 813.5922 | +0.07% |

**开启/关闭数据均来自 156 的物理卡 0–3。** 开启绑核参考为 2026-10-09 的三轮均值，本轮关闭绑核在 2026-10-14 执行。使用相同的固定镜像、代码、只读权重及模型/客户端参数；模型服务配置只改 enable_cpu_binding。日期、宿主机背景 CPU/IO 和调度状态仍可能影响结果，而且本轮每组合只有一次，因此这是同机历史对照，不能保证长期稳定性或将全部差异归为开关的因果影响。

[156 三轮开启绑核原始报告](../../../20261009/mrv2/repeats/README.md)。这个配置同时跳过 CPU binding 流程内的 NUMA 内存迁移；本次是整套 CPU binding 优化开关的对比。

## 版本、配置与隔离

- 主机 `192.168.9.156`（worker-156），Ascend A2 910B3、驱动 25.5.1；Kunpeng-920，256 CPU，8 NUMA nodes。物理卡 0–3，非特权 Ascend runtime，容器 npu-smi 和 torch 均仅见四卡。
- vllm-ascend `bbb5672af80b1972c301852aa505b13374fa6355`；vLLM `ced6857afa0ea7b2e3f0846a62e1394e90f15607`、`0.30.0+empty`。逐组核验 Ascend/vLLM tracked 源码无差异，四个 worker 实际运行 MRV2。
- CANN 9.1 和 9.2 直接复用原 12 组的不可变 Image ID，未迁移或重新构建；两环境七项核心 Python 依赖完全一致。CANN 版本和构建元数据记录在 results.json。
- 两个模型直接复用原 12 组实验所在 156 的原模型目录，同路径只读挂载，没有复制或重新下载权重。数据和所有脚本沿用原实验；脚本哈希核验确认只有 01_start_server.sh 改了一个配置值。
- TP4、async scheduling、max-num-seqs=16、max-model-len/max-num-batched-tokens=16384、gpu-memory-utilization=0.9；FULL_DECODE_ONLY，[1,2,4,8,16]，MRV2，端口 8007。
- 每组新容器、独立空 vLLM/Triton 编译缓存、全新模型服务；串行使用同一四卡，每组启动前核验无 NPU 占用。测试后停模型服务，再离线解析并开始下一组。
- 每组 180 正式请求，输入 656793、输出 270000 tokens；batch_size=45、request_rate=0、temperature=0、ignore_eos=true、max_out_len=1500。BF16 内部预热 1 请求；W8A8 先 18 请求 perf-warm，两次 AISBench 调用各内部预热 1 请求。
- 正式轮内部预热结束后至少 35 秒，等待 prompt throughput=0、Running=16 的稳定 decode 窗口；start_profile/stop_profile 均 HTTP 200，间隔约 1 秒；每组四 rank trace 和 kernel CSV 解析完成。吞吐包含 profiler 开关及导出开销。

## 关闭绑核生效证据

以下 PID 是当时容器内 worker PID。四组容器的允许 CPU 范围均为 0–255，所有 worker 主线程都继承相同范围；不再限制到原先每 rank 的 28 个 CPU。服务日志没有执行 `mode=topo_affinity` 绑定流程。已采集全部 worker 的线程亲和性状态，原始快照保留服务器。

| 模型 | CANN | rank | PID | 主线程 Cpus_allowed_list | 采集线程数 |
| --- | --- | ---: | ---: | --- | ---: |
| BF16 | 9.1.0 | 0 | 617 | 0–255 | 84 |
| BF16 | 9.1.0 | 1 | 618 | 0–255 | 83 |
| BF16 | 9.1.0 | 2 | 619 | 0–255 | 83 |
| BF16 | 9.1.0 | 3 | 620 | 0–255 | 83 |
| BF16 | 9.2.0 | 0 | 609 | 0–255 | 83 |
| BF16 | 9.2.0 | 1 | 610 | 0–255 | 82 |
| BF16 | 9.2.0 | 2 | 611 | 0–255 | 82 |
| BF16 | 9.2.0 | 3 | 612 | 0–255 | 82 |
| W8A8 | 9.1.0 | 0 | 617 | 0–255 | 93 |
| W8A8 | 9.1.0 | 1 | 636 | 0–255 | 92 |
| W8A8 | 9.1.0 | 2 | 682 | 0–255 | 92 |
| W8A8 | 9.1.0 | 3 | 728 | 0–255 | 92 |
| W8A8 | 9.2.0 | 0 | 609 | 0–255 | 93 |
| W8A8 | 9.2.0 | 1 | 627 | 0–255 | 92 |
| W8A8 | 9.2.0 | 2 | 672 | 0–255 | 92 |
| W8A8 | 9.2.0 | 3 | 717 | 0–255 | 92 |

## Profiling 路径（192.168.9.156）

| 模型 | CANN | 开关间隔秒 | 本地 profiling |
| --- | --- | ---: | --- |
| BF16 | 9.1.0 | 1.0011 | `/mnt/share/z00943141/qwen-cibbb-mrv2-nobind-20261014-115240/bf16/cann910-bf16-profile/profiling` |
| BF16 | 9.2.0 | 1.0009 | `/mnt/share/z00943141/qwen-cibbb-mrv2-nobind-20261014-115240/bf16/cann920-bf16-profile/profiling` |
| W8A8 | 9.1.0 | 1.0010 | `/mnt/share/z00943141/qwen-cibbb-mrv2-nobind-20261014-115240/w8a8/cann910-w8a8-profile/profiling` |
| W8A8 | 9.2.0 | 1.0011 | `/mnt/share/z00943141/qwen-cibbb-mrv2-nobind-20261014-115240/w8a8/cann920-w8a8-profile/profiling` |

所有原始 profiling、解析产物、配置差异、环境和 CPU 亲和性证据、启动日志及脚本位于 `/mnt/share/z00943141/qwen-cibbb-mrv2-nobind-20261014-115240`。仓库发布四份 AISBench 最终日志、分析报告和结构化结果；原始 profiling 保留服务器。模型服务已停止。

批次开始：2026-10-14T11:56:15.822590+08:00；完成：2026-10-14T13:02:39.603603+08:00。时间使用 Asia/Shanghai。
