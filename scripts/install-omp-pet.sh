#!/bin/bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh"
DRY_RUN=0
if [[ ${1:-} == --dry-run && $# == 1 ]]; then DRY_RUN=1
elif [[ $# != 0 ]]; then fail 'Usage: install-omp-pet.sh [--dry-run]'; fi
# Discover the newest published release on each invocation. The resolved tag
# selects its matching plugin/app for this run; no tag is stored in this repo.
install_app='const { ensurePetApp } = await import(process.argv[1]); console.log(await ensurePetApp());'
if [[ $DRY_RUN == 1 ]]; then
  log '[dry-run] Query GitHub releases/latest; install github:sohamb117/omp-pet#<latest-release-tag>.'
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
if [[ -n "$existing" ]]; then
  linked="$(printf '%s' "$existing" | jq -r '.path // empty')"
  enabled="$(printf '%s' "$existing" | jq -r '.enabled != false')"
  if [[ $enabled != true ]]; then
    log 'OMP Pet is disabled; enable it explicitly through OMP plugin controls.'
    exit 0
  fi
  # Preserve explicitly linked/custom sources; update official GitHub installs.
  source_file="${linked%/node_modules/omp-pet}/package.json"
  source_spec=''
  if [[ -f $source_file ]]; then
    source_spec="$(jq -r '.dependencies["omp-pet"] // empty' "$source_file")"
  fi
  case "$source_spec" in
    github:sohamb117/omp-pet|github:sohamb117/omp-pet\#*|https://github.com/sohamb117/omp-pet|https://github.com/sohamb117/omp-pet\#*) ;;
    *) log "Custom OMP Pet source preserved at $linked; select the official release through OMP plugin controls to receive updates."; exit 0 ;;
  esac
fi
release="$(curl --fail --show-error --silent --location --proto '=https' --tlsv1.2 \
  --connect-timeout 15 --max-time 60 --retry 2 \
  https://api.github.com/repos/sohamb117/omp-pet/releases/latest \
  | jq -er 'select(.draft == false and .prerelease == false) | .tag_name')"
[[ $release =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || fail 'Latest OMP Pet release must have a stable vX.Y.Z tag.'
version="${release#v}"
package="github:sohamb117/omp-pet#$release"
installed_version="$(printf '%s' "$existing" | jq -r '.version // .manifest.version // empty')"
if [[ -z "$existing" || $installed_version != "$version" ]]; then
  mise -C "$HOME" exec github:can1357/oh-my-pi -- omp plugin install "$package"
  plugins="$(mise -C "$HOME" exec github:can1357/oh-my-pi -- omp plugin list --json)"
  existing="$(printf '%s' "$plugins" | jq -c '[.npm[]? | select(.name == "omp-pet")] | first // empty')"
fi
[[ -n "$existing" ]] || fail 'OMP Pet installation did not produce a discoverable plugin.'
linked="$(printf '%s' "$existing" | jq -r '.path // empty')"
installed_version="$(printf '%s' "$existing" | jq -r '.version // .manifest.version // empty')"
[[ $installed_version == "$version" && -f "$linked/extension/installer.ts" ]] || fail 'OMP Pet plugin does not match the latest release or is missing its installer.'
# Bun executes the release plugin's installer only; no compilation or model calls.
# It honors OMP_PET_APP/development-app overrides and reuses the app cache offline.
mise -C "$HOME" exec -- bun -e "$install_app" "$linked/extension/installer.ts"
printf '\nIn OMP: /reload-plugins, then /pet show. No app was launched by setup.\n'
