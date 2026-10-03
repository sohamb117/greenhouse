# Source and installation references

OMP installation, global discovery and OMP Pet release installation checked on **2026-10-03**; the remaining sources were checked on **2026-10-02**. `docs/STACK-ORIGINAL.md` is the complete source message with ChatGPT citation markers removed. `STACK.md` reflects the user's final OrbStack and OMP Pet selections.

| Tool / behavior | Primary source |
|---|---|
| Homebrew installer and platform prerequisites | [Installation](https://docs.brew.sh/Installation) |
| Brewfile and upgrade behavior | [Homebrew Bundle](https://docs.brew.sh/Brew-Bundle-and-Brewfile) |
| mise global fragments and precedence | [Configuration](https://mise.jdx.dev/configuration.html) |
| Rust components and mbx integration | [mise Rust](https://mise.jdx.dev/lang/rust.html) |
| mbx installation and setup | [mr-boxington](https://github.com/jdx/mr-boxington) |
| cargo-binstall binary/source strategies | [CLI reference](https://github.com/cargo-bins/cargo-binstall/blob/main/HELP.md) |
| OMP official mise install and other options | [Oh My Pi](https://github.com/can1357/oh-my-pi) |
| mise GitHub release backend | [GitHub backend](https://mise.jdx.dev/dev-tools/backends/github.html) |
| OMP user settings and compaction keys | [Settings](https://github.com/can1357/oh-my-pi/blob/main/docs/settings.md) |
| OMP native MCP shape | [MCP configuration](https://github.com/can1357/oh-my-pi/blob/main/docs/mcp-config.md) |
| CKG install/version example, actual CLI argument order and language scope | [CKG](https://github.com/phins-group/ckg) |
| Worktrunk zsh integration | [Shell integration](https://worktrunk.dev/shell-integration/) |
| Worktrunk worktree path template | [Configuration](https://worktrunk.dev/config/) |
| Greptile installation and human onboarding | [CLI onboarding](https://www.greptile.com/docs/code-review/cli-onboarding) |
| Greptile agent review | [CLI](https://www.greptile.com/cli) |
| uv-managed Python | [Installing Python](https://docs.astral.sh/uv/guides/install-python/) |
| 1Password integration | [CLI guide](https://www.1password.dev/cli/get-started) |
| OrbStack installation and Docker context | [Installation](https://docs.orbstack.dev/install), [Docker](https://docs.orbstack.dev/docker/) |
| OrbStack Homebrew cask and platform requirements | [Cask](https://formulae.brew.sh/cask/orbstack) |
| OrbStack personal-use plan | [Pricing](https://orbstack.dev/pricing) |
| OMP Pet release, download checks and runtime requirements | [Release](https://github.com/sohamb117/omp-pet/releases/tag/v0.1.2), [Pinned installer](https://github.com/sohamb117/omp-pet/blob/v0.1.2/extension/installer.ts) |
| OMP user-level instructions | [Context files](https://github.com/can1357/oh-my-pi/blob/main/docs/context-files.md) |
| MCP subprocess project cwd | [Stdio transport](https://github.com/can1357/oh-my-pi/blob/main/packages/coding-agent/src/mcp/transports/stdio.ts) |
| Docker Compose plugin search path | [Homebrew formula](https://formulae.brew.sh/formula/docker-compose) |

Implementation choices: OMP uses its documented mise GitHub backend with `bin = "omp"` for the native release binary. Setup installs it before the Pet helper; the helper and doctor explicitly invoke mise-managed OMP to avoid an older Homebrew CLI. Bootstrap installation and updates use a Git checkout, with no ZIP installation step. Node 22 supports Greptile/npm tools; it does not replace Bun as the JavaScript project default. Python 3.13 is a bootstrap default, not a version stated in the canonical message. CKG requests the documented 0.1.5 release and permits a source fallback on Intel. mbx is wired through the documented mise Rust option. Existing OMP settings, authentication and model choices remain personal.

OMP Pet setup uses release `v0.1.2` and its exported app installer, not a Rust source build. Release metadata and its README/installer code were checked; the published app archive's SHA-256 matches `SHA256SUMS`. The upstream installer was exercised in a temporary cache, including bundle/signature verification and a repeat with network access disabled. Installation is idempotent through the upstream versioned cache. OMP's installed plugin CLI was checked in dry-run mode; full workstation/account setup was not run. OrbStack remains the personal container-engine selection, with other engine data preserved.

OMP native global settings, context and MCP discovery are documented separately. Shared instructions/settings/server defaults live in the active user/profile agent directory; project files retain their own precedence. The CKG entry uses a relative `.` argument because OMP's native stdio transport explicitly uses `config.cwd ?? getProjectDir()` for subprocesses. Named profiles are isolated, so run configuration for each profile that should receive these defaults.
