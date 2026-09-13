"""Run an offline, replayable access audit of three commerce-evidence views."""
import argparse
import importlib.util
import json
from pathlib import Path
import platform
import subprocess
import sys

HERE=Path(__file__).resolve().parent
SOURCE_ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('graph',SOURCE_ROOT/'tools/commerce_graph.py')
graph=importlib.util.module_from_spec(spec);spec.loader.exec_module(graph)
CONFIG=graph.read(HERE/'config.json')


def artifacts(repo):
    release=repo/graph.GRAPH/'versions'/graph.VERSION
    graph.validate(repo,release)
    output={};metrics=[]
    for provider in CONFIG['providers']:
        view=graph.GraphView(repo,release,role='recommender',provider=provider)
        for arm in CONFIG['arms']:
            number=0;offers=set();byte_count=0
            requests=[{'operation':'find','limit':CONFIG['page_size']}]+CONFIG['queries'][provider]
            log=[]
            for query_index,request in enumerate(requests):
                current=dict(request)
                while True:
                    result=view.query(representation=arm,**current)
                    file=f'{provider}/{arm}/responses/{number:03d}.json'
                    data=graph.pretty(result).encode();output[file]=data;byte_count+=len(data)
                    ids=[o['id'] for o in result['offers']];offers.update(ids)
                    log.append({'request':current,'response_file':file,'response_sha256':graph.sha(data),'returned_record_ids':ids})
                    number+=1
                    if query_index!=0 or result['query']['next_offset'] is None:break
                    current={**current,'offset':result['query']['next_offset']}
            output[f'{provider}/{arm}/queries.jsonl']=''.join(graph.dumps(x)+'\n' for x in log).encode()
            metrics.append({'provider':provider,'representation':arm,'queries':number,'distinct_offers':len(offers),'serialized_response_bytes':byte_count})
    # The test here is information equivalence of retrieval, not an LLM outcome.
    for provider in CONFIG['providers']:
        logs={arm:[json.loads(s) for s in output[f'{provider}/{arm}/queries.jsonl'].decode().splitlines()] for arm in CONFIG['arms']}
        reference=logs['graph']
        for arm,entries in logs.items():
            if [(e['request'],e['returned_record_ids']) for e in entries] != [(e['request'],e['returned_record_ids']) for e in reference]:
                raise ValueError('Representation changes retrieval membership or order')
            for entry,ref in zip(entries,reference):
                value=json.loads(output[entry['response_file']]);expected=json.loads(output[ref['response_file']])
                for key in ('offers','capability_status','capability_definitions','query'):
                    if value[key]!=expected[key]:raise ValueError('Shared evidence differs')
                if arm=='table':
                    if value['relationships']!=expected['graph']['edges']:raise ValueError('Flat and graph relationships differ')
                    table_nodes=value['offers']+value['claims']+value['products']+value['sources']+value['sellers']+value['capability_definitions']
                elif arm=='facts-json':
                    if value['normalization_and_identity_annotations']['relationships']!=expected['graph']['edges']:raise ValueError('Fact and graph relationships differ')
                    table_nodes=value['offers']+value['normalization_and_identity_annotations']['claims']+value['products']+value['sources']+value['sellers']+value['capability_definitions']
                else:table_nodes=expected['graph']['nodes']
                by_id={n['id']:n for n in table_nodes}
                if any(by_id.get(n['id'])!=n for n in expected['graph']['nodes']):raise ValueError('Node evidence differs')
    output['results.json']=graph.pretty({'status':'completed_access_audit','model_calls':0,'evidence_equivalence_checked':True,
                                        'metrics':metrics,'interpretation':'All views retrieve the same scoped evidence; no recommendation or purchase outcome was measured.'}).encode()
    return output


def sources():
    return [Path(__file__),HERE/'verify_runs.py',HERE/'run.sh',HERE/'config.json',HERE/'prompts/agent-access.md',SOURCE_ROOT/'tools/commerce_graph.py']


def run(repo, output, run_id):
    if output.exists():raise ValueError('Output exists; use a fresh directory')
    data=artifacts(repo)
    manifest={'analysis_id':CONFIG['analysis_id'],'version':CONFIG['version'],'run_id':run_id,
              'status':'completed_access_audit','model_calls':0,'model':None,'harness':'python-standard-library',
              'python_version':platform.python_version(),'design':CONFIG,
              'graph_manifest_sha256':graph.sha((repo/graph.GRAPH/'versions'/graph.VERSION/'manifest.json').read_bytes()),
              'source_sha256':{},'artifacts_sha256':{p:graph.sha(b) for p,b in data.items()}}
    for source in sources():
        rel=source.relative_to(SOURCE_ROOT).as_posix();manifest['source_sha256'][rel]=graph.sha(source.read_bytes())
        data['source/'+rel]=source.read_bytes()
    data['manifest.json']=graph.pretty(manifest).encode()
    for rel,value in data.items():
        target=output/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(value)
    return json.loads(data['results.json'])


def verify_current(repo, directory):
    meta=graph.read(directory/'manifest.json')
    if meta['design']!=CONFIG:raise ValueError('Configuration differs')
    if meta['graph_manifest_sha256']!=graph.sha((repo/graph.GRAPH/'versions'/graph.VERSION/'manifest.json').read_bytes()):raise ValueError('Graph version differs')
    fresh=artifacts(repo)
    if meta['artifacts_sha256']!={rel:graph.sha(data) for rel,data in fresh.items()}:raise ValueError('Audit artifact inventory differs')
    for rel,value in fresh.items():
        if graph.safe_path(directory,rel).read_bytes()!=value:raise ValueError('Audit does not replay')
    for rel,digest in meta['source_sha256'].items():
        if graph.sha(graph.safe_path(SOURCE_ROOT,rel).read_bytes())!=digest:raise ValueError('Recorded source differs')
    if meta['status']!='completed_access_audit' or meta['model_calls']!=0 or meta['model'] is not None:raise ValueError('Invalid audit status')
    return {'status':'verified','model_calls':0,'query_count':sum(m['queries'] for m in json.loads(fresh['results.json'])['metrics'])}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--repo',type=Path,default=SOURCE_ROOT)
    parser.add_argument('--output-dir',type=Path);parser.add_argument('--run-id');parser.add_argument('--verify-current',type=Path)
    args=parser.parse_args()
    if args.verify_current:result=verify_current(args.repo.resolve(),args.verify_current.resolve())
    else:
        if not args.output_dir or not args.run_id:parser.error('Provide output-dir and run-id')
        if not all(c.isalnum() or c in '._-' for c in args.run_id):parser.error('Use a portable run ID')
        result=run(args.repo.resolve(),args.output_dir.resolve(),args.run_id)
    print(graph.pretty(result),end='')


if __name__=='__main__':main()
