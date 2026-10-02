#!/bin/bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh"
load_brew || fail 'Homebrew is missing. Run bootstrap.sh first.'
exec uv run --no-project --python 3.13 python "$BOOTSTRAP_ROOT/scripts/configure.py" "$@"
