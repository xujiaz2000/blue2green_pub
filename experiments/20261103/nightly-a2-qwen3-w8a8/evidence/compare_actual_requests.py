import ast
import hashlib
import json
import pathlib
import os
import statistics
import sqlite3
import zipfile

root = pathlib.Path(__file__).parent

def parse_value(node):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, (ast.List, ast.Tuple)):
        return [parse_value(value) for value in node.elts]
    if isinstance(node, ast.Dict):
        return {parse_value(k): parse_value(v) for k, v in zip(node.keys, node.values)}
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'dict' and not node.args:
        return {item.arg: parse_value(item.value) for item in node.keywords}
    raise ValueError('Unsupported configuration node: ' + type(node).__name__)

def config(path):
    tree = ast.parse(path.read_text(encoding='utf-8-sig'))
    data = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            data[node.targets[0].id] = parse_value(node.value)
        else:
            raise ValueError('Unsupported configuration statement')
    return data

def differences(a, b, path=''):
    if isinstance(a, dict) and isinstance(b, dict):
        result = []
        for key in sorted(set(a) | set(b)):
            if key not in a or key not in b:
                result.append({'field':path + '.' + key, 'ci':a.get(key), 'local':b.get(key)})
            else:
                result.extend(differences(a[key], b[key], path + '.' + key))
        return result
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return [item for i, (left, right) in enumerate(zip(a, b))
                for item in differences(left, right, path + '[' + str(i) + ']')]
    return [] if a == b else [{'field':path, 'ci':a, 'local':b}]

def digest(value):
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(text.encode()).hexdigest()

def records(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8-sig').splitlines() if line.strip()]

ci = config(root / 'ci_aisbench_formal_config.py')
local = config(root / 'ci_pinned02/aisbench_configs/20261103_093850_9196.py')
diff = differences(ci, local)
expected = {'.cli_args.cfg_time_str', '.cli_args.dir_time_str', '.datasets[0].path',
            '.infer.partitioner.out_dir', '.models[0].host_port', '.models[0].model',
            '.models[0].path', '.work_dir'}
left = sorted(records(root / 'ci_aisbench_details.jsonl'), key=lambda row: row['id'])
right = sorted(records(root / 'ci_pinned02/aisbench_details.jsonl'), key=lambda row: row['id'])
by_id = {row['id']:row for row in right}
input_mismatch = []
token_mismatch = []
prediction_match = 0
prediction_prefix_lengths = []
input_hashes = []
for row in left:
    other = by_id.get(row['id'])
    if other is None or digest(row['input']) != digest(other['input']):
        input_mismatch.append(row['id'])
    if other is None or any(row.get(key) != other.get(key) for key in ['input_tokens','output_tokens','success']):
        token_mismatch.append(row['id'])
    if other is not None and digest(row['prediction']) == digest(other['prediction']):
        prediction_match += 1
    if other is not None and isinstance(row['prediction'], str) and isinstance(other['prediction'], str):
        prediction_prefix_lengths.append(len(os.path.commonprefix([row['prediction'], other['prediction']])))
    input_hashes.append({'id':row['id'], 'sha256':digest(row['input']),
                         'input_tokens':row['input_tokens'], 'output_tokens':row['output_tokens']})
result = {'source_job':124914290773, 'source_artifact':13093366197,
          'configuration_differences':diff,
          'unexpected_configuration_differences':[item for item in diff if item['field'] not in expected],
          'ci_requests':len(left), 'local_requests':len(right),
          'input_mismatch_ids':input_mismatch,'token_or_success_mismatch_ids':token_mismatch,
          'identical_prediction_count':prediction_match,
          'prediction_common_prefix_chars': {'min':min(prediction_prefix_lengths),
              'median':statistics.median(prediction_prefix_lengths), 'max':max(prediction_prefix_lengths),
              'at_least_64_chars':sum(value >= 64 for value in prediction_prefix_lengths)},
          'predictions_note':'Outputs can depend on continuous-batch composition and numerical nondeterminism; matching predictions does not establish byte-identical weights.',
          'request_input_hashes':input_hashes}
(root / 'actual_request_comparison.json').write_text(json.dumps(result, indent=2))
print(json.dumps({key:value for key,value in result.items() if key not in ['request_input_hashes','configuration_differences']}, indent=2))
with zipfile.ZipFile(root / 'ci_qwen3_w8a8_41327490550.zip') as archive:
    name = 'default/20261101_171543/performances/vllm-api-stream-chat/db_data/6bfc911b.db'
    database = root / 'ci_aisbench_times.db'
    database.write_bytes(archive.read(name))
    with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True) as connection:
        schema = connection.execute("SELECT name,sql FROM sqlite_master WHERE type='table'").fetchall()
        print('CI_TIMING_DATABASE_SCHEMA', json.dumps(schema))
        print('TIME_POINT_REFERENCE', json.dumps(left[0]['time_points']))
