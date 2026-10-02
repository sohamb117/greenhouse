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
# No upgrades or removal of packages on a rerun; no services are started.
export HOMEBREW_NO_AUTO_UPDATE=1
run brew bundle install --no-upgrade --file="$BOOTSTRAP_ROOT/Brewfile"
if [[ $CLI_ONLY == 0 ]]; then run brew bundle install --no-upgrade --file="$BOOTSTRAP_ROOT/Brewfile.apps"; fi
if [[ $EXTRAS == 1 ]]; then run brew bundle install --no-upgrade --file="$BOOTSTRAP_ROOT/Brewfile.optional"; fi
if [[ $DATA_TOOLS == 1 ]]; then run brew bundle install --no-upgrade --file="$BOOTSTRAP_ROOT/Brewfile.data"; fi
log 'Configure shell, mise, Worktrunk and OMP with backups.'
run uv python install 3.13
run uv run --no-project --python 3.13 python "$BOOTSTRAP_ROOT/scripts/configure.py"
log 'Install language runtimes and agent compatibility CLIs.'
# Neutral cwd avoids inheriting the downloaded package as a project config.
run mise -C "$HOME" trust "${XDG_CONFIG_HOME:-$HOME/.config}/mise/conf.d/50-mac-dev-bootstrap.toml"
run mise -C "$HOME" install bun node go rust mr-boxington npm:greptile npm:typescript npm:typescript-language-server npm:pyright
run mise -C "$HOME" reshim
if [[ $CLI_ONLY == 0 ]]; then
  run "$BOOTSTRAP_ROOT/scripts/install-omp-pet.sh"
fi
log 'Install CKG, preferring a release binary and allowing a source build.'
if [[ $DRY_RUN == 1 ]]; then
  run mise -C "$HOME" exec -- cargo binstall --no-confirm --disable-strategies quick-install ckg@0.1.5
else
  export PATH="${CARGO_HOME:-$HOME/.cargo}/bin:$HOME/.local/bin:$PATH"
  if command -v ckg >/dev/null 2>&1; then
    printf 'CKG already available: %s (preserved).\n' "$(command -v ckg)"
  else
    # cargo-binstall can fall back to compiling if a platform artifact is absent.
    mise -C "$HOME" exec -- cargo binstall --no-confirm --disable-strategies quick-install ckg@0.1.5
  fi
fi
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
