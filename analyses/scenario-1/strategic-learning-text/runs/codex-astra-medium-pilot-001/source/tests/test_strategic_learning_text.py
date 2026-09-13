"""The strategic-learning rerun changes only recommender instructions and keeps replay intact."""
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
HERE = ROOT/'analyses/scenario-1/strategic-learning-text'
spec = importlib.util.spec_from_file_location('strategic_learning_study', HERE/'run_study.py')
study = importlib.util.module_from_spec(spec); spec.loader.exec_module(study)


class StrategicLearningTextChecks(unittest.TestCase):
    def test_schedule_runs_only_five_text_conditions(self):
        cases = study.plan(1, 0)
        self.assertEqual(len(cases), 5)
        self.assertTrue(all(c['arm_order'] == ['text-enabled'] for c in cases))
        with self.assertRaisesRegex(ValueError, 'text-enabled'):
            study.StrategicLearningGame(cases[0], 'list-only')
        self.assertEqual(study.plan(1, 0), study.plan(1, 17))

    def test_only_recommender_instruction_changes(self):
        for case in study.plan(1, 0):
            old, new = study.base.FactsGame(case, 'text-enabled'), study.StrategicLearningGame(case, 'text-enabled')
            self.assertEqual(old.catalog, new.catalog)
            self.assertEqual(old.facts, new.facts)
            self.assertIn('Explicit consideration of product facts', new.prompt('recommender', {}))
            self.assertEqual(old.context, new.context)
            self.assertEqual(old.rules(), new.rules())
            for role in ('recommender', 'buyer', 'disclosure', 'followup'):
                self.assertEqual(old.schema(role), new.schema(role))
                before, after = old.prompt(role, {'sentinel': 'same data'}), new.prompt(role, {'sentinel': 'same data'})
                if role == 'recommender':
                    added = (HERE/'prompts/strategic-learning.md').read_text()
                    self.assertEqual(after, before.replace('\n## Game rules\n', '\n'+added+'\n## Game rules\n', 1))
                else:
                    self.assertEqual(before, after)

    def test_complete_mock_study_and_archived_replay(self):
        def invoke(role, prompt, args, directory, prefix, version, *, schema_file, **kwargs):
            payload = fixtures.info(prompt)
            if role == 'disclosure': output = fixtures.plan_output()
            elif role == 'followup': output = fixtures.plan_output(True)
            elif role == 'buyer': output = fixtures.buyer_output(payload['observed_history'])
            else:
                self.assertIn('No-regret and fictitious-play inspired response selection', prompt)
                case = {'providers': [payload['provider']], 'condition': 'informed-recommender', 'display_order': 'bing-first'}
                output = fixtures.rec_output(study.StrategicLearningGame(case, 'text-enabled'), payload['provider'])
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
            self.assertEqual(len(meta['cases']), 5)
            self.assertFalse((out/'comparisons.json').exists())
            self.assertTrue((out/'outcomes.json').exists())
            verifier = study.engine.runtime.load_module('strategic_learning_verifier', HERE/'verify_runs.py')
            self.assertEqual(verifier.verify(out), {'status': 'completed', 'cases': 5, 'completed_cases': 5})
            stages = list(out.glob('*/text-enabled/**/input.md'))
            self.assertEqual(len(stages), 18)
            self.assertEqual(sum('No-regret and fictitious-play inspired response selection' in p.read_text() for p in stages), 10)


if __name__ == '__main__':
    unittest.main()
