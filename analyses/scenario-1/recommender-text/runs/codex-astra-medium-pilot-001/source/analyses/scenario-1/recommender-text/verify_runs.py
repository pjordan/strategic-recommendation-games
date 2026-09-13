"""Verify trusted study archives offline using their checked, recorded sources."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def verify(directory):
    directory = directory.resolve()
    meta = json.loads((directory/'manifest.json').read_text())
    with tempfile.TemporaryDirectory(prefix='text-study-replay-') as temporary:
        root = Path(temporary)
        for rel, digest in meta['source_sha256'].items():
            path = Path(rel)
            if path.is_absolute() or '..' in path.parts:
                raise ValueError('Invalid archived source path')
            source = (directory/'source'/path).resolve()
            if (directory/'source').resolve() not in source.parents:
                raise ValueError('Source escapes archive')
            data = source.read_bytes()
            if hashlib.sha256(data).hexdigest() != digest:
                raise ValueError('Archived source hash mismatch')
            target = root/path; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)
        shutil.copytree(REPO/'scenarios', root/'scenarios')
        script = root/HERE.relative_to(REPO)/'run_study.py'
        result = subprocess.check_output([sys.executable, '-B', str(script), '--verify', str(directory)], text=True)
        return json.loads(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directories', nargs='*', type=Path)
    args = parser.parse_args()
    directories = args.directories or sorted((HERE/'runs').iterdir())
    print(json.dumps([{'run_id': p.name, **verify(p)} for p in directories], indent=2))
