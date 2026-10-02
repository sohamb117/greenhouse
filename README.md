# Portable macOS developer bootstrap

A reusable setup for Soham's canonical LLM-native engineering stack. `STACK.md` records the canonical stack with OrbStack and the subsequent `omp-pet` addition; `docs/STACK-ORIGINAL.md` preserves the full source message from **GPUI Rewrite Scope**. This package installs workstation tools and language tooling; project libraries stay in their language's dependency files.

## On a fresh Mac

Copy or unzip this folder into `~/Documents/code/mac-dev-bootstrap`, open Terminal as your normal user, then:

```sh
cd ~/Documents/code/mac-dev-bootstrap
./scripts/bootstrap.sh --dry-run
./scripts/bootstrap.sh
```

If Apple Command Line Tools are missing, setup opens Apple's installer and stops. Finish that dialog and rerun. The Homebrew installer may ask for your Mac password. Run from a native Apple Silicon terminal on ARM Macs; Intel Macs use `/usr/local`. Use a macOS release supported by the current Homebrew packages and app vendors; the current OrbStack cask requires macOS 14 or newer.

Open a new terminal after setup, then:

```sh
./scripts/doctor.sh
```

Complete [manual setup](docs/MANUAL.md): GitHub login and Git identity, 1Password integration, OMP provider/model selection, opening OrbStack for first-time setup and showing OMP Pet, and Greptile onboarding in each chosen repository.

## Options

```sh
./scripts/bootstrap.sh --cli-only    # Skip kitty, Zed, 1Password, OrbStack apps and OMP Pet app/plugin
./scripts/bootstrap.sh --extras      # Add lazygit, direnv and ShellCheck
./scripts/bootstrap.sh --data-tools  # Add Postgres 17, SQLite, DuckDB and Valkey binaries
./scripts/bootstrap.sh --dry-run --extras --data-tools
```

The 1Password CLI remains in the core set. `--cli-only` skips OrbStack while retaining Docker CLI/Compose/Buildx; install or use an existing container engine separately. Full setup installs OrbStack but leaves first launch to you. Native data packages are optional and setup does not launch their services. Project libraries, cloud accounts and hosted infrastructure are documented rather than provisioned.

## What installs where

| Layer | Manager / configuration |
|---|---|
| Workstation CLIs, OMP, OrbStack, apps | Homebrew; `Brewfile` and companion Brewfiles |
| Bun, Go, Rust, mbx | mise; `mise.toml` copied into a global config fragment |
| Node 22 and Greptile, TypeScript LSP, Pyright | mise; Node is compatibility tooling, Bun is the JS project default |
| Python 3.13 and project environments | uv; no global project libraries |
| OMP Pet | `scripts/install-omp-pet.sh`; pinned source under `${XDG_DATA_HOME:-$HOME/.local/share}/mac-dev-bootstrap/omp-pet`, with an OMP-linked plugin |
| CKG | cargo-binstall, requested version 0.1.5; may compile when no binary is available |
| zsh integration | Small managed blocks in `.zprofile` and `.zshrc` |
| Worktrunk / OMP defaults | Created only when their user config is absent |
| Agent instructions | `AGENTS.md` here; `templates/AGENTS.md` is the reusable starter |

Homebrew can bring its own Go/Rust/Python dependencies. Project versions still come from mise or uv. Follow existing repo lockfiles and tool versions.

## Add the starter to a project

```sh
./scripts/init-repo.sh "$HOME/Documents/code/my-project"
cd "$HOME/Documents/code/my-project"
ckg index "$PWD"
omp
```

This creates `AGENTS.md` and a project `.omp/mcp.json` for CKG when absent, and adds local index/log/session paths to `.gitignore`. It preserves existing agent instructions and MCP config; merge the starter manually in that case. Each worktree needs an index and an MCP entry pointing to its own directory. The current MCP entry has an absolute path: regenerate or edit it when moving the checkout to a new Mac. See [manual setup](docs/MANUAL.md) for the MCP format.

Fill in the project facts at the top of the starter: purpose, directories, exact install/check commands, services and environment names. These are project-specific and cannot be guessed by a workstation setup.

## Re-running and updating

Rerun `bootstrap.sh` after interruption. Homebrew uses `--no-upgrade` and never runs package cleanup. Configuration uses atomic writes; unchanged managed files are left alone. Changed files receive adjacent `.mac-dev-backup-<UTC timestamp>` copies. Existing OMP and Worktrunk settings are preserved. Shell source blocks are replaced in place without replacing the rest of your rc files. `ZDOTDIR`, `XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `DOCKER_CONFIG`, `PI_CODING_AGENT_DIR` and `CARGO_HOME` are respected where relevant.

The mise fragment has lower priority than your existing global/project config. Check `mise config` and `mise ls` if a pre-existing version overrides it. Python remains selected by `uv run --python 3.13` or the project's `.python-version`. A rerun is convergent, but rolling selectors can resolve newer releases: this package is portable, not a byte-identical lock of Homebrew or all language binaries. CKG preserves a CLI already present on PATH.

For deliberate upgrades, use `brew update`, upgrade selected formulae/casks, and run `mise -C "$HOME" upgrade`. Pin and commit exact project versions and lockfiles when reproducibility matters. Review OMP settings after an OMP upgrade. To upgrade CKG explicitly, use `mise exec -- cargo binstall --no-confirm --disable-strategies quick-install ckg@VERSION` with your chosen release.

To refresh copied config only:

```sh
./scripts/configure.sh
```

To refresh the managed OMP Pet build after changing `config/omp-pet.rev`, run `./scripts/install-omp-pet.sh`. The helper reuses the existing build and plugin link on unchanged reruns, and refuses to reset local source edits. Existing OMP Pet plugins linked elsewhere are preserved; setup prints the command to switch them explicitly. `OMP_PET_DIR` (absolute path) and `OMP_PET_GIT_URL` can override the managed directory and clone URL.

For non-interactive agents, use `mise exec -- COMMAND` inside the project or put mise shims on PATH. Do not rely on `.zshrc` being read by background apps. Zed launched from a terminal inherits that terminal's environment; configure its project language settings if a GUI launch uses different binaries.

## Small agent log helper

`agent-run COMMAND ...` retains complete stdout/stderr locally by SHA-256, prints a compact status and log path, and includes the last 80 lines on failure. It preserves the original exit status. This supplies the stack's persistent full-output workflow without an extension:

```sh
agent-run mise exec -- cargo nextest run
agent-run uv run pytest
```

Logs live under `${XDG_STATE_HOME:-$HOME/.local/state}/mac-dev-bootstrap/tool-results`. There is no automatic deletion; remove old logs when no longer needed. Avoid including secrets in logged output. Streaming dev servers and interactive commands should be run directly.

## Verification and packaging

The included checks exercise configuration preservation, repeat runs, unusual directory names and command exit status, plus shell/config syntax. They do not install the stack or authenticate accounts:

```sh
uv run --no-project --python 3.13 python -m unittest discover -s tests -v
```

The original delivery was also checked against current upstream installation documentation. See [sources](docs/SOURCES.md) and [validation](docs/VALIDATION.md).

To create another ZIP from the current tracked file contents:

```sh
# After unzip, initialize and stage this folder if you want to repackage it:
git init -b main
git add .
./scripts/package.sh "$HOME/Downloads/mac-dev-bootstrap.zip"
```

The ZIP contains tracked package files, with executable permissions; `.git`, backups, caches and untracked files are excluded. The archive does not contain user credentials.

## Rollback

Remove the managed source blocks from your `.zprofile`/`.zshrc`, then remove the `mac-dev-bootstrap` shell folder, `mise/conf.d/50-mac-dev-bootstrap.toml` and `~/.local/bin/agent-run` if you no longer want them. Restore a changed file from its adjacent backup when appropriate. OMP/Worktrunk files were created only when missing; remove those only if you have not since customized them. The Docker config change appends Homebrew's CLI plugin directory; remove just that entry if needed. Restore existing settings rather than deleting whole config directories. OrbStack engine data is separate; stop it through the app when appropriate and preserve its disks/volumes. Existing Colima installations and data are left intact. For OMP Pet, unlink it through OMP's plugin controls before removing the managed source/app directory. Installed packages remain until explicitly uninstalled.
