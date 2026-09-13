"""One informed recommender move followed by one independent buyer decision."""
import argparse
import importlib.util
import json
import platform
import re
import subprocess
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
spec = importlib.util.spec_from_file_location('analysis_runtime', REPO/'tools/analysis_runtime.py')
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


text_json = runtime.text_json


def records(provider):
    if provider not in ('bing', 'google'):
        raise ValueError('This analysis runs separate Bing or Google games')
    return adapter.load_universe(provider)


check_schema = runtime.check_schema


check_ids = runtime.check_ids


check_purchase = runtime.check_purchase


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
    return runtime.validate_buyer(output, response, json.loads((HERE/'buyer-schema.json').read_text()))


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
    return [REPO/'tools/analysis_runtime.py', REPO/'tools/analysis_replay.py', HERE/'run_game.py', HERE/'verify_runs.py', ORACLE, REPO/'tools/scenario.py', HERE/'config.json',
            HERE/'recommender-schema.json', HERE/'buyer-schema.json',
            *sorted((HERE/'prompts').glob('*.md'))]


def invoke(role, prompt, args, directory, prefix, version):
    return runtime.invoke(role, prompt, args, directory, prefix, version,
                          schema_file=HERE/(role+'-schema.json'), adapter=adapter,
                          include_participant=False, temporary_prefix='informed-game-')


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
