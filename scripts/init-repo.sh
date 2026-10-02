#!/bin/bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh"
[[ $# == 1 ]] || fail 'Usage: ./scripts/init-repo.sh /absolute/path/to/existing/repo'
[[ -d $1 ]] || fail 'Target directory does not exist.'
target="$(cd -- "$1" && pwd -P)"
[[ $target != "$BOOTSTRAP_ROOT" ]] || fail 'Choose a project repo, not the bootstrap itself.'
command -v jq >/dev/null 2>&1 || { load_brew || fail 'Homebrew is missing.'; }
command -v jq >/dev/null 2>&1 || fail 'jq is missing. Run bootstrap.sh first.'
# Existing project instructions always win; never overwrite them.
if [[ -e "$target/AGENTS.md" || -L "$target/AGENTS.md" ]]; then
  printf 'Preserved existing AGENTS.md. Merge templates/AGENTS.md manually.\n'
else
  cp "$BOOTSTRAP_ROOT/templates/AGENTS.md" "$target/AGENTS.md"
  printf 'Created %s/AGENTS.md\n' "$target"
fi
mkdir -p "$target/.omp"
config="$target/.omp/mcp.json"
if [[ -e $config || -L $config ]]; then
  printf 'Preserved existing .omp/mcp.json. Add CKG manually (docs/MANUAL.md).\n'
else
  # JSON serialization handles paths with spaces, quotes, and backslashes.
  jq -n --arg repo "$target" '{mcpServers: {ckg: {type: "stdio", command: "ckg", args: ["mcp", $repo, "--compact"]}}}' > "$config"
  printf 'Created %s\n' "$config"
fi
# These contain agent logs/state or a generated local index.
ignore_backed_up=0
for entry in '.ckg/' '.omp/sessions/' '.omp/logs/'; do
  if ! grep -Fqx "$entry" "$target/.gitignore" 2>/dev/null; then
    if [[ $ignore_backed_up == 0 && -e "$target/.gitignore" ]]; then
      backup="$(mktemp "$target/.gitignore.mac-dev-backup-XXXXXX")"
      cp -p "$target/.gitignore" "$backup"
      ignore_backed_up=1
    fi
    printf '\n%s\n' "$entry" >> "$target/.gitignore"
  fi
done
printf '\nNext: ckg index %q\nThen launch omp from that directory.\n' "$target"
