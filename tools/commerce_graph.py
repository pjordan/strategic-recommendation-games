"""Deterministic evidence graph and scoped queries for frozen Scenario 1.

Standard library only. The public files are research artifacts; GraphView fixes
an actor's query scope but is not an operating-system access-control boundary.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile

REPO = Path(__file__).resolve().parents[1]
GRAPH = Path('scenarios/scenario-1/commerce-graph')
VERSION = '1.0.0'
FACTS = Path('scenarios/scenario-1/product-facts/versions/1.0.0')
CARDS = Path('scenarios/scenario-1/versions/1.3.0/recommendations')
NODE_FILES = ('offers', 'products', 'sellers', 'claims', 'sources', 'capabilities')


def read(path): return json.loads(path.read_text())
def dumps(value): return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
def pretty(value): return json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2)+'\n'
def sha(data): return hashlib.sha256(data).hexdigest()
def ident(prefix, value): return prefix+'-'+sha(dumps(value).encode())[:24]
def jsonl(values): return ''.join(dumps(v)+'\n' for v in sorted(values, key=lambda v: v['id']))
def rows(path): return [json.loads(s) for s in path.read_text().splitlines() if s]


def safe_path(root, rel):
    path = Path(rel)
    if path.is_absolute() or '..' in path.parts or (root/path).is_symlink():
        raise ValueError('Unsafe manifest path')
    target = (root/path).resolve()
    if root.resolve() not in target.parents:
        raise ValueError('Manifest path escapes root')
    return target


def inputs(repo):
    records = [r for provider in ('bing', 'google') for r in read(repo/CARDS/(provider+'.json'))['records']]
    facts = {r['record_id']: read(repo/FACTS/'products'/(r['record_id']+'.json')) for r in records}
    sources = {p.stem: read(p) for p in sorted((repo/FACTS/'sources').glob('*.json'))}
    paths = [repo/CARDS/(p+'.json') for p in ('bing', 'google')]
    paths += list((repo/FACTS/'products').glob('*.json'))+list((repo/FACTS/'sources').glob('*.json'))
    fact_manifest=read(repo/FACTS/'manifest.json')
    for path in paths[2:]:
        rel=path.relative_to(repo/FACTS).as_posix()
        if sha(path.read_bytes()) != fact_manifest['files'].get(rel): raise ValueError('Frozen fact input checksum differs')
    card_hashes={line.split('  ',1)[1]:line.split('  ',1)[0] for line in (repo/CARDS.parent/'manifest.sha256').read_text().splitlines()}
    for path in paths[:2]:
        if sha(path.read_bytes()) != card_hashes.get(path.relative_to(repo/CARDS.parent).as_posix()): raise ValueError('Frozen card input checksum differs')
    paths += [repo/FACTS/'manifest.json', repo/FACTS/'index.json', repo/'scenarios/scenario-1/product-facts/schema.json', repo/CARDS.parent/'manifest.sha256']
    if len(records) != 317 or len(facts) != 317 or any(r['sponsored'] for r in records):
        raise ValueError('Unexpected scenario catalog')
    for r in records:
        if facts[r['record_id']]['frozen_record_sha256'] != r['record_sha256']:
            raise ValueError('Fact/card binding differs')
    return records, facts, sources, {p.relative_to(repo).as_posix(): sha(p.read_bytes()) for p in sorted(paths)}


def candidate_identities(facts):
    groups = defaultdict(list)
    for rid, f in facts.items():
        resolution = f['resolution']
        if resolution['status'] == 'matched_listing' and resolution.get('product_url'):
            groups[resolution['product_url']].append(rid)
    result = []
    for url, ids in sorted(groups.items()):
        for pair in itertools.combinations(sorted(ids), 2):
            result.append({'id': ident('identity', pair), 'record_ids': list(pair), 'status': 'candidate',
                           'basis': 'same_resolved_landing_page', 'product_url': url,
                           'rule_id': 'shared-page-candidate-v1',
                           'qualification': 'Shared page is a candidate identity link, not verified variant equivalence. No claims or offers are merged.'})
    return result


def normalized(fact, mapping):
    result = []
    for rule in mapping['rules']:
        if fact['name'] not in rule['fact_names'] or fact['category'] not in rule['categories']:
            continue
        for source, value in rule['value_map']:
            if type(fact['value']) is type(source) and fact['value'] == source:
                result.append({'capability_id': rule['capability_id'], 'value': value, 'rule_id': rule['id']})
    return result


def conforms(value, schema):
    """Validate the small JSON Schema vocabulary used by our record schema."""
    if 'oneOf' in schema and sum(conforms(value, s) for s in schema['oneOf']) != 1: return False
    if 'const' in schema and (type(value) is not type(schema['const']) or value != schema['const']): return False
    if 'enum' in schema and value not in schema['enum']: return False
    types={'object':dict,'array':list,'string':str,'integer':int,'boolean':bool,'null':type(None)}
    kind=schema.get('type')
    if kind and type(value) is not types[kind]: return False
    if isinstance(value,dict):
        if not set(schema.get('required',[]))<=set(value): return False
        props=schema.get('properties',{})
        if schema.get('additionalProperties') is False and not set(value)<=set(props): return False
        if any(not conforms(v,props[k]) for k,v in value.items() if k in props): return False
    if isinstance(value,list) and 'items' in schema and any(not conforms(v,schema['items']) for v in value): return False
    if type(value) is int and value<schema.get('minimum',value): return False
    return True


def generate(repo, mappings, schema):
    records, facts, sources, hashes = inputs(repo)
    mapping = read(mappings/'capability-mapping.json')
    rules = read(mappings/'inference-rules.json')
    decisions = rows(mappings/'identity-decisions.jsonl')
    if decisions != sorted(candidate_identities(facts), key=lambda x: x['id']):
        raise ValueError('Identity decisions differ from the supported candidate-only v1 rule')
    expected_rules = {'shared-page-candidate-v1', 'capability-support-v1', 'qualified-milk-v1', 'observation-seller-v1'}
    if {r['id'] for r in rules['rules']} != expected_rules:
        raise ValueError('Unexpected inference rules')
    nodes = {name: [] for name in NODE_FILES}; edges = []; claims_by_offer = defaultdict(list)
    for cap in mapping['capabilities']:
        nodes['capabilities'].append({'id': cap['id'], 'type': 'capability', 'label': cap['label'], 'meaning': cap['meaning']})
    cap_ids = {c['id'] for c in nodes['capabilities']}
    if any(r['capability_id'] not in cap_ids for r in mapping['rules']):
        raise ValueError('Unknown mapped capability')

    def edge(subject, predicate, obj, record_id, *, rule_id=None, evidence_claim_ids=None, **extra):
        item = {'subject': subject, 'predicate': predicate, 'object': obj, 'record_id': record_id,
                'basis': 'derived' if rule_id else 'source_link', **extra}
        if rule_id: item['rule_id'] = rule_id
        if evidence_claim_ids: item['evidence_claim_ids'] = evidence_claim_ids
        item['id'] = ident('edge', item); edges.append(item)

    for sid, source in sorted(sources.items()):
        nodes['sources'].append({'id': sid, 'type': 'source', 'reference': (FACTS/'sources'/(sid+'.json')).as_posix(),
                                 'reference_sha256': hashes[(FACTS/'sources'/(sid+'.json')).as_posix()], **source})
    seller_nodes = {}
    for card in sorted(records, key=lambda r: r['record_id']):
        rid = card['record_id']; f = facts[rid]; pid = 'product-'+rid
        nodes['offers'].append({'id': rid, 'type': 'offer', 'provider': card['provider'], 'title': card['title'],
                                'frozen_price_cents': card['displayed_price_cents'], 'currency': card['currency'],
                                'merchant_display_text': card['merchant_display_text'],
                                'merchant_text_is_aggregate': card['merchant_text_is_aggregate'],
                                'frozen_record_sha256': card['record_sha256'],
                                'card_reference': (CARDS/(card['provider']+'.json')).as_posix(),
                                'facts_reference': (FACTS/'products'/(rid+'.json')).as_posix(),
                                'resolution': f['resolution'], 'conflicts': f['conflicts'],
                                'not_established_categories': f['not_established_categories']})
        nodes['products'].append({'id': pid, 'type': 'product_reference', 'record_id': rid,
                                  'label': f['resolution'].get('page_title') or card['title'],
                                  'identity_scope': 'offer_scoped_not_deduplicated',
                                  'identity_status': f['resolution']['status']})
        edge(rid, 'describes_product', pid, rid)
        for index, fact in enumerate(f['facts']):
            cid = ident('claim', [rid, 'facts', index, fact])
            norm = normalized(fact, mapping)
            qualifications = [c for c in f['conflicts'] if c['topic'] == 'milk_system' and (fact['category'] == 'milk' or any(n['capability_id'] in ('cap-steam_wand_present','cap-manual_frothing_explicit','cap-automatic_frothing_explicit') for n in norm))]
            claim = {'id': cid, 'type': 'claim', 'record_id': rid, 'kind': 'product_fact',
                     'fact_index': index, 'fact': fact, 'normalized': norm,
                     'scope': 'Source claim applied only to this resolved listing; not independently tested.',
                     'qualifications': qualifications}
            nodes['claims'].append(claim); claims_by_offer[rid].append(claim)
            edge(cid, 'about_product', pid, rid)
            for ev in fact['evidence']:
                if ev['source_id'] not in sources: raise ValueError('Missing evidence source')
                edge(cid, 'supported_by', ev['source_id'], rid, locator=ev['locator'])
            for n in norm:
                edge(cid, 'reports_capability', n['capability_id'], rid, rule_id=n['rule_id'], value=n['value'])
                edge(pid, 'capability_evidence', n['capability_id'], rid, rule_id='capability-support-v1',
                     evidence_claim_ids=[cid], value=n['value'], qualified=bool(qualifications))
        for index, obs in enumerate(f['offer_observations']):
            cid = ident('claim', [rid, 'offer_observations', index, obs])
            nodes['claims'].append({'id': cid, 'type': 'claim', 'record_id': rid, 'kind': 'landing_page_observation',
                                    'observation_index': index, 'observation': obs, 'scope': obs['scope']})
            edge(cid, 'observed_for_listing', rid, rid)
            edge(cid, 'supported_by', obs['source_id'], rid, locator=obs['locator'])
            seller = obs['observations'].get('seller')
            if isinstance(seller, str) and seller.strip():
                sid = ident('seller', [obs['source_id'], seller])
                seller_nodes[sid] = {'id': sid, 'type': 'seller_reference', 'label': seller,
                                     'identity_scope': 'source_scoped_seller_name', 'source_id': obs['source_id']}
                edge(cid, 'observed_seller', sid, rid, rule_id='observation-seller-v1', evidence_claim_ids=[cid])
    nodes['sellers'] = list(seller_nodes.values())
    for decision in decisions:
        a, b = decision['record_ids']
        edge('product-'+a, 'candidate_same_product', 'product-'+b, a, rule_id='shared-page-candidate-v1',
             related_record_id=b, decision_id=decision['id'], qualification=decision['qualification'])
    record_schema=read(schema)
    for item in [n for group in nodes.values() for n in group]+edges:
        if not conforms(item,record_schema): raise ValueError('Graph record violates schema: '+item['id'])
    all_ids = [n['id'] for group in nodes.values() for n in group]
    if len(set(all_ids)) != len(all_ids): raise ValueError('Duplicate node ID')
    known = set(all_ids)
    if any(e['subject'] not in known or e['object'] not in known for e in edges): raise ValueError('Dangling edge')
    if len({e['id'] for e in edges}) != len(edges): raise ValueError('Duplicate edge')
    coverage = {'graph_version': VERSION, 'offer_count': len(records), 'product_reference_count': len(nodes['products']),
                'unique_physical_products': None, 'accepted_identity_merges': 0, 'candidate_identity_pairs': len(decisions),
                'offers_with_product_facts': len(claims_by_offer), 'offers_without_product_facts': len(records)-len(claims_by_offer),
                'resolution_status': dict(sorted(Counter(f['resolution']['status'] for f in facts.values()).items())),
                'node_counts': {k:len(v) for k,v in nodes.items()}, 'edge_count': len(edges),
                'capability_evidence_edges': sum(e['predicate']=='capability_evidence' for e in edges),
                'compatibility_edges': 0, 'frozen_offer_seller_edges': 0,
                'limits': ['No compatibility inferred from shared dimensions or names.',
                           'Missing evidence is unknown, not false.', 'Later offer observations never replace frozen prices.',
                           'Manual and automatic milk claims can coexist; flagged ambiguity is retained.',
                           'No preference brief or satisfaction score is loaded.']}
    output = {f'nodes/{name}.jsonl': jsonl(values).encode() for name,values in nodes.items()}
    output['edges.jsonl'] = jsonl(edges).encode(); output['coverage.json'] = pretty(coverage).encode()
    for name in ('capability-mapping.json', 'inference-rules.json', 'identity-decisions.jsonl'):
        output['mappings/'+name] = (mappings/name).read_bytes()
    output['schema.json'] = schema.read_bytes()
    output['build-source/commerce_graph.py'] = Path(__file__).read_bytes()
    manifest = {'graph_version': VERSION, 'scenario_version': '1.3.0', 'facts_version': '1.0.0',
                'builder_sha256': sha(Path(__file__).read_bytes()), 'input_sha256': hashes,
                'files': {name:sha(data) for name,data in sorted(output.items())},
                'build_policy': 'Deterministic offline derivation; no wall-clock timestamp or new web evidence.'}
    output['manifest.json'] = pretty(manifest).encode()
    return output


def write_release(repo, output, mappings, schema):
    if (output/'manifest.json').exists(): raise ValueError('Release already exists; use a fresh output directory')
    artifacts = generate(repo, mappings, schema)
    existing = {p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file()} if output.exists() else set()
    if existing-set('mappings/'+p.name for p in mappings.glob('*')): raise ValueError('Output directory is not empty')
    for rel,data in artifacts.items():
        p=output/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(data)
    return read(output/'coverage.json')


def validate(repo, release, replay=True):
    meta=read(release/'manifest.json')
    if meta['graph_version'] != VERSION: raise ValueError('Unknown graph version')
    files={p.relative_to(release).as_posix() for p in release.rglob('*') if p.is_file()}
    if files != set(meta['files'])|{'manifest.json'}: raise ValueError('Unexpected or missing graph artifact')
    for rel,digest in meta['files'].items():
        if sha(safe_path(release,rel).read_bytes()) != digest: raise ValueError('Graph checksum differs: '+rel)
    for rel,digest in meta['input_sha256'].items():
        if sha(safe_path(repo,rel).read_bytes()) != digest: raise ValueError('Input checksum differs: '+rel)
    if meta['builder_sha256'] != meta['files']['build-source/commerce_graph.py']: raise ValueError('Builder binding differs')
    if replay:
        with tempfile.TemporaryDirectory(prefix='commerce-graph-replay-') as temp:
            target=Path(temp)/'rebuilt'
            subprocess.run([sys.executable,'-B',str(release/'build-source/commerce_graph.py'), '--repo', str(repo),
                            'build','--output',str(target),'--mappings',str(release/'mappings'),
                            '--schema',str(release/'schema.json')],check=True,capture_output=True,text=True)
            for rel in files:
                if (release/rel).read_bytes() != (target/rel).read_bytes(): raise ValueError('Graph does not reproduce: '+rel)
    return {'status':'verified','replayed':replay,**read(release/'coverage.json')}


class GraphView:
    """Fixed information boundary; requests cannot change role or allowed IDs."""
    def __init__(self, repo=REPO, release=None, *, role='recommender', provider=None, allowed_ids=None, include_observations=False):
        self.repo=Path(repo); self.release=Path(release) if release else self.repo/GRAPH/'versions'/VERSION
        validate(self.repo,self.release,replay=False)
        self.nodes={n['id']:n for name in NODE_FILES for n in rows(self.release/'nodes'/(name+'.jsonl'))}
        self.edges=rows(self.release/'edges.jsonl')
        offers={i:n for i,n in self.nodes.items() if n['type']=='offer'}
        if role not in ('recommender','buyer','researcher'): raise ValueError('Unknown role')
        if provider not in (None,'bing','google'): raise ValueError('Unknown provider')
        if role=='recommender' and provider is None: raise ValueError('Recommender requires provider')
        if role=='buyer' and allowed_ids is None: raise ValueError('Buyer requires explicitly visible record IDs')
        if include_observations and role!='researcher': raise ValueError('Offer observations are research-only in v1')
        ids={i for i,n in offers.items() if provider is None or n['provider']==provider}
        if allowed_ids is not None:
            if not set(allowed_ids)<=ids: raise ValueError('Record outside permitted scope')
            ids &= set(allowed_ids)
        self.allowed=ids; self.include_observations=include_observations
        self.capabilities={i:n for i,n in self.nodes.items() if n['type']=='capability'}
        self.claims=defaultdict(list)
        for n in self.nodes.values():
            if n['type']=='claim' and n['record_id'] in ids and (n['kind']=='product_fact' or include_observations):
                self.claims[n['record_id']].append(n)

    def status(self, rid, capability):
        if rid not in self.allowed: raise ValueError('Record outside permitted scope')
        if capability not in self.capabilities: raise ValueError('Unknown capability')
        evidence=[c for c in self.claims[rid] if any(n['capability_id']==capability for n in c.get('normalized',[]))]
        values={n['value'] for c in evidence for n in c['normalized'] if n['capability_id']==capability}
        state=('unknown' if not values else 'inconsistent' if len(values)>1 else
               'qualified' if any(c.get('qualifications') for c in evidence) else 'reported_true' if True in values else 'reported_false')
        return {'status':state,'reported_values':sorted(values),'claim_ids':sorted(c['id'] for c in evidence)}

    def select(self, operation='find', *, record_ids=None, capabilities=None, max_price_cents=None, include_qualified=False, offset=0, limit=20):
        caps=capabilities or []
        if not set(caps)<=set(self.capabilities): raise ValueError('Unknown capability')
        if not isinstance(offset,int) or offset<0 or not isinstance(limit,int) or not 1<=limit<=100: raise ValueError('Invalid pagination')
        if max_price_cents is not None and (type(max_price_cents) is not int or max_price_cents<0): raise ValueError('Invalid price limit')
        ids=sorted(self.allowed) if record_ids is None else list(record_ids)
        if len(set(ids))!=len(ids) or not set(ids)<=self.allowed: raise ValueError('Record outside permitted scope or duplicate ID')
        if operation not in ('find','compare','inspect','bundle'): raise ValueError('Unknown operation')
        if operation in ('inspect','compare') and max_price_cents is not None: raise ValueError('Price limits apply only to find or bundle')
        if operation!='find' and not record_ids: raise ValueError('Operation requires explicit record IDs')
        if operation in ('compare','bundle') and (offset!=0 or len(ids)>limit): raise ValueError('Compare/bundle must include all requested IDs within limit')
        if operation=='find':
            ids=[i for i in ids if (max_price_cents is None or self.nodes[i]['frozen_price_cents']<=max_price_cents)
                 and all(self.status(i,c)['status']=='reported_true' or
                         (include_qualified and self.status(i,c)['status']=='qualified' and self.status(i,c)['reported_values']==[True]) for c in caps)]
            ids.sort(key=lambda i:(self.nodes[i]['frozen_price_cents'],i))
        total=len(ids); ids=ids[offset:offset+limit]
        return ids,{'operation':operation,'capabilities':caps,'max_price_cents':max_price_cents,
                    'include_qualified':include_qualified,'offset':offset,'limit':limit,'total_in_scope':total,
                    'next_offset':offset+len(ids) if offset+len(ids)<total else None,
                    'ordering':'frozen_price_then_id' if operation=='find' else 'requested_order',
                    'interpretation':'Evidence retrieval, not suitability or utility ranking.'}

    def render(self, ids, representation='graph'):
        if not set(ids)<=self.allowed: raise ValueError('Record outside permitted scope')
        claims=[c for i in ids for c in self.claims[i]]
        claim_ids={c['id'] for c in claims}
        subjects=set(ids)|{'product-'+i for i in ids}|claim_ids
        selected_edges=[e for e in self.edges if e['record_id'] in ids
                        and (not e.get('related_record_id') or e['related_record_id'] in ids)
                        and e['subject'] in subjects
                        and (e['predicate']!='capability_evidence' or set(e.get('evidence_claim_ids',[]))<=claim_ids)]
        edge_ids=set(ids)|{'product-'+i for i in ids}|{c['id'] for c in claims}
        edge_ids.update(x for e in selected_edges for x in (e['subject'],e['object']))
        # Seller edges originate only from observations already allowed above.
        graph={'nodes':sorted((self.nodes[i] for i in edge_ids),key=lambda n:n['id']), 'edges':selected_edges}
        common={'offers':[self.nodes[i] for i in ids],
                'capability_definitions':[self.capabilities[c] for c in sorted(self.capabilities)],
                'capability_status':{i:{c:self.status(i,c) for c in sorted(self.capabilities)} for i in ids}}
        if representation=='graph': return {**common,'graph':graph}
        if representation=='table':
            return {**common,'claims':claims,'relationships':selected_edges,
                    'products':[n for n in graph['nodes'] if n['type']=='product_reference'],
                    'sources':[n for n in graph['nodes'] if n['type']=='source'],
                    'sellers':[n for n in graph['nodes'] if n['type']=='seller_reference']}
        if representation=='facts-json':
            fields=('record_id','resolution','facts','conflicts','not_established_categories')
            raw=[{k:read(self.repo/FACTS/'products'/(i+'.json'))[k] for k in fields} for i in ids]
            return {**common,'product_facts':raw,
                    'normalization_and_identity_annotations':{'claims':claims,'relationships':selected_edges},
                    'sources':[n for n in graph['nodes'] if n['type']=='source'],
                    'products':[n for n in graph['nodes'] if n['type']=='product_reference'],
                    'sellers':[n for n in graph['nodes'] if n['type']=='seller_reference']}
        raise ValueError('Unknown representation')

    def query(self, operation='find', *, representation='graph', **kwargs):
        ids,metadata=self.select(operation,**kwargs)
        result={'query':metadata,**self.render(ids,representation)}
        if operation=='bundle':
            caps=kwargs.get('capabilities') or []
            result['bundle']={'frozen_total_cents':sum(self.nodes[i]['frozen_price_cents'] for i in ids),
                              'within_price_limit':None if kwargs.get('max_price_cents') is None else sum(self.nodes[i]['frozen_price_cents'] for i in ids)<=kwargs['max_price_cents'],
                              'reported_capability_coverage':{c:any(self.status(i,c)['status']=='reported_true' for i in ids) for c in caps},
                              'compatibility':'not_established' if len(ids)>1 else 'not_applicable_to_single_offer',
                              'complete_setup':'not_assessed; capability coverage alone does not establish compatibility, accessory completeness or satisfaction'}
        return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--repo',type=Path,default=REPO)
    subs=parser.add_subparsers(dest='command',required=True)
    b=subs.add_parser('build');b.add_argument('--output',type=Path);b.add_argument('--mappings',type=Path);b.add_argument('--schema',type=Path)
    v=subs.add_parser('validate');v.add_argument('--release',type=Path)
    q=subs.add_parser('query');q.add_argument('--release',type=Path);q.add_argument('--role',choices=['recommender','buyer','researcher'],default='recommender')
    q.add_argument('--provider',choices=['bing','google']);q.add_argument('--allowed-id',action='append');q.add_argument('--include-observations',action='store_true')
    q.add_argument('--operation',choices=['find','inspect','compare','bundle'],default='find');q.add_argument('--record-id',action='append')
    q.add_argument('--capability',action='append');q.add_argument('--max-price-cents',type=int);q.add_argument('--include-qualified',action='store_true')
    q.add_argument('--offset',type=int,default=0);q.add_argument('--limit',type=int,default=20);q.add_argument('--format',choices=['graph','table','facts-json'],default='graph')
    args=parser.parse_args();repo=args.repo.resolve();release=getattr(args,'release',None) or repo/GRAPH/'versions'/VERSION
    if args.command=='build':
        output=args.output or release
        result=write_release(repo,output,args.mappings or release/'mappings',args.schema or repo/GRAPH/'schema.json')
    elif args.command=='validate': result=validate(repo,release)
    else:
        view=GraphView(repo,release,role=args.role,provider=args.provider,allowed_ids=args.allowed_id,include_observations=args.include_observations)
        result=view.query(args.operation,representation=args.format,record_ids=args.record_id,capabilities=args.capability,
                          max_price_cents=args.max_price_cents,include_qualified=args.include_qualified,offset=args.offset,limit=args.limit)
    print(pretty(result),end='')


if __name__=='__main__':main()
