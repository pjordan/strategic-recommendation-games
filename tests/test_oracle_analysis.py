import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'analyses/scenario-1/oracle-access'
spec = importlib.util.spec_from_file_location('oracle_runner', HERE / 'run_model.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class OracleAnalysisChecks(unittest.TestCase):
    def test_prompt_contains_exact_complete_records(self):
        for provider in ('bing', 'google'):
            prompt = runner.build_prompt(provider)
            data = json.loads(prompt.split('## Complete frozen recommendation records\n\n', 1)[1])
            self.assertEqual(data['records'], runner.scenario.load_records(provider))
            self.assertEqual(data['record_count'], len(data['records']))
            self.assertIn((runner.SCENARIO / 'private/user_preferences.md').read_text(), prompt)
            self.assertNotIn('none of the 408', prompt)

    def test_combined_universe_preserves_every_record(self):
        expected = runner.scenario.load_records('bing') + runner.scenario.load_records('google')
        prompt = runner.build_prompt('combined')
        data = json.loads(prompt.split('## Complete frozen recommendation records\n\n', 1)[1])
        self.assertEqual(data['records'], expected)
        self.assertEqual(data['record_count'], 465)
        self.assertEqual(len({r['record_id'] for r in data['records']}), 465)
        self.assertIn('components may come from either provider', prompt)
        self.assertNotIn('do not use products from the other provider', prompt)
        self.assertEqual(json.loads(runner.schema_path('combined').read_text())['properties']['provider']['enum'], ['combined'])

    def test_cross_provider_choice_allowed_only_in_combined(self):
        result = self.decision()
        bing = runner.scenario.load_records('bing')[0]
        google = min(runner.scenario.load_records('google'), key=lambda r:r['displayed_price_cents'])
        result['provider'] = 'combined'
        result['candidates'][1]['record_ids'] = [bing['record_id'], google['record_id']]
        result['candidates'][1]['displayed_total_cents'] = bing['displayed_price_cents'] + google['displayed_price_cents']
        runner.validate_decision(result, 'combined')
        result['provider'] = 'bing'
        with self.assertRaisesRegex(ValueError, 'record IDs'):
            runner.validate_decision(result, 'bing')

    def test_reasonable_policy_changes_only_evidence_paragraph(self):
        for provider in ('bing', 'google', 'combined'):
            original = runner.build_prompt(provider)
            revised = runner.build_prompt(provider, 'reasonable-representation')
            old_sections = original.split('\n\n')
            new_sections = revised.split('\n\n')
            self.assertEqual(len(old_sections), len(new_sections))
            differences = [(a,b) for a,b in zip(old_sections,new_sections) if a != b]
            self.assertEqual(len(differences), 1)
            self.assertIn('ordinary US household compatibility', differences[0][1])
            self.assertIn('recommendation-system results accurately represent', differences[0][1])
            self.assertEqual(original.split('## Shared background',1)[1], revised.split('## Shared background',1)[1])

    def decision(self):
        records = runner.scenario.load_records('bing')[:4]
        candidates = [{'candidate_id':'decline','action':'decline','record_ids':[], 'displayed_total_cents':0,'preference_rank':1}]
        candidates += [{'candidate_id':r['record_id'],'action':'purchase','record_ids':[r['record_id']], 'displayed_total_cents':r['displayed_price_cents'],'preference_rank':2} for r in records]
        return {'provider':'bing','selected_action':'decline','selected_record_ids':[], 'purchase_value_cents':0,'candidates':candidates}

    def test_foreign_record_and_wrong_price_are_rejected(self):
        valid = self.decision()
        runner.validate_decision(valid, 'bing')
        bad = copy.deepcopy(valid)
        bad['candidates'][1]['record_ids'] = ['invented-product']
        with self.assertRaisesRegex(ValueError, 'record IDs'):
            runner.validate_decision(bad, 'bing')
        bad = copy.deepcopy(valid)
        bad['candidates'][1]['displayed_total_cents'] += 1
        with self.assertRaisesRegex(ValueError, 'arithmetic'):
            runner.validate_decision(bad, 'bing')

    def test_selected_action_must_match_ranking(self):
        bad = self.decision()
        bad['candidates'][0]['preference_rank'] = 3
        with self.assertRaisesRegex(ValueError, 'highest-ranked'):
            runner.validate_decision(bad, 'bing')


if __name__ == '__main__':
    unittest.main()
