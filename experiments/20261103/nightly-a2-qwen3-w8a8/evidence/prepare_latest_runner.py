import pathlib
root=pathlib.Path(__file__).resolve().parent
source=(root/'inside_runner.py').read_text(encoding='utf8')
source=source.replace('b3b82c137ee242a774c29b56325133771f5f069d','23e0e3764293f0c85ebf96c1383fbbf431b8fbb3')
source=source.replace("'torch-npu': '2.10.0.post4'","'torch-npu': '2.10.0.post7'")
source=source.replace("'triton-ascend': '3.2.2'","'triton-ascend': '3.6.0.post2'")
source=source.replace("'started_ns': time.time_ns(), 'success': False}","'started_ns': time.time_ns(), 'success': False, 'measurement_kind': 'latest_rolling_image_not_exact_ci', 'ci_ascend_sha': 'b3b82c137ee242a774c29b56325133771f5f069d', 'ci_torch_npu_version': '2.10.0.post4'}")
source=source.replace("result['relative_to_ci_767_3497_pct'] =", "result['target_802'] = {'target':802,'pass':throughput >= 802}\n        result['relative_to_ci_767_3497_pct'] =")
(root/'inside_runner_latest.py').write_text(source,encoding='utf8')
print('Latest-image runner prepared; pinned to inspected 23e0e376, post7 and Triton3.6.0.post2.')
