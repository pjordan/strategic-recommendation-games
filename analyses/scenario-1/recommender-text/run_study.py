"""Fresh paired whole-game reruns with and without recommender commentary."""
import argparse
import copy
import json
import platform
import random
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO/'tools'))
import analysis_runtime as runtime
import scenario_current as scenario

BASE = HERE.parent/'two-round-strategic-disclosure'
adapter = runtime.load_module('oracle_adapter', HERE.parent/'oracle-access/run_model.py')
sha, write_json = adapter.sha, adapter.write_json
SCENARIO = REPO/'scenarios/scenario-1'
CONFIG = json.loads((HERE/'config.json').read_text())
MODES = CONFIG['arms']


def read(path):
    return json.loads(path.read_text())


def plan(replicates, seed):
    if replicates < 1:
        raise ValueError('Replicates must be positive')
    pairs = []
    for replicate in range(1, replicates+1):
        for stratum in CONFIG['strata']:
            suffix = '-'+stratum['providers'][0] if len(stratum['providers']) == 1 else ''
            pairs.append({**stratum, 'replicate': replicate,
                          'pair_id': stratum['condition']+suffix+'-r'+str(replicate).zfill(3),
                          'display_order': 'bing-first' if replicate % 2 else 'google-first'})
    first = [MODES[i % 2] for i in range(len(pairs))]
    random.Random(seed).shuffle(first)
    for pair, mode in zip(pairs, first):
        pair['arm_order'] = [mode, next(m for m in MODES if m != mode)]
    return pairs


class Game:
    def __init__(self, pair, mode):
        if mode not in MODES:
            raise ValueError('Unknown response policy')
        self.pair, self.mode = pair, mode
        self.providers = pair['providers']
        self.order = [p for p in (['bing', 'google'] if pair['display_order'] == 'bing-first' else ['google', 'bing']) if p in self.providers]
        self.adaptive = pair['condition'] in ('strategic-disclosure', 'two-round-strategic-disclosure')
        self.round_count = 2 if pair['condition'] == 'two-round-strategic-disclosure' else 1
        self.context = scenario.load_context('buyer', SCENARIO)
        self.catalog = {p: scenario.load_records(p, SCENARIO) for p in self.providers}
        # Each instance has its own legacy validator namespace. Only the record
        # source is rebound; no legacy runner or global shared data is changed.
        self.validator = runtime.load_module('validators', BASE/'run_game.py')
        self.validator.records = lambda p: self.catalog[p]
        self.facts = {}
        for p in self.providers:
            self.facts[p] = [{k: f[k] for k in ('record_id', 'resolution', 'facts', 'conflicts', 'not_established_categories')}
                             for f in scenario.load_facts(p, root=SCENARIO)]

    def schema(self, role):
        schema = read(BASE/(role+'-schema.json'))
        if role == 'recommender':
            item = schema['properties']['candidates']['items']
            if self.mode == 'list-only':
                del item['properties']['message']
                item['required'].remove('message')
            if len(self.providers) == 1:
                item['properties']['predicted_buyer_choice']['enum'] = ['own_provider', 'decline']
        return schema

    def rules(self):
        policy = ('Recommenders may return an ordered list of unchanged cards AND an accompanying message. Only the selected message is forwarded.'
                  if self.mode == 'text-enabled' else
                  'Recommenders return ONLY an ordered list of unchanged cards, with provider/round labels. No message field, commentary, explanations, fact attachments or private justifications reach the buyer, in any round. Buyer-to-recommender messages remain permitted.')
        knowledge = ('Recommenders receive only their addressed buyer context and own catalog/facts; the buyer retains the true private brief.' if self.adaptive else
                     'Every recommender receives the complete true buyer preference brief and its own catalog/facts.')
        return {'providers': self.providers, 'provider_display_order': self.order,
                'rounds': self.round_count, 'communication_policy': policy,
                'information_policy': knowledge,
                'sequence': ('Buyer initial messages, independent round-1 replies, buyer follow-ups, independent round-2 replies, final buyer decision.' if self.round_count == 2 else
                             ('Buyer initial messages, independent replies, final buyer decision.' if self.adaptive else 'Fixed user request, independent replies, final buyer decision.')),
                'sealed_replies': 'No recommender sees a same-round rival reply. No actor receives another arm or earlier run.'}

    def prompt(self, role, payload):
        return ((HERE/'prompts/common.md').read_text()+'\n'+(HERE/'prompts'/(role+'.md')).read_text()
                +'\n## Game rules\n\n'+runtime.text_json(self.rules())
                +'\n## Public scenario\n\n'+self.context['public_context']
                +'\n## Your information\n\n'+runtime.text_json(payload)+'\n')

    def legacy_output(self, output):
        value = copy.deepcopy(output)
        if self.mode == 'list-only':
            for candidate in value['candidates']:
                candidate['message'] = ''
        return value

    @staticmethod
    def legacy_response(response):
        return {'message': '', **response}

    def select(self, output, provider, prior=None):
        runtime.check_schema(output, self.schema('recommender'))
        selected = self.validator.validate_recommender(self.legacy_output(output), provider,
                    self.legacy_response(prior) if prior is not None else None)
        return next(c for c in output['candidates'] if c['candidate_id'] == selected['candidate_id'])

    def response(self, output, provider, prior=None):
        chosen = self.select(output, provider, prior)
        catalog = {r['record_id']: r for r in self.catalog[provider]}
        result = {'provider': provider, 'records': [catalog[i] for i in chosen['ordered_record_ids']]}
        if self.mode == 'text-enabled':
            result['message'] = chosen['message']
        return result

    def history(self, rounds):
        return [{'round': i+1, 'responses': [rs[p] for p in self.order]} for i, rs in enumerate(rounds)]

    def combined(self, rounds):
        records = {}
        for rs in rounds:
            for p in self.order:
                for r in rs[p]['records']:
                    records.setdefault(r['record_id'], r)
        return {'records': list(records.values())}

    def run(self, call):
        """Explicit move order; call is live execution or deterministic replay."""
        buyer_context = {'true_private_user_preferences': self.context['private_user_preferences']}
        disclosure = None
        if self.adaptive:
            disclosure = call('disclosure', 'disclosure', self.prompt('disclosure', buyer_context), self.schema('disclosure'))
            selected = self.validator.validate_disclosure(disclosure)
            messages = selected['messages']
            buyer_context['selected_initial_state'] = {'selected_plan': selected, 'selection_reason': disclosure['selection_reason']}
        else:
            request = (HERE.parent/'informed-recommender/prompts/request.md').read_text()
            messages = {p: request for p in self.providers}
        rounds, outputs, choices, transcript = [], [], [], []
        addressed = None
        for i in range(self.round_count):
            def recommend(p):
                payload = {'provider': p, 'round': i+1, 'addressed_initial_message': messages[p],
                           'own_catalog': self.catalog[p], 'own_frozen_product_facts': self.facts[p]}
                if not self.adaptive:
                    payload.update(buyer_context)
                if i:
                    old = outputs[0][p]
                    payload.update(own_selected_prior_state={'selected_candidate': self.select(old, p),
                                   'selection_reason': old['selection_reason'], 'buyer_belief': old['buyer_belief']},
                                   own_prior_public_response=rounds[0][p], addressed_followup=addressed[p])
                output = call('round-'+str(i+1)+'/'+p, 'recommender', self.prompt('recommender', payload), self.schema('recommender'))
                prior = rounds[0][p] if i else None
                return output, self.response(output, p, prior), self.select(output, p, prior)
            # Both submissions finish before any response is shown to the buyer.
            with ThreadPoolExecutor(max_workers=len(self.providers)) as executor:
                futures = {p: executor.submit(recommend, p) for p in self.providers}
                results = {p: futures[p].result() for p in self.providers}
            outputs.append({p: results[p][0] for p in self.providers})
            rounds.append({p: results[p][1] for p in self.providers})
            choices.append({p: results[p][2] for p in self.providers})
            transcript.extend({'round': i+1, 'role': 'buyer', 'recipient': p,
                               'content': messages[p] if not i else addressed[p]} for p in self.providers)
            transcript.extend({'round': i+1, 'role': 'recommender', 'provider': p,
                               'content': rounds[i][p]} for p in self.order)
            if i == 0 and self.round_count == 2:
                followup = call('followup', 'followup', self.prompt('followup', {**buyer_context, 'observed_history': self.history(rounds)}), self.schema('followup'))
                legacy = {p: self.legacy_response(rounds[0][p]) for p in self.providers}
                addressed = self.validator.followups(followup, legacy)
                buyer_context['selected_followup_state'] = self.validator.followup_state(followup, legacy)
        buyer = call('buyer', 'buyer', self.prompt('buyer', {**buyer_context, 'observed_history': self.history(rounds)}), self.schema('buyer'))
        available = self.combined(rounds)
        runtime.validate_buyer(buyer, available, self.schema('buyer'))
        purchased = set(buyer['selected_record_ids'])
        revenue = {p: sum(r['displayed_price_cents'] for r in available['records'] if r['provider'] == p and r['record_id'] in purchased) for p in self.providers}
        assert sum(revenue.values()) == buyer['purchase_value_cents']
        outcome = {'buyer_action': buyer['selected_action'], 'purchased_record_ids': buyer['selected_record_ids'],
                   'purchase_value_cents': buyer['purchase_value_cents'], 'purchased_item_count': len(purchased),
                   'provider_revenue_cents': revenue, 'unique_returned_count': len(available['records']),
                   'recommender_choices': choices, 'buyer_reason': buyer['selected_outcome_reason'],
                   'buyer_strategic_response': buyer['strategic_response']}
        transcript.append({'role': 'buyer', 'stage': 'final_decision', 'content': buyer})
        return {'outcome.json': outcome, 'responses.json': self.history(rounds), 'transcript.json': transcript}


def comparison(pair, results):
    row = {**pair, 'status': 'completed' if all(m in results for m in MODES) else 'incomplete'}
    row['arms'] = {m: {k: v[k] for k in ('buyer_action', 'purchased_record_ids', 'purchase_value_cents', 'purchased_item_count', 'provider_revenue_cents', 'unique_returned_count', 'buyer_reason')} for m, v in results.items()}
    if row['status'] == 'completed':
        text, lists = (results[m] for m in MODES)
        row['text_minus_list'] = {k: text[k]-lists[k] for k in ('purchase_value_cents', 'purchased_item_count', 'unique_returned_count')}
        row['text_minus_list']['provider_revenue_cents'] = {p: text['provider_revenue_cents'][p]-lists['provider_revenue_cents'][p] for p in pair['providers']}
        row['purchase_changed'] = (text['buyer_action'], sorted(text['purchased_record_ids'])) != (lists['buyer_action'], sorted(lists['purchased_record_ids']))
        row['ordered_lists_changed'] = [[c[p]['ordered_record_ids'] for p in pair['providers']] for c in text['recommender_choices']] != [[c[p]['ordered_record_ids'] for p in pair['providers']] for c in lists['recommender_choices']]
    return row


def source_files():
    return sorted(set([Path(__file__), HERE/'verify_runs.py', HERE/'run.sh', HERE/'config.json',
                       *sorted((HERE/'prompts').glob('*.md')), *sorted(BASE.glob('*-schema.json')),
                       *runtime.load_module('base_sources', BASE/'run_game.py').source_files(),
                       HERE.parent/'informed-recommender/prompts/request.md', REPO/'tools/scenario_current.py',
                       REPO/'tests/test_recommender_text.py']))


def data_hashes():
    paths = [SCENARIO/'manifest.sha256', SCENARIO/'versions/1.2.0/manifest.sha256',
             SCENARIO/'versions/1.3.0/manifest.sha256', SCENARIO/'product-facts/versions/1.0.0/manifest.json']
    return {p.relative_to(REPO).as_posix(): sha(p.read_bytes()) for p in paths}


def verify_current(directory, *, config=CONFIG, game_type=Game, compare=comparison):
    meta = read(directory/'manifest.json')
    plan_key = config.get('plan_key', 'pairs')
    if meta.get('study_design', config) != config:
        raise ValueError('Study configuration differs')
    scenario.validate(SCENARIO)
    if meta['data_manifest_sha256'] != data_hashes():
        raise ValueError('Frozen data manifests differ')
    for rel, digest in meta['source_sha256'].items():
        if sha((REPO/rel).read_bytes()) != digest:
            raise ValueError('Replay requires the recorded source tree')
    for rel, digest in meta['artifacts_sha256'].items():
        if sha((directory/rel).read_bytes()) != digest:
            raise ValueError('Study artifact hash mismatch')
    comparisons = []
    for pair in meta[plan_key]:
        results = {}
        for mode in pair['arm_order']:
            arm = directory/pair['pair_id']/mode
            arm_meta = read(arm/'manifest.json')
            if arm_meta['status'] != 'completed':
                continue
            game = game_type(pair, mode)
            def replay(stage, role, prompt, schema):
                path = arm/stage
                m = read(path/'manifest.json')
                if m['status'] != 'completed' or (path/'input.md').read_text() != prompt:
                    raise ValueError('Actor input or status differs')
                if read(arm/'schemas'/(role+'.json')) != schema:
                    raise ValueError('Actor schema differs')
                for file, key in [('input.md', 'input_sha256'), ('output.json', 'output_sha256'), ('events.jsonl', 'events_sha256')]:
                    if sha((path/file).read_bytes()) != m[key]:
                        raise ValueError('Actor artifact hash differs')
                if sha((arm/'schemas'/(role+'.json')).read_bytes()) != m['output_schema_sha256']:
                    raise ValueError('Actor schema hash differs')
                if any(m[k] != meta[k] for k in ('harness', 'harness_version', 'model_requested', 'reasoning_effort_requested')):
                    raise ValueError('Actor execution profile differs')
                return read(path/'output.json')
            for name, value in game.run(replay).items():
                if read(arm/name) != value:
                    raise ValueError('Game artifact does not replay')
                if name == 'outcome.json': results[mode] = value
        comparisons.append(compare(pair, results))
    if comparisons != read(directory/config.get('summary_file', 'comparisons.json')):
        raise ValueError('Paired comparison differs')
    return {'status': meta['status'], plan_key: len(comparisons), 'completed_'+plan_key: sum(c['status'] == 'completed' for c in comparisons)}


def main(*, config=CONFIG, game_type=Game, make_plan=plan, compare=comparison, get_sources=source_files):
    """Execute a study definition while preserving each condition's explicit moves."""
    plan_key = config.get('plan_key', 'pairs')
    summary_file = config.get('summary_file', 'comparisons.json')
    parser = argparse.ArgumentParser(description=config.get('description', __doc__))
    parser.add_argument('--verify', type=Path)
    parser.add_argument('--harness', choices=['codex', 'claude'])
    parser.add_argument('--model')
    parser.add_argument('--effort')
    parser.add_argument('--codex-version')
    parser.add_argument('--run-id')
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--replicates', type=int, default=1)
    parser.add_argument('--plan-seed', type=int, default=0)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    if args.verify:
        print(json.dumps(verify_current(args.verify.resolve(), config=config, game_type=game_type, compare=compare), indent=2)); return
    if not all((args.harness, args.model, args.effort, args.run_id, args.output_dir)):
        parser.error('Provide harness, model, effort, run-id and output-dir')
    if not re.fullmatch(r'[A-Za-z0-9._-]+', args.run_id): parser.error('Use a portable run ID')
    prefix = [args.harness]
    if args.codex_version:
        if args.harness != 'codex' or not re.fullmatch(r'\d+\.\d+\.\d+', args.codex_version): parser.error('Use an exact Codex version')
        prefix = ['npx', '--yes', '--package', '@openai/codex@'+args.codex_version, 'codex']
    pairs = make_plan(args.replicates, args.plan_seed)
    scenario.validate(SCENARIO)
    out = args.output_dir.resolve()
    if out.exists(): parser.error('Output exists; use a fresh study directory')
    version = None if args.dry_run else subprocess.check_output(prefix+['--version'], text=True).strip()
    out.mkdir(parents=True)
    meta = {'analysis_id': config['analysis_id'], 'analysis_version': config['version'], 'run_id': args.run_id,
            'scenario_version': config['scenario_version'], 'facts_version': config['facts_version'],
            'harness': args.harness, 'harness_version': version, 'model_requested': args.model,
            'reasoning_effort_requested': args.effort, 'codex_version_requested': args.codex_version,
            'model_seed': None, 'temperature': None, 'plan_seed': args.plan_seed, plan_key: pairs, 'study_design': config,
            'started_at': datetime.now(timezone.utc).isoformat(), 'python_version': platform.python_version(),
            'repository_commit_at_start': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip(),
            'repository_dirty_at_start': bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=REPO, text=True).strip()),
            'data_manifest_sha256': data_hashes(), 'source_sha256': {}, 'artifacts_sha256': {}, 'status': 'prepared'}
    for file in get_sources():
        relative = file.relative_to(REPO).as_posix()
        target = out/'source'/relative; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(file.read_bytes()); meta['source_sha256'][relative] = sha(file.read_bytes())
    write_json(out/'manifest.json', meta)
    comparisons = []
    try:
        for pair in pairs:
            results = {}
            for mode in pair['arm_order']:
                arm = out/pair['pair_id']/mode; arm.mkdir(parents=True)
                game = game_type(pair, mode)
                arm_meta = {'pair_id': pair['pair_id'], 'mode': mode, 'status': 'prepared'}
                write_json(arm/'manifest.json', arm_meta)
                (arm/'schemas').mkdir()
                for role in ('recommender', 'buyer', 'disclosure', 'followup'):
                    write_json(arm/'schemas'/(role+'.json'), game.schema(role))
                def live(stage, role, prompt, schema):
                    print(pair['pair_id']+' / '+mode+' / '+stage, flush=True)
                    path = arm/stage; path.parent.mkdir(parents=True, exist_ok=True)
                    return runtime.invoke(role, prompt, args, path, prefix, version,
                                          schema_file=arm/'schemas'/(role+'.json'), adapter=adapter,
                                          include_participant=True, temporary_prefix='text-game-')
                try:
                    if args.dry_run:
                        # Initial inputs only; no downstream responses are fabricated.
                        def prepare(stage, role, prompt, schema):
                            target = arm/stage; target.mkdir(parents=True, exist_ok=True)
                            (target/'input.md').write_text(prompt)
                            raise DryRun()
                        try: game.run(prepare)
                        except DryRun: pass
                        arm_meta['status'] = 'dry_run_not_executed'
                    else:
                        artifacts = game.run(live)
                        for name, value in artifacts.items(): write_json(arm/name, value)
                        results[mode] = artifacts['outcome.json']
                        arm_meta['status'] = 'completed'
                except Exception as error:
                    arm_meta['status'] = 'failed'
                    failure = str(error)
                    try: adapter.screen(failure)
                    except ValueError: failure = type(error).__name__+'; inspect ignored private logs'
                    arm_meta['failure'] = failure
                    print('Arm failed: '+failure, flush=True)
                finally:
                    write_json(arm/'manifest.json', arm_meta)
            comparisons.append(compare(pair, results))
            write_json(out/summary_file, comparisons)
        meta['status'] = ('dry_run_not_executed' if args.dry_run else
                          ('completed' if all(c['status'] == 'completed' for c in comparisons) else 'partial_failure'))
    except BaseException:
        meta['status'] = 'interrupted'
        raise
    finally:
        meta['completed_at'] = datetime.now(timezone.utc).isoformat()
        meta['artifacts_sha256'] = {p.relative_to(out).as_posix(): sha(p.read_bytes()) for p in sorted(out.rglob('*'))
                                   if p.is_file() and p != out/'manifest.json' and not {'source', 'private'} & set(p.relative_to(out).parts)}
        write_json(out/'manifest.json', meta)
    print('Study status: '+meta['status'], flush=True)


class DryRun(Exception):
    pass


if __name__ == '__main__':
    main()
