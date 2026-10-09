# MRV1 四组测试的 CPU 绑核证据链

**BF16 / W8A8 × CANN 9.1 / 9.2 四组的全部 16 个 worker 主线程，实际 CPU 亲和性均与 topo_affinity 计划一致。**

本证据补充于既有 2026-10-09 实验，没有重新启动模型或改变亲和性。四组使用 vllm-ascend `bbb5672af80b1972c301852aa505b13374fa6355`、vLLM 0.30.0、MRV1、TP4、物理 NPU 0–3。各组正式 180 请求、失败 0，采集约 1 秒 profiling。

## 配置 → 服务日志 → 内核快照

[BF16 服务脚本](evidence/config/bf16/01_start_server.sh) 与 [W8A8 服务脚本](evidence/config/w8a8/01_start_server.sh) 都设置 `VLLM_USE_V2_MODEL_RUNNER=0` 和 `enable_cpu_binding=true`。完整日志中的 `gpu_model_runner.py` 记录可同时确认实际使用 MRV1。

控制器在正式性能测试过程中、调用 `start_profile` 之前，从服务日志识别 Worker_TP rank/PID，再通过容器内 `/proc/<pid>/status` 取得真实 CPU 掩码；[BF16 控制器](evidence/config/bf16/run.py)、[W8A8 控制器](evidence/config/w8a8/run.py) 保存了这一采集顺序。

| 模型 / 环境 | rank | 实际 PID | 内核 Cpus_allowed_list | 日志分配计划 |
| --- | ---: | ---: | --- | --- |
| bf16-cann910 | 0 | 617 | 194-221 | [server.log 第 282 行](evidence/bf16-cann910/server.log#L282) |
| bf16-cann910 | 1 | 618 | 226-253 | [server.log 第 286 行](evidence/bf16-cann910/server.log#L286) |
| bf16-cann910 | 2 | 619 | 130-157 | [server.log 第 289 行](evidence/bf16-cann910/server.log#L289) |
| bf16-cann910 | 3 | 620 | 162-189 | [server.log 第 294 行](evidence/bf16-cann910/server.log#L294) |
| bf16-cann920 | 0 | 609 | 194-221 | [server.log 第 293 行](evidence/bf16-cann920/server.log#L293) |
| bf16-cann920 | 1 | 610 | 226-253 | [server.log 第 285 行](evidence/bf16-cann920/server.log#L285) |
| bf16-cann920 | 2 | 611 | 130-157 | [server.log 第 281 行](evidence/bf16-cann920/server.log#L281) |
| bf16-cann920 | 3 | 612 | 162-189 | [server.log 第 289 行](evidence/bf16-cann920/server.log#L289) |
| w8a8-cann910 | 0 | 617 | 194-221 | [server.log 第 298 行](evidence/w8a8-cann910/server.log#L298) |
| w8a8-cann910 | 1 | 636 | 226-253 | [server.log 第 303 行](evidence/w8a8-cann910/server.log#L303) |
| w8a8-cann910 | 2 | 681 | 130-157 | [server.log 第 306 行](evidence/w8a8-cann910/server.log#L306) |
| w8a8-cann910 | 3 | 728 | 162-189 | [server.log 第 295 行](evidence/w8a8-cann910/server.log#L295) |
| w8a8-cann920 | 0 | 609 | 194-221 | [server.log 第 299 行](evidence/w8a8-cann920/server.log#L299) |
| w8a8-cann920 | 1 | 627 | 226-253 | [server.log 第 303 行](evidence/w8a8-cann920/server.log#L303) |
| w8a8-cann920 | 2 | 672 | 130-157 | [server.log 第 295 行](evidence/w8a8-cann920/server.log#L295) |
| w8a8-cann920 | 3 | 717 | 162-189 | [server.log 第 307 行](evidence/w8a8-cann920/server.log#L307) |

每个 rank 的主线程限制为 28 个逻辑 CPU。四组的同 rank CPU 范围完全相同。完整日志、绑核摘录、原始 `/proc` 快照及环境与性能元数据按组保存在以下目录：

- [bf16-cann910](evidence/bf16-cann910)：输出吞吐 781.8579 token/s；亲和性快照源文件保存时间（北京时间）2026-10-09T18:59:05.100000+08:00。
- [bf16-cann920](evidence/bf16-cann920)：输出吞吐 769.151 token/s；亲和性快照源文件保存时间（北京时间）2026-10-09T19:12:27.440000+08:00。
- [w8a8-cann910](evidence/w8a8-cann910)：输出吞吐 791.625 token/s；亲和性快照源文件保存时间（北京时间）2026-10-09T16:11:28.924000+08:00。
- [w8a8-cann920](evidence/w8a8-cann920)：输出吞吐 775.0892 token/s；亲和性快照源文件保存时间（北京时间）2026-10-09T16:28:40.776000+08:00。

## 原始证据与校验

[capture-provenance.json](evidence/capture-provenance.json) 记录 156 源文件路径、SHA256 与源文件 mtime。mtime 表示文件保存时点，不冒充逐个 PID 的读取时间；每组快照保存时间均早于该组 profile-control.json 的 start_profile 调用。重新读取的四份原始快照与先前已公布 JSON 内容一致。

[校验脚本](evidence/verify_evidence.py) 验证文件哈希、MRV1 配置、实际日志 rank/PID 对应、16 个 CPU 掩码与计划相等、每 rank 28 CPU、快照先于采样以及 180 请求全部成功：

```bash
cd experiments/20261009/mrv1/evidence
python3 verify_evidence.py
```

## 证据范围与限制

实际确认的是 worker 主线程 CPU affinity。日志另有 ACL / release 线程绑核计划，但没有保存所有 `/proc/<pid>/task/<tid>/status`，因此不能扩展为所有子线程都逐一验证成功。四组均提示 `/proc/irq is not writable`，IRQ 亲和性调整未执行。NUMA migrate 日志与 Mems_allowed_list 也不能证明所有内存页都完成迁移。

同模型两个 CANN 的主线程绑定结果一致，当前吞吐差异不能用主线程绑核一组成功、一组失败解释。[原有性能结果、profiling 与分析](README.md)。
