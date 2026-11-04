# Qwen3-30B-A3B W8A8 A2：Nightly 环境复现与三轮重复

实验日期为 **2026-11-03（Asia/Shanghai）**，2026-11-04 整理上传。目标是复现 [Nightly-A2 (scheduled) 的 qwen3-30b-a3b-w8a8-a2-performance](https://github.com/vllm-project/vllm-ascend/actions/runs/41327490550/job/124914290773)，其正式输出吞吐为 **767.3497 token/s**；用户期望约 **802 token/s**。

先按用户选择，使用刚拉取的滚动镜像原样测试，再用对应历史 CI 构建的固定 arm64 镜像测试和补跑。**本机四轮有效测试均超过 802，未复现 CI 低吞吐。** 固定 CI 镜像三轮为 **818.2533 / 820.0483 / 827.4128 token/s**，均值 **821.9048**，样本 CV **0.5906%**。这些本机重复只能描述本机波动；真实 GitHub CI runner 未重跑，CI 侧波动和根因仍待验证。

用户要求的 Ascend 回退条件是“本机也复现接近 CI、且低于 802 的结果”。本次没有触发该条件，因此**没有执行 `bbb5672` 回退测试**，本报告不包含其假设性结果。临时 CI 门限没有作为判断优化是否恢复的依据。

## 结果与门限

以下均为 **180 正式请求**的 AISBench 汇总，未将 18 请求的 `perf-warm` 结果混入。三轮统计包含此前的 `ci_pinned02` 一轮和新增的 `ci_pinned03`、`ci_pinned04` 两轮；`ci_pinned01` 是失败的设备预检，不是有效性能样本。

| 环境 / 轮次 | 输出吞吐 token/s | 平均 TPOT ms | 平均 TTFT ms | 平均 E2EL ms | 正式时长 ms | 成功 / 失败 | 证据 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 目标 CI | 767.3497 | 19.3 | 48035.8 | 77018.9 | 351860.4314 | 180 / 0 | [CI 日志存档](evidence/ci_job_124914290773.txt) |
| 滚动镜像原样 | 816.8281 | 18.1 | 45154.2 | 72318.1 | 330546.8913 | 180 / 0 | [结果](evidence/latest_baseline01/result.json) · [环境](evidence/latest_baseline01/environment.json) · [服务日志](evidence/latest_baseline01/pytest.log) · [AISBench](evidence/latest_baseline01/aisbench_formal_stdout.txt) |
| 固定 CI 镜像第 1 轮 | 818.2533 | 18.0 | 44953.3 | 72004.3 | 329971.1644 | 180 / 0 | [结果](evidence/ci_pinned02/result.json) · [环境](evidence/ci_pinned02/environment.json) · [服务日志](evidence/ci_pinned02/pytest.log) · [AISBench](evidence/ci_pinned02/aisbench_formal_stdout.txt) |
| 固定 CI 镜像第 2 轮（补测） | 820.0483 | 18.0 | 44949.2 | 71981.7 | 329248.8936 | 180 / 0 | [结果](evidence/ci_pinned03/result.json) · [环境](evidence/ci_pinned03/environment.json) · [服务日志](evidence/ci_pinned03/pytest.log) · [AISBench](evidence/ci_pinned03/aisbench_formal_stdout.txt) |
| 固定 CI 镜像第 3 轮（补测） | 827.4128 | 17.8 | 44496.4 | 71249.4 | 326318.3858 | 180 / 0 | [结果](evidence/ci_pinned04/result.json) · [环境](evidence/ci_pinned04/environment.json) · [服务日志](evidence/ci_pinned04/pytest.log) · [AISBench](evidence/ci_pinned04/aisbench_formal_stdout.txt) |

| 固定 CI 镜像三轮统计 | 值 |
| --- | ---: |
| 样本数 | 3 |
| 均值 token/s | 821.9048 |
| 中位数 token/s | 820.0483 |
| 样本标准差（n−1）token/s | 4.8538 |
| CV（样本标准差 / 均值） | 0.5906% |
| 最小 / 最大 token/s | 818.2533 / 827.4128 |
| 极差 / 均值 | 1.1144% |
| 本机均值相对目标 CI | +7.1095% |
| 超过 802 次数 | 3 / 3 |

完整机器可读数据为 [results.json](results.json)、[results.csv](results.csv) 和 [三轮统计](evidence/repeat_summary.json)。所有有效轮次均为输入 **656793**、输出 **270000** tokens；每轮 180 请求全部成功。最新滚动镜像的单轮不计入固定 CI 镜像均值。

| 判定口径 | baseline | threshold | 下限 token/s | 本机四轮 |
| --- | ---: | ---: | ---: | --- |
| 用户期望的绝对性能目标 | 802 | — | 802 | 全部超过 |
| 用户原门限 | 802 | 0.97 | 777.94 | 全部通过 |
| 原 W8A8 用例 baseline | 805.872 | 0.97 | 781.69584 | 全部通过 |
| 本次 CI YAML 中的临时门限 | 765 | 0.97 | 742.05 | 全部通过 |

保留原 CI YAML 的临时 baseline=765 是为了复现该 job；没有把临时通过当作恢复到 802，也没有修改项目中的性能门限。

## 时间、范围与隔离

| 轮次目录 | runner 启动时间 | runner 完成时间 |
| --- | --- | --- |
| `latest_baseline01` | 2026-11-03 17:09:23 +08:00 | 2026-11-03 17:24:55 +08:00 |
| `ci_pinned02` | 2026-11-03 17:29:45 +08:00 | 2026-11-03 17:45:46 +08:00 |
| `ci_pinned03` | 2026-11-03 18:54:23 +08:00 | 2026-11-03 19:10:09 +08:00 |
| `ci_pinned04` | 2026-11-03 19:10:15 +08:00 | 2026-11-03 19:26:06 +08:00 |

时间为北京时间；包含启动、模型加载、编译、预热、正式测量及清理，区别于上表的正式压测时长。补跑串行执行，同一时刻仅一套实验容器使用 NPU0–3；每轮前检查无其他 NPU0–3 进程。每轮重新启动服务，使用独立 vLLM / Triton / TorchInductor 缓存目录。全局 CANN 缓存和 OS 文件缓存没有强制清空。

本次未采集 profiler；`detailed_telemetry=false`。仅每 30 秒记录基础 cgroup、进程 status/schedstat 等只读快照。CPU 策略保持 **ondemand**，没有人为锁定频率；执行前后的 governor 和频率上下限相同，不能将其表述为“实际频率恒定”。

## 镜像与代码版本

| 项目 | 用户指定滚动镜像当时的内容 | 对应历史 CI 的固定镜像 |
| --- | --- | --- |
| vLLM commit | `5df63a7203cdb9328d824a27b682e77c7b9928be` | 相同 |
| vLLM package | `0.32.0+empty` | 相同 |
| vllm-ascend commit | `23e0e3764293f0c85ebf96c1383fbbf431b8fbb3` | `b3b82c137ee242a774c29b56325133771f5f069d` |
| vllm-ascend package | `0.19.1rc2.dev3276+g23e0e3764` | `0.19.1rc2.dev3242+gb3b82c137` |
| Python | `3.12.16` | 相同 |
| torch | `2.10.0+cpu` | 相同 |
| torch-npu | `2.10.0.post7` | `2.10.0.post4` |
| triton | `3.6.0` | `3.5.0` |
| triton-ascend | `3.6.0.post2` | `3.2.2` |
| transformers | `5.19.0` | 相同 |
| AISBench | `3.1.20260609` | 相同 |
| numpy / datasets | `1.26.4` / `3.6.0` | 相同 |
| CANN | `9.2.1` | 相同 |
| CANN innerversion | `V100R001C12SPC002B201` | 相同 |

完整 pip 列表及环境见 [滚动镜像审计](evidence/pulled_image_audit.json)、[固定镜像审计](evidence/ci_pinned_image_audit.json)、各轮 `environment.json`。滚动镜像与固定镜像共有 [12 项 Python 包差异](evidence/package_diff_all.json)，因此两者的性能差不能单独归因于 Ascend 提交。

镜像仓库：`swr.cn-north-12.myhuaweicloud.com/base_image/ascend-ci/vllm-ascend`。

| 用途 | 固定引用 |
| --- | --- |
| 当时拉取的 `nightly-ci-main-a2` | `@sha256:076d9edae928079d9863b748a1ed56e7dd3ea1e271fd1ddc3a2b18346a14e874` |
| 历史 CI arm64 镜像 | `@sha256:51acbdd308d677c4add19eee604174fbc29eff784d46675968e82c8e1299b9df` |
| 历史发布 tag | `nightly-ci-main-a2-cann9.2.1-20261101-r63` |

历史镜像来自 [构建 run 41318495994](https://github.com/vllm-project/vllm-ascend/actions/runs/41318495994)，由 [merge job 124903756474](https://github.com/vllm-project/vllm-ascend/actions/runs/41318495994/job/124903756474) 在 **2026-11-01 16:07:48 UTC** 发布，早于目标性能 job。其代码节点、CANN 和核心包版本与目标 job 匹配。**目标 job 只记录了滚动 tag，没有记录实际解析的 digest**，因此固定镜像是对应历史构建的可复现引用，不是从该 job 直接取得的镜像字节身份证明。

来源存档：[arm64 构建日志](evidence/ci_image_build_arm64.txt)、[多架构发布日志](evidence/ci_image_merge_124903756474.txt)、[构建 jobs](evidence/ci_image_jobs.json)。固定镜像三轮的 Python 包版本、Ascend 原生 `.so` 哈希及 tracked 源码状态逐项相同，见 [一致性校验](evidence/repeat_validation.json)。原生哈希范围是 Ascend 仓库内的扩展，镜像 digest 才用于固定整个镜像。

## 本机硬件、驱动与容器

公开记录以 `A2_LOCAL_HOST` / `a2-local.example` 替代真实连接地址及主机名；保留实验路径、容器名、拓扑和性能数值。

| 项目 | 实际环境 |
| --- | --- |
| 宿主 OS / kernel | Ubuntu 22.04；`5.15.0-94-generic`，aarch64 |
| CPU | Kunpeng-920，4 sockets × 64 cores，256 逻辑核，1 thread/core |
| NUMA | 8 nodes，每 node 32 cores |
| 内存 | 约 2 TiB |
| CPU 调频 | `ondemand`，允许 200000–3000000 kHz；未手动锁频 |
| 容器 CPU / memory quota | `cpu.max=max 100000`；`memory.max=max`；未观察到 CPU throttling |
| cpuset | CPU `0-255`，memory nodes `0-7` |
| NPU | 8 × Ascend 910B3，单卡 65536 MiB HBM；实验只用物理卡 0–3 |
| driver / npu-smi | `25.5.2` |
| NPU0 firmware | `7.8.0.6.201`；本次没有刷固件 |
| Docker | `29.1.3` |
| 容器网络 / shm | host network；32 GiB shm |
| 容器权限 | non-privileged，显式设备映射和驱动只读挂载；没有额外安装 Ascend Docker runtime 插件 |
| 输入和结果 | NFS `/mnt/share`；输入只读挂载，结果独立目录 |

设备映射为 `/dev/davinci0`–`/dev/davinci3`、`/dev/davinci_manager`、`/dev/devmm_svm`、`/dev/hisi_hdc`。只读挂载 `/usr/local/Ascend/driver`、`/usr/local/dcmi`、`/usr/local/bin/npu-smi`、`/etc/ascend_install.info`，宿主存在时再挂载 `/usr/lib64/aicpu_kernels`。完整创建参数及 Docker inspect 位于 [remote_metadata](evidence/remote_metadata/)。

| NPU / rank | NUMA | 本机 main CPU | acl | release | CI main CPU |
| ---: | ---: | --- | ---: | ---: | --- |
| 0 | 6 | 194–221（28 核） | 222 | 223 | 146–165（20 核） |
| 1 | 7 | 226–253（28 核） | 254 | 255 | 170–189（20 核） |
| 2 | 4 | 130–157（28 核） | 158 | 159 | 98–117（20 核） |
| 3 | 5 | 162–189（28 核） | 190 | 191 | 122–141（20 核） |

四 rank 均输出 CPU 分配方案，无 `Bind cpus failed`；`runtime.jsonl` 中实际 `/proc` 亲和性与分配一致。NUMA 页迁移没有独立验证，`[migrate]` 日志本身不能证明物理页已成功迁移。`/proc/irq` 不可写的跳过记录在 CI 和本机都有，不作为本次独有差异。

证据：[复跑前宿主快照](evidence/repeats_before_host_snapshot.json)、[第 2 轮后](evidence/ci_pinned03_after_host_snapshot.json)、[第 3 轮后](evidence/ci_pinned04_after_host_snapshot.json)、[容器采集](evidence/repeat_environment.json)、[测试后 NPU 状态](evidence/npu_smi_after_measurements.txt)。前后 CPU governor 和频率上下限的校验均通过。

### 宿主准备记录

初始主机没有 Docker、Ascend 设备节点和可用驱动。安装 Docker、DKMS/build 工具、numactl 等后，使用正确的 **910b 25.5.2 arm64** 驱动安装包，内置完整性检查通过，安装返回 0，未重启即识别 8 张健康 910B3。此前通用 910 包因设备型号不符被安装器拒绝，没有强制安装。

- 正确安装包 URL 及流程：[install_910b.py](evidence/install_910b.py)。
- 文件大小 **120936131 bytes**；SHA256 **`96863152f7aa416246119690c5f9f290e573b3e4e864e5d0e78e47a060db0bfd`**。
- [安装状态](evidence/remote_setup/driver_910b_status.json)、[910b 安装日志](evidence/remote_setup/driver_910b_install.log)、[初始主机记录](evidence/host_preflight_initial.json)。
- 宿主 apt 源从 HTTP 改为 HTTPS以完成安装，保留了原文件备份；没有进行整机发行版升级。

驱动安装脚本属于这台新机器的准备记录。已有健康 25.5.2 驱动的 A2 可以直接进入镜像复现步骤；不会需要上传或重装镜像外的大型驱动二进制。

## 模型、数据与实际请求一致性

| 项目 | 值 |
| --- | --- |
| 模型 | `Eco-Tech/Qwen3-30B-A3B-w8a8` |
| 数据集 | `vllm-ascend/GSM8K-in3500-bs400` |
| 数据加载 | ModelScope `snapshot_download`，当时默认 `master`；之后只读挂载 |
| 容器内模型 / 数据 | `/inputs/model` / `/inputs/dataset` |
| dataset test.jsonl SHA256 | `2beccaa48329cfaee02c28583ca17863bfe27fc80e162370d0ed5cf2475a1d9b` |
| 正式请求 | 前 180 条，stream chat，host_ip=`localhost` |
| 并发 / request_rate | 45 / 0 |
| 输出长度 / temperature | 每请求 1500 tokens / 0 |
| ignore_eos | true |
| 预热 | 18 请求 perf-warm；每次 AISBench 调用另有内部 `num_warmups=1` |

从目标 CI 的 [artifact 13093366197](https://github.com/vllm-project/vllm-ascend/actions/runs/41327490550/artifacts/13093366197) 取得实际生成配置、请求明细和时序数据库。**180 条实际输入内容、顺序、逐请求输入/输出 token 数和成功状态与本机完全一致**；实际 AISBench 配置只有时间标识、路径、模型服务名和随机端口等预期差异。见 [实际请求比较](evidence/actual_request_comparison.json)、[CI 原始 artifact ZIP](evidence/ci_qwen3_w8a8_41327490550.zip)。

CI 日志对已有 ModelScope 缓存给出了无法确认 `master` revision 的警告，未提供权重文件哈希。本机保存了模型配置、数据文件哈希和下载状态，但没有独立重算全部权重内容的 SHA256。因此本机重复使用相同只读权重这一条件成立，**CI 历史权重与本机权重的字节一致性仍未证实**。

CI 与本机、以及本机相同镜像两轮之间，1500-token 完整生成文本都不是逐字相同；相同输入不保证本用例连续批次中的完整长输出逐字一致。本机包和扩展哈希相同的控制中也出现这种差异，因此不能仅凭输出文本差异认定权重或代码不同。批次构成、数值行为和 MoE 路由的具体影响没有单独量化。

## 服务参数与环境变量

核心服务命令如下；端口由测试框架分配，模型参数替换为只读本地路径：

```bash
vllm serve /inputs/model \
  --async-scheduling --tensor-parallel-size 4 --port "$SERVER_PORT" \
  --max-num-seqs 16 --max-model-len 16384 --max-num-batched-tokens 16384 \
  --gpu-memory-utilization 0.9 --trust-remote-code \
  --additional-config '{"enable_cpu_binding":true}' \
  --compilation-config '{"cudagraph_mode":"FULL_DECODE_ONLY","cudagraph_capture_sizes":[1,2,4,8,16]}' \
  --quantization ascend
```

| 变量 | 值 |
| --- | --- |
| `ASCEND_RT_VISIBLE_DEVICES` / `ASCEND_VISIBLE_DEVICES` | `0,1,2,3` |
| `HCCL_BUFFSIZE` / `HCCL_OP_EXPANSION_MODE` | `512` / `AIV` |
| `OMP_NUM_THREADS` / `OMP_PROC_BIND` | `1` / `false` |
| `PYTORCH_NPU_ALLOC_CONF` | `expandable_segments:True` |
| `TASK_QUEUE_ENABLE` / `VLLM_ASCEND_ENABLE_NZ` | `1` / `2` |
| `NPU_MEMORY_FRACTION` | `0.95`（原 YAML）；serve 的 gpu-memory-utilization 为 0.9 |
| `VLLM_WORKER_MULTIPROC_METHOD` | `spawn` |
| `VLLM_USE_V2_MODEL_RUNNER` | unset，使用该版本默认 MRV2 |
| `HF_HUB_OFFLINE` / `HF_DATASETS_OFFLINE` | `1` / `1` |
| `VLLM_USE_MODELSCOPE` | `true` |
| `VLLM_ENGINE_READY_TIMEOUT_S` | `1800` |
| vLLM / Triton / Inductor cache | `/results/<run>/cache/{vllm,triton,torchinductor}` |

原 YAML 中 `VLLM_USE_V1=1` 是引擎开关，不能据此判定使用 Model Runner V1。本次依据四个真实 worker 的 MRV2 日志判定。每轮完整环境、原 YAML、替换本地路径后的 YAML 和 `original_config.json` 都在对应证据目录。

运行原仓库同一测试入口：

```bash
pytest -sv tests/e2e/common/single_node/test_single_node.py
```

## CI 与本机的差异、结论边界

| 已确认差异 | CI | 本机 |
| --- | --- | --- |
| CPU main 核数 | 每 rank 20 | 每 rank 28 |
| 执行环境 | Actions job container，经 Kubernetes runner hook | 独立 Docker，host network，显式设备/驱动映射 |
| 物理设备暴露 | 初始 npu-smi 可见 8 卡 | 容器仅暴露 0–3；实际计算都为 TP4 |
| 模型/数据来源 | 已有 ModelScope 缓存 | 本次下载，NFS 只读挂载；实际 180 输入相同 |
| 编译缓存 | 默认路径 | 每轮独立 vLLM/Triton/Inductor 缓存目录 |
| 压测前卡温 | 0–3 号卡约 33–37°C | 对照轮约 50–53°C |
| 准备与日志 | uv 0.13.6、MAX_JOBS=184、代理/CA 环境、tee/GHA 日志链路 | 原镜像工具环境、文件日志；请求同为 localhost |

实际代码、核心推理包、CANN、TP4、MRV2、绑核开启、请求规模等已对齐。完整十类差异及证据见 [ci_local_differences.json](evidence/ci_local_differences.json)。以上差异没有被逐项控制实验验证为性能根因。

CI 的 **CPU 型号/调频策略、内核、NPU 固件、CPU/memory quota、CPU weight、宿主竞争、正式阶段实际频率/功率限制、物理 NUMA 页分布** 未在目标 job 中完整记录；这些属于待核实项，不能说已经证实与本机不同。初始温度也不能单独用于推断正式阶段热降频。

本次本机三轮观测范围 818.2533–827.4128，不覆盖目标 CI 的 767.3497。它支持优先核查 CI runner 的资源和运行环境，但不证明“只是核数”“一定是代码回归”或“CI 不存在更大波动”。本机的单次最新镜像结果也不能量化 Ascend 单个提交或绑核开关的因果收益。CI 平均 TPOT=19.3 ms，本机三轮为 18.0 / 18.0 / 17.8 ms；这是客户端流式观测，不能全部当作 NPU 算子耗时。

后续应在真实 CI runner 采集下述同类环境、固定同一镜像重复，随后再分别控制 CPU 集合/频率/NUMA，以及分析 decode 的 CPU 调度、HCCL 和 NPU 算子时序。本次没有执行这些后续因果实验。

## 可复现步骤

下面使用固定 CI 镜像。宿主需有健康的四张 910B3、兼容驱动、足够磁盘及已有模型/数据目录。同一物理卡组只保留一套实验容器，避免设备 namespace 占用。所有路径和容器名可在新的实验副本中调整。

```bash
REGISTRY=swr.cn-north-12.myhuaweicloud.com/base_image/ascend-ci/vllm-ascend
CI_IMAGE="$REGISTRY@sha256:51acbdd308d677c4add19eee604174fbc29eff784d46675968e82c8e1299b9df"
SETUP_ROOT=/home/ubuntu/qwen_nightly_setup_recheck
RUN_ROOT=/mnt/share/z00943141/qwen3_nightly_recheck
MODEL_HOST_DIR=/path/to/Eco-Tech/Qwen3-30B-A3B-w8a8
DATASET_HOST_DIR=/path/to/vllm-ascend/GSM8K-in3500-bs400
CONTAINER=z00943141_qwen3_nightly_ci_recheck

# 把本目录 evidence/*.py 复制到 SETUP_ROOT；模型和数据可以使用已验证快照。
# 原下载方法保存在 evidence/download_inputs.py，下载状态见 evidence/download_status.json。
mkdir -p "$SETUP_ROOT" "$RUN_ROOT/outputs"
docker pull "$CI_IMAGE"
npu-smi info
docker run -d --name "$CONTAINER" --network host --shm-size 32g \
  --label codex.qwen3.run=124914290773 \
  -e ASCEND_RT_VISIBLE_DEVICES=0,1,2,3 -e ASCEND_VISIBLE_DEVICES=0,1,2,3 -e LANG=C.UTF-8 \
  --device /dev/davinci0 --device /dev/davinci1 --device /dev/davinci2 --device /dev/davinci3 \
  --device /dev/davinci_manager --device /dev/devmm_svm --device /dev/hisi_hdc \
  -v /usr/local/Ascend/driver:/usr/local/Ascend/driver:ro \
  -v /usr/local/dcmi:/usr/local/dcmi:ro \
  -v /usr/local/bin/npu-smi:/usr/local/bin/npu-smi:ro \
  -v /etc/ascend_install.info:/etc/ascend_install.info:ro \
  -v "$SETUP_ROOT:/setup:ro" -v "$RUN_ROOT/outputs:/results" \
  -v "$MODEL_HOST_DIR:/inputs/model:ro" -v "$DATASET_HOST_DIR:/inputs/dataset:ro" \
  --entrypoint /bin/bash "$CI_IMAGE" -elc 'sleep infinity'
# 若宿主存在 /usr/lib64/aicpu_kernels，按原创建记录补上同路径只读挂载。
docker exec "$CONTAINER" bash -elc 'python3 /setup/audit_image.py'
for ROUND in 01 02 03; do
  docker exec "$CONTAINER" bash -elc \
    "python3 -u /setup/inside_runner.py --output /results/recheck_$ROUND"
done
```

该 runner 会核验 commit、核心包、CANN B201、4 张可见 NPU 和输入目录；仅替换模型/数据本地路径；选择原 pytest 入口；最后检查 180 请求、输入/输出总量及真实四个 MRV2 worker。每轮查看 `$RUN_ROOT/outputs/recheck_<round>/{result.json,environment.json,pytest.log,runtime.jsonl}`。使用新的输出目录，避免覆盖已有证据。

若复现本次“滚动镜像原样”轮次，将镜像改为固定 `@sha256:076d9edae928079d9863b748a1ed56e7dd3ea1e271fd1ddc3a2b18346a14e874`，并使用 `inside_runner_latest.py`。不要用今天的可变 tag 代替当时镜像，再声称版本相同。原实验的容器控制、补跑及恢复脚本也完整保留：[remote_control.py](evidence/remote_control.py)、[repeat_ci.py](evidence/repeat_ci.py)、[inside_runner.py](evidence/inside_runner.py)。`prepare_*.py` 是当时工作区的 runner 生成辅助记录，实际执行入口是已经生成并归档的 `inside_runner*.py`。

### 在 CI 上补充只读环境记录

[capture_ci_environment.py](evidence/capture_ci_environment.py) 仅使用 Python 标准库和已有命令，读取 CPU/NUMA、调频、cgroup、内核、NPU board/sensors/common/power、核心包和指定环境变量，不修改系统配置。可在正式测试前后运行并上传 JSON；命令不支持或字段不可读会记录返回值。

```bash
python3 capture_ci_environment.py --output /tmp/test-logs/env-before.json
# 执行原 pytest / AISBench 流程
python3 capture_ci_environment.py --output /tmp/test-logs/env-after.json
```

本机用于验证该脚本的采集在最后一轮启动阶段进行，正式测试还未开始；没有用这份启动阶段的读数声称掌握正式阶段实际时钟。后续若采样运行中频率，应单独标记监测开销和采样时段。

### 重新计算本报告

```bash
python3 evidence/summarize_repeats.py
python3 evidence/validate_repeats.py
python3 evidence/compare_actual_requests.py
python3 evidence/build_ci_local_differences.py
```

这些分析脚本只读取已保存结果和 CI ZIP，不启动推理。`compare_actual_requests.py` 以 AST 解析生成的配置，没有执行 CI 配置代码；SQLite 以只读方式读取。运行分析会在 `evidence/` 更新派生报告，应在工作副本中操作。

## 预检失败、清理日志与最终状态

`ci_pinned01` 在设备预检报告 0 张可见卡，npu-smi 返回设备被使用；正式 pytest 尚未启动，没有吞吐结果。当时已测完的最新镜像容器仍保持运行，停止该容器后，固定镜像无需改变包或驱动就能识别 4 张 910B3，后续 `ci_pinned02` 正常完成。证据：[失败 result](evidence/ci_pinned01/result.json)、[预检环境](evidence/ci_pinned01/environment.json)、[原始诊断 stdout](evidence/ci_pinned_device_diagnostic.json.txt)。

第 3 轮在 **11:25:43.641 UTC** 保存正式结果，**11:25:46 UTC** 记录 perf 完成、触发 `mode=abort` 服务清理并杀掉 EngineCore；随后输出线程记录 `EngineDeadError`。该错误发生在结果写出后的 teardown，180 请求已经全部成功，pytest 返回 0。保留完整日志，不将这段清理错误当作正式请求失败，也不隐去它。详见 [repeat_validation.json](evidence/repeat_validation.json) 及 [原日志](evidence/ci_pinned04/pytest.log)。

实验完成时 `z00943141_qwen3_nightly_test` 恢复为 running（容器常驻、模型服务已停止），`z00943141_qwen3_nightly_ci_pinned` 停止保留。该状态记录于 2026-11-03，不能代表未来服务器状态：[repeat_state.json](evidence/repeat_state.json)。2026-11-04 上传准备仅只读导出已有产物，没有新增推理测试、启停容器或变更镜像。

原服务器实验目录：`/mnt/share/z00943141/qwen3_nightly_20261103_124914290773`；准备脚本：`/home/ubuntu/qwen_nightly_setup`。连接地址通过用户自己的私有运维记录获取，未写入本公开仓库。

## 与 2026-10-09 实验的关系

[之前的 MRV2 重复实验](../../20261009/mrv2/repeats/README.md) 是 BF16 / W8A8 × CANN 9.1 / 9.2，各三次，共 12 组；并非 12 次 W8A8 重复。其 W8A8+CANN9.2 三次为 **814.4012 / 811.9460 / 812.7597**，均值 **813.0356**，CV 约 **0.15%**，仅供参考。

旧实验在另一台 A2、driver **25.5.1**、Ascend **bbb5672af80b1972c301852aa505b13374fa6355**、vLLM **ced6857afa0ea7b2e3f0846a62e1394e90f15607 / 0.30.0+empty**，每组还采了约 1 秒 profiling。此次 driver **25.5.2**、CANN **9.2.1**、vLLM **0.32.0**、没有 profiling。因此旧值与本次并非仅改变 Ascend 的单因素对照，不能把差异都归因于插件提交。

## 证据、校验与公开处理

- [publication_manifest.json](publication_manifest.json)：每份证据的原始 SHA256、公开副本 SHA256、字节数和处理规则。
- [SHA256SUMS](SHA256SUMS)：整个公开实验目录的文件校验值（不含清单自身）。
- `evidence/<run>/`：原始 `result.json`、完整环境/pip 列表、原/本地 YAML、实际环境变量、pytest 日志、AISBench 正式 stdout、实际配置、逐请求明细、SQLite 时间戳数据库、基础运行快照。
- [CI 原始 artifact](evidence/ci_qwen3_w8a8_41327490550.zip)：原 ZIP 未改动；CI 的实际请求和时间数据作为公开原始依据保留。
- `evidence/remote_metadata/`、`evidence/remote_setup/`：容器创建/inspect、控制器状态和宿主准备日志。
- [公开资料校验结果](PUBLICATION_VALIDATION.json)：统计重算、JSON/链接/哈希、凭据模式扫描和工作树检查。

公开副本替换连接地址、主机名及芯片唯一标识，凭据不上传；原始副本继续保留在实验机和本地私有分析目录。文本统一为 UTF-8 / LF，JSON 重新缩进；文本统一为 UTF-8 / LF，JSON 重新缩进；性能数值、代码提交、依赖版本、CPU 拓扑/亲和性、请求文本和时序数据不作改写。在 JSON 后附带驱动文本的诊断 stdout 以 `.json.txt` 保存，避免将其冒充合法 JSON。模型权重、下载数据缓存、容器镜像、驱动安装包、编译缓存、Python 字节码及已被完整日志覆盖的 partial log 不上传；实际请求内容仍保留在 AISBench 明细中。
