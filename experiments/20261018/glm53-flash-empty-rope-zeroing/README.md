# GLM-5.3-Flash empty RoPE zeroing failure

Original service log before adding the empty-component guard in PR [#18931](https://github.com/vllm-project/vllm-ascend/pull/18931).

- Hardware: Atlas 800I A3, 16 NPUs; TP8 / PP2 / MTP5.
- Model: GLM-5.3-Flash BF16.
- CANN: 9.2.0; Model Runner V2; KV-cache dtype `auto`.
- Target graph: `FULL_DECODE_ONLY`; speculative draft eager enabled.
- vLLM: `c4df37dfcc7f72ca41cd43801a468526ecf99a2b`.
- vllm-ascend baseline: `22730f46da2d821dc3955f47d56d16284eb2de81`.
- Failure time: 2026-10-18 05:00:32 UTC / 13:00:32 Asia/Shanghai.

The server started, but its first actual chat request failed. An empty RoPE tensor view was registered with the block zeroer, leading to a zero-work kernel launch.

See [serve.log, line 1380](serve.log#L1380). The original error is `_zero_kv_blocks_kernel` with `coreDim=0` (`Invalid_Argument(EE1003)`). This is the GLM empty-tensor failure, distinct from the later DeepSeek V4.1 nested-tuple `numel()` error.

Source on the A3 server:

```text
/mnt/share/z00943141/glm_53_flash_pp_mtp/runs/minimal_fix_20261018_045646/01_draft_eager/serve.log
```

The log is archived byte-for-byte. SHA-256:

```text
a0bd18dfb7167e0d5b0a31f1e9d61f5ba26018bc8bc39d927ff0a24da3f7448a
```