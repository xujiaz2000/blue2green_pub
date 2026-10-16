# GLM-5.3-Flash：MRV2 异步 MTP+PP 问题复盘与最小修复

整理日期：2026-10-16。本文说明已提交上游的两处修复：草稿 embedding 漏载，以及合法空 RoPE 组件触发 MRV2 清零 kernel 错误。
本文记录的是已有 GLM/PP 能力上的 bug 修复；最终代码没有新增模型，也没有新增 PP transport 或 model runner 执行逻辑。

- 上游 PR：[vllm-project/vllm-ascend#18931](https://github.com/vllm-project/vllm-ascend/pull/18931)。
- 修复提交：[`eaa7247d77aa2cbc42e5d9827c451ee80c6c8b41`](https://github.com/xujiaz2000/vllm-ascend/commit/eaa7247d77aa2cbc42e5d9827c451ee80c6c8b41)，包含 Signed-off-by。
- 真权重验证基线：Ascend `6560f4af2b1daa3b10a1fb3d78655aa40982b969`；配对 vLLM `c4df37dfcc7f72ca41cd43801a468526ecf99a2b`。
- 验证条件：BF16、A3 单机16个逻辑NPU、MRV2、异步调度、EP、eager；本轮没有采 profiling。

## 1. 实际遇到了什么问题

| 问题 | 直接表现 | 根本原因 | 修复位置 |
|---|---|---|---|
| 首请求清零失败 | 普通 PP、MTP3+PP 可以 ready，但首请求 HTTP 500，清零 kernel 报 `coreDim=0` | NoPE 模型合法的零宽度 RoPE 组件被创建了零维 launch grid | `worker/v2/utils.py::AscendV2KVBlockZeroer.__init__()` |
| MTP+PP 接受率异常低 | 解决清零问题后可以返回文本，但 MTP3+PP 草稿接受率仅12.88%；不开PP约80.90% | MTP loader 过滤掉公共 embedding，PP末级又无法共享首级的目标 embedding | `models/glm5next/mtp.py::Glm5NextMTP.load_weights()` |

这两个问题应分别判断：清零修复解决首请求报错；embedding 修复解决能生成文本但草稿路径未正确初始化的问题。服务 ready 或有文本输出，都不能单独证明 MTP 路径已经正确。

最初还遇到过 Ascend 与配套 vLLM 接口版本不匹配。该问题通过安装冻结的配对版本并重建解决，没有保留相关兼容补丁，也不将其作为模型不支持 PP 的证据。

## 2. 为什么必须加载 PP 末级的 MTP embedding

### 2.1 权重与原始加载路径

本次 BF16 checkpoint 的实际架构为 `Glm5NextForConditionalGeneration`：45个主模型层，1个 MTP 层（第45层）。公共输入 embedding 的键是 `model.language_model.embed_tokens.weight`；本次 checkpoint 没有第45层独立 embedding。

原 loader 已经会去掉 `model.language_model.` 的多模态前缀，但是随后立刻调用 `get_spec_layer_idx_from_weight_name()`，仅保留 MTP 层权重。公共 `model.embed_tokens.weight` 不属于 MTP 层，因此被跳过。

```text
公共 model.language_model.embed_tokens.weight
  -> 归一化为 model.embed_tokens.weight
  -> 原 loader 以 MTP 层号筛选
  -> 公共 embedding 被跳过
  -> PP 末级目标 embedding 为 PPMissingLayer
  -> 原 sharing helper 无可用目标副本，草稿 embedding 未从 checkpoint 初始化
```

不开 PP 时，目标模型 embedding 与草稿在同一阶段，上游既有 `maybe_share_target_embed()` 可以将目标 embedding 共享给草稿，所以没有暴露同样的接受率塌陷。开 PP 时，目标 embedding 在首级，MTP 草稿在末级；跨阶段不能依靠这一对象共享来取得首级 embedding。

上游共享逻辑见：[maybe_share_target_embed()](https://github.com/vllm-project/vllm/blob/c4df37dfcc7f72ca41cd43801a468526ecf99a2b/vllm/v1/worker/gpu/spec_decode/eagle/utils.py#L44)。原模型未声明 `has_own_embed_tokens` 时，该 helper 在 PP 路径提前返回；不能仅从“没有缺权重异常”推断 embedding 已加载。

### 2.2 修复具体做了什么

1. 在归一化多模态键之后、筛选 MTP 层之前，识别公共 `model.embed_tokens.weight`。
2. 调用该参数原有的 `weight_loader`，没有自写 TP 切分或直接复制完整权重。实际 TP 分片仍由已有 loader 处理。
3. 用 `loaded_params` 避免公共 embedding 覆盖已经加载的 MTP 专用 embedding。若公共权重先到，后续专用权重正常覆盖；若专用权重先到，公共权重被跳过。
4. 完成加载后设置实例字段 `has_own_embed_tokens`，复用上游原有共享与缺失权重校验逻辑。不开 PP 的相同权重仍可与目标 embedding 共享。

最终方法：[Glm5NextMTP.load_weights()](https://github.com/xujiaz2000/vllm-ascend/blob/eaa7247d77aa2cbc42e5d9827c451ee80c6c8b41/vllm_ascend/models/glm5next/mtp.py#L294)。

这不是增加新的 embedding 网络层：草稿 embedding 本来已经存在，此处补齐其权重初始化和所有权信息。改动发生在加载阶段，没有增加逐 token 的 PP 通信、设备到CPU拷贝或额外 draft forward。

### 2.3 必要性的直接证据

| MTP3 对照 | 草稿接受率 A/D | 平均接受草稿长度 A/N | 含目标 token 长度 1+A/N | 输出 token/s |
|---|---:|---:|---:|---:|
| 原 MTP+PP，仅含公共清零保护 | 12.88% | 0.386 | 1.386 | 48.97 |
| 原 MTP 不开 PP，含公共清零保护 | 80.90% | 2.427 | 3.427 | 126.86 |
| 补齐 embedding 后的 MTP+PP | 80.98% | 2.430 | 3.430 | 104.81 |

PP 修复前后使用同一 TP8/PP2、相同160题及评测协议，公共清零保护均已存在。草稿轮数由11,831降至4,796；第1/2/3位置累计接受比例从35.54%/2.96%/0.14%恢复到94.12%/82.61%/66.22%。不开PP的对照为94.31%/82.23%/66.18%。

CPU 回归复现进一步证明了漏载：测试在草稿 embedding 中放入哨兵值，执行真实 loader 和共享 helper。原 loader 不会加载公共 embedding，修复后能正确加载并在末级保留本地副本。这里的哨兵仅用于证明漏载，不代表真实 NPU 实验中观察到了 NaN。

**如果移除这处修复**：普通 PP 仍可能运行，MTP+PP 也可能返回文本，但公共 embedding 再次被过滤，末级草稿的初始化问题仍在。因此不能以普通 PP 成功或 GSM8K 有输出为由删除该修复。

## 3. 为什么需要 MRV2 空组件保护

### 3.1 合法空组件不应触发清零 kernel

本 checkpoint 的 `qk_rope_head_dim=0`。真实 `_reshape_combined_mla_kv_cache()` 可以返回：

```text
latent component: [4, 640, 1, 512]  # 非空
RoPE component:   [4, 640, 1,   0]  # numel()==0
```

两者共享底层存储。空 RoPE 视图是模型维度为0产生的合法返回值，不是缓存分配失败、缺少本地层或需要放宽分组规则。原清零器仅检查 `component is not None`，会为该空组件构造子清零器，并生成 `[1,1,0]` launch grid，触发 `coreDim=0`。

### 3.2 修复的边界与必要性

只将 `component is not None` 收紧为 `component is not None and component.numel() > 0`。空组件没有需要写零的元素；非空 latent 组件继续进入原有子清零器。tuple/list 顺序、非空组件和排除层的行为由 UT 看护。

`numel()` 读取张量形状元数据，不会像设备张量 `item()` 一样读取设备数据；条件位于清零器构造阶段。没有修改 cache 配置、分配、分组、预算或视图，也没有关闭真实非空缓存的清零。

最终方法：[AscendV2KVBlockZeroer.__init__()](https://github.com/xujiaz2000/vllm-ascend/blob/eaa7247d77aa2cbc42e5d9827c451ee80c6c8b41/vllm_ascend/worker/v2/utils.py#L28)。

旧成功基线没有 `AscendV2KVBlockZeroer` 及其初始化路径。[PR18256](https://github.com/vllm-project/vllm-ascend/pull/18256) 引入新清零路径后，暴露了合法零宽度组件的边界条件。这解释了为什么“之前普通 PP 能跑”，而新 main 会在首请求失败：新增路径触发了原先没有执行的 kernel launch。

**如果移除这行保护**：在本次冻结 main 与 NoPE 配置下，普通 PP 和 MTP3+PP 的首请求仍会复现清零错误。它是公共 MRV2 bug 修复，不能把 embedding 修复当作替代方案。

## 4. 全部非测试生产改动：精确 diff

以下内容直接导出自上述修复提交，相对于冻结 Ascend 基线；生产文件只有2个。完整提交（含对应 UT）见同目录 [glm53-mrv2-mtp-pp.patch](glm53-mrv2-mtp-pp.patch)。

```diff
diff --git a/vllm_ascend/models/glm5next/mtp.py b/vllm_ascend/models/glm5next/mtp.py
index 5cd7266..c4fddd6 100644
--- a/vllm_ascend/models/glm5next/mtp.py
+++ b/vllm_ascend/models/glm5next/mtp.py
@@ -327,6 +327,16 @@ class Glm5NextMTP(nn.Module, DeepseekV2MixtureOfExperts):
             # prefix to match.
             if name.startswith("model.language_model."):
                 name = name.replace("model.language_model.", "model.", 1)
+            # The target embedding is absent on the last PP stage. Load a
+            # local copy before filtering for MTP layers, while allowing an
+            # MTP-specific embedding to take precedence in either file order.
+            if name == "model.embed_tokens.weight":
+                if name not in loaded_params:
+                    param = params_dict[name]
+                    weight_loader = getattr(param, "weight_loader", default_weight_loader)
+                    weight_loader(param, loaded_weight)
+                    loaded_params.add(name)
+                continue
             spec_layer = get_spec_layer_idx_from_weight_name(self.config, name)
             if spec_layer is None:
                 continue
@@ -406,5 +416,6 @@ class Glm5NextMTP(nn.Module, DeepseekV2MixtureOfExperts):
                 raise ValueError(f"MTP speculative decoding layer {layer_idx} weights missing from checkpoint.")
         if self.is_rot_weight_used and "rot.weight" not in loaded_params:
             raise ValueError("GLM5-Next MTP requires rot.weight when the quantization config sets is_rot_used.")
+        self.has_own_embed_tokens = "model.embed_tokens.weight" in loaded_params
         self._maybe_set_own_lm_head(loaded_params)
         return loaded_params
diff --git a/vllm_ascend/worker/v2/utils.py b/vllm_ascend/worker/v2/utils.py
index 4597795..c4c4b6d 100644
--- a/vllm_ascend/worker/v2/utils.py
+++ b/vllm_ascend/worker/v2/utils.py
@@ -71,7 +71,7 @@ class AscendV2KVBlockZeroer(KVBlockZeroer):
                         component = kv_cache
                     elif isinstance(kv_cache, (tuple, list)) and component_id < len(kv_cache):
                         component = kv_cache[component_id]
-                    if component is not None:
+                    if component is not None and component.numel() > 0:
                         layer_names.append(layer_name)
                         component_context[layer_name] = SimpleNamespace(kv_cache=component)
                 if layer_names:
```

没有保留旧实验中的 cache_config、attn_utils、PP transport、patch_pp_mtp 或 model_runner 适配改动；也没有修改 vLLM Ascend 的 docs。修复复用已有模型、参数 loader 和共享 helper。

## 5. UT 与真权重验证

| 文件 | 作用 |
|---|---|
| [tests/ut/models/test_glm5next_mtp_embedding.py](https://github.com/xujiaz2000/vllm-ascend/blob/eaa7247d77aa2cbc42e5d9827c451ee80c6c8b41/tests/ut/models/test_glm5next_mtp_embedding.py) | 7项：两种权重前缀、末级本地副本、不分PP共享、缺 embedding 异常、两种加载顺序的专用权重优先、缺 MTP 层异常 |
| [tests/ut/worker/v2/test_kv_block_zeroer.py](https://github.com/xujiaz2000/vllm-ascend/blob/eaa7247d77aa2cbc42e5d9827c451ee80c6c8b41/tests/ut/worker/v2/test_kv_block_zeroer.py) | 8项：真实 helper 生成的共享存储空视图、tuple/list及位置、全部为空、非空组件与排除层 |

相关 UT 共35项通过；未修复 loader 时，新增 embedding UT 为5 failed / 2 passed，修复后全部通过。完整 `bash format.sh ci` 已通过。提 PR 前，又在与 main `14022ee93b089299eac93bd65440e85ea5134aa2` 的无冲突临时合并副本中跑过同样35项 UT。真权重结果仍对应前述冻结基线，不将临时合并 UT 表述为完成了合并版本的真权重复测。

采用 UT 的理由：权重筛选、对象共享、加载顺序及空组件选取都可用确定性测试直接复现。CPU UT 可进入既有每PR测试流程，整机真权重测试作为补充验证，不为这两处初始化修复额外引入昂贵的模型服务 e2e 流水线。

### GSM8K 160题结果

所有模式使用相同固定160题、5-shot、greedy、seed1024、C16、max_tokens4096，预热2题不计时。MRV2异步、EP和eager保持一致，prefix caching关闭；每个模式先通过12项短/长输入、并发及请求复用检查，最长检查prompt为9,625 token。所有八组均无请求错误、无截断。

PP拓扑为TP8/PP2；不开PP为TP16/PP1，均为16个逻辑NPU。max_model_len32768、max_num_seqs16、max_num_batched_tokens512、gpu_memory_utilization0.85；block-size输入512、原生混合模型路径对齐为640。

| 模式 | 正确数/160 | 准确率 | 输出 token/s | 同拓扑加速比 | 草稿接受率 | 平均接受草稿长度 |
|---|---:|---:|---:|---:|---:|---:|
| 普通 PP | 148 | 92.500% | 42.13 | 1.000x | — | — |
| MTP3+PP | 151 | 94.375% | 104.81 | 2.488x | 80.98% | 2.430 |
| MTP5+PP | 149 | 93.125% | 112.95 | 2.681x | 64.64% | 3.232 |
| MTP7+PP | 148 | 92.500% | 112.14 | 2.662x | 51.07% | 3.575 |
| 普通，不开 PP | 148 | 92.500% | 43.06 | 1.000x | — | — |
| MTP3，不开 PP | 148 | 92.500% | 130.29 | 3.026x | 80.90% | 2.427 |
| MTP5，不开 PP | 149 | 93.125% | 121.89 | 2.831x | 64.49% | 3.225 |
| MTP7，不开 PP | 147 | 91.875% | 121.27 | 2.816x | 50.63% | 3.544 |

输出吞吐为 API completion token 总数除以完整请求测量耗时；加速比按输出吞吐比计算。草稿接受率=A/D，平均接受草稿长度=A/N，含目标token的长度=1+A/N。指标使用测试前后 Prometheus counter 差值，所有MTP组的 N+A+160 均精确等于 API 输出token数。MTP5/7不开PP为同代码、同协议补测，其余六组沿用前一轮结果。

## 6. 复核结论：为什么这是必要且最小的修改

| 复核问题 | 结论 |
|---|---|
| 原生 main 是否没有 GLM 的 PP 架构？ | 不能这样归因。模型已有PP及异步MTP路径；本次复现的是合法空组件清零错误和末级draft embedding漏载。 |
| 普通 PP 能跑，能否证明 MTP+PP 无需修改？ | 不能。普通 PP 不使用 MTP embedding；MTP路径需要额外核对接受计数和权重初始化。 |
| 能否仅保留 embedding 修复？ | 不足以解决新MRV2清零路径的首请求错误。 |
| 能否仅保留空组件保护？ | 能越过清零错误，但MTP+PP仍有低接受率，草稿embedding缺陷未解决。 |
| 是否需要为此新增 PP 通信或改 model runner？ | 本轮修复及验证没有证明这种必要性，最终补丁未包含这些改动。 |
| 是否必须修改缓存配置或重新设计视图？ | 不需要。唯一清零改动只是跳过无元素组件，非空组件按原路径处理。 |

交付依据是：确定的报错/加载链条、可回归的UT、同拓扑修复前后接受率对照，以及真实BF16权重的服务和GSM8K测试。结论限定于本文记录的模型、版本和验证条件。

## 7. 原始实验材料索引

验证机上的相对目录：

```text
glm_53_flash_pp/results/bf16_main_mtp_pp_20261015_205912/
├── pp_native2/、mtp3_native2/              # 原生首请求清零失败
├── mtp3_guard1/                           # 仅含清零保护的低接受率
├── mtp3_nopp_isolate1/                    # 原生MTP不开PP对照
├── *_embedfix1/                           # 两处修复后的完整复测
├── mtp5_nopp_compare1/、mtp7_nopp_compare1/ # 补充不开PP测试
├── mtp3_embedding.*、mtp_embedding.*       # 加载链复现与红/绿UT
├── zeroer_legal_empty.*                   # 合法零宽度组件直接证据
├── final.related_ut.*、final.format.*
├── pr_merge_check.related_ut.*            # 提PR前与上游合并的35项UT
├── final.validation.json、nopp_mtp5_7.validation.json
└── REPORT.md、RUNBOOK.md、PR_GLM53_MTP_PP.md
```

每个真权重测试案例均保留 serve.log、service_checks.json、GSM8K responses.jsonl/summary.json、预热记录和测试前后 Prometheus metrics。本文公开复盘与代码补丁，未复制服务器访问凭据或与修复无关的配置。
