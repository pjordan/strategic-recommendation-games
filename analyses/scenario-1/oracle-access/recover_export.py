"""Recover a successful model answer rejected by the original warning filter; no model call."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('runner', HERE / 'run_model.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_directory')
    args = parser.parse_args()
    directory = Path(args.run_directory)
    manifest = json.loads((directory/'manifest.json').read_text())
    if manifest['status'] != 'failed' or manifest['exit_code'] != 0:
        raise ValueError('Recovery requires an export failure after successful CLI execution')
    parsed = [json.loads(line) for line in (directory/'private/stdout.txt').read_text().splitlines() if line.strip()]
    item_types = sorted({e.get('item',{}).get('type') for e in parsed if e.get('item',{}).get('type')})
    if set(item_types)-{'agent_message','reasoning','error'}:
        raise ValueError('Unexpected tool execution')
    if any(e.get('type') in ('error','turn.failed') for e in parsed) or not any(e.get('type') == 'turn.completed' for e in parsed):
        raise ValueError('Model turn did not succeed')
    messages = [e['item']['text'] for e in parsed if e.get('type') == 'item.completed' and e.get('item',{}).get('type') == 'agent_message']
    output = messages[-1]
    result = json.loads(output)
    runner.validate_decision(result, manifest['provider'])
    events = [e for e in parsed if e.get('type') in ('turn.started','turn.completed') or (e.get('type') == 'item.completed' and e.get('item',{}).get('type') == 'agent_message')]
    runner.screen(output);runner.screen(json.dumps(events))
    (directory/'output.json').write_text(output,encoding='utf-8')
    (directory/'events.jsonl').write_text(''.join(json.dumps(e,ensure_ascii=False)+'\n' for e in events),encoding='utf-8')
    manifest['initial_export_status'] = {'status':manifest['status'],'failure':manifest.pop('failure')}
    manifest['status'] = 'completed'
    manifest['output_origin'] = 'Exact final agent_message text recovered from raw CLI events after the first exporter rejected a tool-disable warning; no model rerun or answer editing.'
    manifest['postprocessor_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    manifest['observed_item_types'] = item_types
    manifest['harness_warnings'] = [e['item'].get('message','') for e in parsed if e.get('item',{}).get('type') == 'error']
    manifest['usage'] = [e.get('usage') for e in parsed if e.get('type') == 'turn.completed']
    manifest['output_sha256'] = hashlib.sha256(output.encode()).hexdigest()
    manifest['events_sha256'] = hashlib.sha256((directory/'events.jsonl').read_bytes()).hexdigest()
    manifest['event_projection'] = 'Public final message, turn status and usage; session IDs, reasoning summaries and raw diagnostics excluded.'
    runner.screen(json.dumps(manifest))
    runner.write_json(directory/'manifest.json',manifest)
    print(json.dumps({'run_id':manifest['run_id'],'selected_action':result['selected_action'],'purchase_value_cents':result['purchase_value_cents']}))


if __name__ == '__main__':
    main()
