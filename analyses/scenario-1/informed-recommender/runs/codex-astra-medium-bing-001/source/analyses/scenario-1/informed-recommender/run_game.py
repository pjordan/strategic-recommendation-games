"""One informed recommender move followed by one independent buyer decision."""
import argparse
import hashlib
import importlib.util
import json
import os
import platform
import re
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ORACLE = HERE.parent / 'oracle-access/run_model.py'
spec = importlib.util.spec_from_file_location('oracle_adapter', ORACLE)
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
sha = adapter.sha
write_json = adapter.write_json
SCENARIO = adapter.SCENARIO


def text_json(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def records(provider):
    if provider not in ('bing', 'google'):
        raise ValueError('This analysis runs separate Bing or Google games')
    return adapter.load_universe(provider)


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


def validate_recommender(output, provider):
    check_schema(output, json.loads((HERE/'recommender-schema.json').read_text()))
    catalog = {r['record_id']: r for r in records(provider)}
    candidates = output['candidates']
    if len({c['candidate_id'] for c in candidates}) != len(candidates):
        raise ValueError('Duplicate candidate IDs')
    if len({text_json([c['ordered_record_ids'], c['message']]) for c in candidates}) != len(candidates):
        raise ValueError('Duplicate response candidates')
    if not any(not c['ordered_record_ids'] for c in candidates):
        raise ValueError('Missing empty-list response candidate')
    for c in candidates:
        check_ids(c['ordered_record_ids'], catalog)
        returned = {i: catalog[i] for i in c['ordered_record_ids']}
        check_purchase(c['predicted_buyer_action'], c['predicted_purchased_ids'], c['predicted_purchase_value_cents'], returned)
    chosen = [c for c in candidates if c['candidate_id'] == output['selected_candidate_id']]
    if len(chosen) != 1 or chosen[0]['preference_rank'] != min(c['preference_rank'] for c in candidates):
        raise ValueError('Recommender selected response disagrees with ranking')
    return chosen[0]


def materialize(output, provider):
    chosen = validate_recommender(output, provider)
    catalog = {r['record_id']: r for r in records(provider)}
    # Only public message and exact records cross the information boundary.
    return {'provider': provider, 'message': chosen['message'],
            'records': [catalog[i] for i in chosen['ordered_record_ids']]}


def validate_buyer(output, response):
    check_schema(output, json.loads((HERE/'buyer-schema.json').read_text()))
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


def common_context(provider):
    context = adapter.scenario.load_context('buyer', SCENARIO, '1.2.0')
    return ('\n## Provider\n\n' + provider + '\n## Shared background\n\n' + context['public_context']
            + '\n## User preference brief\n\n' + context['private_user_preferences']
            + '\n## Initial user request\n\n' + (HERE/'prompts/request.md').read_text())


def recommender_prompt(provider):
    return ((HERE/'prompts/recommender.md').read_text() + common_context(provider)
            + '\n## Exact buyer decision instructions\n\n' + (HERE/'prompts/buyer.md').read_text()
            + '\n## Complete frozen provider catalog\n\n' + text_json(records(provider)) + '\n')


def buyer_prompt(provider, response):
    return ((HERE/'prompts/buyer.md').read_text() + common_context(provider)
            + '\n## Returned recommendation\n\n' + text_json(response) + '\n')


def source_files():
    return [HERE/'run_game.py', ORACLE, REPO/'tools/scenario.py', HERE/'config.json',
            HERE/'recommender-schema.json', HERE/'buyer-schema.json',
            *sorted((HERE/'prompts').glob('*.md'))]


def invoke(role, prompt, args, directory, prefix, version):
    directory.mkdir()
    schema_file = HERE/(role+'-schema.json')
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
    argv = adapter.command(args.harness, args.model, args.effort, schema_file, Path('OUTPUT_JSON'))
    meta['command_argv'] = prefix + [x.replace(str(schema_file),'OUTPUT_SCHEMA_JSON') for x in argv[1:]]
    write_json(directory/'manifest.json', meta)
    env = os.environ.copy()
    if args.harness == 'codex':
        env.pop('OPENAI_API_KEY', None)
        env.pop('CODEX_API_KEY', None)
    start = time.monotonic()
    try:
        with tempfile.TemporaryDirectory(prefix='informed-game-') as temporary:
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


def outcome(provider, rec, buyer, response):
    selected = validate_recommender(rec, provider)
    validate_buyer(buyer, response)
    return {'provider':provider, 'selected_response_candidate_id':rec['selected_candidate_id'],
            'returned_record_ids':[r['record_id'] for r in response['records']],
            'omitted_record_count':len(records(provider))-len(response['records']),
            'predicted_buyer_action':selected['predicted_buyer_action'],
            'predicted_purchased_ids':selected['predicted_purchased_ids'],
            'predicted_purchase_value_cents':selected['predicted_purchase_value_cents'],
            'actual_buyer_action':buyer['selected_action'], 'purchased_record_ids':buyer['selected_record_ids'],
            'realized_purchase_value_cents':buyer['purchase_value_cents'],
            'recommender_payoff_cents':buyer['purchase_value_cents'],
            'prediction_matched':selected['predicted_buyer_action']==buyer['selected_action'] and set(selected['predicted_purchased_ids'])==set(buyer['selected_record_ids']),
            'buyer_reason':buyer['selected_outcome_reason'], 'recommender_reason':rec['selection_reason']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--provider', choices=['bing','google'], required=True)
    parser.add_argument('--harness', choices=['codex','claude'], required=True)
    parser.add_argument('--model', required=True)
    parser.add_argument('--effort', required=True)
    parser.add_argument('--codex-version')
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9._-]+', args.run_id):
        parser.error('Use a portable run ID')
    prefix = [args.harness]
    if args.codex_version:
        if args.harness != 'codex' or not re.fullmatch(r'\d+\.\d+\.\d+', args.codex_version):
            parser.error('codex-version requires Codex and an exact numeric version')
        prefix = ['npx','--yes','--package','@openai/codex@'+args.codex_version,'codex']
    adapter.scenario.validate_version('1.2.0')
    out = Path(args.output_dir).resolve()
    if out.exists():
        parser.error('Output exists; use a new directory to preserve previous runs')
    out.mkdir(parents=True)
    version = subprocess.check_output(prefix+['--version'], text=True).strip()
    config = json.loads((HERE/'config.json').read_text())
    if config['scenario_manifest_sha256'] != sha(adapter.scenario_manifest_path('satisfaction').read_bytes()):
        raise ValueError('Scenario version does not match analysis configuration')
    meta = {'run_id':args.run_id, 'analysis_id':config['analysis_id'], 'provider':args.provider,
            'scenario_version':'1.2.0', 'scenario_manifest_sha256':config['scenario_manifest_sha256'],
            'base_scenario_manifest_sha256':config['base_scenario_manifest_sha256'],
            'record_count':len(records(args.provider)), 'status':'prepared',
            'harness':args.harness,'harness_version':version,'model_requested':args.model,
            'reasoning_effort_requested':args.effort, 'sampling_note':'No seed or temperature set; fresh samples need not reproduce choices.',
            'started_at':datetime.now(timezone.utc).isoformat(), 'python_version':platform.python_version(),
            'os_family':platform.system(), 'buyer_access':'returned_list_only',
            'repository_commit_at_start':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
            'repository_dirty_at_start':bool(subprocess.check_output(['git','status','--porcelain'],cwd=REPO,text=True).strip()),
            'source_sha256':{}, 'artifacts_sha256':{}}
    provenance = out/'source'; provenance.mkdir()
    for file in source_files():
        relative = file.relative_to(REPO).as_posix()
        target = provenance/relative; target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(file.read_bytes())
        meta['source_sha256'][relative] = sha(file.read_bytes())
    write_json(out/'manifest.json',meta)
    try:
        if args.dry_run:
            (out/'recommender-input.md').write_text(recommender_prompt(args.provider))
            meta['status'] = 'dry_run_not_executed'
            meta['note'] = 'Buyer input depends on an actual recommender output and is not fabricated for a dry run.'
            return
        print(args.provider+': running informed recommender', flush=True)
        rec = invoke('recommender', recommender_prompt(args.provider), args, out/'recommender', prefix, version)
        response = materialize(rec, args.provider)
        write_json(out/'response.json',response)
        print(args.provider+': running fresh buyer on selected response', flush=True)
        buyer = invoke('buyer', buyer_prompt(args.provider,response), args, out/'buyer', prefix, version)
        result = outcome(args.provider,rec,buyer,response)
        write_json(out/'outcome.json',result)
        transcript = [{'role':'user','content':(HERE/'prompts/request.md').read_text()},
                      {'role':'recommender','content':response},
                      {'role':'buyer','content':buyer}]
        write_json(out/'transcript.json',transcript)
        meta['artifacts_sha256'] = {f:sha((out/f).read_bytes()) for f in ['response.json','outcome.json','transcript.json']}
        meta['status'] = 'completed'
        print(text_json(result), flush=True)
    except Exception as error:
        meta['status'] = 'failed'; meta['failure'] = str(error)
        raise
    finally:
        meta['completed_at'] = datetime.now(timezone.utc).isoformat()
        write_json(out/'manifest.json',meta)


if __name__ == '__main__':
    main()
