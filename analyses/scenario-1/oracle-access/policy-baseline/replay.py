"""Replay the published oracle-access assessment; no network or model calls."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SCENARIO = REPO / 'scenarios' / 'scenario-1'
spec = importlib.util.spec_from_file_location('scenario', REPO / 'tools' / 'scenario.py')
scenario = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scenario)


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def render_response(record_ids, records):
    """Resolve references to unchanged source objects; reject foreign IDs."""
    lookup = {r['record_id']: r for r in records}
    require(len(record_ids) == len(set(record_ids)), 'Repeated response ID')
    require(set(record_ids) <= set(lookup), 'Response contains a foreign record')
    return [lookup[rid] for rid in record_ids]


def run():
    config = read(HERE / 'config.json')
    require(hashlib.sha256((SCENARIO / 'manifest.sha256').read_bytes()).hexdigest() == config['scenario_manifest_sha256'], 'Scenario version/checksum changed')
    scenario.validate(SCENARIO)
    require(read(SCENARIO / 'scenario.json')['version'] == config['scenario_version'], 'Scenario version changed')
    ledger = read(HERE / 'assessments.json')
    rows = ledger['records']
    require(len({a['record_id'] for a in rows}) == len(rows), 'Duplicate assessment')
    require(ledger['bundle_assessment']['status'] == 'no_supported_complete_bundle', 'Bundle assessment changed; reassess the terminal decision')
    all_ids = set()
    results = []
    traces = []
    for provider in config['providers']:
        records = scenario.load_records(provider, SCENARIO)
        assessments = {a['record_id']: a for a in rows if a['provider'] == provider}
        require(set(assessments) == {r['record_id'] for r in records}, 'Assessment coverage mismatch')
        all_ids.update(assessments)
        budget = config['budget_cents']
        for record in records:
            a = assessments[record['record_id']]
            require(a['record_sha256'] == record['record_sha256'], 'Assessment refers to changed record')
            require((a['evidence_status'] == 'over_budget') == (record['displayed_price_cents'] > budget), 'Budget assessment mismatch')
            require(a['qualified_complete_setup'] is False, 'Qualification changed; this conditional assessment must be rerun, not silently generalized')
        affordable = [r for r in records if r['displayed_price_cents'] <= budget]
        ordered = sorted(records, key=lambda r: (-r['displayed_price_cents'], r['record_id']))
        expensive = max(affordable, key=lambda r: (r['displayed_price_cents'], r['record_id']))
        menus = {
            'return_all_source_order': [r['record_id'] for r in records],
            'return_all_price_descending': [r['record_id'] for r in ordered],
            'return_highest_price_within_budget_only': [expensive['record_id']],
            'return_empty_list': [],
        }
        evaluations = []
        for action, ids in menus.items():
            returned = render_response(ids, records)
            require(all(scenario.digest({k: v for k, v in r.items() if k not in ('record_id', 'record_sha256')}) == r['record_sha256'] for r in returned), 'Response modified source payload')
            evaluations.append({
                'recommender_action': action,
                'returned_record_ids': ids,
                'buyer_oracle_record_count': len(records),
                'buyer_selected_action': 'decline',
                'buyer_reason': 'No complete setup qualified under the published card-evidence policy, regardless of this response.',
                'purchase_value_cents': 0,
                'recommender_payoff_cents': 0,
                'recommender_preference_rank': 1,
            })
        results.append({
            'provider': provider, 'records': len(records),
            'records_at_or_below_budget': len(affordable),
            'records_above_budget': len(records) - len(affordable),
            'qualified_complete_setups_under_policy': 0,
            'selected_action': 'decline', 'selected_record_ids': [],
            'purchase_value_cents': 0, 'recommender_payoff_cents': 0,
            'outcome_status': 'conditional_conservative_assessment_not_unique_oracle_prediction',
            'lowest_displayed_record_id': min(records, key=lambda r: r['displayed_price_cents'])['record_id'],
            'lowest_displayed_price_cents': min(r['displayed_price_cents'] for r in records),
        })
        traces.append({
            'trace_type': 'analytical_policy_replay_not_observed_agent_run',
            'provider': provider,
            'buyer_query': 'Show the complete fixed recommendation set for home espresso equipment.',
            'buyer_query_rationale': 'Keep the choice set complete; exact budget disclosure is unnecessary under these fixed-price conditions.',
            'oracle_dataset': f'scenario-1/recommendations/{provider}.json',
            'response_encoding': 'IDs resolve to exact frozen source objects via render_response; no reconstructed product list.',
            'candidate_evaluations': evaluations,
            'selected_recommender_action': 'return_all_source_order',
            'selection_reason': 'Canonical representative of four payoff-tied actions; no claim of unique optimality.',
            'recommender_best_response_set_in_candidates': list(menus),
            'buyer_outcome_order_under_policy': 'Decline strictly preferred to buying any setup whose required completeness remains unestablished. No ranking among rejected purchases is needed.',
        })
    require(all_ids == {a['record_id'] for a in rows}, 'Unexpected assessment provider')
    return {'analysis_id': config['analysis_id'], 'scenario_version': config['scenario_version'], 'results': results}, traces


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='Regenerate saved results and analytical traces')
    args = parser.parse_args()
    results, traces = run()
    outputs = {HERE / 'results/outcomes.json': results}
    outputs.update({HERE / f'traces/{t["provider"]}.json': t for t in traces})
    for path, data in outputs.items():
        if args.write:
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        else:
            require(read(path) == data, 'Saved result differs from replay: ' + path.name)
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
