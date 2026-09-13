"""Offline loader for Scenario 1.3.0 and its opt-in product facts.

Legacy tools/scenario.py remains unchanged so archived traces retain their meaning.
"""
import argparse
import hashlib
import json
from pathlib import Path
from scenario import ROOT, check, load_context as legacy_context, read, validate_dataset, validate_version

VERSION='1.3.0'
FACTS_VERSION='1.0.0'

def scenario_root(root=ROOT):return root/'versions'/VERSION

def load_records(provider,root=ROOT):
    check(provider in ('bing','google'),'Unknown provider')
    return read(scenario_root(root)/'recommendations'/f'{provider}.json')['records']

def load_context(role='recommender',root=ROOT):
    check(role in ('buyer','recommender'),'Unknown role')
    result={'public_context':(root/'public_context.md').read_text()}
    if role=='buyer':result['private_user_preferences']=(scenario_root(root)/'private/user_preferences.md').read_text()
    return result

def load_facts(provider=None,record_ids=None,root=ROOT):
    """Only selected IDs, or an explicitly requested provider catalog. Never a hidden buyer brief."""
    check(provider in ('bing','google',None),'Unknown provider')
    check(provider is not None or record_ids is not None,'Specify a provider or record IDs')
    allowed={r['record_id'] for p in ('bing','google') if provider is None or p==provider for r in load_records(p,root)}
    ids=sorted(allowed) if record_ids is None else list(record_ids)
    check(set(ids)<=allowed,'Record does not belong to the requested provider/current scenario')
    fr=root/'product-facts'/'versions'/FACTS_VERSION
    return [read(fr/'products'/f'{rid}.json') for rid in ids]

def verify_hashes(root,entries):
    for rel,expected in entries.items():
        path=(root/rel).resolve()
        check(path.is_relative_to(root.resolve()),'Manifest path escapes release')
        check(hashlib.sha256(path.read_bytes()).hexdigest()==expected,'Checksum mismatch: '+rel)

def validate(root=ROOT):
    validate_version('1.2.0',root) # Includes original hashes and publication checks.
    vr=scenario_root(root);fr=root/'product-facts'/'versions'/FACTS_VERSION
    verify_hashes(vr,{line.split('  ',1)[1]:line.split('  ',1)[0] for line in (vr/'manifest.sha256').read_text().splitlines()})
    meta=read(vr/'scenario.json');check(meta['version']==VERSION,'Version mismatch')
    check(meta['base_scenario_manifest_sha256']==hashlib.sha256((root/'versions/1.2.0/manifest.sha256').read_bytes()).hexdigest(),'Base version mismatch')
    check((vr/'private/user_preferences.md').read_bytes()==(root/'versions/1.2.0/private/user_preferences.md').read_bytes(),'Preferences changed')
    summaries=[];records=[]
    for provider in ('bing','google'):
        d=read(vr/'recommendations'/f'{provider}.json');summaries.append(validate_dataset(d))
        original=read(root/'recommendations'/f'{provider}.json')['records']
        check(d['records']==[r for r in original if not r['sponsored']],'Surviving cards/order changed')
        records.extend(d['records'])
    check(len(records)==317 and all(not r['sponsored'] for r in records),'Wrong nonsponsored catalog')
    manifest=read(fr/'manifest.json');verify_hashes(fr,manifest['files'])
    check(manifest['scenario_manifest_sha256']==hashlib.sha256((vr/'manifest.sha256').read_bytes()).hexdigest(),'Facts bound to different scenario')
    check(manifest['schema_sha256']==hashlib.sha256((root/'product-facts/schema.json').read_bytes()).hexdigest(),'Fact schema changed')
    index=read(fr/'index.json');check(index['record_count']==317,'Wrong fact index count')
    check({i['record_id'] for i in index['products']}=={r['record_id'] for r in records},'Fact coverage differs from catalog')
    check({p.stem for p in (fr/'products').glob('*.json')}=={r['record_id'] for r in records},'Extra or missing product file')
    by_id={r['record_id']:r for r in records}
    for item in index['products']:
        product=read(fr/item['file']);rid=product['record_id'];r=by_id[rid]
        check(product['frozen_record_sha256']==r['record_sha256'],'Product facts bound to wrong card')
        check(item['fact_count']==len(product['facts']),'Fact count mismatch')
        for fact in product['facts']:
            check(bool(fact['evidence']),'Unsupported fact')
            for e in fact['evidence']:
                source=read(fr/'sources'/f"{e['source_id']}.json")
                check(bool(e['locator']) and len(source['content_sha256'])==64,'Missing source provenance')
        if product['resolution']['status'] in ['unresolved','unavailable','ambiguous']:
            check(not product['facts'],'Unmatched listing has attributed facts')
    check('private_user_preferences' not in load_context('recommender',root),'Preference leak')
    return {'scenario_version':VERSION,'recommendations':summaries,'facts_version':FACTS_VERSION,'coverage':index['coverage'],'source_count':index['source_count']}

def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='command',required=True)
    sub.add_parser('validate')
    p=sub.add_parser('records');p.add_argument('--provider',choices=['bing','google'],required=True)
    p=sub.add_parser('context');p.add_argument('--role',choices=['buyer','recommender'],default='recommender')
    p=sub.add_parser('facts');p.add_argument('--provider',choices=['bing','google']);p.add_argument('--record-id',action='append')
    args=ap.parse_args()
    if args.command=='validate':out=validate()
    elif args.command=='records':out=load_records(args.provider)
    elif args.command=='facts':out=load_facts(args.provider,args.record_id)
    else:print('\n'.join(load_context(args.role).values()),end='');return
    print(json.dumps(out,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
