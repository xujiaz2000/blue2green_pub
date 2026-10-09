_base_ = []
import os
from ais_bench.benchmark.models import VLLMCustomAPIChat
from ais_bench.benchmark.utils.postprocess.model_postprocessors import extract_non_reasoning_content

models = [
    dict(
        attr="service",
        type=VLLMCustomAPIChat,
        abbr="vllm-api-stream-chat",
        path=os.environ.get("MODEL_PATH", '/root/.cache/modelscope/hub/models/Qwen/Qwen3-30B-A3B'),
        model='Qwen/Qwen3-30B-A3B',
        stream=True,
        request_rate=0,
        use_timestamp=False,
        retry=2,
        api_key="",
        host_ip='127.0.0.1',
        host_port=int(os.environ.get("SERVER_PORT", "8007")),
        url="",
        max_out_len=1500,
        batch_size=45,
        trust_remote_code=True,
        generation_kwargs=dict(
            temperature=0,
            ignore_eos=True,
        ),
        pred_postprocessor=dict(type=extract_non_reasoning_content),
    )
]
