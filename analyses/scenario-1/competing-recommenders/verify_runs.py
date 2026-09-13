"""Verify saved competing-recommender games without another model call."""
import argparse
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('competition',HERE/'run_game.py')
game=importlib.util.module_from_spec(spec);spec.loader.exec_module(game)


def verify(directory):
    meta=json.loads((directory/'manifest.json').read_text())
    game.adapter.scenario.validate_version('1.2.0')
    if meta['scenario_manifest_sha256']!=game.sha(game.adapter.scenario_manifest_path('satisfaction').read_bytes()):
        raise ValueError('Scenario manifest mismatch')
    if meta['base_scenario_manifest_sha256']!=game.sha((game.SCENARIO/'manifest.sha256').read_bytes()):
        raise ValueError('Base scenario manifest mismatch')
    for relative,digest in meta['source_sha256'].items():
        if game.sha((directory/'source'/relative).read_bytes())!=digest:
            raise ValueError('Archived source mismatch')
        if meta['status']=='completed' and game.sha((game.REPO/relative).read_bytes())!=digest:
            raise ValueError('Source changed; verify using the recorded repository version')
    if meta['status']!='completed':
        return {'run_id':meta['run_id'],'status':meta['status']}
    for relative,digest in meta['artifacts_sha256'].items():
        if game.sha((directory/relative).read_bytes())!=digest:
            raise ValueError('Artifact hash mismatch')
    recs={p:json.loads((directory/'recommenders'/p/'output.json').read_text()) for p in ('bing','google')}
    responses={p:game.materialize(recs[p],p) for p in ('bing','google')}
    if responses!=json.loads((directory/'responses.json').read_text()):
        raise ValueError('Returned responses are not the exact committed records and messages')
    buyer=json.loads((directory/'buyer/output.json').read_text())
    result=game.outcome(recs,buyer,responses,meta['display_order'])
    if result!=json.loads((directory/'outcome.json').read_text()):
        raise ValueError('Outcome/revenue attribution does not replay')
    transcript=[{'role':'user','content':(HERE/'prompts/request.md').read_text()}]
    transcript += [{'role':'recommender','provider':p,'content':responses[p]} for p in game.presentation_order(meta['display_order'])]
    transcript += [{'role':'buyer','content':buyer}]
    if transcript!=json.loads((directory/'transcript.json').read_text()):
        raise ValueError('Transcript does not replay')
    stages=[(directory/'recommenders'/p,'recommender',game.recommender_prompt(p,meta['display_order'])) for p in ('bing','google')]
    stages.append((directory/'buyer','buyer',game.buyer_prompt(responses,meta['display_order'])))
    for stage,role,prompt in stages:
        m=json.loads((stage/'manifest.json').read_text())
        if m['status']!='completed' or (stage/'input.md').read_text()!=prompt:
            raise ValueError('Actor input/status mismatch')
        for file,key in [('input.md','input_sha256'),('output.json','output_sha256'),('events.jsonl','events_sha256')]:
            if game.sha((stage/file).read_bytes())!=m[key]:
                raise ValueError('Actor artifact hash mismatch')
        if game.sha((HERE/(role+'-schema.json')).read_bytes())!=m['output_schema_sha256']:
            raise ValueError('Actor schema hash mismatch')
    return {'run_id':meta['run_id'],'status':'completed',**result}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directories',nargs='*')
    args=parser.parse_args()
    directories=list(map(Path,args.directories)) if args.directories else sorted((HERE/'runs').glob('*'))
    print(json.dumps([verify(p) for p in directories],indent=2))
