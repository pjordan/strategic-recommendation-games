#!/usr/bin/env bash
set -euo pipefail
analysis_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 -B "$analysis_dir/run_game.py" "$@"
