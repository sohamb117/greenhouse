#!/bin/bash
# Standalone helper, also installed as ~/.local/bin/agent-run.
set -euo pipefail
[[ $# -gt 0 ]] || { printf 'Usage: agent-run COMMAND [ARGS...]\n' >&2; exit 2; }
store="${XDG_STATE_HOME:-$HOME/.local/state}/mac-dev-bootstrap/tool-results"
mkdir -p "$store"
temporary="$(mktemp "$store/.capture.XXXXXX")"
trap 'rm -f "$temporary"' EXIT
started=$SECONDS
status=0
"$@" > "$temporary" 2>&1 || status=$?
digest="$(shasum -a 256 "$temporary")"
digest=${digest%% *}
result="$store/$digest.log"
if [[ -e $result ]]; then rm -f "$temporary"; else mv "$temporary" "$result"; fi
chmod 600 "$result"
if [[ $status == 0 ]]; then label=PASS; else label=FAIL; fi
printf '%s — exit %s — %ss — sha256:%s\nFull output: %s\n' "$label" "$status" "$((SECONDS-started))" "$digest" "$result"
if [[ $status != 0 ]]; then tail -n 80 "$result"; fi
exit "$status"
