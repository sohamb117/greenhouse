#!/bin/bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh"
[[ $# == 1 ]] || fail 'Usage: package.sh /absolute/path/to/output.zip'
[[ $1 == /* && $1 == *.zip ]] || fail 'Provide an absolute .zip output path.'
mkdir -p "$(dirname -- "$1")"
# Enumerate checked-in files so credentials and untracked local files stay out.
git -C "$BOOTSTRAP_ROOT" rev-parse --is-inside-work-tree >/dev/null
uv run --no-project --python 3.13 python "$BOOTSTRAP_ROOT/scripts/package.py" "$1"
