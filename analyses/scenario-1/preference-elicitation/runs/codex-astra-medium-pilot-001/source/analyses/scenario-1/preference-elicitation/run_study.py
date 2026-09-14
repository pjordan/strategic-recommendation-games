"""Two-round sales discovery with truthful, strategic buyer answers."""
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
spec = importlib.util.spec_from_file_location('learning_base', HERE.parent/'strategic-learning-text/run_study.py')
base = importlib.util.module_from_spec(spec); spec.loader.exec_module(base)
engine = base.engine
CONFIG = json.loads((HERE/'config.json').read_text())
summarize_case = base.summarize_case


def plan(replicates, seed):
    return [case for case in base.plan(replicates, seed)
            if case['condition'] == 'two-round-strategic-disclosure']


class ElicitationGame(base.StrategicLearningGame):
    def prompt(self, role, payload):
        original = super().prompt(role, payload)
        section = ('discovery' if payload['round'] == 1 else 'final-offer') if role == 'recommender' else role
        if section == 'buyer':
            return original
        return original.replace('\n## Game rules\n', '\n'+(HERE/'prompts'/(section+'.md')).read_text()+'\n## Game rules\n', 1)

    def select(self, output, provider, prior=None):
        if prior is not None:
            return super().select(output, provider, prior)
        # Discovery forecasts concern eventual sales, not immediate availability.
        # Only response() materializes the selected ordered_record_ids as cards.
        runtime = engine.runtime
        runtime.check_schema(output, self.schema('recommender'))
        catalog = {r['record_id']: r for r in self.catalog[provider]}
        candidates = output['candidates']
        if len({c['candidate_id'] for c in candidates}) != len(candidates):
            raise ValueError('Duplicate candidate IDs')
        if len({runtime.text_json([c['ordered_record_ids'], c['message']]) for c in candidates}) != len(candidates):
            raise ValueError('Duplicate response candidates')
        if not any(not c['ordered_record_ids'] for c in candidates):
            raise ValueError('Missing empty-list response candidate')
        for c in candidates:
            runtime.check_ids(c['ordered_record_ids'], catalog)
            action = 'purchase' if c['predicted_buyer_choice'] in ('own_provider', 'mixed_bundle') else 'decline'
            runtime.check_purchase(action, c['predicted_own_purchased_ids'], c['predicted_own_revenue_cents'], catalog, enforce_budget=False)
        chosen = [c for c in candidates if c['candidate_id'] == output['selected_candidate_id']]
        if len(chosen) != 1 or chosen[0]['preference_rank'] != min(c['preference_rank'] for c in candidates):
            raise ValueError('Recommender selected response disagrees with ranking')
        return chosen[0]


def source_files():
    return sorted(set([*base.source_files(), Path(__file__), HERE/'verify_runs.py', HERE/'run.sh',
                       HERE/'config.json', *sorted((HERE/'prompts').glob('*.md')), REPO/'tests/test_preference_elicitation.py']))


def main():
    engine.main(config=CONFIG, game_type=ElicitationGame, make_plan=plan, compare=summarize_case, get_sources=source_files)


if __name__ == '__main__':
    main()
