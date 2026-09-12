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
