# Source and installation references

Checked on **2026-10-02**. `docs/STACK-ORIGINAL.md` is the complete source message with ChatGPT citation markers removed. `STACK.md` applies the user's later Colima and OMP Pet selections.

| Tool / behavior | Primary source |
|---|---|
| Homebrew installer and platform prerequisites | [Installation](https://docs.brew.sh/Installation) |
| Brewfile and upgrade behavior | [Homebrew Bundle](https://docs.brew.sh/Brew-Bundle-and-Brewfile) |
| mise global fragments and precedence | [Configuration](https://mise.jdx.dev/configuration.html) |
| Rust components and mbx integration | [mise Rust](https://mise.jdx.dev/lang/rust.html) |
| mbx installation and setup | [mr-boxington](https://github.com/jdx/mr-boxington) |
| cargo-binstall binary/source strategies | [CLI reference](https://github.com/cargo-bins/cargo-binstall/blob/main/HELP.md) |
| OMP official tap and install options | [Oh My Pi](https://github.com/can1357/oh-my-pi) |
| OMP user settings and compaction keys | [Settings](https://github.com/can1357/oh-my-pi/blob/main/docs/settings.md) |
| OMP native MCP shape | [MCP configuration](https://github.com/can1357/oh-my-pi/blob/main/docs/mcp-config.md) |
| CKG install/version example, actual CLI argument order and language scope | [CKG](https://github.com/phins-group/ckg) |
| Worktrunk zsh integration | [Shell integration](https://worktrunk.dev/shell-integration/) |
| Worktrunk worktree path template | [Configuration](https://worktrunk.dev/config/) |
| Greptile installation and human onboarding | [CLI onboarding](https://www.greptile.com/docs/code-review/cli-onboarding) |
| Greptile agent review | [CLI](https://www.greptile.com/cli) |
| uv-managed Python | [Installing Python](https://docs.astral.sh/uv/guides/install-python/) |
| 1Password integration | [CLI guide](https://www.1password.dev/cli/get-started) |
| Colima VM installation/startup | [Colima](https://github.com/abiosoft/colima) |
| OMP Pet build, plugin and runtime requirements | [Pinned source](https://github.com/sohamb117/omp-pet/tree/37425540df16b37160f6bfb76632e6606696c906) |
| Docker Compose plugin search path | [Homebrew formula](https://formulae.brew.sh/formula/docker-compose) |

Implementation choices: OMP uses its official Homebrew tap instead of a separate Bun-global install, so the stable `omp` path also works for background agents. Node 22 supports Greptile/npm tools; it does not replace Bun as the JavaScript project default. Python 3.13 is a bootstrap default, not a version stated in the canonical message. CKG requests the documented 0.1.5 release and permits a source fallback on Intel. mbx is wired through the documented mise Rust option. Existing OMP settings, authentication and model choices remain personal.

OMP Pet installation was verified from the repository's README, `package.json`, `scripts/build-app.sh` and `extension/commands.ts`, and the installed OMP 18.4.10 CLI's `install --help`, `plugin list --json` and local-install dry run. The pet uses a local plugin link and a native source build, not an invented Homebrew package. Colima replaces OrbStack in the current selection; existing VM state is left untouched.
