"""Offline equivalence checks against recorded games; no harness is launched."""
import contextlib
import copy
import importlib.util
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
CONDITIONS = ('informed-recommender', 'competing-recommenders',
              'strategic-disclosure', 'two-round-strategic-disclosure')


def load_verifier(condition):
    path = ROOT/'analyses/scenario-1'/condition/'verify_runs.py'
    spec = importlib.util.spec_from_file_location('verifier', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def completed_run(verifier):
    return next(p for p in sorted((verifier.HERE/'runs').iterdir())
                if json.loads((p/'manifest.json').read_text())['status'] == 'completed')


def harness_result(harness, output, failure=None):
    """Emulate only the external process, exercising real parsing and writing."""
    def run(argv, *, input, text, capture_output, cwd, env):
        assert {p.name for p in cwd.iterdir()} == {'schema.json'}
        assert input and text and capture_output
        if harness == 'codex':
            assert 'OPENAI_API_KEY' not in env and 'CODEX_API_KEY' not in env
            (cwd/'output.json').write_text(json.dumps(output, ensure_ascii=False)+'\n')
            events = [{'type': 'turn.started'},
                      {'type': 'item.completed', 'item': {'type': 'reasoning', 'text': 'private'}},
                      {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': 'result'}},
                      {'type': 'turn.completed', 'usage': {'input_tokens': 1}}]
            if failure == 'tool':
                events.insert(1, {'type': 'item.completed', 'item': {'type': 'command_execution'}})
            if failure == 'incomplete':
                events.pop()
            stdout = '\n'.join(json.dumps(e) for e in events)
        else:
            result = {'structured_output': output, 'modelUsage': {'fixture-model': {}},
                      'usage': {'input_tokens': 1}, 'is_error': failure == 'model_error'}
            if failure == 'result_fallback':
                result.pop('structured_output')
                result['result'] = json.dumps(output)
            stdout = json.dumps(result)
        return subprocess.CompletedProcess(argv, 1 if failure == 'exit' else 0, stdout, '')
    return run


class RuntimeChecks(unittest.TestCase):
    def test_all_archived_games_replay_and_match_current_code(self):
        for condition in CONDITIONS:
            verifier = load_verifier(condition)
            for run in sorted((verifier.HERE/'runs').iterdir()):
                with self.subTest(condition=condition, run=run.name):
                    # Both paths validate exact actor prompts, schemas, cards,
                    # transcripts and outcomes, not just aggregate spending.
                    self.assertEqual(verifier.verify(run),
                                     verifier.verify(run, implementation='current'))

    def test_executor_matches_archived_implementations(self):
        for condition in CONDITIONS:
            verifier = load_verifier(condition)
            fixture = completed_run(verifier)
            output = json.loads((fixture/'buyer/output.json').read_text())

            def compare(directory, *, game, HERE, check_source=True):
                for harness in ('codex', 'claude'):
                    with self.subTest(condition=condition, harness=harness), tempfile.TemporaryDirectory() as temp:
                        args = SimpleNamespace(harness=harness, model='fixture-model', effort='medium')
                        manifests = []
                        for name, runner in [('recorded', game), ('current', verifier.game)]:
                            stage = Path(temp)/name/'buyer'
                            stage.parent.mkdir()
                            with patch.object(subprocess, 'run', side_effect=harness_result(harness, output)):
                                self.assertEqual(runner.invoke('buyer', 'Fixed input', args, stage, [harness], 'fixture-version'), output)
                            meta = json.loads((stage/'manifest.json').read_text())
                            for key in ('started_at', 'completed_at', 'elapsed_seconds'):
                                meta.pop(key)
                            manifests.append(meta)
                        self.assertEqual(manifests[0], manifests[1])
                        for file in ('input.md', 'output.json', 'events.jsonl'):
                            self.assertEqual((Path(temp)/'recorded/buyer'/file).read_bytes(),
                                             (Path(temp)/'current/buyer'/file).read_bytes())
            verifier.replay.verify(fixture, verifier.game, compare)

    def test_executor_rejects_failures_and_keeps_failure_manifest(self):
        verifier = load_verifier(CONDITIONS[0])
        output = json.loads((completed_run(verifier)/'buyer/output.json').read_text())
        for harness, failure, message in [('codex', 'tool', 'Tool or unexpected'),
                                         ('codex', 'incomplete', 'did not complete'),
                                         ('codex', 'exit', 'exited unsuccessfully'),
                                         ('claude', 'model_error', 'Claude reported'),
                                         ('claude', 'schema', 'fields differ'),
                                         ('codex', 'screen', 'local path')]:
            with self.subTest(harness=harness, failure=failure), tempfile.TemporaryDirectory() as temp:
                bad = copy.deepcopy(output)
                if failure == 'schema':
                    bad['unexpected'] = True
                if failure == 'screen':
                    bad['selected_outcome_reason'] = 'file://'+'private-detail'
                stage = Path(temp)/'buyer'
                args = SimpleNamespace(harness=harness, model='fixture-model', effort='medium')
                with patch.object(subprocess, 'run', side_effect=harness_result(harness, bad, failure)):
                    with self.assertRaisesRegex(ValueError, message):
                        verifier.game.invoke('buyer', 'Fixed input', args, stage, [harness], 'fixture-version')
                meta = json.loads((stage/'manifest.json').read_text())
                self.assertEqual(meta['status'], 'failed')
                self.assertIn('completed_at', meta)
                self.assertFalse((stage/'events.jsonl').exists())
                self.assertFalse((stage/'output.json').exists())

    def test_claude_result_fallback(self):
        verifier = load_verifier(CONDITIONS[0])
        output = json.loads((completed_run(verifier)/'buyer/output.json').read_text())
        with tempfile.TemporaryDirectory() as temp:
            args = SimpleNamespace(harness='claude', model='fixture-model', effort='medium')
            with patch.object(subprocess, 'run', side_effect=harness_result('claude', output, 'result_fallback')):
                self.assertEqual(verifier.game.invoke('buyer', 'Fixed input', args, Path(temp)/'buyer', ['claude'], 'fixture-version'), output)

    def test_new_run_snapshots_shared_dependencies_and_replays(self):
        verifier = load_verifier(CONDITIONS[0])
        fixture = completed_run(verifier)
        outputs = iter(json.loads((fixture/role/'output.json').read_text()) for role in ('recommender', 'buyer'))
        provider = json.loads((fixture/'manifest.json').read_text())['provider']
        def run(argv, **kwargs):
            return harness_result('codex', next(outputs))(argv, **kwargs)
        def version(argv, **kwargs):
            return 'fixture-version' if argv[-1] == '--version' else ('0'*40 if 'rev-parse' in argv else '')
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)/'run'
            argv = ['run_game.py', '--provider', provider, '--harness', 'codex',
                    '--model', 'fixture-model', '--effort', 'medium', '--run-id', 'offline-fixture',
                    '--output-dir', str(out)]
            with patch('sys.argv', argv), patch.object(subprocess, 'run', side_effect=run), patch.object(subprocess, 'check_output', side_effect=version), contextlib.redirect_stdout(io.StringIO()):
                verifier.game.main()
            meta = json.loads((out/'manifest.json').read_text())
            self.assertEqual(meta['status'], 'completed')
            self.assertIn('tools/analysis_runtime.py', meta['source_sha256'])
            self.assertIn('tools/analysis_replay.py', meta['source_sha256'])
            self.assertEqual(verifier.verify(out), verifier.verify(out, implementation='current'))

    def test_corrupt_archive_rejected_before_import(self):
        verifier = load_verifier(CONDITIONS[0])
        fixture = completed_run(verifier)
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)/'run'
            shutil.copytree(fixture, out)
            meta = json.loads((out/'manifest.json').read_text())
            source = out/'source'/next(iter(meta['source_sha256']))
            source.write_text('raise AssertionError("Corrupt archive was executed")\n')
            with self.assertRaisesRegex(ValueError, 'Archived source hash mismatch'):
                verifier.verify(out)
            meta['source_sha256'] = {'../escape.py': 'invalid'}
            with self.assertRaisesRegex(ValueError, 'Invalid archived source path'):
                verifier.replay.archived_sources(out, meta)


if __name__ == '__main__':
    unittest.main()
