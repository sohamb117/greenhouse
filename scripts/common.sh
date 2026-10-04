#!/bin/bash
set -euo pipefail
BOOTSTRAP_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
log() { printf '\n%s\n' "$*"; }
fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
run() {
  if [[ ${DRY_RUN:-0} == 1 ]]; then
    printf '[dry-run]'; printf ' %q' "$@"; printf '\n'
  else
    "$@"
  fi
}
load_brew() {
  if [[ -x /opt/homebrew/bin/brew && $(uname -m) == arm64 ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv bash)"
  elif [[ -x /usr/local/bin/brew ]]; then
    eval "$(/usr/local/bin/brew shellenv bash)"
  elif command -v brew >/dev/null 2>&1; then
    eval "$(brew shellenv bash)"
  else
    return 1
  fi
}

# Resolve at invocation time, not from installed Python or a checked-in version.
latest_python() {
  uv python list --only-downloads --output-format json | jq -er '
    [.[] | select(.implementation == "cpython" and .variant == "default")
      | select(.version | test("^[0-9]+\\.[0-9]+\\.[0-9]+$"))]
    | max_by(.version | split(".") | map(tonumber)) | .version // error("No stable CPython download available")'
}
