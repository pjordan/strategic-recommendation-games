"""Replay trusted repository runs with their recorded sources, without model calls.

Hashes establish consistency with a run manifest, not trust in arbitrary code.
Only replay source archives from repositories you trust.
"""
import hashlib
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path


def archived_sources(directory, meta):
    """Read and check every source before any archived Python is imported."""
    source = (directory/'source').resolve()
    checked = {}
    for relative, digest in meta['source_sha256'].items():
        path = Path(relative)
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('Invalid archived source path')
        target = (source/path).resolve()
        if source not in target.parents:
            raise ValueError('Archived source escapes its directory')
        data = target.read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError('Archived source hash mismatch')
        checked[path] = data
    return checked


def verify(directory, current_game, verify_game, implementation='recorded'):
    """Separate historical replay from explicit current-code compatibility checks."""
    if implementation not in ('recorded', 'current'):
        raise ValueError('Unknown replay implementation')
    directory = Path(directory).resolve()
    meta = json.loads((directory/'manifest.json').read_text())
    sources = archived_sources(directory, meta)
    if implementation == 'current':
        # Deliberately allow changed active sources; still check the archive,
        # frozen data, actor inputs, schemas, artifacts and reconstructed results.
        return verify_game(directory, game=current_game, HERE=current_game.HERE,
                           check_source=False)
    if meta['status'] != 'completed':
        # An unfinished run has no complete interaction to reconstruct.
        return verify_game(directory, game=current_game, HERE=current_game.HERE,
                           check_source=False)
    relative_runner = (current_game.HERE/'run_game.py').relative_to(current_game.REPO)
    if relative_runner not in sources:
        raise ValueError('Archived runner is missing from source manifest')
    with tempfile.TemporaryDirectory(prefix='analysis-replay-') as temporary:
        root = Path(temporary)
        for relative, data in sources.items():
            destination = root/relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        # A private copy makes the recorded repository layout self-contained.
        # The verifier checks its pinned scenario manifests before using cards.
        shutil.copytree(current_game.REPO/'scenarios', root/'scenarios')
        spec = importlib.util.spec_from_file_location('recorded_game', root/relative_runner)
        recorded = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(recorded)
        return verify_game(directory, game=recorded, HERE=recorded.HERE)
