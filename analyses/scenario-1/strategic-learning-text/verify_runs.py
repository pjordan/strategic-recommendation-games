"""Replay trusted strategic-learning instruction studies from their recorded sources, offline."""
import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
spec = importlib.util.spec_from_file_location('archive_verifier', HERE.parent/'recommender-text/verify_runs.py')
archive = importlib.util.module_from_spec(spec); spec.loader.exec_module(archive)


def verify(directory):
    return archive.verify(directory, script_relative=HERE.relative_to(REPO)/'run_study.py')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directories', nargs='*', type=Path)
    args = parser.parse_args()
    paths = args.directories or sorted((HERE/'runs').iterdir())
    print(json.dumps([{'run_id': p.name, **verify(p)} for p in paths], indent=2))
