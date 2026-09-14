"""Discovery protocol, conditional forecasts, information boundaries and archived replay."""
import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import test_recommender_text as fixtures

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT/'analyses/scenario-1/preference-elicitation'
spec = importlib.util.spec_from_file_location('strategic_learning_study', HERE/'run_study.py')
study = importlib.util.module_from_spec(spec); spec.loader.exec_module(study)


class PreferenceElicitationChecks(unittest.TestCase):
    def test_schedule_and_staged_prompts(self):
        cases = study.plan(2, 0)
        self.assertEqual(len(cases), 2)
        self.assertEqual([c['display_order'] for c in cases], ['bing-first', 'google-first'])
        self.assertTrue(all(c['condition'] == 'two-round-strategic-disclosure' for c in cases))
        self.assertEqual(study.plan(1, 0), study.plan(1, 17))
        new = study.ElicitationGame(cases[0], 'text-enabled')
        old = study.base.StrategicLearningGame(cases[0], 'text-enabled')
        self.assertEqual(new.catalog, old.catalog)
        self.assertEqual(new.facts, old.facts)
        self.assertEqual(new.rules(), old.rules())
        self.assertEqual(new.prompt('buyer', {}), old.prompt('buyer', {}))
        for role in ('disclosure', 'followup', 'buyer', 'recommender'):
            self.assertEqual(new.schema(role), old.schema(role))
        self.assertIn('sales discovery before', new.prompt('recommender', {'round': 1}))
        self.assertIn('optimized offer after', new.prompt('recommender', {'round': 2}))
        with self.assertRaises(ValueError): study.plan(0, 0)
        with self.assertRaises(ValueError): study.ElicitationGame(cases[0], 'list-only')

    def test_conditional_forecast_does_not_materialize_an_offer(self):
        game = study.ElicitationGame(study.plan(1, 0)[0], 'text-enabled')
        output = fixtures.rec_output(game, 'bing')
        candidate = output['candidates'][0]
        candidate['ordered_record_ids'] = []
        candidate['message'] = 'Targeted discovery questions'
        response = game.response(output, 'bing')
        self.assertEqual(response['records'], [])
        self.assertNotIn('predicted_own_purchased_ids', response)
        self.assertGreater(game.select(output, 'bing')['predicted_own_revenue_cents'], 0)
        with self.assertRaises(ValueError): game.select(output, 'bing', response)
        rival = fixtures.rec_output(game, 'google')['candidates'][0]
        candidate['predicted_own_purchased_ids'] = rival['predicted_own_purchased_ids']
        candidate['predicted_own_revenue_cents'] = rival['predicted_own_revenue_cents']
        with self.assertRaises(ValueError): game.select(output, 'bing')

    def test_complete_mock_study_and_archived_replay(self):
        def invoke(role, prompt, args, directory, prefix, version, *, schema_file, **kwargs):
            payload = fixtures.info(prompt)
            if role == 'disclosure': output = fixtures.plan_output()
            elif role == 'followup': output = fixtures.plan_output(True)
            elif role == 'buyer': output = fixtures.buyer_output(payload['observed_history'])
            else:
                self.assertIn('No-regret and fictitious-play inspired response selection', prompt)
                case = study.plan(1, 0)[0]
                self.assertNotIn('true_private_user_preferences', payload)
                self.assertNotIn('observed_history', payload)
                self.assertTrue(all(r['provider'] == payload['provider'] for r in payload['own_catalog']))
                output = fixtures.rec_output(study.ElicitationGame(case, 'text-enabled'), payload['provider'])
                if payload['round'] == 1:
                    output['candidates'][0]['ordered_record_ids'] = []
                    output['candidates'][0]['message'] = 'Targeted discovery questions'
                else:
                    self.assertEqual(payload['own_prior_public_response']['records'], [])
                    self.assertNotIn('RECOMMENDER_PROSE_'+('google' if payload['provider'] == 'bing' else 'bing'), prompt)
            directory.mkdir()
            (directory/'input.md').write_text(prompt)
            study.engine.write_json(directory/'output.json', output)
            (directory/'events.jsonl').write_text('{"type":"turn.completed"}\n')
            meta = {'status': 'completed', 'harness': args.harness, 'harness_version': version,
                    'model_requested': args.model, 'reasoning_effort_requested': args.effort,
                    'output_schema_sha256': study.engine.sha(schema_file.read_bytes())}
            for file, key in [('input.md', 'input_sha256'), ('output.json', 'output_sha256'), ('events.jsonl', 'events_sha256')]:
                meta[key] = study.engine.sha((directory/file).read_bytes())
            study.engine.write_json(directory/'manifest.json', meta)
            return output
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)/'study'
            argv = ['run_study.py', '--harness', 'codex', '--model', 'fixture', '--effort', 'medium',
                    '--run-id', 'fixture', '--output-dir', str(out)]
            with patch('sys.argv', argv), patch.object(study.engine.runtime, 'invoke', side_effect=invoke), patch.object(study.engine.subprocess, 'check_output', return_value='fixture-version'), contextlib.redirect_stdout(io.StringIO()):
                study.main()
            meta = study.engine.read(out/'manifest.json')
            self.assertEqual(meta['status'], 'completed')
            self.assertEqual(meta['analysis_id'], study.CONFIG['analysis_id'])
            self.assertEqual(len(meta['cases']), 1)
            self.assertFalse((out/'comparisons.json').exists())
            self.assertTrue((out/'outcomes.json').exists())
            verifier = study.engine.runtime.load_module('strategic_learning_verifier', HERE/'verify_runs.py')
            self.assertEqual(verifier.verify(out), {'status': 'completed', 'cases': 1, 'completed_cases': 1})
            stages = list(out.glob('*/text-enabled/**/input.md'))
            self.assertEqual(len(stages), 7)
            self.assertEqual(sum('No-regret and fictitious-play inspired response selection' in p.read_text() for p in stages), 4)


if __name__ == '__main__':
    unittest.main()
