# Qwen3-30B-A3B：全部 26 组实验与环境核验

以下是同一历史 main 节点下已完成的 26 组正式实验：原单轮 8 组、MRV2 三轮复测 12 组、MRV2 关闭绑核 4 组、MRV1 关闭绑核 BF16 2 组。没有重新跑性能测试。

## 全部结果

输出吞吐单位 token/s；每个数值都是独立的一轮测试，点击数值查看 AISBench 最终日志。差异 = CANN 9.2 / 9.1 − 1；三轮复测逐轮展示。日期为 Asia/Shanghai 下实际 profiling 的日期。

| 批次（日期） | 模型 | Runner | CPU 绑核 | CANN 9.1.0 | CANN 9.2.0 | 9.2 相对 9.1 |
| --- | --- | --- | --- | ---: | ---: | ---: |
| 原单轮（10-09） | BF16 | MRV1 | 开 | [781.8579](../20261009/mrv1/logs/bf16-cann910-aisbench-final-result.log) | [769.1510 †](../20261009/mrv1/logs/bf16-cann920-aisbench-final-result.log) | -1.63% |
| 原单轮（10-09） | W8A8 | MRV1 | 开 | [791.6250](../20261009/mrv1/logs/w8a8-cann910-aisbench-final-result.log) | [775.0892 †](../20261009/mrv1/logs/w8a8-cann920-aisbench-final-result.log) | -2.09% |
| 原单轮（10-09） | BF16 | MRV2 | 开 | [800.3532](../20261009/mrv2/logs/bf16-cann910-aisbench-final-result.log) | [799.0187](../20261009/mrv2/logs/bf16-cann920-aisbench-final-result.log) | -0.17% |
| 原单轮（10-09） | W8A8 | MRV2 | 开 | [824.7901](../20261009/mrv2/logs/w8a8-cann910-aisbench-final-result.log) | [813.6934](../20261009/mrv2/logs/w8a8-cann920-aisbench-final-result.log) | -1.35% |
| 复测第1轮（10-09） | BF16 | MRV2 | 开 | [806.9349](../20261009/mrv2/repeats/round-01/logs/bf16-cann910-aisbench-final-result.log) | [799.3618](../20261009/mrv2/repeats/round-01/logs/bf16-cann920-aisbench-final-result.log) | -0.94% |
| 复测第1轮（10-09） | W8A8 | MRV2 | 开 | [826.4111](../20261009/mrv2/repeats/round-01/logs/w8a8-cann910-aisbench-final-result.log) | [814.4012](../20261009/mrv2/repeats/round-01/logs/w8a8-cann920-aisbench-final-result.log) | -1.45% |
| 复测第2轮（10-10） | BF16 | MRV2 | 开 | [808.3401](../20261009/mrv2/repeats/round-02/logs/bf16-cann910-aisbench-final-result.log) | [801.9841](../20261009/mrv2/repeats/round-02/logs/bf16-cann920-aisbench-final-result.log) | -0.79% |
| 复测第2轮（10-10） | W8A8 | MRV2 | 开 | [818.0495](../20261009/mrv2/repeats/round-02/logs/w8a8-cann910-aisbench-final-result.log) | [811.9460](../20261009/mrv2/repeats/round-02/logs/w8a8-cann920-aisbench-final-result.log) | -0.75% |
| 复测第3轮（10-10） | BF16 | MRV2 | 开 | [806.1744](../20261009/mrv2/repeats/round-03/logs/bf16-cann910-aisbench-final-result.log) | [802.3243](../20261009/mrv2/repeats/round-03/logs/bf16-cann920-aisbench-final-result.log) | -0.48% |
| 复测第3轮（10-10） | W8A8 | MRV2 | 开 | [817.3749](../20261009/mrv2/repeats/round-03/logs/w8a8-cann910-aisbench-final-result.log) | [812.7597](../20261009/mrv2/repeats/round-03/logs/w8a8-cann920-aisbench-final-result.log) | -0.56% |
| 关绑核补测（10-14） | BF16 | MRV2 | 关 | [805.5155](../20261014/mrv2/cpu-binding-off-156/logs/bf16-cann910-aisbench-final-result.log) | [795.8386](../20261014/mrv2/cpu-binding-off-156/logs/bf16-cann920-aisbench-final-result.log) | -1.20% |
| 关绑核补测（10-14） | W8A8 | MRV2 | 关 | [803.6051](../20261014/mrv2/cpu-binding-off-156/logs/w8a8-cann910-aisbench-final-result.log) | [813.5922](../20261014/mrv2/cpu-binding-off-156/logs/w8a8-cann920-aisbench-final-result.log) | +1.24% |
| 关绑核补测（10-14） | BF16 | MRV1 | 关 | [782.0327](../20261014/mrv1/cpu-binding-off-156/logs/bf16-cann910-aisbench-final-result.log) | [770.0517 †](../20261014/mrv1/cpu-binding-off-156/logs/bf16-cann920-aisbench-final-result.log) | -1.53% |

† 低于原 CI 下限：BF16 778.365054、W8A8 781.695840 token/s。共 **23/26** 个观测值达到下限。

所有 26 组均为 **180 正式请求、失败 0、生成 270000 tokens**，均采约 **1 秒 profiling**，各组 **4 个 rank 解析完成**。正式请求总计 4680、生成 tokens 7020000。MRV1 关闭绑核的 W8A8 尚未测试。

## 环境是否相同

**固定基础条件一致，但所有实验的完整环境并非完全相同。** 已逐组复核保存的版本与源码证据、运行日志，并只读核对原测试主机上的脚本、容器镜像和扩展库。

一致的条件：

- 所有组使用同一台原 A2 测试主机，Ascend 910B3、driver 25.5.1、Kunpeng-920；均隔离物理 NPU **0–3**，Ascend runtime、非特权容器，容器 npu-smi 仅见四卡，无 Docker CPU cpuset 限制。
- vLLM **0.30.0+empty**，commit `ced6857afa0ea7b2e3f0846a62e1394e90f15607`；vllm-ascend **0.19.1rc2.dev2433+gbbb5672af**，commit `bbb5672af80b1972c301852aa505b13374fa6355`。每组保存的核验记录中，7159 个 vLLM、4280 个 Ascend tracked 文件均无修改。
- torch **2.10.0+cpu**、torch_npu **2.10.0.post4**、triton_ascend **3.2.2**、transformers **5.14.1**、AISBench **3.1.20260609**。同一 CANN 内，13 组的**完整 Python 包版本清单一致**。
- TP4、async scheduling、max-num-seqs=16、max-model-len/max-num-batched-tokens=16384、gpu-memory-utilization=0.9；端口 8007；**非 eager**，FULL_DECODE_ONLY，capture sizes=[1,2,4,8,16]。
- GSM8K 数据和正式客户端参数一致：180 请求、batch_size=45、rate=0、temperature=0、ignore_eos=true、每请求输出 1500 tokens；每组输入 tokens 均为 656793。同模型复用同一路径的只读权重。
- 同模型全部脚本在归一化 **VLLM_USE_V2_MODEL_RUNNER** 与 **enable_cpu_binding** 两个值后逐字节一致，客户端和数据配置未变。实际四 rank Runner 日志与开关一致；开绑核主线程每 rank 28 CPU，关绑核为 0–255。

需要保留的差别：

- **实验变量**：CANN 9.1/9.2、MRV1/MRV2、绑核开/关、BF16/W8A8。CANN runtime/ops/compiler 构建标记分别为 `20260730_231653901`、`20260930_161523958`。跨 CANN 有 **13 项附带 Python 包/工具的版本或安装状态差异**，详细记录保留本地；现有公开的各组环境证据见下方链接。所以跨 CANN 比较的是两套 CANN 软件栈。
- **镜像**：原 W8A8 MRV1 的两个 Image ID 与后续组不同；同 CANN 下完整 Python 包清单、tracked 源码和核验的 **6 个 Ascend 扩展 .so 哈希一致**。其余组按 CANN 复用同一 Image ID。没有据此声称整个镜像文件系统完全相同。
- **模型与预热**：BF16 内部预热 1 请求；W8A8 先额外跑 18 请求 perf-warm，两次 AISBench 调用各内部预热 1 请求。W8A8 使用独立权重和 `--quantization ascend`。同模型内预热协议一致，跨模型不同。
- **批次状态**：测试日期、顺序、主机 CPU/IO 背景不同；关闭绑核组额外读取全部线程亲和性。各组新服务、独立编译缓存，但没有清空系统页缓存。1 秒窗口的 KV 长度和专家路由也未逐 step 对齐；每轮吞吐均包含 profiling 开销。

因此：**同模型、同 CANN 的服务脚本只差 MRV/绑核开关；核心软件版本已拉齐。所有组不能称为完全相同的运行环境，也不能把跨日期单轮的全部差异归因于某一个开关。**

## 结果解读

[仅 BF16：CANN、MRV 与绑核的独立对比报告](bf16-factor-comparison.md)

原开启绑核四个组合中，MRV2 相对 MRV1 均更快；MRV2 开绑核三轮中，CANN 9.2 每轮均略低于 9.1，均值差约 BF16 −0.73%、W8A8 −0.92%。MRV1 BF16 关闭绑核相对原开启仅 +0.02% / +0.12%，CANN 9.2 仍未达到原 CI 下限。MRV2 关闭绑核的 W8A8 则出现 CANN 排序反转，不能认定关闭绑核能统一解决 CANN 性能差异。

每个关闭组合仅一次。上述达标仅指带 profiling 的吞吐观测达到 YAML 下限；稳定因果收益仍需同日交错重复测试。

## 证据与 profiling 路径

- 完整逐组审计记录保留本地；各组 profiling 路径沿用下列已发布报告。
- [原八组完整报告](../20261009/README.md)
- [MRV2 三轮报告](../20261009/mrv2/repeats/README.md)
- [MRV2 关闭绑核四组](mrv2/cpu-binding-off-156/README.md)
- [MRV1 关闭绑核 BF16 两组](mrv1/cpu-binding-off-156/README.md)
- [此前完整汇总分析与 kernel 排查方向](https://github.com/xujiaz2000/blue2green_pub/blob/dde1f9e1c64ed3d0378a824f81885cbd59ffc939/experiments/20261014/README.md)

本表重新核对 26 份最终日志与各组结构化结果；环境核验只读进行，没有启动模型服务。所有本批测试容器当前均已停止。核验范围包括包版本、tracked 源码、同模型脚本、6 个 Ascend 扩展库与只读权重挂载；没有重新全量计算模型权重张量哈希或全镜像哈希。
