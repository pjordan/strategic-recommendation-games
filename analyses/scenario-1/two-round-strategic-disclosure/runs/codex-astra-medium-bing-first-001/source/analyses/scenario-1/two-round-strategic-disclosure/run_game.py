"""Two rounds of strategic buyer disclosure and independent recommender replies."""
import argparse
from concurrent.futures import ThreadPoolExecutor
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
        raise ValueError('Unknown provider')
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


def validate_recommender(output, provider, prior_response=None):
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
        if prior_response is not None:
            validate_response(prior_response, provider)
            returned.update({r['record_id']:r for r in prior_response['records']})
        choice = c['predicted_buyer_choice']
        action = 'purchase' if choice in ('own_provider','mixed_bundle') else 'decline'
        check_purchase(action, c['predicted_own_purchased_ids'], c['predicted_own_revenue_cents'], returned, enforce_budget=False)
    chosen = [c for c in candidates if c['candidate_id'] == output['selected_candidate_id']]
    if len(chosen) != 1 or chosen[0]['preference_rank'] != min(c['preference_rank'] for c in candidates):
        raise ValueError('Recommender selected response disagrees with ranking')
    return chosen[0]


def materialize(output, provider, prior_response=None):
    chosen = validate_recommender(output, provider, prior_response)
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


def public_context():
    return (SCENARIO/'public_context.md').read_text()


def private_context():
    return adapter.scenario.load_context('buyer',SCENARIO,'1.2.0')['private_user_preferences']


def validate_disclosure(output):
    check_schema(output,json.loads((HERE/'disclosure-schema.json').read_text()))
    candidates=output['candidates']
    if len({c['candidate_id'] for c in candidates})!=len(candidates):
        raise ValueError('Duplicate disclosure candidate IDs')
    if len({text_json(c['messages']) for c in candidates})!=len(candidates):
        raise ValueError('Duplicate disclosure plans')
    chosen=[c for c in candidates if c['candidate_id']==output['selected_candidate_id']]
    if len(chosen)!=1 or chosen[0]['preference_rank']!=min(c['preference_rank'] for c in candidates):
        raise ValueError('Selected disclosure plan disagrees with ranking')
    return chosen[0]


def disclosure_prompt(display_order='bing-first'):
    return ((HERE/'prompts/disclosure.md').read_text()
            + '\n## Public scenario\n\n'+public_context()
            + '\n## True private user preferences\n\n'+private_context()
            + '\n## Buyer provider-block order\n\n'+', then '.join(presentation_order(display_order))
            + '\n## Adaptive buyer follow-up instructions\n\n'+(HERE/'prompts/followup.md').read_text()
            + '\n## Recommender decision instructions\n\n'+(HERE/'prompts/recommender.md').read_text()
            + '\n## Final buyer decision instructions\n\n'+(HERE/'prompts/buyer.md').read_text())


def buyer_state(disclosure):
    selected=validate_disclosure(disclosure)
    return {'selected_plan':selected,'selection_reason':disclosure['selection_reason']}


def presentation_order(display_order):
    if display_order not in ('bing-first', 'google-first'):
        raise ValueError('Unknown display order')
    return ['bing','google'] if display_order == 'bing-first' else ['google','bing']


def recommender_prompt(provider, message, display_order='bing-first'):
    records(provider)
    return ((HERE/'prompts/recommender.md').read_text()
            + '\n## Your provider\n\n'+provider
            + '\n## Public scenario\n\n'+public_context()
            + '\n## Buyer provider-block order\n\n'+', then '.join(presentation_order(display_order))
            + '\n## Generic final buyer decision instructions (private brief not supplied)\n\n'+(HERE/'prompts/buyer.md').read_text()
            + '\n## Context message addressed only to you\n\n'+message
            + '\n## Complete frozen own-provider catalog\n\n'+text_json(records(provider))+'\n')


def validate_response(response, provider):
    if set(response) != {'provider','message','records'} or response['provider'] != provider:
        raise ValueError('Unexpected public response fields or provider')
    catalog = {r['record_id']:r for r in records(provider)}
    check_ids([r['record_id'] for r in response['records']],catalog)
    if any(r != catalog[r['record_id']] for r in response['records']):
        raise ValueError('Returned product record was modified')


def combine_responses(rounds, display_order='bing-first'):
    if not rounds or len(rounds)>2:
        raise ValueError('Expected one or two response rounds')
    combined = {}
    for responses in rounds:
        if set(responses) != {'bing','google'}:
            raise ValueError('Buyer must receive both committed responses per round')
        for provider in presentation_order(display_order):
            response=responses[provider]
            validate_response(response,provider)
            for r in response['records']:
                combined.setdefault(r['record_id'],r)
    return {'records':list(combined.values())}


def history(rounds, display_order='bing-first'):
    combine_responses(rounds,display_order)
    return [{'round':i+1,'responses':[rs[p] for p in presentation_order(display_order)]} for i,rs in enumerate(rounds)]


def validate_followup(output, first_responses):
    check_schema(output,json.loads((HERE/'followup-schema.json').read_text()))
    candidates=output['candidates']
    if len({c['candidate_id'] for c in candidates})!=len(candidates):
        raise ValueError('Duplicate follow-up candidate IDs')
    if len({text_json([c['messages'],c['shared_record_ids']]) for c in candidates})!=len(candidates):
        raise ValueError('Duplicate follow-up plans')
    catalog={r['record_id']:r for r in combine_responses([first_responses])['records']}
    for c in candidates:
        for ids in c['shared_record_ids'].values():
            check_ids(ids,catalog)
    selected=[c for c in candidates if c['candidate_id']==output['selected_candidate_id']]
    if len(selected)!=1 or selected[0]['preference_rank']!=min(c['preference_rank'] for c in candidates):
        raise ValueError('Selected follow-up disagrees with ranking')
    return selected[0]


def followups(output, first_responses):
    selected=validate_followup(output,first_responses)
    catalog={r['record_id']:r for r in combine_responses([first_responses])['records']}
    return {p:{'message':selected['messages'][p],
               'shared_records':[catalog[i] for i in selected['shared_record_ids'][p]]} for p in ('bing','google')}


def followup_state(output, first_responses):
    return {'selected_plan':validate_followup(output,first_responses),'selection_reason':output['selection_reason']}


def followup_prompt(first_responses, disclosure, display_order='bing-first'):
    return ((HERE/'prompts/followup.md').read_text()
            + '\n## Public scenario\n\n'+public_context()
            + '\n## True private user preferences\n\n'+private_context()
            + '\n## Your selected initial disclosure state\n\n'+text_json(buyer_state(disclosure))
            + '\n## Both first-round public responses\n\n'+text_json(history([first_responses],display_order))
            + '\n## Recommender instructions\n\n'+(HERE/'prompts/recommender.md').read_text()
            + '\n## Final buyer instructions\n\n'+(HERE/'prompts/buyer.md').read_text())


def recommender_state(output, provider):
    return {'selected_candidate':validate_recommender(output,provider),
            'selection_reason':output['selection_reason'],'buyer_belief':output['buyer_belief']}


def second_recommender_prompt(provider, initial_message, first_output, addressed_followup, display_order='bing-first'):
    # No full buyer follow-up plan or rival response object enters this function.
    if set(addressed_followup)!={'message','shared_records'}:
        raise ValueError('Unexpected addressed follow-up fields')
    return (recommender_prompt(provider,initial_message,display_order)
            + '\n## Current stage: ROUND 2, final reply\n\n'
            + 'The context message above was your round-1 input. This is your second and final response. '
              'Your previous offers below remain available regardless of what you return now.\n'
            + '\n## Your own selected round-1 state\n\n'+text_json(recommender_state(first_output,provider))
            + '\n## Your public first-round response\n\n'+text_json(materialize(first_output,provider))
            + '\n## Buyer follow-up addressed only to you and buyer-selected evidence\n\n'+text_json(addressed_followup)+'\n')


def buyer_prompt(rounds, disclosure, followup, display_order='bing-first'):
    if len(rounds)!=2:
        raise ValueError('Final buyer requires both rounds')
    combine_responses(rounds,display_order)
    return ((HERE/'prompts/buyer.md').read_text()
            + '\n## Public scenario\n\n'+public_context()
            + '\n## True private user preferences\n\n'+private_context()
            + '\n## Your selected initial disclosure state\n\n'+text_json(buyer_state(disclosure))
            + '\n## Your selected follow-up state\n\n'+text_json(followup_state(followup,rounds[0]))
            + '\n## All four returned recommendation responses\n\n'+text_json(history(rounds,display_order))+'\n')


def source_files():
    return [HERE/'run_game.py', HERE/'verify_runs.py', REPO/'tests/test_two_round_disclosure.py', ORACLE, REPO/'tools/scenario.py', HERE/'config.json',
            HERE/'recommender-schema.json', HERE/'buyer-schema.json', HERE/'disclosure-schema.json',
            HERE/'followup-schema.json', HERE/'run.sh', *sorted((HERE/'prompts').glob('*.md'))]


def invoke(role, prompt, args, directory, prefix, version):
    directory.mkdir()
    schema_file = HERE/(role+'-schema.json')
    (directory/'input.md').write_text(prompt)
    meta = {'role': role, 'participant': directory.name, 'harness': args.harness, 'harness_version': version,
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
        with tempfile.TemporaryDirectory(prefix='two-round-game-') as temporary:
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


def outcome(recommenders, buyer, rounds, disclosure, followup, display_order='bing-first'):
    if len(recommenders)!=2 or len(rounds)!=2:
        raise ValueError('Outcome requires two full rounds')
    combined=combine_responses(rounds,display_order)
    validate_buyer(buyer,combined)
    purchased=set(buyer['selected_record_ids'])
    participants={}
    for p in ('bing','google'):
        own=[r for r in combined['records'] if r['provider']==p and r['record_id'] in purchased]
        own_ids=[r['record_id'] for r in own]
        info={'actual_own_purchased_ids':own_ids,
              'realized_own_revenue_cents':sum(r['displayed_price_cents'] for r in own), 'rounds':[]}
        seen=set()
        for i in range(2):
            prior=rounds[0][p] if i else None
            selected=validate_recommender(recommenders[i][p],p,prior)
            if materialize(recommenders[i][p],p,prior)!=rounds[i][p]:
                raise ValueError('Response differs from selected recommender action')
            returned=[r['record_id'] for r in rounds[i][p]['records']]
            info['rounds'].append({'round':i+1,'selected_candidate_id':selected['candidate_id'],
                'returned_record_ids':returned,'new_record_ids':[rid for rid in returned if rid not in seen],
                'predicted_buyer_choice':selected['predicted_buyer_choice'],
                'predicted_own_purchased_ids':selected['predicted_own_purchased_ids'],
                'predicted_own_revenue_cents':selected['predicted_own_revenue_cents'],
                'own_purchase_prediction_matched':set(own_ids)==set(selected['predicted_own_purchased_ids']),
                'buyer_belief':recommenders[i][p]['buyer_belief'],
                'selection_reason':recommenders[i][p]['selection_reason']})
            seen.update(returned)
        info['unique_returned_count']=len(seen)
        participants[p]=info
    if sum(v['realized_own_revenue_cents'] for v in participants.values())!=buyer['purchase_value_cents']:
        raise ValueError('Revenue attribution does not conserve purchase value')
    winners=[p for p,v in participants.items() if v['actual_own_purchased_ids']]
    for p,info in participants.items():
        actual='decline' if not winners else ('mixed_bundle' if len(winners)==2 else ('own_provider' if p in winners else 'other_provider'))
        info['actual_buyer_choice']=actual
        for rnd in info['rounds']:
            rnd['destination_prediction_matched']=actual==rnd['predicted_buyer_choice']
    first_ids={r['record_id'] for r in combine_responses([rounds[0]])['records']}
    return {'initial_disclosure':buyer_state(disclosure), 'followup':followup_state(followup,rounds[0]),
            'buyer_action':buyer['selected_action'],'purchased_record_ids':buyer['selected_record_ids'],
            'purchase_value_cents':buyer['purchase_value_cents'],'credited_providers':winners,
            'unique_returned_count':len(combined['records']),
            'selected_records_first_available_round':{rid:1 if rid in first_ids else 2 for rid in buyer['selected_record_ids']},
            'display_order':presentation_order(display_order),'recommenders':participants,
            'buyer_reason':buyer['selected_outcome_reason']}


def transcript(disclosure, followup, rounds, buyer, display_order):
    messages=validate_disclosure(disclosure)['messages']
    addressed=followups(followup,rounds[0])
    result=[]
    for i in range(2):
        result += [{'round':i+1,'role':'buyer','recipient':p,'content':messages[p] if i==0 else addressed[p]} for p in ('bing','google')]
        result += [{'round':i+1,'role':'recommender','provider':p,'content':rounds[i][p]} for p in presentation_order(display_order)]
    return result+[{'role':'buyer','stage':'final_decision','content':buyer}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--display-order', choices=['bing-first','google-first'], default='bing-first')
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
    meta = {'run_id':args.run_id, 'analysis_id':config['analysis_id'], 'providers':['bing','google'], 'display_order':args.display_order,
            'scenario_version':'1.2.0', 'scenario_manifest_sha256':config['scenario_manifest_sha256'],
            'base_scenario_manifest_sha256':config['base_scenario_manifest_sha256'],
            'catalog_record_counts':{p:len(records(p)) for p in ('bing','google')}, 'status':'prepared',
            'harness':args.harness,'harness_version':version,'model_requested':args.model,
            'reasoning_effort_requested':args.effort, 'sampling_note':'No seed or temperature set; fresh samples need not reproduce choices.',
            'started_at':datetime.now(timezone.utc).isoformat(), 'python_version':platform.python_version(),
            'os_family':platform.system(), 'buyer_access':'union_of_all_four_returned_lists', 'recommender_submission':'Independent sealed responses each round; own catalog, own selected prior state and addressed buyer messages/evidence only',
            'buyer_state_policy':'Fresh disclosure, follow-up and final calls linked by selected plans/reasons and public history; true preferences supplied to all three',
            'recommender_state_policy':'Fresh round-2 calls linked by own selected round-1 strategy/reason/belief/response and addressed buyer history only',
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
            (out/'disclosure-input.md').write_text(disclosure_prompt(args.display_order))
            meta['status']='dry_run_not_executed'
            meta['note']='Later actor inputs depend on generated messages/responses and are not fabricated.'
            return
        print('Buyer is selecting separately addressed disclosure messages',flush=True)
        disclosure=invoke('disclosure',disclosure_prompt(args.display_order),args,out/'disclosure',prefix,version)
        selected=validate_disclosure(disclosure)
        messages=selected['messages']
        write_json(out/'disclosures.json',messages)
        write_json(out/'buyer-state.json',buyer_state(disclosure))
        rounds=[];recommenders=[]
        for index in range(2):
            stages=out/('round-'+str(index+1));stages.mkdir()
            print('Round '+str(index+1)+': independent recommender replies',flush=True)
            if index==0:
                prompts={p:recommender_prompt(p,messages[p],args.display_order)+'\n## Current stage: ROUND 1\n\nAnticipate the adaptive follow-up and final second-round replies.\n' for p in ('bing','google')}
            else:
                prompts={p:second_recommender_prompt(p,messages[p],recommenders[0][p],addressed[p],args.display_order) for p in ('bing','google')}
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures={p:pool.submit(invoke,'recommender',prompts[p],args,stages/p,prefix,version) for p in ('bing','google')}
                recs={p:futures[p].result() for p in ('bing','google')}
            rs={p:materialize(recs[p],p,rounds[0][p] if index else None) for p in ('bing','google')}
            recommenders.append(recs);rounds.append(rs)
            write_json(out/('round-'+str(index+1)+'-responses.json'),rs)
            if index==0:
                print('Both first replies committed; buyer selects separate follow-ups',flush=True)
                followup=invoke('followup',followup_prompt(rs,disclosure,args.display_order),args,out/'followup',prefix,version)
                addressed=followups(followup,rs)
                write_json(out/'followups.json',addressed)
                write_json(out/'followup-state.json',followup_state(followup,rs))
        write_json(out/'responses.json',rounds)
        print('All four replies committed; buyer chooses using true preferences',flush=True)
        buyer=invoke('buyer',buyer_prompt(rounds,disclosure,followup,args.display_order),args,out/'buyer',prefix,version)
        result=outcome(recommenders,buyer,rounds,disclosure,followup,args.display_order)
        write_json(out/'outcome.json',result)
        write_json(out/'transcript.json',transcript(disclosure,followup,rounds,buyer,args.display_order))
        meta['artifacts_sha256']={f:sha((out/f).read_bytes()) for f in ['disclosures.json','buyer-state.json','round-1-responses.json','followups.json','followup-state.json','round-2-responses.json','responses.json','outcome.json','transcript.json']}
        meta['status']='completed'
        print(text_json(result),flush=True)
    except Exception as error:
        meta['status'] = 'failed'; meta['failure'] = str(error)
        raise
    finally:
        meta['completed_at'] = datetime.now(timezone.utc).isoformat()
        write_json(out/'manifest.json',meta)


if __name__ == '__main__':
    main()
