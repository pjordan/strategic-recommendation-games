"""Build a descriptive report from a verified finished paired study, offline."""
import argparse
import hashlib
import importlib.util
import json
import os
import shlex
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
spec = importlib.util.spec_from_file_location('verifier', HERE/'verify_runs.py')
verifier = importlib.util.module_from_spec(spec); spec.loader.exec_module(verifier)


def read(path): return json.loads(path.read_text())
def clean(text): return str(text).replace('|', '\\|').replace('\n', ' ')
def money(cents): return ('$' if cents >= 0 else '-$')+f'{abs(cents)/100:,.2f}'


def summarize(directory, output):
    output = output.resolve()
    checked = verifier.verify(directory)
    if checked['status'] not in ('completed', 'partial_failure'):
        raise ValueError('Study is not finished')
    meta = read(directory/'manifest.json')
    rows = read(directory/'comparisons.json')
    complete = [r for r in rows if r['status'] == 'completed']
    summary = {'run_id': meta['run_id'], 'verification': checked,
               'purchase_changed_pairs': sum(r['purchase_changed'] for r in complete),
               'ordered_lists_changed_pairs': sum(r['ordered_lists_changed'] for r in complete),
               'paired_spending_differences_cents': {r['pair_id']: r['text_minus_list']['purchase_value_cents'] for r in complete},
               'study_manifest_sha256': hashlib.sha256((directory/'manifest.json').read_bytes()).hexdigest(),
               'comparisons_sha256': hashlib.sha256((directory/'comparisons.json').read_bytes()).hexdigest(),
               'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    communication = {}
    for row in complete:
        arms = {}
        for mode in ('text-enabled', 'list-only'):
            transcript = read(directory/row['pair_id']/mode/'transcript.json')
            arms[mode] = {i: [{k: item[k] for k in ('recipient', 'content')} for item in transcript
                              if item['role'] == 'buyer' and item.get('round') == i]
                          for i in (1, 2)}
        communication[row['pair_id']] = {str(i): arms['text-enabled'][i] != arms['list-only'][i]
                                         for i in (1, 2) if arms['text-enabled'][i] or arms['list-only'][i]}
    summary['buyer_messages_changed_by_round'] = communication
    rel = Path(os.path.relpath(directory, output.parent)).as_posix()
    command_directory = shlex.quote(Path(os.path.relpath(directory, REPO)).as_posix())
    design_link = Path(os.path.relpath(HERE/'README.md', output.parent)).as_posix()
    lines = ['# Recommender text: paired whole-game pilot', '',
             f"Study: [{meta['run_id']}]({rel}/manifest.json). Profile: **{meta['harness_version']} / {meta['model_requested']} / {meta['reasoning_effort_requested']}** requested effort. Scenario {meta['scenario_version']}; frozen facts {meta['facts_version']}.", '',
             f"**{len(complete)} of {len(rows)} pairs completed.** Among completed pairs, the purchased outcome changed in **{summary['purchase_changed_pairs']}**, and the ordered recommendation lists changed in **{summary['ordered_lists_changed_pairs']}**.", '',
             'Each arm reran the whole game with its communication policy known to every agent. Product selection, disclosure and follow-ups could adapt. Paired spending differences below are **text-enabled minus list-only**; more spending is not automatically better satisfaction.', '',
             '| Paired condition | Text-enabled purchase | List-only purchase | Spending difference | Unique returned records (text/list) | Ordered lists changed |',
             '|---|---:|---:|---:|---:|---|']
    for row in rows:
        values = [money(row['arms'][m]['purchase_value_cents']) if m in row['arms'] else 'Incomplete' for m in ('text-enabled', 'list-only')]
        diff = money(row['text_minus_list']['purchase_value_cents']) if row['status'] == 'completed' else '—'
        changed = str(row.get('ordered_lists_changed', '—'))
        counts = '/'.join(str(row['arms'][m]['unique_returned_count']) if m in row['arms'] else '—' for m in ('text-enabled', 'list-only'))
        lines.append('| '+clean(row['pair_id'])+' | '+' | '.join(values)+' | '+diff+' | '+counts+' | '+changed+' |')
    lines += ['', '## Choices and recorded reasons', '']
    catalog = {r['record_id']: r for p in ('bing', 'google') for r in read(REPO/'scenarios/scenario-1/versions/1.3.0/recommendations'/f'{p}.json')['records']}
    for row in rows:
        lines += ['### '+row['pair_id'], '', 'Arm execution order: '+', then '.join(row['arm_order'])+'. Provider order: '+row['display_order']+'.', '']
        if row['pair_id'] in communication:
            lines += ['Buyer-addressed messages changed: '+', '.join('round '+i+' '+('yes' if changed else 'no') for i, changed in communication[row['pair_id']].items())+'.', '']
        for mode in ('text-enabled', 'list-only'):
            arm = directory/row['pair_id']/mode
            link = f"{rel}/{row['pair_id']}/{mode}"
            if mode not in row['arms']:
                lines += [f"**{mode}: incomplete.** See [arm status]({link}/manifest.json).", '']
                continue
            outcome = read(arm/'outcome.json')
            lines += [f"**{mode}: {outcome['buyer_action']}, {money(outcome['purchase_value_cents'])}.** [Outcome]({link}/outcome.json); [selected interaction]({link}/transcript.json).", '']
            for rid in outcome['purchased_record_ids']:
                card = catalog[rid]
                lines += ['- '+clean(card['title'] if 'title' in card else card.get('name', rid))+' — '+money(card['displayed_price_cents'])+' (`'+rid+'`).']
            if outcome['purchased_record_ids']: lines.append('')
            lines += ['Attributed revenue: '+', '.join(p+' '+money(v) for p, v in outcome['provider_revenue_cents'].items())+'.', '',
                      'Buyer’s recorded reason: '+clean(outcome['buyer_reason']), '']
            for i, choices in enumerate(outcome['recommender_choices']):
                for provider, choice in choices.items():
                    lines += [f"- Round {i+1}, {provider}: selected `{choice['candidate_id']}`, returned {len(choice['ordered_record_ids'])} records. "+clean(choice['strategic_justification'])]
            lines.append('')
    lines += ['## Interpretation and limits', '',
              'This is one pair per strategic condition, with independent model samples. Changes can reflect both the communication policy and sampling variation. No significance, calibrated treatment-effect estimate, equilibrium or general ranking of policies is established. The heterogeneous conditions are not interchangeable statistical replicates.', '',
              'The treatment removes a channel for factual information as well as persuasion: both arms give recommenders identical own-product facts, while buyers receive only returned cards and permitted commentary. Buyer-written context remains allowed. Text can therefore change which products are offered and how buyer follow-ups develop, not just the final response to a fixed list.', '',
              'Both competitive providers switch policy together; this does not isolate one provider’s marginal text contribution. Frozen card titles and descriptions remain visible in both arms.', '',
              'Message-change flags compare exact selected addressed content, including forwarded cards. Wording changes can be paraphrases rather than substantive changes in disclosure strategy.', '',
              'The reported reasons are agents’ explanations of their selected actions, not independent evidence that text caused a choice or improved satisfaction. Purchase value and within-run candidate ranks are not numeric user utility. Incomplete pairs are retained and excluded from completed-pair differences; no failed attempt is silently replaced.', '',
              'Historical analyses used different data and role templates, so their outcomes are not controls for this intervention. The appropriate comparison is between the two freshly generated arms of each pair.', '',
              '## Reproduce', '', '```bash',
              'python3 analyses/scenario-1/recommender-text/verify_runs.py '+command_directory,
              'python3 analyses/scenario-1/recommender-text/summarize.py '+command_directory, '```', '',
              'See [study design and fresh-run command]('+design_link+') for the exact pairing, prompt templates, information boundaries and execution settings.', '']
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text('\n'.join(lines))
    output.with_suffix('.json').write_text(json.dumps(summary, indent=2)+'\n')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--output', type=Path, default=HERE/'results.md')
    args = parser.parse_args()
    print(json.dumps(summarize(args.directory.resolve(), args.output), indent=2))
