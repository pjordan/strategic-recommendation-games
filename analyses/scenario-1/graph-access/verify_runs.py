"""Replay trusted graph-access audits using their recorded sources, offline."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]


def verify(directory,repo=REPO):
    directory=directory.resolve();meta=json.loads((directory/'manifest.json').read_text())
    for rel,digest in meta['source_sha256'].items():
        path=Path(rel)
        if path.is_absolute() or '..' in path.parts:raise ValueError('Unsafe source path')
        source=(directory/'source'/path).resolve()
        if (directory/'source').resolve() not in source.parents:raise ValueError('Source escapes archive')
        if hashlib.sha256(source.read_bytes()).hexdigest()!=digest:raise ValueError('Source checksum differs')
    entry='analyses/scenario-1/graph-access/run_analysis.py'
    if entry not in meta['source_sha256']:raise ValueError('Missing replay entry')
    result=subprocess.check_output([sys.executable,'-B',str(directory/'source'/entry),'--repo',str(repo),'--verify-current',str(directory)],text=True)
    return json.loads(result)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('directories',nargs='*',type=Path);args=parser.parse_args()
    print(json.dumps([{'run_id':p.name,**verify(p)} for p in args.directories or sorted((HERE/'runs').iterdir())],indent=2))
