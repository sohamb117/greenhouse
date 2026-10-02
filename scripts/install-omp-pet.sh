#!/bin/bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh"
DRY_RUN=0
if [[ ${1:-} == --dry-run && $# == 1 ]]; then DRY_RUN=1
elif [[ $# != 0 ]]; then fail 'Usage: install-omp-pet.sh [--dry-run]'; fi
source_dir="${OMP_PET_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/mac-dev-bootstrap/omp-pet}"
source_url="${OMP_PET_GIT_URL:-https://github.com/sohamb117/omp-pet.git}"
revision="$(cat "$BOOTSTRAP_ROOT/config/omp-pet.rev")"
[[ $source_dir == /* ]] || fail 'OMP_PET_DIR must be an absolute path.'
[[ $revision =~ ^[0-9a-f]{40}$ ]] || fail 'config/omp-pet.rev must contain a full commit SHA.'
if [[ $DRY_RUN == 1 ]]; then
  run git clone --no-checkout --depth 1 "$source_url" "$source_dir"
  run git -C "$source_dir" fetch --depth 1 origin "$revision"
  run git -C "$source_dir" checkout --detach "$revision"
  run mise -C "$HOME" exec -- uv run --no-project --python 3.13 /bin/sh "$source_dir/scripts/build-app.sh"
  run omp install "$source_dir"
  exit 0
fi
[[ $(uname -s) == Darwin ]] || fail 'OMP Pet requires macOS.'
load_brew || fail 'Homebrew is missing. Run bootstrap.sh first.'
for tool in git mise uv omp jq; do command -v "$tool" >/dev/null 2>&1 || fail "Missing $tool. Run bootstrap.sh first."; done
if [[ ! -e "$source_dir" ]]; then
  mkdir -p "$(dirname -- "$source_dir")"
  git clone --no-checkout --depth 1 "$source_url" "$source_dir"
  new_checkout=1
else
  new_checkout=0
  [[ -d "$source_dir/.git" ]] || fail "Preserving existing non-repository directory: $source_dir"
  [[ $(git -C "$source_dir" remote get-url origin) == "$source_url" ]] || fail 'Existing OMP Pet checkout has a different origin; preserved.'
  [[ -z $(git -C "$source_dir" status --porcelain) ]] || fail 'Existing OMP Pet checkout has local changes; preserved. Resolve them before rerunning.'
fi
source_dir="$(cd -- "$source_dir" && pwd -P)"
if [[ $new_checkout == 1 || $(git -C "$source_dir" rev-parse HEAD) != "$revision" ]]; then
  git -C "$source_dir" fetch --depth 1 origin "$revision"
  git -C "$source_dir" checkout --detach "$revision"
fi
app="$source_dir/dist/OMP Pet.app/Contents/MacOS/omp-pet"
stamp="$source_dir/.git/mac-dev-bootstrap-built-revision"
if [[ ! -x "$app" || ! -r "$stamp" || $(cat "$stamp") != "$revision" ]]; then
  # Upstream build-app.sh invokes python3/tomllib; uv supplies Python >=3.11.
  # mise supplies Rust and the configured Cargo/mbx wrapper.
  mise -C "$HOME" exec -- uv run --no-project --python 3.13 /bin/sh "$source_dir/scripts/build-app.sh"
  [[ -x "$app" ]] || fail 'OMP Pet build did not produce the expected app executable.'
  printf '%s\n' "$revision" > "$stamp"
else
  log 'OMP Pet app is already built at the pinned revision.'
fi
plugins="$(omp plugin list --json)"
linked="$(printf '%s' "$plugins" | jq -r '[.npm[]? | select(.name == "omp-pet") | .path] | first // empty')"
if [[ -n "$linked" ]]; then
  if [[ -d "$linked" && $(cd -- "$linked" && pwd -P) == "$source_dir" ]]; then
    log 'OMP Pet is already linked; plugin configuration preserved.'
  else
    log "Existing OMP Pet plugin preserved at $linked."
    printf 'To switch to the managed build, run: omp install %q\n' "$source_dir"
  fi
else
  omp install "$source_dir"
fi
printf '\nIn OMP: /reload-plugins, then /pet show. No app was launched by setup.\n'
