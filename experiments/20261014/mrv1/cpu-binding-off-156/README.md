# MRV1 关闭 CPU 绑核：156 上 BF16 × CANN 9.1 / 9.2

补充两组正式 profiling 实验。与上一组 MRV2 关闭绑核的 BF16 脚本逐文件、逐字节比对，唯一服务配置变化是 `VLLM_USE_V2_MODEL_RUNNER=1` → `0`。`VLLM_USE_V1=1` 与 `enable_cpu_binding=false` 保持不变；没有改源码、重新编译或安装软件。

## 正式结果

| CANN | 输出吞吐 token/s | TPOT | TTFT | E2EL | 成功 / 失败 | 达到原 CI 下限 | 最终日志 |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| 9.1.0 | 782.0327 | 19.1 ms | 47794.3 ms | 76455.1 ms | 180 / 0 | 是 | [AISBench](logs/bf16-cann910-aisbench-final-result.log) |
| 9.2.0 | 770.0517 | 19.4 ms | 48517.8 ms | 77630.9 ms | 180 / 0 | 否 | [AISBench](logs/bf16-cann920-aisbench-final-result.log) |

CANN 9.2 相对 9.1 的输出吞吐变化为 **-1.53%**。CI 下限 778.365054 token/s；本次吞吐包含 profiling 与导出开销，达到下限仅表示观测值满足该指标。

## 与已完成 BF16 实验比较

| CANN | MRV1 开绑核历史单轮 | MRV1 关绑核本轮 | MRV1 关/开变化 | MRV2 关绑核上一轮 | 关绑核 MRV2/MRV1 变化 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 9.1.0 | 781.8579 | 782.0327 | +0.02% | 805.5155 | +3.00% |
| 9.2.0 | 769.1510 | 770.0517 | +0.12% | 795.8386 | +3.35% |

本轮 MRV1 关闭绑核相对历史开启结果，9.1 变化 **+0.02%**，9.2 为 **+0.12%**。两次观测与原结果接近，关闭绑核后 CANN 9.2 仍低于 9.1，且 770.0517 仍低于原 BF16 CI 下限；本轮未观察到关闭绑核消除该差距。关闭绑核条件下，上一轮 MRV2 相对本轮 MRV1 的观测吞吐分别高 **+3.00%**、**+3.35%**。这些是有限样本差异，不能据此确立唯一性能根因。

单位 token/s。开启绑核的 MRV1 数据来自 2026-10-09；关闭绑核的 MRV1/MRV2 来自 2026-10-14，同在 156 的物理卡 0–3。每个关闭组合只有一次，执行时间及顺序不同，不能将差异全部归为开关的因果影响。这个开关同时控制 CPU 绑定及流程中的 NUMA 内存迁移，不能拆成两者各自的效果。

[完整 MRV/CANN/绑核汇总](../../README.md)；[原 MRV1 数据](../../../20261009/mrv1/README.md)；[上一组 MRV2 关闭绑核](../../mrv2/cpu-binding-off-156/README.md)。

## 环境、配置与核验

- 主机 192.168.9.156（worker-156），Ascend 910B3，驱动 25.5.1；Kunpeng-920，256 CPU、8 NUMA nodes。Ascend runtime 容器仅见物理卡 0–3，npu-smi 和 torch device_count 均核验四卡。
- vllm-ascend `0.19.1rc2.dev2433+gbbb5672af`，commit `bbb5672af80b1972c301852aa505b13374fa6355`；vLLM `0.30.0+empty`，commit `ced6857afa0ea7b2e3f0846a62e1394e90f15607`。各组核验 4280 个 Ascend tracked 文件、7159 个 vLLM tracked 文件，均无修改。
- 四个 rank 的实际服务日志均显示 `model_runner_v1.py`，确认运行 MRV1。两个 CANN 环境的七项核心 Python 依赖一致；同 CANN 与上一组 MRV2 BF16 的完整 Python 包列表也一致。CANN 附带软件随 CANN 版本变化，完整元数据见 results.json。
- 复用原固定 Image ID、原只读 BF16 权重和 GSM8K 数据。CANN 9.1 构建标记 20260730_231653901；9.2 为 20260930_161523958。
- TP4、async scheduling、max-num-seqs=16、max-model-len/max-num-batched-tokens=16384、gpu-memory-utilization=0.9，端口 8007；非 eager，FULL_DECODE_ONLY，[1,2,4,8,16]。
- 每组内部预热 1 请求；正式 180 请求，batch_size=45、request_rate=0、temperature=0、ignore_eos=true、每请求输出 1500 tokens。每组输入 656793、输出 270000 tokens，失败 0。
- 每组全新容器和模型服务、独立 vLLM/Triton 编译缓存；串行运行。测试结束停止模型服务，再在对应容器中离线解析。没有清空宿主机系统页缓存。
- 正式轮内部预热后至少 35 秒，在 prompt throughput=0、Running=16 的 decode 窗口采约 1 秒 profiling。start/stop HTTP 200，各组四 rank trace 和 kernel CSV 均解析完成。

## 关闭绑核生效证据

服务没有 `mode=topo_affinity` 绑定记录。八个 worker 主线程、采集的全部 662 条线程记录的允许 CPU 范围均为 0–255；以下 PID 为当时容器内 PID。原开启绑核主线程每 rank 限制为 28 CPU。现场线程快照读取在性能轮内完成，与上一组 MRV2 关闭绑核诊断流程相同。

| CANN | rank | PID | Cpus_allowed_list | 线程记录数 |
| --- | ---: | ---: | --- | ---: |
| 9.1.0 | 0 | 617 | 0–255 | 84 |
| 9.1.0 | 1 | 618 | 0–255 | 83 |
| 9.1.0 | 2 | 619 | 0–255 | 83 |
| 9.1.0 | 3 | 620 | 0–255 | 83 |
| 9.2.0 | 0 | 609 | 0–255 | 83 |
| 9.2.0 | 1 | 610 | 0–255 | 82 |
| 9.2.0 | 2 | 611 | 0–255 | 82 |
| 9.2.0 | 3 | 612 | 0–255 | 82 |

## Profiling 本地路径（192.168.9.156）

| CANN | 开关间隔秒 | 已解析 profiling |
| --- | ---: | --- |
| 9.1.0 | 1.0010 | `/mnt/share/z00943141/qwen-cibbb-bf16-mrv1-nobind-20261014-141901/bf16/cann910-bf16-profile/profiling` |
| 9.2.0 | 1.0011 | `/mnt/share/z00943141/qwen-cibbb-bf16-mrv1-nobind-20261014-141901/bf16/cann920-bf16-profile/profiling` |

服务器批次根目录：`/mnt/share/z00943141/qwen-cibbb-bf16-mrv1-nobind-20261014-141901`。原始 profiling、解析产物、启动日志、实际 runner 和亲和性证据、脚本及配置差异均保留该目录；仓库仅发布两份 AISBench 最终日志、报告和结构化结果。两个模型服务及实验容器已停止。

批次开始：2026-10-14T14:22:33.295393+08:00；结束：2026-10-14T14:51:34.490118+08:00（Asia/Shanghai）。
