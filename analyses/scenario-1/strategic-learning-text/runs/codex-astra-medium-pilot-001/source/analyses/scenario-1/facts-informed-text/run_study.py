"""Rerun text-enabled games with explicit consideration of frozen product facts."""
import json
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
spec = importlib.util.spec_from_file_location('text_engine', HERE.parent/'recommender-text/run_study.py')
engine = importlib.util.module_from_spec(spec); spec.loader.exec_module(engine)
CONFIG = json.loads((HERE/'config.json').read_text())


class FactsGame(engine.Game):
    def __init__(self, case, mode):
        if mode != 'text-enabled':
            raise ValueError('This study reruns text-enabled games only')
        super().__init__(case, mode)

    def prompt(self, role, payload):
        original = super().prompt(role, payload)
        if role != 'recommender':
            return original
        return original.replace('\n## Game rules\n', '\n'+(HERE/'prompts/facts-use.md').read_text()+'\n## Game rules\n', 1)


def plan(replicates, seed):
    return [{**case, 'arm_order': ['text-enabled']} for case in engine.plan(replicates, seed)]


def summarize_case(case, results):
    result = {'case_id': case['pair_id'], 'condition': case['condition'], 'providers': case['providers'],
              'replicate': case['replicate'], 'display_order': case['display_order'],
              'status': 'completed' if 'text-enabled' in results else 'incomplete'}
    if 'text-enabled' in results:
        outcome = results['text-enabled']
        result['outcome'] = {k: outcome[k] for k in ('buyer_action', 'purchased_record_ids', 'purchase_value_cents',
                            'purchased_item_count', 'provider_revenue_cents', 'unique_returned_count', 'buyer_reason')}
    return result


def source_files():
    return sorted(set([*engine.source_files(), Path(__file__), HERE/'verify_runs.py', HERE/'run.sh',
                       HERE/'config.json', HERE/'prompts/facts-use.md', REPO/'tests/test_facts_informed_text.py']))


def main():
    engine.main(config=CONFIG, game_type=FactsGame, make_plan=plan, compare=summarize_case, get_sources=source_files)


if __name__ == '__main__':
    main()
