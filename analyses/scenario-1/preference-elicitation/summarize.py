"""Build a descriptive, verified comparison and selected dialogue report."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def read(path): return json.loads(path.read_text())
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def money(cents): return f'${cents/100:,.2f}'
def link(path, base): return Path(os.path.relpath(path, base)).as_posix()
def selected(output): return next(c for c in output['candidates'] if c['candidate_id'] == output['selected_candidate_id'])


def verify(path, analysis):
    spec = importlib.util.spec_from_file_location('report_verifier', HERE.parent/analysis/'verify_runs.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module.verify(path)


def summarize(directory, reference, output):
    checks = {'current': verify(directory, 'preference-elicitation'),
              'reference': verify(reference, 'strategic-learning-text')}
    if checks['current']['status'] != 'completed':
        raise ValueError('A complete study is required for this report')
    meta, before_meta = read(directory/'manifest.json'), read(reference/'manifest.json')
    report = {'verification': checks, 'run_manifest_sha256': digest(directory/'manifest.json'),
              'reference_manifest_sha256': digest(reference/'manifest.json'), 'generator_sha256': digest(Path(__file__)),
              'profile_matches_reference': all(meta[k] == before_meta[k] for k in ('harness', 'harness_version', 'model_requested', 'reasoning_effort_requested')),
              'data_matches_reference': meta['data_manifest_sha256'] == before_meta['data_manifest_sha256'],
              'comparison_status': 'Historical descriptive comparison of a combined protocol treatment and fresh model draws; no causal effect or equilibrium established.', 'cases': []}
    lines = ['# Sales discovery: observed pilot', '',
             f"Profile: **{meta['harness_version']} / {meta['model_requested']} / {meta['reasoning_effort_requested']}**. Scenario {meta['scenario_version']}; facts {meta['facts_version']}.", '',
             'The new protocol asks recommenders to elicit preferences before tailoring final offers. Buyer answers come from the unchanged hidden brief; unanswered or unspecified preferences must not be invented. Both providers retain their sales revenue objective.', '']
    for case in read(directory/'outcomes.json'):
        cid = case['case_id']; arm = directory/cid/'text-enabled'
        prior = reference/cid/'text-enabled'
        current = read(arm/'outcome.json')
        before = read(prior/'outcome.json') if (prior/'outcome.json').exists() else None
        history = read(arm/'responses.json')
        card_map = {r['record_id']:r for h in history for response in h['responses'] for r in response['records']}
        row = {'case_id': cid, 'outcome': current, 'selected_opening': selected(read(arm/'disclosure/output.json')),
               'selected_answers': selected(read(arm/'followup/output.json')),
               'first_round_count': sum(len(r['records']) for r in history[0]['responses']),
               'new_round_two_ids': sorted({r['record_id'] for s in history[1]['responses'] for r in s['records']}-{r['record_id'] for s in history[0]['responses'] for r in s['records']}),
               'responses': history}
        if before:
            row['historical_comparison'] = {'purchase_changed': current['purchased_record_ids'] != before['purchased_record_ids'] or current['buyer_action'] != before['buyer_action'],
                'spending_difference_cents': current['purchase_value_cents']-before['purchase_value_cents'],
                'previous_purchase_value_cents': before['purchase_value_cents'], 'previous_purchased_record_ids': before['purchased_record_ids'],
                'previous_distinct_returned_count': before['unique_returned_count'],
                'previous_purchase_missing_from_new_offers': sorted(set(before['purchased_record_ids'])-set(card_map))}
        report['cases'].append(row)
        lines += ['## '+cid, '', f"**{current['buyer_action'].capitalize()}: {money(current['purchase_value_cents'])}.**", '']
        for rid in current['purchased_record_ids']:
            lines += ['- '+card_map[rid]['title']+' (`'+rid+'`).']
        lines += ['', current['buyer_reason'], '', 'Realized provider revenue: '+', '.join(p+' '+money(v) for p,v in current['provider_revenue_cents'].items())+'.', '',
                  f"Returned {row['first_round_count']} cards in round 1, {len(row['new_round_two_ids'])} new cards in round 2, and {current['unique_returned_count']} distinct cards overall.", '']
        if before:
            lines += [f"Historical two-round strategic-learning pilot: {money(before['purchase_value_cents'])}, {before['unique_returned_count']} distinct cards. Purchase changed: {row['historical_comparison']['purchase_changed']}. Spending difference: {current['purchase_value_cents']-before['purchase_value_cents']} cents.", '']
            if row['historical_comparison']['previous_purchase_missing_from_new_offers']:
                lines += ['The previous purchased offer is absent from the new returned set. This is not a direct preference reversal between identical available options.', '']
        lines += [f"[Full selected interaction]({link(arm/'transcript.json', output.parent)}); [exact inputs and outputs]({link(arm, output.parent)}).", '']
        for provider in ('bing', 'google'):
            lines += ['### '+provider.capitalize(), '', 'Buyer opening:', '', row['selected_opening']['messages'][provider], '', 'Round-1 selected discovery message:', '', current['recommender_choices'][0][provider]['message'], '',
                      'Buyer addressed answer:', '', row['selected_answers']['messages'][provider], '']
            for i in (1, 2):
                choice = current['recommender_choices'][i-1][provider]
                actor = read(arm/f'round-{i}'/provider/'output.json')
                lines += [f"Round {i}: selected `{choice['candidate_id']}` from {len(actor['candidates'])} candidates; returned {len(choice['ordered_record_ids'])} cards; forecast own revenue {money(choice['predicted_own_revenue_cents'])}.", '',
                          'Recorded selection rationale: '+actor['selection_reason'], '', 'Recorded buyer belief: '+actor['buyer_belief'], '']
                if i == 2:
                    lines += ['Final ordered list:', '']
                    lines += ['- '+card_map[rid]['title']+' — '+money(card_map[rid]['displayed_price_cents'])+' (`'+rid+'`).' for rid in choice['ordered_record_ids']]
                    lines += ['', 'Final selected sales message:', '', choice['message'], '']
        lines += ['Buyer strategic assessment:', '', current['buyer_strategic_response'], '']
    lines += ['## Interpretation limits', '', 'These are recorded choices and agent-provided rationales, not independent proof of the mechanism. First-round forecasts are conditional eventual sales; second-round forecasts concern actually offered products. Neither is measured regret or realized revenue. This historical comparison changes discovery instructions, buyer opening/answer instructions and first-round forecast semantics together, and resamples all actors. One game cannot separate these effects or establish that discovery improves satisfaction. Price is not a satisfaction score.', '', 'See [pilot interpretation](pilot-notes.md) for the question/answer audit. Reproduce the report from the repository root:', '', '```bash', 'python3 analyses/scenario-1/preference-elicitation/summarize.py '+link(directory, REPO), '```', '']
    output.write_text('\n'.join(lines))
    output.with_suffix('.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    return {k:v for k,v in report.items() if k != 'cases'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--reference', type=Path, default=HERE.parent/'strategic-learning-text/runs/codex-astra-medium-pilot-001')
    parser.add_argument('--output', type=Path, default=HERE/'results.md')
    args = parser.parse_args()
    print(json.dumps(summarize(args.directory.resolve(), args.reference.resolve(), args.output.resolve()),indent=2))
