#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
cache_dir="${1:?Usage: bash scripts/collect_product_facts.sh CACHE_DIRECTORY OUTPUT_DIRECTORY}"
output_dir="${2:?Specify a new output directory; do not overwrite the frozen release}"
python3 tools/product_facts_collect.py --cache-dir "$cache_dir" --stage all
python3 tools/product_facts_build.py --cache-dir "$cache_dir" --output "$output_dir"
