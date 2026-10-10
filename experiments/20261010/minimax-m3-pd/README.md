# MiniMax M3：双机 A3 PD 分离，MRV1 / MRV2 对比

测试日期：2026-10-10（北京时间）。两轮仅切换 `VLLM_USE_V2_MODEL_RUNNER=0/1`，其余服务及压测参数一致。两轮各完成 576 个请求，失败数均为 0。

## 实验环境

两台 Ascend A3 服务器，各 16 张 NPU，共 32 张；Prefill、Decode 各占一台。两台运行环境的软件版本已核对一致。

| 项目 | 配置 |
| --- | --- |
| vLLM | `0.30.0+empty`（安装包版本字符串） |
| vLLM Ascend | `0.19.1rc2.dev2667+g7fca7cae5` |
| CANN | `9.2.0`，内部版本 `V100R001C25B114` |
| 镜像 | `swr.cn-north-12.myhuaweicloud.com/base_image/ascend-ci/vllm-ascend:nightly-ci-main-a3` |
| 主模型 | `Eco-Tech_MiniMax-M3-w8a8-0626`，Ascend W8A8 量化 |
| 推测解码 | `MiniMax-M3-EAGLE3-GQA`，推测 token 数为 3 |
| 最大上下文长度 | 263000 tokens |

| 服务参数 | Prefill | Decode |
| --- | --- | --- |
| 并行配置 | DP2 × TP4 × PP2 | DP4 × TP4 × PP1 |
| Pipeline 层数 | 30、30 | 单阶段 |
| 显存利用率 | 0.85 | 0.92 |
| `max-num-batched-tokens` | 8192 | 32768 |
| `max-num-seqs` | 32 | 128 |
| 执行模式 | Eager | `FULL_DECODE_ONLY` |

Runner 选择：MRV2 为 `VLLM_USE_V2_MODEL_RUNNER=1`，MRV1 为 `VLLM_USE_V2_MODEL_RUNNER=0`。两轮均使用前缀缓存和相同 PD 拓扑。

## 压测配置与流程

使用 [aisbench_auto_tools_prefix](https://github.com/rayn-zzz/aisbench_auto_tools_prefix)，工具代码节点为 `ef2b6d8653d57487b622b0dc9db458f8a1e8dec6`，调用 AISBench 测试流式 Chat API。

| 项目 | 配置 |
| --- | --- |
| 数据 | GSM8K 构造的长前缀，单前缀，配置重复率 100% |
| 输入长度 | 配置 131072 tokens；实际每请求 131248 tokens，包含 Chat 格式开销 |
| 输出长度 | 每请求 1024 tokens |
| 正式请求数量 | 576 |
| 并发上限 | 144 |
| 请求速率 | `request_rate=0`，立即发送，受并发上限约束 |
| 接口方式 | 流式 |
| 采样参数 | `temperature=0`，`ignore_eos=True` |
| 请求重试 | `retry=2` |
| 前缀预热 | 先执行 2 个前缀请求，输出长度为 1；AISBench 自身 `num-warmups=0` |
| 工具种子参数 | `seed=1170821076` |

流程：服务启动与 PD 转发验证 → 两个前缀预热请求 → 576 请求、144 并发正式压测 → 汇总性能及 Prefill 缓存命中率。下表统计正式阶段，预热阶段不计入。

## 最终结果

| 指标 | MRV2 | MRV1 |
| --- | --- | --- |
| 成功 / 总请求数 | 576 / 576 | 576 / 576 |
| 失败请求数 | 0 | 0 |
| 最大并发 | 144 | 144 |
| 平均并发 | 134.656 | 130.880 |
| 压测耗时（s） | 323.1390 | 211.3252 |
| 请求吞吐（req/s） | 1.7825 | 2.7257 |
| 输出吞吐（tokens/s） | 1825.2950 | 2791.0734 |
| 平均 E2EL（ms） | 75542.7 | 48017.8 |
| 平均 TTFT（ms） | 7340.9 | 5776.5 |
| TTFT P90（ms） | 17163.4 | 16517.7 |
| TTFT P99（ms） | 24091.6 | 24660.6 |
| 平均 TPOT（ms） | 66.7 | 41.3 |
| TPOT P90（ms） | 79.1 | 44.5 |
| TPOT P99（ms） | 93.4 | 57.9 |
| 输入 token 总数 | 75598848 | 75598848 |
| 输出 token 总数 | 589824 | 589824 |
| Prefill 前缀缓存命中率 | 99.8659% | 99.8659% |

本轮 MRV1 的输出吞吐比 MRV2 高 **52.91%**。两轮脚本重新抽取了 GSM8K 前缀，实际 token 长度相同，但内容及 SHA-256 不同；种子参数未固定该分支的前缀抽取。因此这两轮是相同参数下的实测对比，并非固定输入的严格 A/B 实验，不能将全部差异归因于 Runner。

## 原始结果与日志

| 内容 | MRV2 | MRV1 |
| --- | --- | --- |
| AISBench 最终结果日志 | [最终汇总](mrv2/aisbench-final-result.log) | [最终汇总](mrv1/aisbench-final-result.log) |
| AISBench 完整运行日志 | [日志](mrv2/aisbench.log) | [日志](mrv1/aisbench.log) |
| 总体性能指标 | [JSON](mrv2/gsm8k.json) | [JSON](mrv1/gsm8k.json) |
| 请求指标及分位数 | [CSV](mrv2/gsm8k.csv) | [CSV](mrv1/gsm8k.csv) |
| 性能和缓存汇总 | [汇总](mrv2/summary.json) | [汇总](mrv1/summary.json) |
| 输入数据哈希 | [SHA-256](mrv2/dataset-sha256.txt) | [SHA-256](mrv1/dataset-sha256.txt) |

JSON、CSV、完整日志和汇总 JSON 均保留原始字节；最终结果日志截取原始日志最后一组性能表及其后内容。原始日志时间为 UTC，实验日期说明采用北京时间。文件校验清单见 [SHA256SUMS](SHA256SUMS)。

## Decode profiling

[MRV1 / MRV2 全部 Decode profiling](profiling/README.md)：每轮 DP0–DP3 四个实例、16 个 worker，共 32 份原始数据及解析结果，压缩包位于仓库 Release。之前的 DP0 子集仍保留。本次 AISBench 在采集成功后提前结束。
