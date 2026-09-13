"""Replay and validate saved informed-recommender games without model calls."""
import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('game', HERE/'run_game.py')
game = importlib.util.module_from_spec(spec)
spec.loader.exec_module(game)


def verify(directory):
    meta = json.loads((directory/'manifest.json').read_text())
    game.adapter.scenario.validate_version('1.2.0')
    if meta['scenario_manifest_sha256'] != game.sha(game.adapter.scenario_manifest_path('satisfaction').read_bytes()):
        raise ValueError('Scenario hash mismatch')
    if meta['base_scenario_manifest_sha256'] != game.sha((game.SCENARIO/'manifest.sha256').read_bytes()):
        raise ValueError('Base scenario hash mismatch')
    for relative, digest in meta['source_sha256'].items():
        if game.sha((directory/'source'/relative).read_bytes()) != digest:
            raise ValueError('Archived source hash mismatch')
        if meta['status'] == 'completed' and game.sha((game.REPO/relative).read_bytes()) != digest:
            raise ValueError('Source changed: verify with the recorded repository version')
    if meta['status'] != 'completed':
        return {'run_id':meta['run_id'],'status':meta['status']}
    for relative, digest in meta['artifacts_sha256'].items():
        if game.sha((directory/relative).read_bytes()) != digest:
            raise ValueError('Artifact hash mismatch')
    provider = meta['provider']
    rec = json.loads((directory/'recommender/output.json').read_text())
    response = game.materialize(rec,provider)
    if response != json.loads((directory/'response.json').read_text()):
        raise ValueError('Response is not the exact selected frozen records/message')
    buyer = json.loads((directory/'buyer/output.json').read_text())
    result = game.outcome(provider,rec,buyer,response)
    if result != json.loads((directory/'outcome.json').read_text()):
        raise ValueError('Outcome does not replay')
    expected_transcript = [{'role':'user','content':(HERE/'prompts/request.md').read_text()},
                           {'role':'recommender','content':response}, {'role':'buyer','content':buyer}]
    if json.loads((directory/'transcript.json').read_text()) != expected_transcript:
        raise ValueError('Transcript differs from selected interaction')
    for role, prompt in [('recommender',game.recommender_prompt(provider)),('buyer',game.buyer_prompt(provider,response))]:
        stage = directory/role
        m = json.loads((stage/'manifest.json').read_text())
        if m['status'] != 'completed' or (stage/'input.md').read_text() != prompt:
            raise ValueError('Role input/status mismatch')
        for file,key in [('input.md','input_sha256'),('output.json','output_sha256'),('events.jsonl','events_sha256')]:
            if game.sha((stage/file).read_bytes()) != m[key]:
                raise ValueError('Role artifact hash mismatch')
        if game.sha((HERE/(role+'-schema.json')).read_bytes()) != m['output_schema_sha256']:
            raise ValueError('Role schema mismatch')
    return {'run_id':meta['run_id'],'status':'completed',**result}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directories', nargs='*')
    args = parser.parse_args()
    directories = list(map(Path,args.directories)) if args.directories else sorted((HERE/'runs').iterdir())
    print(json.dumps([verify(p) for p in directories],indent=2))
