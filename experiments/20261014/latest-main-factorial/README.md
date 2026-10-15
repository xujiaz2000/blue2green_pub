# 最新 main：16 组纯性能实验

vllm-ascend 锁定 2026-10-14T16:33:34.168738+08:00 获取的 main 节点 [`1e15410985`](https://github.com/vllm-project/vllm-ascend/commit/1e15410985615b468f10c9c2dfef3adb7be63deb)；vLLM 固定 **0.30.0+empty**、commit [`ced6857afa`](https://github.com/vllm-project/vllm/commit/ced6857afa0ea7b2e3f0846a62e1394e90f15607)。所有组均不采 profiling。

## 完整结果

输出吞吐单位 token/s；每格为一次独立测试。CANN 差异 = 9.2 / 9.1 − 1。

| 模型 | Runner | CPU 绑核 | CANN 9.1.0 | CANN 9.2.0 | 9.2 相对 9.1 |
| --- | --- | --- | ---: | ---: | ---: |
| BF16 | MRV1 | 开 | [176.9164](mrv1/cpu-binding-on/logs/bf16-cann910-aisbench-final-result.log) | [789.9205](mrv1/cpu-binding-on/logs/bf16-cann920-aisbench-final-result.log) | +346.49% |
| BF16 | MRV1 | 关 | [176.8330](mrv1/cpu-binding-off/logs/bf16-cann910-aisbench-final-result.log) | [786.4353](mrv1/cpu-binding-off/logs/bf16-cann920-aisbench-final-result.log) | +344.73% |
| BF16 | MRV2 | 开 | [178.8631](mrv2/cpu-binding-on/logs/bf16-cann910-aisbench-final-result.log) | [815.3556](mrv2/cpu-binding-on/logs/bf16-cann920-aisbench-final-result.log) | +355.85% |
| BF16 | MRV2 | 关 | [178.6686](mrv2/cpu-binding-off/logs/bf16-cann910-aisbench-final-result.log) | [813.0797](mrv2/cpu-binding-off/logs/bf16-cann920-aisbench-final-result.log) | +355.08% |
| W8A8 | MRV1 | 开 | [154.1893](mrv1/cpu-binding-on/logs/w8a8-cann910-aisbench-final-result.log) | [791.0612](mrv1/cpu-binding-on/logs/w8a8-cann920-aisbench-final-result.log) | +413.05% |
| W8A8 | MRV1 | 关 | [153.9960](mrv1/cpu-binding-off/logs/w8a8-cann910-aisbench-final-result.log) | [789.2985](mrv1/cpu-binding-off/logs/w8a8-cann920-aisbench-final-result.log) | +412.54% |
| W8A8 | MRV2 | 开 | [155.7870](mrv2/cpu-binding-on/logs/w8a8-cann910-aisbench-final-result.log) | [825.2207](mrv2/cpu-binding-on/logs/w8a8-cann920-aisbench-final-result.log) | +429.71% |
| W8A8 | MRV2 | 关 | [155.9398](mrv2/cpu-binding-off/logs/w8a8-cann910-aisbench-final-result.log) | [823.9977](mrv2/cpu-binding-off/logs/w8a8-cann920-aisbench-final-result.log) | +428.41% |

全部 **16/16 组**完成，每组 **180 请求、失败 0、生成 270000 tokens**。正式请求总计 2880、生成 4320000 tokens。

## 主要结论

本轮在相同最新 main 源码、vLLM 0.30.0 和同机隔离四卡下，CANN 9.1 软件栈的吞吐远低于 CANN 9.2，且这一现象同时出现在两个模型、两个 Runner 和绑核开/关组合中。

- BF16：CANN 9.1 为 **176.8330–178.8631**，CANN 9.2 为 **786.4353–815.3556 token/s**。固定 Runner/绑核后，9.1 相对 9.2 低 **77.51%–78.06%**。
- W8A8：CANN 9.1 为 **153.9960–155.9398**，CANN 9.2 为 **789.2985–825.2207 token/s**。固定 Runner/绑核后，9.1 相对 9.2 低 **80.49%–81.12%**。

MRV2 有收益，但没有消除 CANN 9.1 的低吞吐；关闭绑核同样没有恢复性能。因此，本轮不能将这次低吞吐归因于 MRV1 或 CPU 绑核一个开关。
更应检查该 main 节点在 CANN 9.1 下的算子构建与运行路径兼容性。这是根据本轮结果提出的排查方向，尚未定位到具体算子或提交；本轮没有 profiling，不能据此确认某个算子耗时。
此前历史 bbb5672af 节点在 CANN 9.1 下达到过约 780–825 token/s；那一批的编译产物、预热和 profiling 协议不同，只能作为排查线索，不能直接当作仅变更源码的因果对照。

## 分别比较三个因素

每行固定模型和另外两个因素，只改变所比较的因素。正值表示右侧配置更快。

| 比较因素 | 模型 | 固定条件 | 吞吐变化 |
| --- | --- | --- | ---: |
| MRV1 → MRV2 | BF16 | CANN9.1、绑核开 | +1.10% |
| MRV1 → MRV2 | BF16 | CANN9.2、绑核开 | +3.22% |
| MRV1 → MRV2 | BF16 | CANN9.1、绑核关 | +1.04% |
| MRV1 → MRV2 | BF16 | CANN9.2、绑核关 | +3.39% |
| 开绑核 → 关绑核 | BF16 | MRV1、CANN9.1 | -0.05% |
| 开绑核 → 关绑核 | BF16 | MRV1、CANN9.2 | -0.44% |
| 开绑核 → 关绑核 | BF16 | MRV2、CANN9.1 | -0.11% |
| 开绑核 → 关绑核 | BF16 | MRV2、CANN9.2 | -0.28% |
| MRV1 → MRV2 | W8A8 | CANN9.1、绑核开 | +1.04% |
| MRV1 → MRV2 | W8A8 | CANN9.2、绑核开 | +4.32% |
| MRV1 → MRV2 | W8A8 | CANN9.1、绑核关 | +1.26% |
| MRV1 → MRV2 | W8A8 | CANN9.2、绑核关 | +4.40% |
| 开绑核 → 关绑核 | W8A8 | MRV1、CANN9.1 | -0.13% |
| 开绑核 → 关绑核 | W8A8 | MRV1、CANN9.2 | -0.22% |
| 开绑核 → 关绑核 | W8A8 | MRV2、CANN9.1 | +0.10% |
| 开绑核 → 关绑核 | W8A8 | MRV2、CANN9.2 | -0.15% |

CANN 9.1 → 9.2 的八个对比见完整结果表。各组合仅测一轮，不能据此声称统计显著或长期稳定；没有将不同配置混成一个平均值。

## 控制变量与实际核验

- 同一原 A2 主机，Ascend 910B3、driver 25.5.1、Kunpeng-920；隔离物理 NPU 0–3，容器 npu-smi 和 PyTorch 仅见四卡。没有 Docker CPU cpuset 限制。
- vLLM/vllm-ascend 节点及 tracked 源码已逐组核验无修改；同一 CANN 八组的完整 Python 包版本一致，下面的核心包跨 CANN 也一致。
- 每套 CANN 按相同 main 源码完整编译一次 Ascend 自定义算子/C++ 扩展，再冻结为镜像，其八组复用该镜像。跨 CANN 原生二进制分别构建，不共用编译产物。
- TP4、async scheduling、max-num-seqs=16、max-model-len/max-num-batched-tokens=16384、gpu-memory-utilization=0.9、端口8007；非 eager，FULL_DECODE_ONLY，capture sizes=[1,2,4,8,16]。
- GSM8K-in3500-bs400；180 正式请求、batch_size=45、rate=0、temperature=0、ignore_eos=true、每请求输出1500 tokens。两个模型均先跑18个额外预热请求；两次 AISBench 调用各自 internal warmup=1。
- 每组新容器/新服务和独立编译缓存，测试后停服务。绑核、Runner 和四卡检查在额外预热后、正式计时前完成；正式客户端通过文件屏障等待检查结束。
- 归一化 VLLM_USE_V2_MODEL_RUNNER 和 enable_cpu_binding 后，所有组的服务脚本逐字节一致；客户端、数据配置和数据文件也一致。两个模型通过同一脚本的参数切换，W8A8 额外启用 --quantization ascend。
- 实际四 rank Runner 日志与 MRV 开关一致，CPU 主线程亲和性与绑核开关一致；具体核验见配置差异表。
- 跨 CANN 除 SDK/runtime/ops/compiler 外有 13 项附带 Python 包或工具的版本/安装状态差异，比较的是两套 CANN 软件栈。完整原始环境、设备和线程审计记录保留本地。
- 未清除宿主机文件系统页缓存；启动/编译/预热耗时不计入正式吞吐。测试顺序交错，但背景 CPU/IO 负载及时间无法完全相同。

| 核心包 | 16 组统一版本 |
| --- | --- |
| vllm | 0.30.0+empty |
| vllm_ascend | 0.19.1rc2.dev2798+g1e1541098 |
| torch | 2.10.0+cpu |
| torch_npu | 2.10.0.post4 |
| triton_ascend | 3.2.2 |
| transformers | 5.14.1 |
| ais_bench_benchmark | 3.1.20260609 |

## 逐组配置差异

| 顺序 | 模型 | CANN | Runner | enable_cpu_binding | 每 rank 主线程可用 CPU 数 |
| ---: | --- | --- | --- | --- | --- |
| 01 | BF16 | 9.1.0 | MRV1 | true | 28, 28, 28, 28 |
| 02 | BF16 | 9.2.0 | MRV1 | true | 28, 28, 28, 28 |
| 03 | BF16 | 9.2.0 | MRV1 | false | 256, 256, 256, 256 |
| 04 | BF16 | 9.1.0 | MRV1 | false | 256, 256, 256, 256 |
| 05 | BF16 | 9.1.0 | MRV2 | false | 256, 256, 256, 256 |
| 06 | BF16 | 9.2.0 | MRV2 | false | 256, 256, 256, 256 |
| 07 | BF16 | 9.2.0 | MRV2 | true | 28, 28, 28, 28 |
| 08 | BF16 | 9.1.0 | MRV2 | true | 28, 28, 28, 28 |
| 09 | W8A8 | 9.1.0 | MRV2 | true | 28, 28, 28, 28 |
| 10 | W8A8 | 9.2.0 | MRV2 | true | 28, 28, 28, 28 |
| 11 | W8A8 | 9.2.0 | MRV2 | false | 256, 256, 256, 256 |
| 12 | W8A8 | 9.1.0 | MRV2 | false | 256, 256, 256, 256 |
| 13 | W8A8 | 9.1.0 | MRV1 | false | 256, 256, 256, 256 |
| 14 | W8A8 | 9.2.0 | MRV1 | false | 256, 256, 256, 256 |
| 15 | W8A8 | 9.2.0 | MRV1 | true | 28, 28, 28, 28 |
| 16 | W8A8 | 9.1.0 | MRV1 | true | 28, 28, 28, 28 |

本轮为最新 main、统一预热、无 profiling 的独立批次；此前 26 组使用历史 bbb5672af 节点且带 profiling，BF16 预热协议也不同，不能当作仅变更源码的一对实验。

[返回旧批次汇总](../README.md)
