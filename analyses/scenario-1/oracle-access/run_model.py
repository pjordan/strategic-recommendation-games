"""Run one independent oracle buyer assessment with a named CLI/model/effort."""
import argparse
import hashlib
import importlib.util
import json
import os
import platform
import re
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SCENARIO = REPO / 'scenarios/scenario-1'
spec = importlib.util.spec_from_file_location('scenario', REPO / 'tools/scenario.py')
scenario = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scenario)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def build_prompt(provider):
    scenario.validate(SCENARIO)
    records = scenario.load_records(provider, SCENARIO)
    public = (SCENARIO / 'public_context.md').read_text(encoding='utf-8')
    private = (SCENARIO / 'private/user_preferences.md').read_text(encoding='utf-8')
    template = (HERE / 'prompts/buyer.md').read_text(encoding='utf-8')
    return (template + '\n## Shared background\n\n' + public + '\n## Private user brief\n\n' + private
            + '\n## Complete frozen recommendation records\n\n'
            + json.dumps({'provider': provider, 'record_count': len(records), 'records': records}, ensure_ascii=False, separators=(',', ':')) + '\n')


def command(harness, model, effort, schema_path, output_path):
    if harness == 'codex':
        args = ['codex', 'exec', '--ignore-user-config', '--ignore-rules', '--ephemeral', '--skip-git-repo-check',
                '--sandbox', 'read-only', '--json', '--color', 'never', '--model', model,
                '-c', 'model_reasoning_effort=' + json.dumps(effort), '-c', 'approval_policy="never"',
                '-c', 'project_doc_max_bytes=0', '-c', 'web_search="disabled"',
                '--output-schema', str(schema_path), '--output-last-message', str(output_path)]
        for feature in ['apps','plugins','hooks','memories','multi_agent','shell_tool','unified_exec','code_mode','code_mode_host','browser_use','browser_use_external','computer_use','in_app_browser','view_image','image_generation','skill_search','workspace_dependencies']:
            args.extend(['--disable', feature])
        return args + ['-']
    return ['claude', '--print', '--safe-mode', '--setting-sources', '', '--tools', '', '--no-chrome',
            '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}', '--disable-slash-commands',
            '--no-session-persistence', '--model', model, '--effort', effort, '--output-format', 'json',
            '--json-schema', schema_path.read_text(encoding='utf-8')]


def validate_decision(result, provider):
    records = {r['record_id']: r for r in scenario.load_records(provider, SCENARIO)}
    if result['provider'] != provider:
        raise ValueError('Wrong provider')
    def check_choice(action, ids, price):
        if len(ids) != len(set(ids)) or not set(ids) <= set(records):
            raise ValueError('Invalid selected record IDs')
        if action == 'decline':
            if ids or price != 0:
                raise ValueError('Decline must have no records and zero price')
        elif not ids or sum(records[r]['displayed_price_cents'] for r in ids) != price:
            raise ValueError('Purchase arithmetic mismatch')
    check_choice(result['selected_action'], result['selected_record_ids'], result['purchase_value_cents'])
    if result['selected_action'] == 'purchase' and result['purchase_value_cents'] > 80000:
        raise ValueError('Selected purchase exceeds scenario budget')
    candidates = result['candidates']
    if len(candidates) < 5 or not any(c['action'] == 'decline' for c in candidates):
        raise ValueError('Candidate set omits required alternatives')
    for candidate in candidates:
        check_choice(candidate['action'], candidate['record_ids'], candidate['displayed_total_cents'])
    chosen = [c for c in candidates if c['action'] == result['selected_action'] and c['record_ids'] == result['selected_record_ids']]
    if not chosen or min(c['preference_rank'] for c in chosen) != min(c['preference_rank'] for c in candidates):
        raise ValueError('Selected outcome does not match the highest-ranked candidate')


def screen(text):
    patterns = [r'/(?:Users|home|private|tmp|Volumes)/[^\s"<>]+', r'file://', r'(?<![A-Za-z])[A-Za-z]:\\', r'Bearer\s+\S+']
    if any(re.search(p, text, re.I) for p in patterns):
        raise ValueError('Possible local path or credential in public output; inspect private logs before exporting')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--harness', choices=['codex','claude'], required=True)
    parser.add_argument('--model', required=True, help='Exact CLI model identifier; no fallback substitution')
    parser.add_argument('--effort', required=True)
    parser.add_argument('--provider', choices=['bing','google'], required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--codex-version', help='Use an exact npm @openai/codex version through npx, without replacing the installed CLI')
    parser.add_argument('--dry-run', action='store_true', help='Build exact input and command manifest without a model call')
    args = parser.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9._-]+', args.run_id):
        parser.error('run-id must be a portable identifier')
    out = Path(args.output_dir).resolve()
    if out.exists():
        parser.error('output-dir already exists; use a new directory to preserve earlier runs')
    out.mkdir(parents=True)
    prompt = build_prompt(args.provider)
    (out/'input.md').write_text(prompt, encoding='utf-8')
    prefix = [args.harness]
    if args.codex_version:
        if args.harness != 'codex' or not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', args.codex_version):
            parser.error('codex-version requires harness codex and an exact numeric version')
        prefix = ['npx', '--yes', '--package', '@openai/codex@' + args.codex_version, 'codex']
    version = subprocess.check_output(prefix + ['--version'], text=True).strip()
    (out/'runner-source.py').write_bytes(Path(__file__).read_bytes())
    manifest = {
        'run_id': args.run_id, 'run_type': 'independent_oracle_buyer_assessment',
        'harness': args.harness, 'harness_version': version, 'cli_package_version': args.codex_version, 'model_requested': args.model,
        'model_resolved': None, 'model_resolution_note': 'Unknown unless the harness response reports an exact model; an alias may change server-side.',
        'reasoning_effort_requested': args.effort, 'reasoning_effort_observed': None,
        'temperature': None, 'seed': None, 'sampling_note': 'Not set by these CLI adapters; do not infer temperature=0 or deterministic sampling.',
        'provider': args.provider, 'scenario_version': '1.1.0',
        'scenario_manifest_sha256': sha((SCENARIO/'manifest.sha256').read_bytes()),
        'prompt_template_sha256': sha((HERE/'prompts/buyer.md').read_bytes()),
        'input_sha256': sha(prompt.encode()), 'output_schema_sha256': sha((HERE/'output-schema.json').read_bytes()),
        'runner_sha256': sha(Path(__file__).read_bytes()),
        'repository_commit_at_start': subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip(),
        'repository_dirty_at_start': bool(subprocess.check_output(['git','-C',str(REPO),'status','--porcelain'],text=True).strip()),
        'python_version': platform.python_version(), 'os_family': platform.system(),
        'context_isolation': 'Fresh process and empty temporary working directory; no previous conversation or analyst baseline supplied.',
        'system_prompt': 'Harness built-in prompt; not overridden or exported. Harness versions and managed policies may differ.',
        'tools_policy': 'Tools disabled where CLI supports it; any observed tool execution invalidates the run.',
        'started_at': datetime.now(timezone.utc).isoformat(), 'status': 'prepared',
    }
    # Public argv uses symbolic paths; runtime paths never enter the manifest.
    manifest['command_argv'] = command(args.harness,args.model,args.effort,HERE/'output-schema.json',Path('OUTPUT_JSON'))
    manifest['command_argv'] = prefix + manifest['command_argv'][1:]
    manifest['command_argv'] = [x.replace(str(HERE/'output-schema.json'),'OUTPUT_SCHEMA_JSON') for x in manifest['command_argv']]
    if args.dry_run:
        manifest['status'] = 'dry_run_not_executed'
        write_json(out/'manifest.json',manifest)
        print('Prepared exact input and command; no model call.')
        return
    env = os.environ.copy()
    if args.harness == 'codex':
        # This experiment uses the existing subscription login, not an API-key override.
        env.pop('OPENAI_API_KEY',None); env.pop('CODEX_API_KEY',None)
    start = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='oracle-run-') as directory:
        cwd = Path(directory)
        (cwd/'schema.json').write_bytes((HERE/'output-schema.json').read_bytes())
        argv = command(args.harness,args.model,args.effort,cwd/'schema.json',cwd/'output.json')
        argv = prefix + argv[1:]
        run = subprocess.run(argv,input=prompt,text=True,capture_output=True,cwd=cwd,env=env)
        raw = out/'private';raw.mkdir()
        (raw/'stdout.txt').write_text(run.stdout,encoding='utf-8')
        (raw/'stderr.txt').write_text(run.stderr,encoding='utf-8')
        manifest['elapsed_seconds'] = round(time.monotonic()-start,3)
        manifest['exit_code'] = run.returncode
        manifest['completed_at'] = datetime.now(timezone.utc).isoformat()
        try:
            if run.returncode:
                raise ValueError('Harness exited unsuccessfully; see ignored private logs')
            events = []
            if args.harness == 'codex':
                parsed = [json.loads(line) for line in run.stdout.splitlines() if line.strip()]
                item_types = sorted({e.get('item',{}).get('type') for e in parsed if e.get('item',{}).get('type')})
                if set(item_types)-{'agent_message','reasoning','error'}:
                    raise ValueError('Tool or unexpected item observed: '+', '.join(item_types))
                if any(e.get('type') in ('error','turn.failed') for e in parsed) or not any(e.get('type') == 'turn.completed' for e in parsed):
                    raise ValueError('Model turn did not complete successfully')
                manifest['harness_warnings'] = [e['item'].get('message','') for e in parsed if e.get('item',{}).get('type') == 'error']
                output = (cwd/'output.json').read_text(encoding='utf-8')
                result = json.loads(output)
                for event in parsed:
                    if event.get('type') in ('turn.started','turn.completed','turn.failed','error'):
                        events.append(event)
                    elif event.get('type') == 'item.completed' and event.get('item',{}).get('type') == 'agent_message':
                        events.append(event)
                manifest['usage'] = [e.get('usage') for e in parsed if e.get('type') == 'turn.completed']
                manifest['observed_item_types'] = item_types
            else:
                response = json.loads(run.stdout)
                if response.get('is_error'):
                    raise ValueError('Claude reported an error')
                result = response.get('structured_output')
                if result is None:
                    result = json.loads(response['result'])
                output = json.dumps(result,ensure_ascii=False,indent=2)+'\n'
                models = list(response.get('modelUsage',{}))
                manifest['model_resolved'] = models[0] if len(models)==1 else None
                manifest['model_usage_reported'] = models
                manifest['usage'] = response.get('usage')
                manifest['tool_use_verification'] = 'Tools disabled by --tools; JSON result does not independently expose every internal event.'
                events = [{'type':'result','result':result}]
            validate_decision(result,args.provider)
            screen(output);screen(json.dumps(events));screen(json.dumps(manifest))
            (out/'output.json').write_text(output,encoding='utf-8')
            (out/'events.jsonl').write_text(''.join(json.dumps(e,ensure_ascii=False)+'\n' for e in events),encoding='utf-8')
            manifest['output_sha256'] = sha(output.encode())
            manifest['events_sha256'] = sha((out/'events.jsonl').read_bytes())
            manifest['event_projection'] = 'Public final messages, turn status and usage only; session IDs, reasoning summaries and raw diagnostics excluded. Ignored private logs retain raw CLI output locally.'
            manifest['status'] = 'completed'
        except Exception as error:
            manifest['status'] = 'failed'
            manifest['failure'] = str(error)
            write_json(out/'manifest.json',manifest)
            raise
    write_json(out/'manifest.json',manifest)
    print(json.dumps({'run_id':args.run_id,'status':manifest['status'],'selected_action':result['selected_action'],'purchase_value_cents':result['purchase_value_cents']}))


if __name__ == '__main__':
    main()
