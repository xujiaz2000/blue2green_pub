# 2026-10-16：GLM-5.3-Flash MRV2 异步 MTP+PP

- [问题复盘、两处适配的必要性与精确代码 diff](glm53-flash-mrv2-mtp-pp/README.md)
- [完整提交补丁（两处生产修复及对应 UT）](glm53-flash-mrv2-mtp-pp/glm53-mrv2-mtp-pp.patch)
- [来源版本和文件 SHA256](glm53-flash-mrv2-mtp-pp/MANIFEST.json)

A3 单机16个逻辑NPU、BF16、MRV2 异步、eager；包含普通 PP、MTP3/5/7+PP，以及不开 PP 的对应四组 GSM8K 160题验证。复盘关联 [vllm-ascend PR #18931](https://github.com/vllm-project/vllm-ascend/pull/18931)，本次仅归档既有验证材料，未重新启动服务或采 profiling。
