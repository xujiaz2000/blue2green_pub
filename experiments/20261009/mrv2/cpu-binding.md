# 两组 MRV2 BF16 的 CPU 绑核证据链

**结论：CANN 9.1 / 9.2 两组的四个 worker 主线程 CPU 亲和性均与 topo_affinity 绑核计划一致。IRQ 亲和性调整未执行。**

本目录对应 2026-10-09 两组 BF16 MRV2 正式测试，vllm-ascend bbb5672、vLLM 0.30.0、TP4、物理卡 0–3。两组输出吞吐为 800.3532 / 799.0187 token/s，各完成 180 请求，失败 0。

## 1. 运行配置

[实际服务脚本](evidence/01_start_server.sh) 设置 `--additional-config '{"enable_cpu_binding":true}'`，MRV2 开关为 1；[与 MRV1 的单行配置差异](evidence/script-config-diff.txt) 一并保存。配置只能说明要求绑核，下面的日志与内核进程快照才验证实际执行结果。

## 2. 运行日志与真实进程一一对应

完整 server.log 保存 Worker_TP 的 rank/PID、`mode=topo_affinity`、CPU 分配计划以及 IRQ 警告。采样前从这份日志取得四个 PID，再读取 `/proc/<pid>/status`。PID 与 rank 的对应关系和捕获顺序可查 [当时的控制脚本](evidence/run.py)。

| 环境 | rank | 实际 PID | 内核 Cpus_allowed_list | 启动绑核计划 |
| --- | ---: | ---: | --- | --- |
| cann910 | 0 | 617 | 194-221 | [server.log 第 286 行](evidence/cann910/server.log#L286) |
| cann910 | 1 | 618 | 226-253 | [server.log 第 290 行](evidence/cann910/server.log#L290) |
| cann910 | 2 | 619 | 130-157 | [server.log 第 278 行](evidence/cann910/server.log#L278) |
| cann910 | 3 | 620 | 162-189 | [server.log 第 282 行](evidence/cann910/server.log#L282) |
| cann920 | 0 | 609 | 194-221 | [server.log 第 286 行](evidence/cann920/server.log#L286) |
| cann920 | 1 | 610 | 226-253 | [server.log 第 290 行](evidence/cann920/server.log#L290) |
| cann920 | 2 | 611 | 130-157 | [server.log 第 282 行](evidence/cann920/server.log#L282) |
| cann920 | 3 | 612 | 162-189 | [server.log 第 278 行](evidence/cann920/server.log#L278) |

四个 rank 分别限制为 28 个逻辑 CPU，两种 CANN 的实际 CPU 范围完全一致。这里的 `/proc/<pid>/status` 对应 worker 主线程，并非所有子线程逐个 TID 的快照。

- CANN 9.1：[完整服务日志](evidence/cann910/server.log)、[绑核日志摘录](evidence/cann910/cpu-binding.log)、[原始进程状态快照](evidence/cann910/worker-affinity-verified.json)。
- CANN 9.2：[完整服务日志](evidence/cann920/server.log)、[绑核日志摘录](evidence/cann920/cpu-binding.log)、[原始进程状态快照](evidence/cann920/worker-affinity-verified.json)。

## 3. 快照采集时点与数据完整性

快照是在 180 请求正式测试进行中、开始 profiling 前保存的留存数据；模型服务在测试结束后已停止。时间与原始文件 SHA256 记录在 [capture-provenance.json](evidence/capture-provenance.json)。

- CANN 9.1：2026-10-09T20:47:24.860000+08:00。
- CANN 9.2：2026-10-09T21:01:49.528000+08:00。

两份原始亲和性 JSON 的本地 SHA256 与服务器源文件哈希一致。每组的 profile-control.json 记录 HTTP 开关时间，可确认亲和性文件先于 start_profile 保存。全部发布文件的 [SHA256SUMS](SHA256SUMS) 与校验脚本一起提供：

```bash
python3 verify_evidence.py
```

校验脚本验证文件哈希、rank/PID 映射、四组 planned / Cpus_allowed_list 的 CPU 集合相等、每个 rank 28 CPU、快照先于采样、180 请求全部成功及 IRQ 警告。

## 4. 证据范围

确认生效的是 worker 主线程 CPU affinity。日志还列出 ACL / release 线程计划，但本次没有保留所有 `/proc/<pid>/task/<tid>/status`，因此不把这些线程计划当作逐线程实际绑定成功的证据。

两组均出现 `/proc/irq is not writable`：IRQ 亲和性调整未执行。日志中的 NUMA migrate 信息也不等于逐页验证完成的内存迁移；本证据链不扩展到 IRQ 或全部内存页绑定。

[两组性能结果及对比分析](README.md)。
