# GLM-5.3-Flash��MRV2 �첽 MTP+PP ���⸴������С�޸�

�������ڣ�2026-10-16������˵�����ύ���ε������޸����ݸ� embedding ©�أ��Լ��Ϸ��� RoPE ������� MRV2 ���� kernel ����
���ļ�¼�������� GLM/PP �����ϵ� bug �޸������մ���û������ģ�ͣ�Ҳû������ PP transport �� model runner ִ���߼���

- ���� PR��[vllm-project/vllm-ascend#18931](https://github.com/vllm-project/vllm-ascend/pull/18931)��
- �޸��ύ��[`eaa7247d77aa2cbc42e5d9827c451ee80c6c8b41`](https://github.com/xujiaz2000/vllm-ascend/commit/eaa7247d77aa2cbc42e5d9827c451ee80c6c8b41)������ Signed-off-by��
- ��Ȩ����֤���ߣ�Ascend `6560f4af2b1daa3b10a1fb3d78655aa40982b969`����� vLLM `c4df37dfcc7f72ca41cd43801a468526ecf99a2b`��
- ��֤������BF16��A3 ����16���߼�NPU��MRV2���첽���ȡ�EP��eager������û�в� profiling��

## 1. ʵ��������ʲô����

| ���� | ֱ�ӱ��� | ����ԭ�� | �޸�λ�� |
|---|---|---|---|
| ����������ʧ�� | ��ͨ PP��MTP3+PP ���� ready���������� HTTP 500������ kernel �� `coreDim=0` | NoPE ģ�ͺϷ�������� RoPE �������������ά launch grid | `worker/v2/utils.py::AscendV2KVBlockZeroer.__init__()` |
| MTP+PP �������쳣�� | ��������������Է����ı����� MTP3+PP �ݸ�����ʽ�12.88%������PPԼ80.90% | MTP loader ���˵����� embedding��PPĩ�����޷������׼���Ŀ�� embedding | `models/glm5next/mtp.py::Glm5NextMTP.load_weights()` |

����������Ӧ�ֱ��жϣ������޸���������󱨴���embedding �޸�����������ı����ݸ�·��δ��ȷ��ʼ�������⡣���� ready �����ı�����������ܵ���֤�� MTP ·���Ѿ���ȷ��

����������� Ascend ������ vLLM �ӿڰ汾��ƥ�䡣������ͨ����װ�������԰汾���ؽ������û�б�����ؼ��ݲ�����Ҳ��������Ϊģ�Ͳ�֧�� PP ��֤�ݡ�

## 2. Ϊʲô������� PP ĩ���� MTP embedding

### 2.1 Ȩ����ԭʼ����·��

���� BF16 checkpoint ��ʵ�ʼܹ�Ϊ `Glm5NextForConditionalGeneration`��45����ģ�Ͳ㣬1�� MTP �㣨��45�㣩���������� embedding �ļ��� `model.language_model.embed_tokens.weight`������ checkpoint û�е�45����� embedding��

ԭ loader �Ѿ���ȥ�� `model.language_model.` �Ķ�ģ̬ǰ׺������������̵��� `get_spec_layer_idx_from_weight_name()`�������� MTP ��Ȩ�ء����� `model.embed_tokens.weight` ������ MTP �㣬��˱�������

```text
���� model.language_model.embed_tokens.weight
  -> ��һ��Ϊ model.embed_tokens.weight
  -> ԭ loader �� MTP ���ɸѡ
  -> ���� embedding ������
  -> PP ĩ��Ŀ�� embedding Ϊ PPMissingLayer
  -> ԭ sharing helper �޿���Ŀ�긱�����ݸ� embedding δ�� checkpoint ��ʼ��
```

���� PP ʱ��Ŀ��ģ�� embedding ��ݸ���ͬһ�׶Σ����μ��� `maybe_share_target_embed()` ���Խ�Ŀ�� embedding �������ݸ壬����û�б�¶ͬ���Ľ��������ݡ��� PP ʱ��Ŀ�� embedding ���׼���MTP �ݸ���ĩ������׶β���������һ��������ȡ���׼� embedding��

���ι����߼�����[maybe_share_target_embed()](https://github.com/vllm-project/vllm/blob/c4df37dfcc7f72ca41cd43801a468526ecf99a2b/vllm/v1/worker/gpu/spec_decode/eagle/utils.py#L44)��ԭģ��δ���� `has_own_embed_tokens` ʱ���� helper �� PP ·����ǰ���أ����ܽ��ӡ�û��ȱȨ���쳣���ƶ� embedding �Ѽ��ء�

### 2.2 �޸���������ʲô

1. �ڹ�һ����ģ̬��֮��ɸѡ MTP ��֮ǰ��ʶ�𹫹� `model.embed_tokens.weight`��
2. ���øò���ԭ�е� `weight_loader`��û����д TP �зֻ�ֱ�Ӹ�������Ȩ�ء�ʵ�� TP ��Ƭ�������� loader ������
3. �� `loaded_params` ���⹫�� embedding �����Ѿ����ص� MTP ר�� embedding��������Ȩ���ȵ�������ר��Ȩ���������ǣ���ר��Ȩ���ȵ�������Ȩ�ر�������
4. ��ɼ��غ�����ʵ���ֶ� `has_own_embed_tokens`����������ԭ�й�����ȱʧȨ��У���߼������� PP ����ͬȨ���Կ���Ŀ�� embedding ������

���շ�����[Glm5NextMTP.load_weights()](https://github.com/xujiaz2000/vllm-ascend/blob/eaa7247d77aa2cbc42e5d9827c451ee80c6c8b41/vllm_ascend/models/glm5next/mtp.py#L294)��

�ⲻ�������µ� embedding ����㣺�ݸ� embedding �����Ѿ����ڣ��˴�������Ȩ�س�ʼ��������Ȩ��Ϣ���Ķ������ڼ��ؽ׶Σ�û�������� token �� PP ͨ�š��豸��CPU��������� draft forward��

### 2.3 ��Ҫ�Ե�ֱ��֤��

| MTP3 ���� | �ݸ������ A/D | ƽ�����ܲݸ峤�� A/N | ��Ŀ�� token ���� 1+A/N | ��� token/s |
|---|---:|---:|---:|---:|
| ԭ MTP+PP�������������㱣�� | 12.88% | 0.386 | 1.386 | 48.97 |
| ԭ MTP ���� PP�����������㱣�� | 80.90% | 2.427 | 3.427 | 126.86 |
| ���� embedding ��� MTP+PP | 80.98% | 2.430 | 3.430 | 104.81 |

PP �޸�ǰ��ʹ��ͬһ TP8/PP2����ͬ160�⼰����Э�飬�������㱣�����Ѵ��ڡ��ݸ�������11,831����4,796����1/2/3λ���ۼƽ��ܱ�����35.54%/2.96%/0.14%�ָ���94.12%/82.61%/66.22%������PP�Ķ���Ϊ94.31%/82.23%/66.18%��

CPU �ع鸴�ֽ�һ��֤����©�أ������ڲݸ� embedding �з����ڱ�ֵ��ִ����ʵ loader �͹��� helper��ԭ loader ������ع��� embedding���޸�������ȷ���ز���ĩ���������ظ�����������ڱ�������֤��©�أ���������ʵ NPU ʵ���й۲쵽�� NaN��

**����Ƴ��⴦�޸�**����ͨ PP �Կ������У�MTP+PP Ҳ���ܷ����ı��������� embedding �ٴα����ˣ�ĩ���ݸ�ĳ�ʼ���������ڡ���˲�������ͨ PP �ɹ��� GSM8K �����Ϊ��ɾ�����޸���

## 3. Ϊʲô��Ҫ MRV2 ���������

### 3.1 �Ϸ��������Ӧ�������� kernel

�� checkpoint �� `qk_rope_head_dim=0`����ʵ `_reshape_combined_mla_kv_cache()` ���Է��أ�

```text
latent component: [4, 640, 1, 512]  # �ǿ�
RoPE component:   [4, 640, 1,   0]  # numel()==0
```

���߹����ײ�洢���� RoPE ��ͼ��ģ��ά��Ϊ0�����ĺϷ�����ֵ�����ǻ������ʧ�ܡ�ȱ�ٱ��ز����Ҫ�ſ��������ԭ����������� `component is not None`����Ϊ�ÿ������������������������ `[1,1,0]` launch grid������ `coreDim=0`��

### 3.2 �޸��ı߽����Ҫ��

ֻ�� `component is not None` �ս�Ϊ `component is not None and component.numel() > 0`�������û����Ҫд���Ԫ�أ��ǿ� latent �����������ԭ������������tuple/list ˳�򡢷ǿ�������ų������Ϊ�� UT ������

`numel()` ��ȡ������״Ԫ���ݣ��������豸���� `item()` һ����ȡ�豸���ݣ�����λ������������׶Ρ�û���޸� cache ���á����䡢���顢Ԥ�����ͼ��Ҳû�йر���ʵ�ǿջ�������㡣

���շ�����[AscendV2KVBlockZeroer.__init__()](https://github.com/xujiaz2000/vllm-ascend/blob/eaa7247d77aa2cbc42e5d9827c451ee80c6c8b41/vllm_ascend/worker/v2/utils.py#L28)��

�ɳɹ�����û�� `AscendV2KVBlockZeroer` �����ʼ��·����[PR18256](https://github.com/vllm-project/vllm-ascend/pull/18256) ����������·���󣬱�¶�˺Ϸ����������ı߽��������������Ϊʲô��֮ǰ��ͨ PP ���ܡ������� main ����������ʧ�ܣ�����·��������ԭ��û��ִ�е� kernel launch��

**����Ƴ����б���**���ڱ��ζ��� main �� NoPE �����£���ͨ PP �� MTP3+PP ���������ԻḴ������������ǹ��� MRV2 bug �޸������ܰ� embedding �޸��������������

## 4. ȫ���ǲ��������Ķ�����ȷ diff

��������ֱ�ӵ����������޸��ύ������ڶ��� Ascend ���ߣ������ļ�ֻ��2���������ύ������Ӧ UT����ͬĿ¼ [glm53-mrv2-mtp-pp.patch](glm53-mrv2-mtp-pp.patch)��

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

û�б�����ʵ���е� cache_config��attn_utils��PP transport��patch_pp_mtp �� model_runner ����Ķ���Ҳû���޸� vLLM Ascend �� docs���޸���������ģ�͡����� loader �͹��� helper��

## 5. UT ����Ȩ����֤

| �ļ� | ���� |
|---|---|
| [tests/ut/models/test_glm5next_mtp_embedding.py](https://github.com/xujiaz2000/vllm-ascend/blob/eaa7247d77aa2cbc42e5d9827c451ee80c6c8b41/tests/ut/models/test_glm5next_mtp_embedding.py) | 7�����Ȩ��ǰ׺��ĩ�����ظ���������PP������ȱ embedding �쳣�����ּ���˳���ר��Ȩ�����ȡ�ȱ MTP ���쳣 |
| [tests/ut/worker/v2/test_kv_block_zeroer.py](https://github.com/xujiaz2000/vllm-ascend/blob/eaa7247d77aa2cbc42e5d9827c451ee80c6c8b41/tests/ut/worker/v2/test_kv_block_zeroer.py) | 8���ʵ helper ���ɵĹ����洢����ͼ��tuple/list��λ�á�ȫ��Ϊ�ա��ǿ�������ų��� |

��� UT ��35��ͨ����δ�޸� loader ʱ������ embedding UT Ϊ5 failed / 2 passed���޸���ȫ��ͨ�������� `bash format.sh ci` ��ͨ������ PR ǰ�������� main `14022ee93b089299eac93bd65440e85ea5134aa2` ���޳�ͻ��ʱ�ϲ��������ܹ�ͬ��35�� UT����Ȩ�ؽ���Զ�Ӧǰ��������ߣ�������ʱ�ϲ� UT ����Ϊ����˺ϲ��汾����Ȩ�ظ��⡣

���� UT �����ɣ�Ȩ��ɸѡ��������������˳�򼰿����ѡȡ������ȷ���Բ���ֱ�Ӹ��֡�CPU UT �ɽ������ÿPR�������̣�������Ȩ�ز�����Ϊ������֤����Ϊ��������ʼ���޸��������밺���ģ�ͷ��� e2e ��ˮ�ߡ�

### GSM8K 160����

����ģʽʹ����ͬ�̶�160�⡢5-shot��greedy��seed1024��C16��max_tokens4096��Ԥ��2�ⲻ��ʱ��MRV2�첽��EP��eager����һ�£�prefix caching�رգ�ÿ��ģʽ��ͨ��12���/�����롢�����������ü�飬����promptΪ9,625 token�����а��������������޽ضϡ�

PP����ΪTP8/PP2������PPΪTP16/PP1����Ϊ16���߼�NPU��max_model_len32768��max_num_seqs16��max_num_batched_tokens512��gpu_memory_utilization0.85��block-size����512��ԭ�����ģ��·������Ϊ640��

| ģʽ | ��ȷ��/160 | ׼ȷ�� | ��� token/s | ͬ���˼��ٱ� | �ݸ������ | ƽ�����ܲݸ峤�� |
|---|---:|---:|---:|---:|---:|---:|
| ��ͨ PP | 148 | 92.500% | 42.13 | 1.000x | �� | �� |
| MTP3+PP | 151 | 94.375% | 104.81 | 2.488x | 80.98% | 2.430 |
| MTP5+PP | 149 | 93.125% | 112.95 | 2.681x | 64.64% | 3.232 |
| MTP7+PP | 148 | 92.500% | 112.14 | 2.662x | 51.07% | 3.575 |
| ��ͨ������ PP | 148 | 92.500% | 43.06 | 1.000x | �� | �� |
| MTP3������ PP | 148 | 92.500% | 130.29 | 3.026x | 80.90% | 2.427 |
| MTP5������ PP | 149 | 93.125% | 121.89 | 2.831x | 64.49% | 3.225 |
| MTP7������ PP | 147 | 91.875% | 121.27 | 2.816x | 50.63% | 3.544 |

�������Ϊ API completion token ���������������������ʱ�����ٱȰ�������±ȼ��㡣�ݸ������=A/D��ƽ�����ܲݸ峤��=A/N����Ŀ��token�ĳ���=1+A/N��ָ��ʹ�ò���ǰ�� Prometheus counter ��ֵ������MTP��� N+A+160 ����ȷ���� API ���token����MTP5/7����PPΪͬ���롢ͬЭ�鲹�⣬������������ǰһ�ֽ����

## 6. ���˽��ۣ�Ϊʲô���Ǳ�Ҫ����С���޸�

| �������� | ���� |
|---|---|
| ԭ�� main �Ƿ�û�� GLM �� PP �ܹ��� | ������������ģ������PP���첽MTP·�������θ��ֵ��ǺϷ��������������ĩ��draft embedding©�ء� |
| ��ͨ PP ���ܣ��ܷ�֤�� MTP+PP �����޸ģ� | ���ܡ���ͨ PP ��ʹ�� MTP embedding��MTP·����Ҫ����˶Խ��ܼ�����Ȩ�س�ʼ���� |
| �ܷ������ embedding �޸��� | �����Խ����MRV2����·������������� |
| �ܷ����������������� | ��Խ��������󣬵�MTP+PP���еͽ����ʣ��ݸ�embeddingȱ��δ����� |
| �Ƿ���ҪΪ������ PP ͨ�Ż�� model runner�� | �����޸�����֤û��֤�����ֱ�Ҫ�ԣ����ղ���δ������Щ�Ķ��� |
| �Ƿ�����޸Ļ������û����������ͼ�� | ����Ҫ��Ψһ����Ķ�ֻ��������Ԫ��������ǿ������ԭ·�������� |

���������ǣ�ȷ���ı���/�����������ɻع��UT��ͬ�����޸�ǰ������ʶ��գ��Լ���ʵBF16Ȩ�صķ����GSM8K���ԡ������޶��ڱ��ļ�¼��ģ�͡��汾����֤������

## 7. ԭʼʵ���������

��֤���ϵ����Ŀ¼��

```text
glm_53_flash_pp/results/bf16_main_mtp_pp_20261015_205912/
������ pp_native2/��mtp3_native2/              # ԭ������������ʧ��
������ mtp3_guard1/                           # �������㱣���ĵͽ�����
������ mtp3_nopp_isolate1/                    # ԭ��MTP����PP����
������ *_embedfix1/                           # �����޸������������
������ mtp5_nopp_compare1/��mtp7_nopp_compare1/ # ���䲻��PP����
������ mtp3_embedding.*��mtp_embedding.*       # �������������/��UT
������ zeroer_legal_empty.*                   # �Ϸ���������ֱ��֤��
������ final.related_ut.*��final.format.*
������ pr_merge_check.related_ut.*            # ��PRǰ�����κϲ���35��UT
������ final.validation.json��nopp_mtp5_7.validation.json
������ REPORT.md��RUNBOOK.md��PR_GLM53_MTP_PP.md
```

ÿ����Ȩ�ز��԰��������� serve.log��service_checks.json��GSM8K responses.jsonl/summary.json��Ԥ�ȼ�¼�Ͳ���ǰ�� Prometheus metrics�����Ĺ�����������벹����δ���Ʒ���������ƾ�ݻ����޸��޹ص����á�
