#!/bin/bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh"
CLI_ONLY=0
if [[ ${1:-} == --cli-only && $# == 1 ]]; then CLI_ONLY=1
elif [[ $# != 0 ]]; then fail 'Usage: doctor.sh [--cli-only]'; fi
load_brew || fail 'Homebrew is missing.'
export PATH="${XDG_DATA_HOME:-$HOME/.local/share}/mise/shims:$HOME/.local/bin:${CARGO_HOME:-$HOME/.cargo}/bin:$PATH"
missing=0
for tool in brew mise git gh rg fd fzf zoxide atuin bat jq xh ast-grep watchexec hyperfine lefthook wt cargo-binstall cargo-nextest uv ruff ty biome golangci-lint sqlc gopls dlv tofu caddy docker ckg; do
  if command -v "$tool" >/dev/null 2>&1; then
    printf 'OK      %-26s %s\n' "$tool" "$(command -v "$tool")"
  else
    printf 'MISSING %s\n' "$tool"; missing=1
  fi
done
for tool in bun node go rustc cargo mbx greptile tsc typescript-language-server pyright rust-analyzer; do
  if MISE_AUTO_INSTALL=0 mise -C "$HOME" exec -- which "$tool" >/dev/null 2>&1; then
    printf 'OK      %s (mise)\n' "$tool"
  else
    printf 'MISSING %s (mise)\n' "$tool"; missing=1
  fi
done
if MISE_AUTO_INSTALL=0 mise -C "$HOME" exec github:can1357/oh-my-pi -- omp --version; then
  printf 'OK      OMP (mise GitHub backend)\n'
else
  printf 'MISSING OMP (mise GitHub backend)\n'; missing=1
fi
if python_path="$(uv python find --managed-python cpython 2>/dev/null)"; then
  "$python_path" --version
else
  printf 'MISSING uv-managed CPython\n'; missing=1
fi
if ! docker compose version; then missing=1; fi
if ! docker buildx version; then missing=1; fi
if [[ $CLI_ONLY == 0 ]]; then
  for app in kitty Zed OrbStack; do
    if [[ -d "/Applications/$app.app" || -d "$HOME/Applications/$app.app" ]]; then
      printf 'OK      %s.app\n' "$app"
    else
      printf 'MISSING %s.app\n' "$app"; missing=1
    fi
  done
  if ! "$BOOTSTRAP_ROOT/scripts/doctor-omp-pet.sh"; then missing=1; fi
fi
printf '\nAccounts and the container engine are manual follow-ups: docs/MANUAL.md\n'
exit "$missing"
