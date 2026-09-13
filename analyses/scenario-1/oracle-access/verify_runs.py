"""Verify published model inputs, outputs and provenance without a model call."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('runner', HERE / 'run_model.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def verify():
    summaries = []
    for directory in sorted((HERE / 'runs').iterdir()):
        manifest_file = directory / 'manifest.json'
        if not manifest_file.exists():
            raise ValueError('Run is unfinished: ' + directory.name)
        manifest = json.loads(manifest_file.read_text())
        evidence_policy = manifest.get('evidence_policy', 'card-evidence')
        for name, key in [('input.md','input_sha256'),('runner-source.py','runner_sha256')]:
            if hashlib.sha256((directory/name).read_bytes()).hexdigest() != manifest[key]:
                raise ValueError('Hash mismatch in '+directory.name+'/'+name)
        if (directory/'input.md').read_text() != runner.build_prompt(manifest['provider'], evidence_policy):
            raise ValueError('Run input differs from the versioned prompt and frozen scenario')
        if hashlib.sha256(runner.schema_path(manifest['provider']).read_bytes()).hexdigest() != manifest['output_schema_sha256']:
            raise ValueError('Output schema differs from recorded run')
        if hashlib.sha256(runner.prompt_path(manifest['provider'], evidence_policy).read_bytes()).hexdigest() != manifest['prompt_template_sha256']:
            raise ValueError('Prompt template differs from recorded run')
        row = {key:manifest[key] for key in ['run_id','harness','harness_version','model_requested','reasoning_effort_requested','provider','status']}
        row['evidence_policy'] = evidence_policy
        if 'postprocessor_sha256' in manifest and hashlib.sha256((HERE/'recover_export.py').read_bytes()).hexdigest() != manifest['postprocessor_sha256']:
            raise ValueError('Postprocessor differs from recorded recovery')
        if manifest['status'] == 'completed':
            for name,key in [('output.json','output_sha256'),('events.jsonl','events_sha256')]:
                if hashlib.sha256((directory/name).read_bytes()).hexdigest() != manifest[key]:
                    raise ValueError('Output/event hash mismatch')
            decision = json.loads((directory/'output.json').read_text())
            runner.validate_decision(decision, manifest['provider'])
            row.update({key:decision[key] for key in ['selected_action','selected_record_ids','purchase_value_cents']})
        else:
            row['failure'] = manifest.get('failure')
        summaries.append(row)
    return summaries


if __name__ == '__main__':
    print(json.dumps(verify(),indent=2))
