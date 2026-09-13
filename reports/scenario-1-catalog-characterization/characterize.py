"""Describe frozen cards and selected-list coverage; no product truth adjudication."""
import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter,defaultdict
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
SOURCES={}


def read(relative):
    raw=(REPO/relative).read_bytes();SOURCES[relative]=hashlib.sha256(raw).hexdigest()
    return json.loads(raw)


def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFKD',text.lower()) if not unicodedata.combining(c))


# Text-based family examples, not a comprehensive taxonomy or product-ID deduplication.
FAMILIES=[
 ('Breville Barista Express Impress',r'barista express.*impress|bes876'),
 ('Breville Barista Express (other)',r'barista express|bes870'),
 ('Breville Barista Touch Impress',r'barista touch.*impress'),
 ('Breville Barista Touch (other)',r'barista touch|bes880'),
 ('Breville Bambino Plus',r'bambino plus'),
 ('Breville Bambino (other)',r'bambino|bes450'),
 ('Breville Oracle Jet',r'oracle jet|bes985'),
 ('Ninja Mini Plus',r'ninja.*mini.*plus'),
 ('Ninja Mini (other)',r'ninja.*mini'),
 ('Ninja Premier',r'ninja.*premier'),
 ('Ninja AutoBarista',r'ninja.*autobarista'),
 ('DeLonghi Magnifica Evo Next',r'magnifica evo next'),
 ('DeLonghi Magnifica Evo (other)',r'magnifica evo'),
 ('DeLonghi Magnifica Start',r'magnifica start'),
 ('DeLonghi Rivelia',r'rivelia'),
 ('DeLonghi La Specialista',r'la specialista'),
 ('Philips Baristina',r'baristina'),
 ('Philips Barista Brew',r'philips.*barista brew'),
 ('Philips 1200',r'philips.*1200'),
 ('Philips 3300',r'philips.*3300'),
 ('Philips 5500',r'philips.*5500'),
 ('Chefman Crema Supreme',r'chefman.*crema supreme'),
 ('Chefman Crema Deluxe',r'(chefman.*crema deluxe|crema deluxe double boiler)'),
 ('Nespresso',r'nespresso'),
]
GAMES=[('informed-recommender','codex-astra-medium-bing-002'),
       ('informed-recommender','codex-astra-medium-google-002'),
       ('competing-recommenders','codex-astra-medium-bing-first-002'),
       ('strategic-disclosure','codex-astra-medium-bing-first-001'),
       ('two-round-strategic-disclosure','codex-astra-medium-bing-first-001')]


def main():
    data={p:read(f'scenarios/scenario-1/recommendations/{p}.json') for p in ['bing','google']}
    records=[r for d in data.values() for r in d['records']]
    seen=set();coverage={}
    for analysis,run in GAMES:
        prefix=f'analyses/scenario-1/{analysis}/runs/{run}'
        assert read(prefix+'/manifest.json')['status']=='completed'
        payload=read(prefix+('/response.json' if analysis=='informed-recommender' else '/responses.json'))
        replies=[payload] if analysis=='informed-recommender' else [reply for rnd in (payload if isinstance(payload,list) else [payload]) for reply in rnd.values()]
        ids={r['record_id'] for reply in replies for r in reply['records']}
        coverage[analysis+'/'+run]=len(ids);seen.update(ids)
    examples=['google-c1ac723b3479e478c13f','google-ce916892b069dd413070',
              'google-e330ec1bb31d6723d074','google-e9bbae1b2b521a845cc4','google-bb29f03511fde44d2851']
    (HERE/'example-cards.json').write_text(json.dumps([r for r in records if r['record_id'] in examples],indent=2,ensure_ascii=False)+'\n')
    rows=[]
    families=defaultdict(list)
    for r in records:
        text=normalize(' '.join([r['title'],*r['image_alt_text']]))
        family=next((name for name,pattern in FAMILIES if re.search(pattern,text)),'unclassified by example rules')
        families[family].append(r)
        price=r['displayed_price_cents']
        rows.append({'record_id':r['record_id'],'provider':r['provider'],'title':r['title'],
                     'price_usd':f'{price/100:.2f}','merchant_display_text':r['merchant_display_text'],
                     'ever_returned_in_five_validated_games':r['record_id'] in seen,
                     'within_800_record_price':price<=80000,'example_family':family,
                     'grinding_or_bean_to_cup_text':bool(re.search(r'grind|bean.to.cup',text)),
                     'milk_froth_or_steam_text':bool(re.search(r'milk|froth|steam',text)),
                     'pressure_marketing_15_or_20_bar':bool(re.search(r'(?:15|20)[\s-]*bar',text)),
                     'title_truncated_flag':r['title_truncated'],'merchant_aggregate_flag':r['merchant_text_is_aggregate'],
                     'numeric_only_merchant_field':bool(re.fullmatch(r'[\d,.]+',r['merchant_display_text'])),
                     'alibaba_merchant_text':'alibaba' in r['merchant_display_text'].lower(),
                     'sponsored':r['sponsored']})
    def write_csv(name,values):
        with (HERE/name).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(values[0]),lineterminator='\n');w.writeheader();w.writerows(values)
    write_csv('records.csv',rows)
    stats={'records':len(rows),'captured_occurrences':sum(len(d['occurrences']) for d in data.values()),
           'exact_title_count':len({r['title'] for r in records}),
           'normalized_title_count':len({re.sub(r'\W+','',normalize(r['title'])) for r in records}),
           'selected_list_coverage':coverage,'ever_returned':len(seen),'never_returned':len(rows)-len(seen),
           'returned_within_budget':sum(r['ever_returned_in_five_validated_games'] and r['within_800_record_price'] for r in rows),
           'never_returned_within_budget':sum(not r['ever_returned_in_five_validated_games'] and r['within_800_record_price'] for r in rows),
           'over_budget':sum(not r['within_800_record_price'] for r in rows),
           'price_bands':dict(Counter('below_100' if r['displayed_price_cents']<10000 else '100_to_below_300' if r['displayed_price_cents']<30000 else '300_to_below_500' if r['displayed_price_cents']<50000 else '500_to_800' if r['displayed_price_cents']<=80000 else 'above_800' for r in records)),
           'flags':{k:sum(r[k] for r in rows) for k in list(rows[0])[8:]},
           'both_function_text':sum(r['grinding_or_bean_to_cup_text'] and r['milk_froth_or_steam_text'] for r in rows),
           'never_returned_within_budget_both_function_text':sum(not r['ever_returned_in_five_validated_games'] and r['within_800_record_price'] and r['grinding_or_bean_to_cup_text'] and r['milk_froth_or_steam_text'] for r in rows)}
    groups=[{'example_family':family,'records':len(rs),'minimum_card_price_usd':f"{min(r['displayed_price_cents'] for r in rs)/100:.2f}",
             'maximum_card_price_usd':f"{max(r['displayed_price_cents'] for r in rs)/100:.2f}",
             'ever_returned':sum(r['record_id'] in seen for r in rs),'record_ids':';'.join(r['record_id'] for r in rs)} for family,rs in families.items()]
    write_csv('family-examples.csv',sorted(groups,key=lambda x:(-x['records'],x['example_family'])))
    (HERE/'summary.json').write_text(json.dumps(stats,indent=2)+'\n')
    (HERE/'sources.json').write_text(json.dumps({'scope':'Five completed strategic games; excludes oracle-access inputs and invalid attempts from selected-list coverage.',
        'family_policy':'Literal text examples only; variant/merchant/package equivalence is not established.',
        'feature_policy':'Title and available image-alt text only; textual claims do not prove suitability.',
        'price_policy':'Frozen record price only, not complete-bundle eligibility or verified checkout price.',
        'source_sha256':dict(sorted(SOURCES.items()))},indent=2)+'\n')
    print(json.dumps(stats,indent=2))
    print('Example families:',[(g['example_family'],g['records'],g['ever_returned']) for g in sorted(groups,key=lambda x:-x['records'])])


if __name__=='__main__':main()
