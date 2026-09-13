"""Paired whole-game policies, actor boundaries, and full offline workflow checks."""
import copy
import contextlib
import io
import tempfile
from unittest.mock import patch
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT/'analyses/scenario-1/recommender-text'
spec = importlib.util.spec_from_file_location('text_study', HERE/'run_study.py')
study = importlib.util.module_from_spec(spec); spec.loader.exec_module(study)


def plan_output(followup=False):
    candidates = []
    for i in range(3):
        item = {'candidate_id': str(i), 'messages': {'bing': 'Bing context '+str(i), 'google': 'Google context '+str(i)},
                'preference_rank': i+1, 'disclosure_and_withholding': 'PRIVATE_PLAN',
                'anticipated_recommender_behavior': 'PRIVATE_FORECAST', 'expected_user_value_tradeoff': 'Value'}
        if followup: item['shared_record_ids'] = {'bing': [], 'google': []}
        candidates.append(item)
    return {'selected_candidate_id': '0', 'candidates': candidates, 'selection_reason': 'PRIVATE_PLAN_REASON', 'limitations': []}


def rec_output(game, provider, empty=False):
    cards = [r for r in game.catalog[provider] if r['displayed_price_cents'] and r['displayed_price_cents'] <= 80000][:2]
    candidates = []
    for i, ids in enumerate(([cards[0]['record_id']], [cards[1]['record_id']], [])):
        c = {'candidate_id': str(i), 'ordered_record_ids': ids, 'preference_rank': (1 if i == 2 else i+2) if empty else i+1,
             'strategic_justification': 'PRIVATE_REC', 'predicted_buyer_choice': 'own_provider' if ids else 'decline',
             'predicted_own_purchased_ids': ids, 'predicted_own_revenue_cents': cards[i]['displayed_price_cents'] if ids else 0}
        if game.mode == 'text-enabled': c['message'] = 'RECOMMENDER_PROSE_'+provider
        candidates.append(c)
    return {'selected_candidate_id': '2' if empty else '0', 'candidates': candidates, 'selection_reason': 'PRIVATE_REC_REASON', 'limitations': [], 'buyer_belief': 'PRIVATE_BELIEF'}


def buyer_output(history):
    record = next(r for rd in history for response in rd['responses'] for r in response['records'])
    rid, price = record['record_id'], record['displayed_price_cents']
    return {'selected_action': 'purchase', 'selected_record_ids': [rid], 'purchase_value_cents': price,
            'candidates': [{'candidate_id': 'buy', 'action': 'purchase', 'record_ids': [rid], 'displayed_total_cents': price,
                            'preference_rank': 1, 'qualification': 'qualifies', 'evidence_and_reason': 'Value'},
                           {'candidate_id': 'decline', 'action': 'decline', 'record_ids': [], 'displayed_total_cents': 0,
                            'preference_rank': 2, 'qualification': 'outside_option', 'evidence_and_reason': 'Less useful'}],
            'selected_outcome_reason': 'Value', 'strategic_response': 'Observed choices', 'material_assumptions': [], 'limitations': []}


def info(prompt):
    return json.loads(prompt.split('\n## Your information\n\n', 1)[1])


class TextStudyChecks(unittest.TestCase):
    def test_schedule_pairs_both_policies_and_counterbalances(self):
        pairs = study.plan(2, 0)
        self.assertEqual(len(pairs), 10)
        self.assertEqual(pairs, study.plan(2, 0))
        self.assertEqual(sum(p['arm_order'][0] == 'list-only' for p in pairs), 5)
        for p in pairs:
            self.assertEqual(set(p['arm_order']), set(study.MODES))
            self.assertEqual(p['display_order'], 'bing-first' if p['replicate'] == 1 else 'google-first')
        with self.assertRaises(ValueError): study.plan(0, 0)

    def test_both_arms_have_identical_frozen_information_before_actions(self):
        for pair in study.plan(1, 0):
            a, b = [study.Game(pair, mode) for mode in study.MODES]
            self.assertEqual(a.catalog, b.catalog)
            self.assertEqual(a.facts, b.facts)
            self.assertEqual(a.context, b.context)
            ra, rb = a.rules(), b.rules()
            ra.pop('communication_policy'); rb.pop('communication_policy')
            self.assertEqual(ra, rb)
            for records in a.catalog.values(): self.assertTrue(all(not r['sponsored'] for r in records))

    def test_list_only_schema_and_candidate_identity(self):
        game = study.Game(study.plan(1, 0)[0], 'list-only')
        output = rec_output(game, 'bing')
        response = game.response(output, 'bing')
        self.assertEqual(set(response), {'provider', 'records'})
        bad = copy.deepcopy(output); bad['candidates'][0]['message'] = 'Forbidden'
        with self.assertRaisesRegex(ValueError, 'fields differ'): game.response(bad, 'bing')
        bad = copy.deepcopy(output); bad['candidates'][1] = copy.deepcopy(bad['candidates'][0]); bad['candidates'][1]['candidate_id'] = '1'
        bad['candidates'][1]['strategic_justification'] = 'Different private rationale'
        with self.assertRaisesRegex(ValueError, 'Duplicate response'): game.response(bad, 'bing')

    def test_all_ten_games_information_boundaries_and_round_one_persistence(self):
        for pair in study.plan(1, 0):
            for mode in study.MODES:
                with self.subTest(pair=pair['pair_id'], mode=mode):
                    game = study.Game(pair, mode)
                    calls = []
                    def call(stage, role, prompt, schema):
                        payload = info(prompt); calls.append((stage, role, payload))
                        if role == 'disclosure': return plan_output()
                        if role == 'followup':
                            self.assertNotIn('PRIVATE_REC', prompt)
                            self.assertNotIn('PRIVATE_BELIEF', prompt)
                            return plan_output(True)
                        if role == 'recommender':
                            provider = payload['provider']
                            if game.adaptive:
                                self.assertNotIn('true_private_user_preferences', payload)
                                self.assertNotIn('PRIVATE_PLAN', prompt)
                                self.assertNotIn('PRIVATE_FORECAST', prompt)
                            else: self.assertIn('true_private_user_preferences', payload)
                            rival = 'google' if provider == 'bing' else 'bing'
                            if rival in game.catalog:
                                self.assertNotIn(game.catalog[rival][0]['record_id'], prompt)
                            self.assertTrue(all(r['provider'] == provider for r in payload['own_catalog']))
                            return rec_output(game, provider, empty=payload['round'] == 2)
                        self.assertIn('true_private_user_preferences', payload)
                        self.assertNotIn('own_frozen_product_facts', payload)
                        self.assertNotIn('PRIVATE_REC', prompt)
                        self.assertNotIn('PRIVATE_BELIEF', prompt)
                        return buyer_output(payload['observed_history'])
                    artifacts = game.run(call)
                    self.assertEqual(len(calls), (7 if game.round_count == 2 else len(game.providers)+1+int(game.adaptive)))
                    outcome = artifacts['outcome.json']
                    self.assertEqual(sum(outcome['provider_revenue_cents'].values()), outcome['purchase_value_cents'])
                    for stage, role, payload in calls:
                        if role in ('buyer', 'followup'):
                            for rd in payload['observed_history']:
                                for response in rd['responses']:
                                    self.assertEqual('message' in response, mode == 'text-enabled')
                    if game.round_count == 2:
                        self.assertTrue(all(not r['records'] for r in artifacts['responses.json'][1]['responses']))
                        self.assertEqual(outcome['purchased_item_count'], 1)
                    row = study.comparison(pair, {m: outcome for m in study.MODES})
                    self.assertFalse(row['purchase_changed'])
                    self.assertEqual(row['text_minus_list']['purchase_value_cents'], 0)
                    self.assertEqual(study.comparison(pair, {mode: outcome})['status'], 'incomplete')

    def test_complete_mock_study_replays_from_archived_sources(self):
        def invoke(role, prompt, args, directory, prefix, version, *, schema_file, **kwargs):
            payload = info(prompt)
            if role == 'disclosure': output = plan_output()
            elif role == 'followup': output = plan_output(True)
            elif role == 'buyer': output = buyer_output(payload['observed_history'])
            else:
                mode = 'text-enabled' if 'message' in study.read(schema_file)['properties']['candidates']['items']['properties'] else 'list-only'
                pair = {'providers': [payload['provider']], 'condition': 'informed-recommender', 'display_order': 'bing-first'}
                output = rec_output(study.Game(pair, mode), payload['provider'])
            directory.mkdir()
            (directory/'input.md').write_text(prompt)
            study.write_json(directory/'output.json', output)
            (directory/'events.jsonl').write_text('{"type":"turn.completed"}\n')
            meta = {'status': 'completed', 'harness': args.harness, 'harness_version': version,
                    'model_requested': args.model, 'reasoning_effort_requested': args.effort,
                    'output_schema_sha256': study.sha(schema_file.read_bytes())}
            for file, key in [('input.md', 'input_sha256'), ('output.json', 'output_sha256'), ('events.jsonl', 'events_sha256')]:
                meta[key] = study.sha((directory/file).read_bytes())
            study.write_json(directory/'manifest.json', meta)
            return output
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)/'study'
            argv = ['run_study.py', '--harness', 'codex', '--model', 'fixture', '--effort', 'medium',
                    '--run-id', 'fixture', '--output-dir', str(out)]
            with patch('sys.argv', argv), patch.object(study.runtime, 'invoke', side_effect=invoke), patch.object(study.subprocess, 'check_output', return_value='fixture-version'), contextlib.redirect_stdout(io.StringIO()):
                study.main()
            self.assertEqual(study.read(out/'manifest.json')['status'], 'completed')
            verifier = study.runtime.load_module('text_verifier', HERE/'verify_runs.py')
            self.assertEqual(verifier.verify(out), {'status': 'completed', 'pairs': 5, 'completed_pairs': 5})
            card_file = next(out.glob('*/list-only/responses.json'))
            card_file.write_text('[]\n')
            with self.assertRaisesRegex(ValueError, 'artifact hash mismatch'):
                study.verify_current(out)

    def test_cannot_forward_unobserved_rival_evidence(self):
        game = study.Game(study.plan(1, 0)[-1], 'list-only')
        responses = {p: game.response(rec_output(game, p), p) for p in game.providers}
        output = plan_output(True)
        output['candidates'][0]['shared_record_ids']['bing'] = ['NOT_OBSERVED']
        with self.assertRaisesRegex(ValueError, 'unavailable record'):
            game.validator.followups(output, {p: game.legacy_response(rs) for p, rs in responses.items()})


if __name__ == '__main__': unittest.main()
