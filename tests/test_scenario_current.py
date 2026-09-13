"""Offline regression checks for catalog boundaries and consequential product facts."""
import json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import scenario_current as current

class CurrentScenarioTests(unittest.TestCase):
    def test_release_and_evidence_integrity(self):
        result=current.validate()
        self.assertEqual(sum(x['records'] for x in result['recommendations']),317)
    def test_recommender_sees_no_private_profile(self):
        self.assertNotIn('private_user_preferences',current.load_context())
        self.assertIn('private_user_preferences',current.load_context('buyer'))
    def test_facts_require_explicit_scope(self):
        with self.assertRaises(ValueError):current.load_facts()
        with self.assertRaises(ValueError):current.load_facts('bing',['google-c1ac723b3479e478c13f'])
    def test_bambino_has_no_integrated_grinder(self):
        product=current.load_facts(record_ids=['google-977666da80b52a214754'])[0]
        values=[f['value'] for f in product['facts'] if f['name']=='integrated_grinder']
        self.assertEqual(values,[False])
    def test_mini_manual_wand_and_conflicting_copy_retained(self):
        product=current.load_facts(record_ids=['google-c1ac723b3479e478c13f'])[0]
        self.assertTrue(any(f['name']=='manual_frothing_explicit' and f['value'] is True for f in product['facts']))
        self.assertTrue(any(c['topic']=='milk_system' for c in product['conflicts']))
    def test_chefman_does_not_inherit_comparison_product_capabilities(self):
        product=current.load_facts(record_ids=['google-ce916892b069dd413070'])[0]
        names={f['name'] for f in product['facts']}
        self.assertIn('dual_boiler_claim',names)
        self.assertNotIn('integrated_scale',names)
        self.assertNotIn('drip_coffee_mode',names)
        self.assertTrue(any(f['name']=='voltage' and f['value']=='120' for f in product['facts']))
    def test_no_one_step_workflow_mistaken_for_grind_setting(self):
        product=current.load_facts(record_ids=['google-9083303fcc2e5fd2dd1d'])[0]
        self.assertEqual({f['value'] for f in product['facts'] if f['name']=='grind_settings'},{'13'})
    def test_uk_bambino_does_not_inherit_watch_or_sage_variant_facts(self):
        product=current.load_facts(record_ids=['google-3b66cec49c3013bc150d'])[0]
        self.assertEqual(product['facts'],[])
        self.assertEqual(product['resolution']['status'],'unresolved')
        self.assertTrue(product['attempts'])

if __name__=='__main__':unittest.main()
