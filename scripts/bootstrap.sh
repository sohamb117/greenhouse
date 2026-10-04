#!/bin/bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh"
DRY_RUN=0
CLI_ONLY=0
EXTRAS=0
DATA_TOOLS=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --cli-only) CLI_ONLY=1 ;;
    --extras) EXTRAS=1 ;;
    --data-tools) DATA_TOOLS=1 ;;
    --help|-h)
      printf 'Usage: ./scripts/bootstrap.sh [--dry-run] [--cli-only] [--extras] [--data-tools]\n'
      exit 0 ;;
    *) fail "Unknown option: $1" ;;
  esac
  shift
done
export DRY_RUN
[[ $(uname -s) == Darwin ]] || fail 'This bootstrap supports macOS only.'
[[ $EUID -ne 0 ]] || fail 'Run as your normal Mac user, not with sudo.'
if [[ $(sysctl -in sysctl.proc_translated 2>/dev/null || true) == 1 ]]; then
  fail 'Run this from a native Apple Silicon terminal, outside Rosetta.'
fi
if [[ $DRY_RUN == 1 ]]; then
  log 'Preview only: no downloads, installs, authentication, or file writes.'
else
  if ! xcode-select -p >/dev/null 2>&1 || ! xcrun --find clang >/dev/null 2>&1; then
    xcode-select --install || true
    fail 'Finish the Apple Command Line Tools dialog, then rerun this script.'
  fi
fi
if [[ $DRY_RUN == 1 ]]; then
  log '[dry-run] If missing, install official Homebrew; load native brew shellenv.'
elif ! load_brew; then
    installer="$(mktemp -t mac-dev-homebrew)"
    trap 'rm -f "$installer"' EXIT
    curl --fail --show-error --silent --location --proto '=https' --tlsv1.2 \
      https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh -o "$installer"
    /bin/bash "$installer"
    rm -f "$installer"
    trap - EXIT
    load_brew || fail 'Homebrew was installed but could not be found.'
fi
# Refresh only the selected stack; do not remove packages or start services.
unset HOMEBREW_NO_AUTO_UPDATE HOMEBREW_BUNDLE_NO_UPGRADE
run brew update
run brew bundle install --file="$BOOTSTRAP_ROOT/Brewfile"
if [[ $CLI_ONLY == 0 ]]; then run brew bundle install --file="$BOOTSTRAP_ROOT/Brewfile.apps"; fi
if [[ $EXTRAS == 1 ]]; then run brew bundle install --file="$BOOTSTRAP_ROOT/Brewfile.optional"; fi
if [[ $DATA_TOOLS == 1 ]]; then run brew bundle install --file="$BOOTSTRAP_ROOT/Brewfile.data"; fi
log 'Configure shell, mise and Worktrunk with backups.'
if [[ $DRY_RUN == 1 ]]; then
  log '[dry-run] Resolve newest stable CPython from updated uv download metadata.'
  bootstrap_python='<latest-stable-python>'
else
  bootstrap_python="$(latest_python)"
fi
run uv python install --no-bin "$bootstrap_python"
run uv run --no-project --managed-python --python "$bootstrap_python" python "$BOOTSTRAP_ROOT/scripts/configure.py" --skip-omp
log 'Install OMP, language runtimes and agent compatibility CLIs through mise.'
# Neutral cwd avoids inheriting the bootstrap checkout as a project config.
run mise -C "$HOME" trust "${XDG_CONFIG_HOME:-$HOME/.config}/mise/conf.d/50-mac-dev-bootstrap.toml"
run mise -C "$HOME" install bun@latest github:can1357/oh-my-pi@latest node@latest go@latest rust@latest mr-boxington@latest npm:greptile@latest npm:typescript@latest npm:typescript-language-server@latest npm:pyright@latest
run mise -C "$HOME" upgrade --no-prune bun@latest github:can1357/oh-my-pi@latest node@latest go@latest rust@latest mr-boxington@latest npm:greptile@latest npm:typescript@latest npm:typescript-language-server@latest npm:pyright@latest
run mise -C "$HOME" reshim
log 'Install shared OMP settings, instructions and CKG MCP defaults.'
run mise -C "$HOME" exec -- uv run --no-project --managed-python --python "$bootstrap_python" python "$BOOTSTRAP_ROOT/scripts/configure.py" --omp-only
if [[ $CLI_ONLY == 0 ]]; then
  run "$BOOTSTRAP_ROOT/scripts/install-omp-pet.sh"
fi
log 'Install or upgrade CKG to the newest crate release, preferring binaries.'
# No PATH-based skip: an older installation must not suppress updates.
run mise -C "$HOME" exec -- cargo binstall --no-confirm --force --disable-strategies quick-install ckg
if [[ $DRY_RUN == 1 ]]; then
  run "$BOOTSTRAP_ROOT/scripts/doctor.sh" --cli-only
else
  if [[ $CLI_ONLY == 1 ]]; then
    "$BOOTSTRAP_ROOT/scripts/doctor.sh" --cli-only
  else
    "$BOOTSTRAP_ROOT/scripts/doctor.sh"
  fi
fi
log 'Setup finished. Open a new terminal, then follow docs/MANUAL.md.'
