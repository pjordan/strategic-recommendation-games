"""Evidence preservation, deterministic replay and actor information boundaries."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('commerce_graph',ROOT/'tools/commerce_graph.py')
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
RELEASE=ROOT/g.GRAPH/'versions/1.0.0'
MINI='google-c1ac723b3479e478c13f'
BAMBINO='google-bbbd53043c8ed53733ef'


class CommerceGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.google=g.GraphView(ROOT,role='recommender',provider='google')
        cls.bing=g.GraphView(ROOT,role='recommender',provider='bing')
        cls.research=g.GraphView(ROOT,role='researcher',include_observations=True)

    def test_exact_rebuild_and_coverage(self):
        result=g.validate(ROOT,RELEASE)
        self.assertEqual(result['offer_count'],317)
        self.assertEqual(result['offers_with_product_facts'],205)
        self.assertEqual(result['offers_without_product_facts'],112)
        self.assertEqual(result['accepted_identity_merges'],0)
        self.assertEqual(result['candidate_identity_pairs'],4)
        self.assertEqual(result['compatibility_edges'],0)
        self.assertNotIn('private',g.dumps(g.read(RELEASE/'manifest.json')['input_sha256']))

    def test_schema_and_source_claims_preserved(self):
        schema=g.read(RELEASE/'schema.json')
        for item in list(self.research.nodes.values())+self.research.edges:
            self.assertTrue(g.conforms(item,schema),item['id'])
        records,facts,sources,_=g.inputs(ROOT)
        for card in records:
            rid=card['record_id'];node=self.research.nodes[rid]
            self.assertEqual(node['frozen_price_cents'],card['displayed_price_cents'])
            self.assertEqual(node['frozen_record_sha256'],card['record_sha256'])
            claims=sorted([c for c in self.research.claims[rid] if c['kind']=='product_fact'],key=lambda c:c['fact_index'])
            self.assertEqual([c['fact'] for c in claims],facts[rid]['facts'])
            for c in claims:
                for e in c['fact']['evidence']:self.assertIn(e['source_id'],sources)
        malformed=copy.deepcopy(self.research.nodes[MINI]);malformed['frozen_price_cents']='44999'
        self.assertFalse(g.conforms(malformed,schema))

    def test_unknown_false_and_qualified_are_distinct(self):
        self.assertEqual(self.google.status('google-977666da80b52a214754','cap-integrated_grinder')['status'],'reported_false')
        self.assertEqual(self.google.status(MINI,'cap-tamper')['status'],'unknown')
        self.assertEqual(self.google.status(MINI,'cap-integrated_scale')['status'],'reported_true')
        self.assertEqual(self.google.status(MINI,'cap-automatic_frothing_explicit')['status'],'qualified')
        self.assertNotEqual(self.google.status(MINI,'cap-manual_frothing_explicit')['status'],'inconsistent')
        self.assertEqual(g.normalized({'name':'integrated_grinder','category':'grinding','value':'true'},g.read(RELEASE/'mappings/capability-mapping.json')),[])
        # A provider's 'Milk Frothing Pitcher' is not proof of an included pitcher.
        self.assertEqual(g.normalized({'name':'Milk Frother','category':'provider_specification','value':'Milk Frothing Pitcher'},g.read(RELEASE/'mappings/capability-mapping.json')),[])

    def test_scopes_and_cross_provider_identity_do_not_leak(self):
        for view,provider in ((self.google,'google'),(self.bing,'bing')):
            data=view.query(limit=100,representation='graph')
            self.assertTrue(all(o['provider']==provider for o in data['offers']))
            other='bing-' if provider=='google' else 'google-'
            self.assertNotIn(other,g.dumps(data))
            for edge in data['graph']['edges']:
                self.assertNotIn('candidate_same_product' if edge.get('related_record_id','').startswith(other) else 'impossible',edge['predicate'])
        with self.assertRaisesRegex(ValueError,'outside permitted'):
            self.bing.query('inspect',record_ids=[MINI])
        with self.assertRaisesRegex(ValueError,'requires explicitly'):
            g.GraphView(ROOT,role='buyer')
        buyer=g.GraphView(ROOT,role='buyer',allowed_ids=[MINI])
        self.assertEqual(buyer.query()['query']['total_in_scope'],1)
        with self.assertRaisesRegex(ValueError,'outside permitted'):
            buyer.query('compare',record_ids=[MINI,BAMBINO])
        empty=g.GraphView(ROOT,role='buyer',allowed_ids=[])
        self.assertEqual(empty.query()['query']['total_in_scope'],0)
        with self.assertRaisesRegex(ValueError,'research-only'):
            g.GraphView(ROOT,provider='google',include_observations=True)

    def test_pagination_and_all_representations_match(self):
        ids=[];offset=0
        while True:
            result=self.google.query(offset=offset,limit=17)
            ids.extend(o['id'] for o in result['offers'])
            if result['query']['next_offset'] is None:break
            offset=result['query']['next_offset']
        self.assertEqual(len(ids),140);self.assertEqual(len(set(ids)),140)
        outputs={fmt:self.google.query('inspect',record_ids=[MINI],representation=fmt) for fmt in ('graph','table','facts-json')}
        for value in outputs.values():
            self.assertEqual(value['offers'],outputs['graph']['offers'])
            self.assertEqual(value['capability_status'],outputs['graph']['capability_status'])
        self.assertEqual(outputs['table']['relationships'],outputs['graph']['graph']['edges'])
        self.assertEqual(outputs['facts-json']['normalization_and_identity_annotations']['relationships'],outputs['table']['relationships'])
        self.assertEqual({c['id'] for c in outputs['table']['claims']},{n['id'] for n in outputs['graph']['graph']['nodes'] if n['type']=='claim'})
        result=self.google.query(capabilities=['cap-integrated_scale'],max_price_cents=80000)
        self.assertIn(MINI,[o['id'] for o in result['offers']])
        result=self.google.query(record_ids=[MINI],capabilities=['cap-automatic_frothing_explicit'])
        self.assertEqual(result['offers'],[])
        result=self.google.query(record_ids=[MINI],capabilities=['cap-automatic_frothing_explicit'],include_qualified=True)
        self.assertEqual([o['id'] for o in result['offers']],[MINI])

    def test_observed_seller_and_price_are_not_frozen_offer_facts(self):
        rid='google-ceb6c802131f2c0a0c32'
        ordinary=self.google.query('inspect',record_ids=[rid])
        research=self.research.query('inspect',record_ids=[rid])
        self.assertFalse(any(n['type']=='seller_reference' for n in ordinary['graph']['nodes']))
        self.assertTrue(any(n['type']=='seller_reference' for n in research['graph']['nodes']))
        self.assertEqual(research['offers'][0]['frozen_price_cents'],33249)
        self.assertFalse(any(e['subject']==rid and e['predicate']=='observed_seller' for e in research['graph']['edges']))
        self.assertTrue(any(c.get('observation',{}).get('observations',{}).get('price')=='368.99' for c in research['graph']['nodes']))

    def test_bundle_is_coverage_not_compatibility_or_suitability(self):
        result=self.google.query('bundle',record_ids=[MINI,BAMBINO],capabilities=['cap-integrated_grinder','cap-tamper'],max_price_cents=80000)
        self.assertEqual(result['bundle']['frozen_total_cents'],94994)
        self.assertFalse(result['bundle']['within_price_limit'])
        self.assertEqual(result['bundle']['compatibility'],'not_established')
        self.assertIn('not_assessed',result['bundle']['complete_setup'])
        with self.assertRaisesRegex(ValueError,'all requested IDs'):
            self.google.query('bundle',record_ids=[MINI,BAMBINO],limit=1)

    def test_tampering_and_unsafe_manifest_paths_fail(self):
        with tempfile.TemporaryDirectory() as temporary:
            release=Path(temporary)/'release';shutil.copytree(RELEASE,release)
            p=release/'nodes/offers.jsonl';p.write_text(p.read_text().replace('44999','44998',1))
            with self.assertRaisesRegex(ValueError,'checksum'):
                g.validate(ROOT,release)
            meta=g.read(release/'manifest.json');meta['files']['nodes/offers.jsonl']=g.sha(p.read_bytes());(release/'manifest.json').write_text(g.pretty(meta))
            with self.assertRaisesRegex(ValueError,'does not reproduce'):
                g.validate(ROOT,release)
            with self.assertRaisesRegex(ValueError,'Unsafe'):
                g.safe_path(release,'../escape')


if __name__=='__main__':unittest.main()
