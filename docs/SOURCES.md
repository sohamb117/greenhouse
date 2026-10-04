# Source and installation references

OMP installation, global discovery and OMP Pet release installation checked on **2026-10-03**; the remaining sources were checked on **2026-10-02**. `docs/STACK-ORIGINAL.md` is the complete source message with ChatGPT citation markers removed. `STACK.md` reflects the user's final OrbStack and OMP Pet selections and removal of 1Password. Credentials use supported provider login or the project's existing source; no replacement secret-manager package is installed.

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
| OrbStack installation and Docker context | [Installation](https://docs.orbstack.dev/install), [Docker](https://docs.orbstack.dev/docker/) |
| OrbStack Homebrew cask and platform requirements | [Cask](https://formulae.brew.sh/cask/orbstack) |
| OrbStack personal-use plan | [Pricing](https://orbstack.dev/pricing) |
| OMP Pet release, download checks and runtime requirements | [Latest release](https://github.com/sohamb117/omp-pet/releases/latest), [Installer](https://github.com/sohamb117/omp-pet/blob/main/extension/installer.ts) |
| OMP user-level instructions | [Context files](https://github.com/can1357/oh-my-pi/blob/main/docs/context-files.md) |
| MCP subprocess project cwd | [Stdio transport](https://github.com/can1357/oh-my-pi/blob/main/packages/coding-agent/src/mcp/transports/stdio.ts) |
| Docker Compose plugin search path | [Homebrew formula](https://formulae.brew.sh/formula/docker-compose) |

Implementation choices, updated **2026-10-04**: all workstation version selectors are rolling. Homebrew updates its metadata and upgrades selected bundles (GUI casks use `greedy: true`); `postgresql` follows Homebrew's current-major alias. mise tools use `latest` and setup explicitly upgrades them without pruning older versions. uv's updated download catalog supplies the highest stable default CPython version for this platform. CKG installs the latest crate release with no fixed version argument. Project library requirements and existing lockfiles belong to their projects.

OMP uses its official mise GitHub backend with `bin = "omp"`. Pet resolves the latest published GitHub release on every install/update, then selects that release's matching plugin and runs its upstream app installer. This transient tag coordinates plugin/app versions and is never a checked-in pin. Older official installs are upgraded; disabled/custom installs are preserved. Checksums, bundle/signature checks and app caching remain the upstream installer's responsibility. A failed latest-release lookup fails before plugin changes. Bootstrap installation and updates use Git; no ZIP installation step or Pet source build is used. Workstation/account setup is separate from editing and validation.

Latest-version behavior follows [Homebrew Bundle](https://docs.brew.sh/Brew-Bundle-and-Brewfile), [mise upgrade](https://mise.jdx.dev/cli/upgrade.html), and [uv Python CLI](https://docs.astral.sh/uv/reference/cli/#uv-python-list). Available Python downloads are bundled with uv, so setup updates Homebrew's uv before resolving Python.

OMP native global settings, context and MCP discovery are documented separately. Shared instructions/settings/server defaults live in the active user/profile agent directory; project files retain their own precedence. The CKG entry uses a relative `.` argument because OMP's native stdio transport explicitly uses `config.cwd ?? getProjectDir()` for subprocesses. Named profiles are isolated, so run configuration for each profile that should receive these defaults.
