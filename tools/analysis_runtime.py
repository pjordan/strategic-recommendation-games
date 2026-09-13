"""Shared execution and validation for the version 1.2 strategic analyses.

The condition runners own prompts, visibility, move order and revenue attribution.
The oracle adapter supplies the existing harness commands and publication screen.
The $800 purchase check is the pinned scenario-1 contract, not a generic budget.
"""
import importlib.util
import json
import os
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path


def load_module(name, path):
    """Load a repository-relative source file without modifying the import path."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def text_json(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def check_schema(value, schema):
    """Validate the small JSON-schema subset used by this analysis, offline."""
    kind = schema['type']
    valid = {'object': type(value) is dict, 'array': type(value) is list,
             'string': type(value) is str, 'integer': type(value) is int}[kind]
    if not valid:
        raise ValueError('Wrong response field type: ' + kind)
    if 'enum' in schema and value not in schema['enum']:
        raise ValueError('Invalid enum value')
    if kind == 'object':
        if set(value) != set(schema['properties']):
            raise ValueError('Response fields differ from schema')
        for key, child in schema['properties'].items():
            check_schema(value[key], child)
    elif kind == 'array':
        if len(value) < schema.get('minItems', 0):
            raise ValueError('Too few response candidates')
        if schema.get('uniqueItems') and len(set(map(text_json, value))) != len(value):
            raise ValueError('Duplicate array entries')
        for item in value:
            check_schema(item, schema['items'])
    elif kind == 'integer' and value < schema.get('minimum', value):
        raise ValueError('Integer below minimum')


def check_ids(ids, catalog):
    if len(ids) != len(set(ids)) or not set(ids) <= set(catalog):
        raise ValueError('Unknown, duplicate, or unavailable record IDs')


def check_purchase(action, ids, value, catalog, enforce_budget=True):
    check_ids(ids, catalog)
    if action == 'decline':
        if ids or value != 0:
            raise ValueError('Decline requires no products and zero value')
    elif action != 'purchase' or not ids or any(catalog[i]['displayed_price_cents'] is None for i in ids):
        raise ValueError('Invalid purchase or unavailable price')
    elif sum(catalog[i]['displayed_price_cents'] for i in ids) != value:
        raise ValueError('Purchase arithmetic mismatch')
    elif enforce_budget and value > 80000:
        raise ValueError('Purchase exceeds total equipment budget')


def validate_buyer(output, response, schema):
    check_schema(output, schema)
    catalog = {r['record_id']: r for r in response['records']}
    check_purchase(output['selected_action'], output['selected_record_ids'], output['purchase_value_cents'], catalog)
    candidates = output['candidates']
    if len({c['candidate_id'] for c in candidates}) != len(candidates):
        raise ValueError('Duplicate buyer candidate IDs')
    if len({text_json([c['action'], sorted(c['record_ids'])]) for c in candidates}) != len(candidates):
        raise ValueError('Duplicate buyer outcomes')
    if not any(c['action'] == 'decline' for c in candidates):
        raise ValueError('Buyer omitted decline')
    if catalog and not any(c['action'] == 'purchase' for c in candidates):
        raise ValueError('Buyer omitted all purchase alternatives')
    for c in candidates:
        check_purchase(c['action'], c['record_ids'], c['displayed_total_cents'], catalog, enforce_budget=False)
    chosen = [c for c in candidates if c['action'] == output['selected_action'] and set(c['record_ids']) == set(output['selected_record_ids'])]
    if len(chosen) != 1 or chosen[0]['preference_rank'] != min(c['preference_rank'] for c in candidates):
        raise ValueError('Buyer selected outcome disagrees with ranking')
    if output['selected_action'] == 'purchase' and chosen[0]['qualification'] != 'qualifies':
        raise ValueError('Buyer selected an outcome it did not qualify')


def validate_disclosure(output, schema):
    check_schema(output,schema)
    candidates=output['candidates']
    if len({c['candidate_id'] for c in candidates})!=len(candidates):
        raise ValueError('Duplicate disclosure candidate IDs')
    if len({text_json(c['messages']) for c in candidates})!=len(candidates):
        raise ValueError('Duplicate disclosure plans')
    chosen=[c for c in candidates if c['candidate_id']==output['selected_candidate_id']]
    if len(chosen)!=1 or chosen[0]['preference_rank']!=min(c['preference_rank'] for c in candidates):
        raise ValueError('Selected disclosure plan disagrees with ranking')
    return chosen[0]


def invoke(role, prompt, args, directory, prefix, version, *, schema_file, adapter,
           include_participant=False, temporary_prefix='informed-game-'):
    directory.mkdir()
    sha = adapter.sha
    write_json = adapter.write_json
    (directory/'input.md').write_text(prompt)
    meta = {'role': role, 'harness': args.harness, 'harness_version': version,
            'model_requested': args.model, 'model_resolved': None,
            'reasoning_effort_requested': args.effort, 'reasoning_effort_observed': None,
            'temperature': None, 'seed': None, 'input_sha256': sha(prompt.encode()),
            'output_schema_sha256': sha(schema_file.read_bytes()), 'status': 'prepared',
            'started_at': datetime.now(timezone.utc).isoformat(),
            'context_isolation': 'Fresh process and empty temporary directory; only this role input supplied.',
            'system_prompt': 'Harness built-in, not exported or overridden. Managed policies may vary.',
            'tool_policy': 'Tools disabled; any observed tool item invalidates the run.'}
    if include_participant:
        meta['participant'] = directory.name
    argv = adapter.command(args.harness, args.model, args.effort, schema_file, Path('OUTPUT_JSON'))
    meta['command_argv'] = prefix + [x.replace(str(schema_file),'OUTPUT_SCHEMA_JSON') for x in argv[1:]]
    write_json(directory/'manifest.json', meta)
    env = os.environ.copy()
    if args.harness == 'codex':
        env.pop('OPENAI_API_KEY', None)
        env.pop('CODEX_API_KEY', None)
    start = time.monotonic()
    try:
        with tempfile.TemporaryDirectory(prefix=temporary_prefix) as temporary:
            cwd = Path(temporary)
            (cwd/'schema.json').write_bytes(schema_file.read_bytes())
            argv = adapter.command(args.harness, args.model, args.effort, cwd/'schema.json', cwd/'output.json')
            run = subprocess.run(prefix+argv[1:], input=prompt, text=True, capture_output=True, cwd=cwd, env=env)
            private = directory/'private'; private.mkdir()
            (private/'stdout.txt').write_text(run.stdout)
            (private/'stderr.txt').write_text(run.stderr)
            meta['exit_code'] = run.returncode
            if run.returncode:
                raise ValueError('Harness exited unsuccessfully; inspect ignored private logs')
            if args.harness == 'codex':
                parsed = [json.loads(line) for line in run.stdout.splitlines() if line.strip()]
                types = sorted({e.get('item',{}).get('type') for e in parsed if e.get('item',{}).get('type')})
                if set(types)-{'agent_message','reasoning','error'}:
                    raise ValueError('Tool or unexpected item observed')
                if any(e.get('type') in ('error','turn.failed') for e in parsed) or not any(e.get('type') == 'turn.completed' for e in parsed):
                    raise ValueError('Model turn did not complete')
                meta['observed_item_types'] = types
                meta['harness_warnings'] = [e['item'].get('message','') for e in parsed if e.get('item',{}).get('type') == 'error']
                output_text = (cwd/'output.json').read_text()
                output = json.loads(output_text)
                events = [e for e in parsed if e.get('type') in ('turn.started','turn.completed') or (e.get('type') == 'item.completed' and e.get('item',{}).get('type') == 'agent_message')]
                meta['usage'] = [e.get('usage') for e in parsed if e.get('type') == 'turn.completed']
            else:
                raw = json.loads(run.stdout)
                if raw.get('is_error'):
                    raise ValueError('Claude reported an error')
                output = raw.get('structured_output')
                if output is None:
                    output = json.loads(raw['result'])
                output_text = json.dumps(output, ensure_ascii=False, indent=2)+'\n'
                models = list(raw.get('modelUsage',{}))
                meta['model_resolved'] = models[0] if len(models) == 1 else None
                meta['usage'] = raw.get('usage')
                meta['tool_use_verification'] = 'Tools disabled by CLI; result does not expose every internal event.'
                events = [{'type':'result','result':output}]
        check_schema(output, json.loads(schema_file.read_text()))
        adapter.screen(output_text); adapter.screen(text_json(events)); adapter.screen(text_json(meta))
        (directory/'output.json').write_text(output_text)
        (directory/'events.jsonl').write_text(''.join(text_json(e)+'\n' for e in events))
        meta['output_sha256'] = sha(output_text.encode())
        meta['events_sha256'] = sha((directory/'events.jsonl').read_bytes())
        meta['status'] = 'completed'
        return output
    except Exception as error:
        meta['status'] = 'failed'
        meta['failure'] = str(error)
        raise
    finally:
        meta['elapsed_seconds'] = round(time.monotonic()-start, 3)
        meta['completed_at'] = datetime.now(timezone.utc).isoformat()
        write_json(directory/'manifest.json', meta)
