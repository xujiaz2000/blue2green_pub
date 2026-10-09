# Qwen3 A2 性能测试

Qwen3-30B-A3B 在 Ascend A2 上的 CI 吞吐统计、CANN 版本对比、profiling 与 CPU 绑核证据。

```text
ci/                              CI 吞吐统计
  20260908-20261008/
    bf16/
    w8a8/
  20260909-20261009/
    non-pr/
experiments/                     本机对比实验
  20261009/
    mrv1/                        BF16、W8A8 × CANN 9.1 / 9.2
    mrv2/                        BF16 / W8A8 × CANN 9.1 / 9.2
archive/                         历史管理记录
  repo-merge/
```

| 内容 | 入口 |
| --- | --- |
| BF16 月度吞吐 | [统计与折线图](ci/20260908-20261008/bf16/README.md) |
| W8A8 月度吞吐 | [统计与折线图](ci/20260908-20261008/w8a8/README.md) |
| 排除 PR 触发的月度吞吐 | [BF16 / W8A8 统计](ci/20260909-20261009/non-pr/README.md) |
| MRV1 / MRV2 八组完整对比 | [2026-10-09 总报告](experiments/20261009/README.md) |
| MRV1 四组实验 | [结果、分析与完整 profiling](experiments/20261009/mrv1/README.md) · [绑核证据](experiments/20261009/mrv1/cpu-binding.md) |
| MRV2 四组 BF16 / W8A8 实验 | [结果与分析](experiments/20261009/mrv2/README.md) · [BF16 绑核证据](experiments/20261009/mrv2/cpu-binding.md) |

目录采用小写英文与短横线；CI 按统计区间归档，实验按测试日期归档。各实验目录的 README 记录模型、代码节点、CANN 版本和完整运行条件。服务器上的原始实验路径保留在报告中。

原 `blue2gree_pub` 已合并并归档；[合并记录](archive/repo-merge/README.md) 与 [目录迁移表](archive/layout.json) 保留来源和路径对应关系。
