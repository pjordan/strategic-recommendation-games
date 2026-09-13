"""Replay two-round disclosure inputs, original cards, purchase and attribution offline."""
import argparse
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('two_round_game',HERE/'run_game.py')
game=importlib.util.module_from_spec(spec);spec.loader.exec_module(game)


def read(directory, relative):
    return json.loads((directory/relative).read_text())


replay = game.runtime.load_module('analysis_replay', game.REPO/'tools/analysis_replay.py')


def verify(directory, *, implementation='recorded'):
    return replay.verify(directory, game, _verify_game, implementation)


def _verify_game(directory, *, game, HERE, check_source=True):
    meta=read(directory,'manifest.json')
    game.adapter.scenario.validate_version('1.2.0')
    if meta['scenario_manifest_sha256']!=game.sha(game.adapter.scenario_manifest_path('satisfaction').read_bytes()):
        raise ValueError('Scenario manifest mismatch')
    if meta['base_scenario_manifest_sha256']!=game.sha((game.SCENARIO/'manifest.sha256').read_bytes()):
        raise ValueError('Base scenario manifest mismatch')
    for relative,digest in meta['source_sha256'].items():
        if game.sha((directory/'source'/relative).read_bytes())!=digest:
            raise ValueError('Archived source mismatch')
        if check_source and meta['status']=='completed' and game.sha((game.REPO/relative).read_bytes())!=digest:
            raise ValueError('Source changed; verify using the recorded repository version')
    if meta['status']!='completed':
        return {'run_id':meta['run_id'],'status':meta['status']}
    for relative,digest in meta['artifacts_sha256'].items():
        if game.sha((directory/relative).read_bytes())!=digest:
            raise ValueError('Artifact hash mismatch')
    order=meta['display_order']
    disclosure=read(directory,'disclosure/output.json')
    messages=game.validate_disclosure(disclosure)['messages']
    if messages!=read(directory,'disclosures.json') or game.buyer_state(disclosure)!=read(directory,'buyer-state.json'):
        raise ValueError('Initial disclosure state mismatch')
    recs=[{p:read(directory,'round-'+str(i+1)+'/'+p+'/output.json') for p in ('bing','google')} for i in range(2)]
    rounds=[]
    for i in range(2):
        rs={p:game.materialize(recs[i][p],p,rounds[0][p] if i else None) for p in ('bing','google')}
        if rs!=read(directory,'round-'+str(i+1)+'-responses.json'):
            raise ValueError('Committed round response mismatch')
        rounds.append(rs)
    if rounds!=read(directory,'responses.json'):
        raise ValueError('Full response history mismatch')
    followup=read(directory,'followup/output.json')
    addressed=game.followups(followup,rounds[0])
    if addressed!=read(directory,'followups.json') or game.followup_state(followup,rounds[0])!=read(directory,'followup-state.json'):
        raise ValueError('Addressed follow-up evidence or state mismatch')
    buyer=read(directory,'buyer/output.json')
    result=game.outcome(recs,buyer,rounds,disclosure,followup,order)
    if result!=read(directory,'outcome.json'):
        raise ValueError('Outcome/revenue attribution does not replay')
    if game.transcript(disclosure,followup,rounds,buyer,order)!=read(directory,'transcript.json'):
        raise ValueError('Transcript does not replay')
    stages=[(directory/'disclosure','disclosure',game.disclosure_prompt(order)),
            (directory/'followup','followup',game.followup_prompt(rounds[0],disclosure,order)),
            (directory/'buyer','buyer',game.buyer_prompt(rounds,disclosure,followup,order))]
    for p in ('bing','google'):
        stages.append((directory/'round-1'/p,'recommender',game.recommender_prompt(p,messages[p],order)+'\n## Current stage: ROUND 1\n\nAnticipate the adaptive follow-up and final second-round replies.\n'))
        stages.append((directory/'round-2'/p,'recommender',game.second_recommender_prompt(p,messages[p],recs[0][p],addressed[p],order)))
    for stage,role,prompt in stages:
        m=read(stage,'manifest.json')
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
    parser.add_argument('--implementation', choices=['recorded', 'current'], default='recorded',
                        help='Recorded-source replay (default) or current-code compatibility check')
    args=parser.parse_args()
    directories=list(map(Path,args.directories)) if args.directories else sorted((HERE/'runs').glob('*'))
    print(json.dumps([verify(p, implementation=args.implementation) for p in directories],indent=2))
