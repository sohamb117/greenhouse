#!/bin/bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh"
DRY_RUN=0
if [[ ${1:-} == --dry-run && $# == 1 ]]; then DRY_RUN=1
elif [[ $# != 0 ]]; then fail 'Usage: install-omp-pet.sh [--dry-run]'; fi
release="$(cat "$BOOTSTRAP_ROOT/config/omp-pet.release")"
[[ $release =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || fail 'config/omp-pet.release must contain a published vX.Y.Z tag.'
version="${release#v}"
package="github:sohamb117/omp-pet#$release"
# The pinned plugin owns release download/checksum/signature/cache handling.
install_app='const { ensurePetApp } = await import(process.argv[1]); console.log(await ensurePetApp());'
if [[ $DRY_RUN == 1 ]]; then
  run mise -C "$HOME" exec github:can1357/oh-my-pi -- omp plugin install "$package"
  log '[dry-run] Read installed omp-pet path from omp plugin list --json.'
  run mise -C "$HOME" exec -- bun -e "$install_app" '<installed-plugin-path>/extension/installer.ts'
  exit 0
fi
[[ $(uname -s) == Darwin ]] || fail 'OMP Pet requires macOS.'
if [[ $(uname -m) != arm64 || $(sysctl -in sysctl.proc_translated 2>/dev/null || true) == 1 ]]; then
  log 'SKIP OMP Pet: published app requires native Apple Silicon. No source-build fallback.'
  exit 0
fi
load_brew || fail 'Homebrew is missing. Run bootstrap.sh first.'
for tool in mise jq; do command -v "$tool" >/dev/null 2>&1 || fail "Missing $tool. Run bootstrap.sh first."; done
MISE_AUTO_INSTALL=0 mise -C "$HOME" exec github:can1357/oh-my-pi -- omp --version >/dev/null || fail 'Missing mise-managed OMP. Run bootstrap.sh first.'
plugins="$(mise -C "$HOME" exec github:can1357/oh-my-pi -- omp plugin list --json)"
existing="$(printf '%s' "$plugins" | jq -c '[.npm[]? | select(.name == "omp-pet")] | first // empty')"
if [[ -z "$existing" ]]; then
  mise -C "$HOME" exec github:can1357/oh-my-pi -- omp plugin install "$package"
  plugins="$(mise -C "$HOME" exec github:can1357/oh-my-pi -- omp plugin list --json)"
  existing="$(printf '%s' "$plugins" | jq -c '[.npm[]? | select(.name == "omp-pet")] | first // empty')"
fi
[[ -n "$existing" ]] || fail 'OMP Pet installation did not produce a discoverable plugin.'
linked="$(printf '%s' "$existing" | jq -r '.path // empty')"
installed_version="$(printf '%s' "$existing" | jq -r '.version // .manifest.version // empty')"
enabled="$(printf '%s' "$existing" | jq -r '.enabled != false')"
if [[ $installed_version != "$version" || $enabled != true || ! -f "$linked/extension/installer.ts" ]]; then
  log "Existing OMP Pet plugin preserved at $linked (version $installed_version)."
  printf 'To select the release explicitly, use OMP plugin controls, then run: mise -C %q exec github:can1357/oh-my-pi -- omp plugin install %q\n' "$HOME" "$package"
  exit 0
fi
# Bun executes the release plugin's installer only; no compilation or model calls.
# It honors OMP_PET_APP/development-app overrides and reuses the app cache offline.
mise -C "$HOME" exec -- bun -e "$install_app" "$linked/extension/installer.ts"
printf '\nIn OMP: /reload-plugins, then /pet show. No app was launched by setup.\n'
