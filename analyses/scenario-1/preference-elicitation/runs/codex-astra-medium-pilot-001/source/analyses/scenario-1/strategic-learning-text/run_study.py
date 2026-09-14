"""Rerun facts-enabled games with strategic-learning inspired instructions."""
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
spec = importlib.util.spec_from_file_location('facts_base', HERE.parent/'facts-informed-text/run_study.py')
base = importlib.util.module_from_spec(spec); spec.loader.exec_module(base)
engine = base.engine
CONFIG = json.loads((HERE/'config.json').read_text())
plan, summarize_case = base.plan, base.summarize_case


class StrategicLearningGame(base.FactsGame):
    def prompt(self, role, payload):
        original = super().prompt(role, payload)
        if role != 'recommender':
            return original
        return original.replace('\n## Game rules\n', '\n'+(HERE/'prompts/strategic-learning.md').read_text()+'\n## Game rules\n', 1)


def source_files():
    return sorted(set([*base.source_files(), Path(__file__), HERE/'verify_runs.py', HERE/'run.sh',
                       HERE/'config.json', HERE/'prompts/strategic-learning.md', REPO/'tests/test_strategic_learning_text.py']))


def main():
    engine.main(config=CONFIG, game_type=StrategicLearningGame, make_plan=plan, compare=summarize_case, get_sources=source_files)


if __name__ == '__main__':
    main()
