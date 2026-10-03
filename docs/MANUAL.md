# Manual account and project setup

## Shell and editor

Open a new kitty/Terminal window after installation. macOS normally already uses zsh; if your account uses another shell, change it explicitly with `chsh -s /bin/zsh`, then log out/in. Set Zed preferences and install the language extensions you use. Avoid replacing an established editor configuration.

## GitHub and Git identity

```sh
gh auth login
gh auth status
# Supply your real identity; use a GitHub noreply address if preferred.
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

SSH keys/signing and organization access depend on your account. The bootstrap does not invent identity, create keys or change existing Git settings.

## 1Password

Sign into the 1Password Mac app. In its settings, enable **Developer → Integrate with 1Password CLI**, then verify with `op whoami`. The sign-in/unlock dialogs and vault permissions are account-specific. Standalone CLI users can follow the [official guide](https://www.1password.dev/cli/get-started).

For provider keys and cloud secrets, use `op run --env-file=... -- COMMAND` with a private, untracked env file containing `op://...` references. Keep real values out of shell rc files, this repo and logs. An already-authorized account is enough; do not repeatedly sign in.

## Oh My Pi

OMP is installed by mise through the official `github:can1357/oh-my-pi` backend. Verify with `mise -C "$HOME" exec github:can1357/oh-my-pi -- omp --version`. Open a new terminal after bootstrap so the managed mise shims take precedence; `type -a omp` can reveal older Homebrew/Bun installs. Existing installations and OMP settings/authentication are preserved. If you want to remove the old Homebrew copy, first verify the mise binary works, then explicitly run `brew uninstall can1357/tap/omp`; bootstrap does not uninstall it for you. Existing global/project mise overrides still take precedence over the managed fragment.

Run `omp setup`, or launch `omp` in a project. Use `/login` for supported subscription/OAuth providers and `/model` to choose the default, smol/scout and slow/implementation roles according to your available accounts. API-key providers can use their documented environment variables through 1Password. No model, subscription or API key is assumed.

Shared OMP settings, instructions and MCP configuration are installed in the native user directory and automatically discovered in every project. Normally this is `~/.omp/agent/`; `PI_CODING_AGENT_DIR` relocates the default profile. `config/omp.yml` supplies cache/compaction defaults. Setup merges missing keys into existing `config.yml` (or `config.yaml`), keeping your current values, providers and model choices. Legacy `settings.json` is retained when seeding YAML. Changed files receive backups; serializing an updated YAML file may normalize formatting/comments.

`AGENTS.md` gets a managed shared-stack block while preserving other text. User-level `mcp.json` gets a `ckg` entry only when absent, using `ckg mcp . --compact`; OMP's stdio transport uses its project cwd. The index still needs refreshing in each checkout. Existing CKG definitions, other servers and enable/disable controls are kept. Repository instructions/configuration can override user defaults; bootstrap does not force the shared policy over project decisions.

Verify with `omp config path`, `omp config get providers.cacheRetention`, `/mcp list` and `/mcp reload`. Named profiles isolate these files. To apply the same defaults to a named profile, run `OMP_PROFILE=work ./scripts/configure.sh`; repeat for profiles you use. A new profile does not inherit default-profile files automatically. `PI_CONFIG_DIR`, `PI_CODING_AGENT_DIR`, `OMP_PROFILE` and `PI_PROFILE` are respected by configuration. No credentials or approval policy are installed.

LSP tools installed: TypeScript language server, Pyright, gopls and rust-analyzer. Go debugging uses `dlv`; LLDB comes from Apple's developer tools. For Python debugging, add `debugpy` to the relevant project's dev dependencies (`uv add --dev debugpy`) and point the adapter at that environment. OMP's LSP/DAP setup should use the project's language environment rather than globally installing that project's libraries. GPUI repositories may need full Xcode and their specified Apple SDK: follow that project's build instructions.

## OMP Pet

Full bootstrap installs the plugin from the published tag in `config/omp-pet.release`, currently `v0.1.2`, then invokes its `ensurePetApp()` installer through Bun. The installer downloads the matching GitHub app release, verifies checksum, bundle version/identity and code signature, and caches it in `~/Library/Application Support/OMP Pet/apps/<version>/`. No Rust build or app launch occurs. `--cli-only` skips Pet. Published apps currently support native Apple Silicon; Intel/Rosetta is skipped without a compilation fallback.

In OMP, run `/reload-plugins` if the session was already open, then `/pet show` and `/pet status`. `/pet install` downloads or repairs the app without launching it. On an upgrade, use `/pet quit` for the old app before `/pet show`. App launch/login and custom sprite selection remain explicit actions. Ad-hoc release signatures are not Apple notarization; use normal macOS first-launch prompts rather than disabling system protections.

Rerun `./scripts/install-omp-pet.sh` after a download failure; the plugin install and app cache are reused. The helper preserves disabled/different-version/custom plugins and prints how to select the desired release explicitly. Pin upgrades by editing `config/omp-pet.release` to a published tag, then selecting it through OMP plugin controls. Existing source checkouts are never built, reset or removed. `OMP_PET_APP` is an explicit app override supported by upstream. Named profiles should check plugin discovery in the profile they use.

## CKG and MCP

Run these from each actual checkout/worktree:

```sh
ckg index "$PWD"
ckg task-context "$PWD" "fix auth refresh race" --max-tokens 2000 --json
ckg doctor "$PWD"
```

OMP already receives a portable user-level CKG entry from bootstrap. For an optional project-specific override, `init-repo.sh` writes this OMP-native schema (with the target path serialized correctly):

```json
{
  "mcpServers": {
    "ckg": {
      "type": "stdio",
      "command": "ckg",
      "args": ["mcp", "/absolute/path/to/this/worktree", "--compact"]
    }
  }
}
```

Use a project `.omp/mcp.json`, and run OMP from the project root. Existing files must be merged, not replaced. In OMP, `/mcp reload` and `/mcp list` let you refresh/check servers. If a GUI cannot find `ckg`, use its absolute executable path from `command -v ckg`. After moving a repo or creating another worktree, update the MCP path to the new directory. An index/watch process must belong to the same worktree as the active agent.

CKG is early alpha; its current parsers cover JS, TypeScript and Rust. Use `rg`, ast-grep and language servers for Python/Go and unsupported constructs. Its best-effort graph complements semantic checks. Use `ckg --help` before assuming watcher features; no persistent watcher is launched by this package.

## Worktrunk and mbx

Shell integration is installed through the managed zsh fragment. Verify `wt config show`, then use `wt switch --create my-feature` in a Git repository. Existing Worktrunk configuration stays intact. Approve project hooks after reading them; the bootstrap does not enable commit generation or run hooks automatically.

mbx is configured through mise's Rust `mr_boxington` option. Use `mise exec -- cargo build` or a mise-activated shell. Calling rustup's Cargo path directly bypasses this integration. Verify `mise which cargo` and `mbx doctor`. Projects that redefine Rust should keep `mr_boxington = true` and include `mr-boxington` in their tools if they want the same behavior. Keep repository-required Rust versions authoritative.

## OrbStack and Docker

Full setup installs the OrbStack app. The core Brewfile keeps Docker CLI/Compose/Buildx, so CLI-only setup still has the clients but skips the engine app. Open OrbStack yourself and finish its first-time setup:

```sh
open -a OrbStack
# After the app reports that the engine is ready:
docker context ls
docker --context orbstack info
docker --context orbstack compose version
docker --context orbstack buildx version
# Optional: make OrbStack the default for subsequent Docker commands.
docker context use orbstack
```

This stack is intended for personal, non-commercial use of OrbStack. See its [licensing information](https://orbstack.dev/pricing) for the applicable plan. Bootstrap does not activate a paid plan or launch the app.

OrbStack also bundles Docker clients; existing Homebrew clients are preserved. This package appends Homebrew's plugin directory to Docker config without replacing credentials or contexts. OrbStack first launch may select its own context; use an explicit context when multiple engines are installed. Inspect `DOCKER_HOST` and `DOCKER_CONTEXT` overrides if commands reach an unexpected engine. See [Docker integration](https://docs.orbstack.dev/docker/) and [installation](https://docs.orbstack.dev/install).

Existing Colima profiles, disks, images, volumes and containers are preserved. They belong to that engine and are not migrated by bootstrap. If Colima is already running, stop it with `colima stop` only when its workloads can be stopped. Stop OrbStack through its app when appropriate; do not delete engine data to switch backends.

## Greptile

In the repository you want reviewed, from your own interactive terminal:

```sh
greptile --version
greptile onboard
greptile whoami
# After that repo's deterministic checks have passed:
greptile review --agent
```

Approve browser sign-in, choose your organization and explicitly choose the repositories the GitHub/GitLab app can access. The CLI requires Node 22+ and onboarding requires CLI 3.2.0+. An org-scoped `GREPTILE_API_KEY` can conflict with onboarding; use browser login for the wizard. Greptile onboarding imports AI rule files as organization context; review the starter's project facts before onboarding. Run review when code submission to the chosen service is authorized. No account, trial, organization or repository integration is created by bootstrap.

## Atuin and optional direnv

Atuin local history works after shell configuration. Sync is optional: use `atuin register` or `atuin login`, then `atuin sync` if you want that account feature. Existing sync credentials/configuration are retained.

direnv is installed only with `--extras`. Uncomment the direnv hook in the installed managed zsh snippet if mise's environment handling is insufficient; copy that change into this package if it should travel to the next Mac. Review each `.envrc` before `direnv allow`.

## Services and infrastructure

Postgres, SQLite, DuckDB and Valkey native tools are available with `--data-tools`. Alternatively use the project's Docker Compose file through OrbStack. Choose service versions, ports, credentials and persistence per project; start a native service explicitly only if needed. Caddy and OpenTofu are installed, with no listeners or infrastructure applied.

S3, turbopuffer, Sentry and hosted Grafana/Prometheus require project/account configuration. OpenTelemetry belongs in application instrumentation; GitHub Actions workflows and OpenTofu state/backend/providers belong in the repo. No managed service is provisioned by this bootstrap.
