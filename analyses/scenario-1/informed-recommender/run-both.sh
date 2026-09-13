#!/usr/bin/env bash
# Runs separate Bing and Google games with the same named harness/model settings.
set -euo pipefail
analysis_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
run_label="${1:?Usage: bash run-both.sh UNIQUE_LABEL [harness/model options]}"
shift
if [[ ! "$run_label" =~ ^[a-zA-Z0-9._-]+$ ]]; then
  echo 'Use a portable run label.' >&2
  exit 2
fi
if [[ "$#" -eq 0 ]]; then
  set -- --harness codex --codex-version 0.154.0 --model gpt-6-astra --effort medium
fi
for provider in bing google; do
  bash "$analysis_dir/run.sh" "$@" --provider "$provider" \
    --run-id "$run_label-$provider" --output-dir "local-runs/$run_label-$provider"
done
