# Portable macOS developer bootstrap

A reusable setup for Soham's canonical LLM-native engineering stack. `STACK.md` records the canonical stack with OrbStack and the subsequent `omp-pet` addition; `docs/STACK-ORIGINAL.md` preserves the full source message from **GPUI Rewrite Scope**. This package installs workstation tools and language tooling; project libraries stay in their language's dependency files.

## On a fresh Mac

Install from a Git checkout. Open Terminal as your normal user. If Git is unavailable, run `xcode-select --install`, finish the Apple Command Line Tools dialog, then continue:

```sh
mkdir -p ~/Documents/code
git clone https://github.com/sohamb117/greenhouse.git ~/Documents/code/mac-dev-bootstrap
cd ~/Documents/code/mac-dev-bootstrap
./scripts/bootstrap.sh --dry-run
./scripts/bootstrap.sh
```

If you already have this checkout, use it directly instead of cloning over it. HTTPS cloning does not require GitHub SSH keys.

If Apple Command Line Tools are missing, setup opens Apple's installer and stops. Finish that dialog and rerun. The Homebrew installer may ask for your Mac password. Run from a native Apple Silicon terminal on ARM Macs; Intel Macs use `/usr/local`. Use a macOS release supported by the current Homebrew packages and app vendors; the current OrbStack cask requires macOS 14 or newer.

Open a new terminal after setup, then:

```sh
./scripts/doctor.sh
```

Complete [manual setup](docs/MANUAL.md): GitHub login and Git identity, project credentials, OMP provider/model selection, opening OrbStack for first-time setup and showing OMP Pet, and Greptile onboarding in each chosen repository.

## Options

```sh
./scripts/bootstrap.sh --cli-only    # Skip kitty, Zed, OrbStack apps and OMP Pet app/plugin
./scripts/bootstrap.sh --extras      # Add lazygit, direnv and ShellCheck
./scripts/bootstrap.sh --data-tools  # Add latest Postgres, SQLite, DuckDB and Valkey binaries
./scripts/bootstrap.sh --dry-run --extras --data-tools
```

`--cli-only` skips OrbStack while retaining Docker CLI/Compose/Buildx; install or use an existing container engine separately. Full setup installs OrbStack but leaves first launch to you. Native data packages are optional and setup does not launch their services. Project libraries, cloud accounts and hosted infrastructure are documented rather than provisioned.

## What installs where

| Layer | Manager / configuration |
|---|---|
| Workstation CLIs, OrbStack, apps | Homebrew; `Brewfile` and companion Brewfiles |
| OMP | mise GitHub backend; `github:can1357/oh-my-pi` exposes the native `omp` binary |
| Bun, Go, Rust, mbx | mise; `mise.toml` copied into a global config fragment |
| Latest Node and Greptile, TypeScript LSP, Pyright | mise; Node is compatibility tooling, Bun is the JS project default |
| Latest stable CPython and project environments | uv; no global project libraries |
| OMP Pet | `scripts/install-omp-pet.sh`; latest release plugin plus prebuilt app cached under `~/Library/Application Support/OMP Pet/apps/<version>/` |
| CKG | cargo-binstall, newest crate release; may compile when no binary is available |
| zsh integration | Small managed blocks in `.zprofile` and `.zshrc` |
| Worktrunk defaults | Created only when user config is absent |
| Shared OMP defaults | User/profile `config.yml` (missing keys merged), `AGENTS.md` (managed block), and `mcp.json` (CKG added only if absent) |
| Agent instructions | Shared OMP instructions apply automatically in every project; `templates/AGENTS.md` remains available for project-specific facts or other harnesses |

Homebrew can bring its own Go/Rust/Python dependencies. Project versions still come from mise or uv. Follow existing repo lockfiles and tool versions.

## Credentials

No secret-management app or CLI is installed. Use OMP's `/login` for supported providers and the project's existing credential source for API keys and cloud access. Provide required environment variables only to the relevant process; keep secret values out of tracked files, shell rc files and logs. See [manual setup](docs/MANUAL.md#credentials) for the lightweight workflow.

## Shared defaults in every OMP project

OMP automatically reads the active user directory's `config.yml`, `AGENTS.md` and `mcp.json`. Default-profile files live in `~/.omp/agent/`; named profiles use their own agent directories. Bootstrap merges missing settings, preserves existing values/auth/model selections, backs up changed files, and adds a managed shared-instructions block without replacing your other instructions. Existing CKG entries and MCP enable/disable choices are preserved.

The user-level CKG entry runs `ckg mcp . --compact`, with the process cwd supplied by OMP. Launch from the intended checkout/worktree and index it with `ckg index "$PWD"`; no per-project setup or absolute machine path is needed for the defaults. Project settings/instructions/MCP entries can override shared behavior. See [manual setup](docs/MANUAL.md) for profiles and precedence.

## Optional project starter

```sh
./scripts/init-repo.sh "$HOME/Documents/code/my-project"
cd "$HOME/Documents/code/my-project"
ckg index "$PWD"
omp
```

This creates `AGENTS.md` and a project `.omp/mcp.json` for CKG when absent, and adds local index/log/session paths to `.gitignore`. It preserves existing agent instructions and MCP config; merge the starter manually in that case. Each worktree needs an index and an MCP entry pointing to its own directory. The current MCP entry has an absolute path: regenerate or edit it when moving the checkout to a new Mac. See [manual setup](docs/MANUAL.md) for the MCP format.

Fill in the project facts at the top of the starter: purpose, directories, exact install/check commands, services and environment names. These are project-specific and cannot be guessed by a workstation setup.

## Re-running and updating

Rerun `bootstrap.sh` after interruption. To update this checkout, commit/stash your local edits as appropriate, run `git pull --ff-only`, then rerun setup. Homebrew metadata is refreshed and selected packages/apps are upgraded on every setup run; package cleanup is never run. Configuration uses atomic writes; unchanged managed files are left alone. Changed files receive adjacent `.mac-dev-backup-<UTC timestamp>` copies. Existing OMP settings remain authoritative while missing defaults are merged; existing Worktrunk settings are preserved. Shell source blocks are replaced in place without replacing the rest of your rc files. `ZDOTDIR`, `XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `DOCKER_CONFIG`, `PI_CODING_AGENT_DIR` and `CARGO_HOME` are respected where relevant.

All bootstrap-managed tools track the latest stable releases. Setup runs `brew update` and upgrade-enabled bundles, installs/upgrades mise tools with `@latest`, resolves the newest stable CPython download from the updated uv catalog, refreshes CKG without a fixed crate version, and queries GitHub's latest published Pet release. Repeated setup keeps settings stable while refreshing software; no release tag is checked into this package.

Existing user/project mise overrides can still take precedence over the managed fragment. Check `mise config` and `mise ls` and change an older override to `latest` if you want that configuration to follow the workstation default. Existing application repositories keep their own dependency requirements and lockfiles; setup does not rewrite their source or databases. A new Postgres major is installed through Homebrew's `postgresql` alias; migrate existing database data separately using the project's procedure.

Rerun `./scripts/bootstrap.sh` to refresh the selected tools; include `--extras` or `--data-tools` for those optional groups. Review OMP settings after an upgrade. To refresh CKG alone, use `mise exec -- cargo binstall --no-confirm --force --disable-strategies quick-install ckg`.

To refresh copied config only:

```sh
./scripts/configure.sh
```

To refresh OMP Pet, run `./scripts/install-omp-pet.sh`; it resolves the newest published GitHub release each time. Fresh setup installs the GitHub plugin and invokes its exported `ensurePetApp()` through Bun to fetch/check the matching prebuilt app, without launching it. Reruns reuse the plugin and app cache. Older official plugin installs are updated; disabled/custom plugin sources are preserved. Release lookup failure stops the update before changing the installed plugin. Existing source checkouts remain untouched. `OMP_PET_APP` remains available for an explicit app override. Native Apple Silicon is currently required for releases; Intel/Rosetta setup skips Pet without a source-build fallback.

For non-interactive agents, use `mise exec -- COMMAND` inside the project or put mise shims on PATH. Do not rely on `.zshrc` being read by background apps. Zed launched from a terminal inherits that terminal's environment; configure its project language settings if a GUI launch uses different binaries.

## Small agent log helper

`agent-run COMMAND ...` retains complete stdout/stderr locally by SHA-256, prints a compact status and log path, and includes the last 80 lines on failure. It preserves the original exit status. This supplies the stack's persistent full-output workflow without an extension:

```sh
agent-run mise exec -- cargo nextest run
agent-run uv run pytest
```

Logs live under `${XDG_STATE_HOME:-$HOME/.local/state}/mac-dev-bootstrap/tool-results`. There is no automatic deletion; remove old logs when no longer needed. Avoid including secrets in logged output. Streaming dev servers and interactive commands should be run directly.

## Verification

The included checks exercise configuration preservation, repeat runs, unusual directory names and command exit status, plus shell/config syntax. They do not install the stack or authenticate accounts:

```sh
uv run --no-project --python python3 python -m unittest discover -s tests -v
```

The original delivery was also checked against current upstream installation documentation. See [sources](docs/SOURCES.md) and [validation](docs/VALIDATION.md).

Installation and updates use Git. The optional `scripts/package.sh` helper exports an archive for storage or sharing; it is not used by installation.

## Rollback

Remove the managed source blocks from your `.zprofile`/`.zshrc`, then remove the `mac-dev-bootstrap` shell folder, `mise/conf.d/50-mac-dev-bootstrap.toml` and `~/.local/bin/agent-run` if you no longer want them. Restore a changed file from its adjacent backup when appropriate. Remove only the OMP managed instructions block and newly added default/MCP keys you no longer want, restoring adjacent backups as appropriate. Preserve other OMP settings and instructions. Worktrunk config was created only when missing; remove it only if you have not since customized it. The Docker config change appends Homebrew's CLI plugin directory; remove just that entry if needed. Restore existing settings rather than deleting whole config directories. OrbStack engine data is separate; stop it through the app when appropriate and preserve its disks/volumes. Existing Colima installations and data are left intact. For OMP Pet, use OMP's plugin controls before removing unwanted cached app versions. Existing source checkouts are separate and preserved. Installed packages remain until explicitly uninstalled.
