#!/bin/bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh"
if [[ $(uname -m) != arm64 || $(sysctl -in sysctl.proc_translated 2>/dev/null || true) == 1 ]]; then
  printf 'SKIP    OMP Pet release (native Apple Silicon only)\n'
  exit 0
fi
load_brew || fail 'Homebrew is missing.'
plugins="$(MISE_AUTO_INSTALL=0 mise -C "$HOME" exec github:can1357/oh-my-pi -- omp plugin list --json)"
plugin="$(printf '%s' "$plugins" | jq -c '[.npm[]? | select(.name == "omp-pet" and .enabled != false)] | first // empty')"
[[ -n "$plugin" ]] || fail 'OMP Pet plugin missing or disabled; run scripts/install-omp-pet.sh or inspect OMP plugin controls.'
linked="$(printf '%s' "$plugin" | jq -r '.path // empty')"
version="$(printf '%s' "$plugin" | jq -r '.version // .manifest.version // empty')"
[[ $version =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?$ ]] || fail 'Invalid OMP Pet plugin version.'
if [[ -n ${OMP_PET_APP:-} ]]; then
  app="$OMP_PET_APP"
elif [[ -x "$linked/dist/OMP Pet.app/Contents/MacOS/omp-pet" ]]; then
  app="$linked/dist/OMP Pet.app"
else
  app="$HOME/Library/Application Support/OMP Pet/apps/$version/OMP Pet.app"
fi
[[ -x "$app/Contents/MacOS/omp-pet" ]] || fail 'OMP Pet app missing; run scripts/install-omp-pet.sh or /pet install in OMP.'
printf 'OK      OMP Pet %s app and enabled plugin: %s\n' "$version" "$app"
