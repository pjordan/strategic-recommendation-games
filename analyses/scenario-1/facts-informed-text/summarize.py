"""Describe a verified facts-consideration rerun and its historical text reference."""
import argparse
import hashlib
import importlib.util
import json
import os
import re
import shlex
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
spec = importlib.util.spec_from_file_location('facts_verifier', HERE/'verify_runs.py')
verifier = importlib.util.module_from_spec(spec); spec.loader.exec_module(verifier)


def read(path): return json.loads(path.read_text())
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def money(cents): return ('$' if cents >= 0 else '-$')+f'{abs(cents)/100:,.2f}'
def clean(value): return str(value).replace('|', '\\|').replace('\n', ' ')
def relative(path, base): return Path(os.path.relpath(path, base)).as_posix()
def actor_payload(path): return json.loads(path.read_text().split('\n## Your information\n\n', 1)[1])


def summarize(directory, output, reference):
    checked = verifier.verify(directory)
    reference_checked = verifier.archive.verify(reference)
    if checked['status'] not in ('completed', 'partial_failure'):
        raise ValueError('Rerun is not finished')
    meta, previous = read(directory/'manifest.json'), read(reference/'manifest.json')
    cases = read(directory/'outcomes.json')
    previous_cases = {c['pair_id']: c for c in previous['pairs']}
    all_cards = {r['record_id']: r for provider in ('bing', 'google') for r in read(REPO/'scenarios/scenario-1/versions/1.3.0/recommendations'/f'{provider}.json')['records']}
    summary = {'run_id': meta['run_id'], 'verification': checked, 'reference_run_id': previous['run_id'],
               'reference_verification': reference_checked, 'comparison_status': 'historical descriptive comparison; both studies had product facts',
               'profile_matches_reference': all(meta[k] == previous[k] for k in ('harness', 'harness_version', 'model_requested', 'reasoning_effort_requested')),
               'data_matches_reference': meta['data_manifest_sha256'] == previous['data_manifest_sha256'],
               'study_manifest_sha256': digest(directory/'manifest.json'), 'reference_manifest_sha256': digest(reference/'manifest.json'),
               'generator_sha256': digest(Path(__file__)), 'cases': []}
    lines = ['# Explicit product-fact consideration: observed rerun', '',
             f"Profile: **{meta['harness_version']} / {meta['model_requested']} / {meta['reasoning_effort_requested']}** requested effort. Scenario {meta['scenario_version']}; frozen facts {meta['facts_version']}. {checked['completed_cases']} of {checked['cases']} cases completed.", '',
             'The previous text-enabled games already received the same own-provider facts. This rerun adds an explicit instruction to examine and consider using them before choosing recommendations. It is a new sample under a revised recommender prompt, not an access-versus-no-access or paired causal experiment.', '',
             '| Condition | Previous text purchase | Explicit-facts rerun | Spending difference | Returned records (previous/new) | Offer changed |',
             '|---|---:|---:|---:|---:|---|']
    lines.insert(5, ('The requested execution profile and frozen data manifests match the historical reference.' if summary['profile_matches_reference'] and summary['data_matches_reference'] else 'Execution profile or frozen data differ from the reference; the comparison includes those differences.'))
    lines.insert(6, '')
    details = []
    for case in cases:
        cid = case['case_id']
        arm = directory/cid/'text-enabled'
        prior_arm = reference/cid/'text-enabled'
        row = {'case_id': cid, 'status': case['status']}
        if case['status'] != 'completed':
            lines.append('| '+cid+' | — | Incomplete | — | — | — |')
            summary['cases'].append(row)
            continue
        result = read(arm/'outcome.json')
        old = read(prior_arm/'outcome.json') if cid in previous_cases and read(prior_arm/'manifest.json')['status'] == 'completed' else None
        row['outcome'] = case['outcome']
        if old:
            returned_ids = {rid for choices in result['recommender_choices'] for choice in choices.values() for rid in choice['ordered_record_ids']}
            row.update(previous_purchase_value_cents=old['purchase_value_cents'], previous_purchased_record_ids=old['purchased_record_ids'],
                       previous_purchased_records_not_returned=sorted(set(old['purchased_record_ids'])-returned_ids),
                       spending_difference_cents=result['purchase_value_cents']-old['purchase_value_cents'],
                       purchase_changed=(result['buyer_action'], sorted(result['purchased_record_ids'])) != (old['buyer_action'], sorted(old['purchased_record_ids'])),
                       ordered_lists_changed=[[c[p]['ordered_record_ids'] for p in case['providers']] for c in result['recommender_choices']] != [[c[p]['ordered_record_ids'] for p in case['providers']] for c in old['recommender_choices']])
        lines.append('| '+cid+' | '+(money(old['purchase_value_cents']) if old else '—')+' | '+money(result['purchase_value_cents'])+' | '+(money(row['spending_difference_cents']) if old else '—')+' | '+(str(old['unique_returned_count']) if old else '—')+'/'+str(result['unique_returned_count'])+' | '+str(row.get('purchase_changed', '—'))+' |')
        row['fact_input_checks'] = []
        details += ['## '+cid, '',
                    f"**{result['buyer_action']}: {money(result['purchase_value_cents'])}.** [Outcome]({relative(arm/'outcome.json', output.parent)}); [selected interaction]({relative(arm/'transcript.json', output.parent)}).", '']
        for rid in result['purchased_record_ids']:
            card = all_cards[rid]
            details.append('- '+clean(card['title'])+' — '+money(card['displayed_price_cents'])+' (`'+rid+'`).')
        details += ['', 'Revenue attribution: '+', '.join(p+' '+money(v) for p, v in result['provider_revenue_cents'].items())+'.', '',
                    'Buyer’s recorded reason: '+clean(result['buyer_reason']), '']
        if row.get('previous_purchased_records_not_returned'):
            details += ['The previously purchased offer(s) were not returned in this rerun: '+', '.join('`'+rid+'`' for rid in row['previous_purchased_records_not_returned'])+'. The changed purchase therefore does not establish a buyer ranking reversal between the same available offers.', '']
        for i, choices in enumerate(result['recommender_choices'], 1):
            for provider, choice in choices.items():
                stage = Path('round-'+str(i))/provider
                payload = actor_payload(arm/stage/'input.md')
                facts = payload['own_frozen_product_facts']
                before = actor_payload(prior_arm/stage/'input.md')['own_frozen_product_facts'] if old else None
                own_sources = {e['source_id'] for f in facts for claim in f['facts'] for e in claim['evidence']}
                emitted = choice['strategic_justification']+'\n'+choice['message']
                cited = sorted(set(re.findall(r'src-[0-9a-f]+', emitted)))
                check = {'round': i, 'provider': provider, 'fact_records_supplied': len(facts),
                         'fact_projection_matches_reference': facts == before if before is not None else None,
                         'source_ids_in_selected_message_or_justification': cited,
                         'cited_source_ids_found_in_own_fact_input': [s for s in cited if s in own_sources]}
                row['fact_input_checks'].append(check)
                details += [f"### Round {i}, {provider}", '',
                            f"Selected `{choice['candidate_id']}`, returning {len(choice['ordered_record_ids'])} records. [Full recommender output]({relative(arm/stage/'output.json', output.parent)}).", '',
                            'Recorded evidence and strategy: '+clean(choice['strategic_justification']), '']
        summary['cases'].append(row)
    completed = [r for r in summary['cases'] if r['status'] == 'completed']
    matched = [r for r in completed if 'purchase_changed' in r]
    summary.update(comparable_completed_cases=len(matched), purchase_changed_cases=sum(r['purchase_changed'] for r in matched),
                   ordered_lists_changed_cases=sum(r['ordered_lists_changed'] for r in matched),
                   all_comparable_fact_inputs_identical=all(check['fact_projection_matches_reference'] for r in matched for check in r['fact_input_checks']))
    lines += ['', f"Among {len(matched)} cases with completed historical references, {summary['purchase_changed_cases']} purchased outcomes and {summary['ordered_lists_changed_cases']} ordered recommendation lists changed. The report compares exact offer IDs, including seller/variant differences, not just product-family labels.", '',
              '## Verification and interpretation', '',
              'Every recommender-stage fact projection is compared with the corresponding historical text-enabled input. Source-ID matching in the machine-readable audit establishes only that a referenced source identifier was supplied; it does not independently verify the claim, its interpretation or a causal effect on choice. Fact use can also be described without source-ID strings. The quoted candidate justifications and complete selected messages allow direct inspection.', '',
              'The initial buyer-planning prompt is unchanged and does not announce the extra recommender instruction, so differences in initial disclosure also reflect fresh sampling. Later follow-ups and purchases can respond to the newly generated recommendations. The additional instruction also asks for more explicit reporting of evidence in existing justifications. Differences in those reports do not by themselves demonstrate changed underlying reasoning. No control run without facts is included, and spending or ordinal ranks are not numerical user utility.', '',
              f"[Study manifest]({relative(directory/'manifest.json', output.parent)}); [reference manifest]({relative(reference/'manifest.json', output.parent)}); [prompt change and fresh-run command]({relative(HERE/'README.md', output.parent)}).", '', *details,
              '## Reproduce this report', '', '```bash',
              'python3 analyses/scenario-1/facts-informed-text/summarize.py '+shlex.quote(relative(directory, REPO))+' --reference '+shlex.quote(relative(reference, REPO)), '```', '']
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text('\n'.join(lines))
    output.with_suffix('.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False)+'\n')
    return {k: v for k, v in summary.items() if k != 'cases'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--reference', type=Path, default=HERE.parent/'recommender-text/runs/codex-astra-medium-pilot-001')
    parser.add_argument('--output', type=Path, default=HERE/'results.md')
    args = parser.parse_args()
    print(json.dumps(summarize(args.directory.resolve(), args.output.resolve(), args.reference.resolve()), indent=2))
