#!/bin/bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh"
load_brew || fail 'Homebrew is missing. Run bootstrap.sh first.'
exec mise -C "$HOME" exec -- uv run --no-project --managed-python --python "$(latest_python)" python "$BOOTSTRAP_ROOT/scripts/configure.py" "$@"
