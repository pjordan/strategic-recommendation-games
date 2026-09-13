"""Extract report tables and provenance from saved traces; no model/network calls."""
import csv
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
BASE=REPO/'analyses/scenario-1'
SOURCES={}


def read(path):
    raw=path.read_bytes()
    SOURCES[path.relative_to(REPO).as_posix()]=hashlib.sha256(raw).hexdigest()
    return json.loads(raw)


def dollars(cents):
    return '' if cents is None else f'{cents/100:.2f}'


def save_csv(name,rows):
    with (HERE/name).open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)


CONDITIONS=[
    ('A','Oracle, combined catalog','oracle-access','codex-astra-medium-combined-satisfaction-001'),
    ('B1','Sole informed Bing recommender','informed-recommender','codex-astra-medium-bing-002'),
    ('B2','Sole informed Google recommender','informed-recommender','codex-astra-medium-google-002'),
    ('C','Competing informed recommenders','competing-recommenders','codex-astra-medium-bing-first-002'),
    ('D','Strategic disclosure, one round','strategic-disclosure','codex-astra-medium-bing-first-001'),
    ('E','Strategic disclosure, two rounds','two-round-strategic-disclosure','codex-astra-medium-bing-first-001'),
]


def main():
    import importlib.util
    spec=importlib.util.spec_from_file_location('scenario',REPO/'tools/scenario.py')
    scenario=importlib.util.module_from_spec(spec);spec.loader.exec_module(scenario)
    scenario.validate_version('1.2.0')
    for relative in ['scenarios/scenario-1/recommendations/bing.json', 'scenarios/scenario-1/recommendations/google.json',
                     'scenarios/scenario-1/manifest.sha256', 'scenarios/scenario-1/versions/1.2.0/private/user_preferences.md']:
        SOURCES[relative]=hashlib.sha256((REPO/relative).read_bytes()).hexdigest()
    # Load the same frozen records through the existing adapter.
    spec=importlib.util.spec_from_file_location('adapter',BASE/'oracle-access/run_model.py')
    adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
    catalog={r['record_id']:r for p in ('bing','google') for r in adapter.load_universe(p)}
    rows=[]
    for code,label,analysis,run in CONDITIONS:
        directory=BASE/analysis/'runs'/run
        m=read(directory/'manifest.json')
        assert m['status']=='completed' and m['scenario_version']=='1.2.0'
        assert m['harness_version']=='codex-cli 0.154.0' and m['model_requested']=='gpt-6-astra' and m['reasoning_effort_requested']=='medium'
        f=directory/('output.json' if code=='A' else 'outcome.json');o=read(f)
        ids=o['selected_record_ids'] if code=='A' else o['purchased_record_ids']
        value=o['realized_purchase_value_cents'] if code.startswith('B') else o['purchase_value_cents']
        assert sum(catalog[i]['displayed_price_cents'] for i in ids)==value<=80000
        bing=google=None
        if code=='A':
            visible=m['record_count'];appearances=visible;calls=1;rounds=0
        elif code.startswith('B'):
            visible=len(o['returned_record_ids']);appearances=visible;calls=2;rounds=1
            if o['provider']=='bing':bing=o['recommender_payoff_cents']
            else:google=o['recommender_payoff_cents']
        else:
            rs=read(directory/'responses.json');rs=rs if isinstance(rs,list) else [rs]
            appearances=sum(len(reply['records']) for rnd in rs for reply in rnd.values())
            visible=len({r['record_id'] for rnd in rs for reply in rnd.values() for r in reply['records']})
            bing=o['recommenders']['bing']['realized_own_revenue_cents']
            google=o['recommenders']['google']['realized_own_revenue_cents']
            assert bing+google==value
            calls={'C':3,'D':4,'E':7}[code];rounds=len(rs)
        rows.append({'condition':code,'description':label,'analysis':analysis,'run_id':run,
                     'scenario_version':m['scenario_version'],'harness_version':m['harness_version'],
                     'model_requested':m['model_requested'],'effort_requested':m['reasoning_effort_requested'],
                     'model_calls':calls,'recommendation_rounds':rounds,
                     'visible_distinct_record_ids':visible,'record_appearances':appearances,
                     'selected_record_ids':';'.join(ids),'selected_titles':';'.join(catalog[i]['title'] for i in ids),
                     'purchase_usd':dollars(value),'unused_budget_usd':dollars(80000-value),
                     'difference_from_oracle_usd':dollars(value-64995),
                     'bing_revenue_usd':dollars(bing),'google_revenue_usd':dollars(google),
                     'outcome_source':f.relative_to(REPO).as_posix()})
    save_csv('comparison.csv',rows)
    attempts=[]
    for analysis in ['oracle-access','informed-recommender','competing-recommenders','strategic-disclosure','two-round-strategic-disclosure']:
        for directory in sorted((BASE/analysis/'runs').iterdir()):
            if not (directory/'manifest.json').exists():continue
            m=read(directory/'manifest.json')
            output=directory/('output.json' if analysis=='oracle-access' else 'buyer/output.json')
            buyer=read(output) if output.exists() else {}
            attempts.append({'analysis':analysis,'run_id':directory.name,
                             'recorded_status':m['status'],'scenario_version_recorded':m.get('scenario_version',''),
                             'buyer_policy_recorded':m.get('buyer_policy',''),
                             'selected_action_if_output_exists':buyer.get('selected_action',''),
                             'selected_price_usd_if_output_exists':dollars(buyer.get('purchase_value_cents')),
                             'outcome_validated':m['status']=='completed',
                             'manifest_source':(directory/'manifest.json').relative_to(REPO).as_posix()})
    save_csv('attempts.csv',attempts)
    (HERE/'evidence.json').write_text(json.dumps({'scope':'Six successful satisfaction-condition traces plus complete attempt inventory for the five analysis directories.',
        'scenario_version':'1.2.0','source_sha256':dict(sorted(SOURCES.items())),
        'notes':['Blank revenue means no such strategic agent was run, not zero revenue.',
                 'A selected price in a failed run is an observed output, not a validated game outcome.',
                 'Differences are descriptive and do not estimate causal effects or user welfare.',
                 'Earlier scenario versions without explicit version fields remain blank in the inventory.']},indent=2)+'\n')
    print(f'Wrote {len(rows)} comparison rows, {len(attempts)} attempt rows and source hashes.')


if __name__=='__main__':main()
