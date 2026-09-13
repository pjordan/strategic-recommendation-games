"""Compare verified strategic-learning prompt runs with the explicit-facts reference."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


def read(path): return json.loads(path.read_text())
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def money(cents): return ('$' if cents >= 0 else '-$')+f'{abs(cents)/100:,.2f}'
def relative(path, base): return Path(os.path.relpath(path, base)).as_posix()
def clean(value): return str(value).replace('|', '\\|').replace('\n', ' ')
def payload(path): return json.loads(path.read_text().split('\n## Your information\n\n', 1)[1])
def returned(outcome): return {rid for choices in outcome['recommender_choices'] for choice in choices.values() for rid in choice['ordered_record_ids']}
def lists(outcome): return [{p: c['ordered_record_ids'] for p, c in choices.items()} for choices in outcome['recommender_choices']]


def summarize(directory, reference, output):
    current_verifier = module('learning_verifier', HERE/'verify_runs.py')
    old_verifier = module('facts_reference_verifier', HERE.parent/'facts-informed-text/verify_runs.py')
    checked, old_checked = current_verifier.verify(directory), old_verifier.verify(reference)
    if checked['status'] not in ('completed', 'partial_failure'):
        raise ValueError('Study is not finished')
    meta, old_meta = read(directory/'manifest.json'), read(reference/'manifest.json')
    cards = {r['record_id']: r for p in ('bing', 'google') for r in read(REPO/'scenarios/scenario-1/versions/1.3.0/recommendations'/f'{p}.json')['records']}
    summary = {'run_id': meta['run_id'], 'reference_run_id': old_meta['run_id'],
               'verification': checked, 'reference_verification': old_checked,
               'study_manifest_sha256': digest(directory/'manifest.json'),
               'reference_manifest_sha256': digest(reference/'manifest.json'),
               'generator_sha256': digest(Path(__file__)),
               'comparison_status': 'Historical descriptive comparison; combined prompt treatment plus fresh sampling, not measured regret or a causal effect.',
               'profile_matches_reference': all(meta[k] == old_meta[k] for k in ('harness', 'harness_version', 'model_requested', 'reasoning_effort_requested')),
               'data_matches_reference': meta['data_manifest_sha256'] == old_meta['data_manifest_sha256'], 'cases': []}
    lines = ['# Strategic-learning inspired prompts: observed pilot', '',
             f"Requested profile: **{meta['harness_version']} / {meta['model_requested']} / {meta['reasoning_effort_requested']}**. Scenario {meta['scenario_version']}; facts {meta['facts_version']}. {checked['completed_cases']} of {checked['cases']} games completed.", '',
             'The new recommender instruction asks for preference inference, a no-regret perspective on candidate opportunity costs, and fictitious-play inspired reasoning about a mixture of opposing behavior. Both studies already explicitly asked recommenders to consider the same product facts. This is a fresh single-arm pilot compared with the historical explicit-facts sample; no regret, equilibrium or causal effect is measured.', '',
             '| Condition | Prior explicit-facts spend | New spend | Difference | Distinct returned cards (prior/new) | Purchase changed |',
             '|---|---:|---:|---:|---:|---|']
    details = []
    for case in read(directory/'outcomes.json'):
        cid = case['case_id']; arm = directory/cid/'text-enabled'; prior_arm = reference/cid/'text-enabled'
        row = {'case_id': cid, 'status': case['status']}
        if case['status'] != 'completed':
            lines.append(f'| {cid} | — | Incomplete | — | — | — |')
            summary['cases'].append(row); continue
        outcome = read(arm/'outcome.json')
        before = read(prior_arm/'outcome.json') if (prior_arm/'outcome.json').exists() and read(prior_arm/'manifest.json')['status'] == 'completed' else None
        row['outcome'] = case['outcome']; row['recommender_decisions'] = []
        if before:
            row.update(previous_outcome={k: before[k] for k in case['outcome']},
                       spending_difference_cents=outcome['purchase_value_cents']-before['purchase_value_cents'],
                       purchase_changed=(outcome['buyer_action'], sorted(outcome['purchased_record_ids'])) != (before['buyer_action'], sorted(before['purchased_record_ids'])),
                       ordered_lists_changed=lists(outcome) != lists(before),
                       previous_purchased_records_not_returned=sorted(set(before['purchased_record_ids'])-returned(outcome)))
        lines.append('| '+cid+' | '+(money(before['purchase_value_cents']) if before else '—')+' | '+money(outcome['purchase_value_cents'])+' | '+(money(row['spending_difference_cents']) if before else '—')+' | '+(str(before['unique_returned_count']) if before else '—')+'/'+str(outcome['unique_returned_count'])+' | '+str(row.get('purchase_changed', '—'))+' |')
        details += ['## '+cid, '', f"**{outcome['buyer_action']}: {money(outcome['purchase_value_cents'])}.** [Outcome]({relative(arm/'outcome.json', output.parent)}); [selected interaction]({relative(arm/'transcript.json', output.parent)}).", '']
        for rid in outcome['purchased_record_ids']:
            details.append('- '+clean(cards[rid]['title'])+' — '+money(cards[rid]['displayed_price_cents'])+' (`'+rid+'`).')
        details += ['', 'Buyer’s recorded reason: '+clean(outcome['buyer_reason']), '',
                    'Realized provider revenue: '+', '.join(p+' '+money(v) for p,v in outcome['provider_revenue_cents'].items())+'.', '']
        if row.get('previous_purchased_records_not_returned'):
            details += ['Previously purchased offers absent from the new returned set: '+', '.join('`'+rid+'`' for rid in row['previous_purchased_records_not_returned'])+'. This is not a direct ranking reversal between the same available offers.', '']
        for i, choices in enumerate(outcome['recommender_choices'], 1):
            for provider, choice in choices.items():
                stage = Path('round-'+str(i))/provider
                actor = read(arm/stage/'output.json')
                info = payload(arm/stage/'input.md')
                old_info = payload(prior_arm/stage/'input.md') if before else None
                audit = {'round': i, 'provider': provider, 'candidate_count': len(actor['candidates']),
                         'selected_candidate': choice, 'buyer_belief': actor['buyer_belief'], 'selection_reason': actor['selection_reason'],
                         'fact_input_matches_reference': info['own_frozen_product_facts'] == old_info['own_frozen_product_facts'] if old_info else None,
                         'catalog_input_matches_reference': info['own_catalog'] == old_info['own_catalog'] if old_info else None,
                         'realized_own_revenue_cents': outcome['provider_revenue_cents'][provider]}
                row['recommender_decisions'].append(audit)
                details += [f'### Round {i}, {provider}', '',
                            f"Selected `{choice['candidate_id']}` from {len(actor['candidates'])} candidates; returned {len(choice['ordered_record_ids'])} cards. [Full output]({relative(arm/stage/'output.json', output.parent)}).", '',
                            'Recorded buyer belief: '+clean(actor['buyer_belief']), '',
                            'Selected candidate justification: '+clean(choice['strategic_justification']), '',
                            'Selection reason: '+clean(actor['selection_reason']), '',
                            'Forecast own revenue: '+money(choice['predicted_own_revenue_cents'])+'; final realized own revenue: '+money(outcome['provider_revenue_cents'][provider])+'. This forecast comparison is not a regret calculation; second-round choices can intervene after a first-round forecast.', '']
        summary['cases'].append(row)
    matched = [r for r in summary['cases'] if 'purchase_changed' in r]
    summary.update(comparable_completed_cases=len(matched), purchase_changed_cases=sum(r['purchase_changed'] for r in matched),
                   ordered_lists_changed_cases=sum(r['ordered_lists_changed'] for r in matched),
                   all_comparable_fact_inputs_identical=all(d['fact_input_matches_reference'] for r in matched for d in r['recommender_decisions']),
                   all_comparable_catalog_inputs_identical=all(d['catalog_input_matches_reference'] for r in matched for d in r['recommender_decisions']))
    lines += ['', f"Across {len(matched)} completed comparable cases, {summary['purchase_changed_cases']} purchases and {summary['ordered_lists_changed_cases']} ordered recommendation lists changed.", '',
              '## Reading this comparison', '',
              'Catalog/fact input equality and the requested profile are checked in the machine-readable report. Agent beliefs and justifications below are recorded explanations, not independently verified mechanisms or executed counterfactuals. Unchanged initial buyer prompts can still generate different disclosures because each full game is resampled. Revealed preferences, returned lists, messages and final decisions may all vary. Spending and ordinal ranks are not cardinal satisfaction.', '',
              'There is no cross-run learning, observed opponent-frequency update, empirical payoff matrix or computed regret. This combined wording treatment cannot isolate its components or distinguish a prompt effect from sampling with one run per condition. The theory and protocol are documented in the [study README](README.md).', '',
              f"[Study manifest]({relative(directory/'manifest.json', output.parent)}); [reference manifest]({relative(reference/'manifest.json', output.parent)}).", '', *details,
              '## Reproduce this report', '', '```bash',
              'python3 analyses/scenario-1/strategic-learning-text/summarize.py '+relative(directory, REPO), '```', '']
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text('\n'.join(lines)); output.with_suffix('.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
    return {k:v for k,v in summary.items() if k != 'cases'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--reference', type=Path, default=HERE.parent/'facts-informed-text/runs/codex-astra-medium-pilot-001')
    parser.add_argument('--output', type=Path, default=HERE/'results.md')
    args = parser.parse_args()
    print(json.dumps(summarize(args.directory.resolve(), args.reference.resolve(), args.output.resolve()),indent=2))
