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

Run `omp setup`, or launch `omp` in a project. Use `/login` for supported subscription/OAuth providers and `/model` to choose the default, smol/scout and slow/implementation roles according to your available accounts. API-key providers can use their documented environment variables through 1Password. No model, subscription or API key is assumed.

Fresh default-profile installs receive `config/omp.yml`: cache retention `long`, automatic append-only context selection and asynchronous compaction. Existing settings are left intact; inspect the file and merge the supported keys manually. Verify with `omp config list` and `omp config path`. Named OMP profiles have separate settings/authentication; apply equivalent defaults in the profile you actually use. Avoid enabling large collections of context-mutating extensions by default. Snapcompact is a fallback with model-dependent retention, not a byte-perfect compression promise.

LSP tools installed: TypeScript language server, Pyright, gopls and rust-analyzer. Go debugging uses `dlv`; LLDB comes from Apple's developer tools. For Python debugging, add `debugpy` to the relevant project's dev dependencies (`uv add --dev debugpy`) and point the adapter at that environment. OMP's LSP/DAP setup should use the project's language environment rather than globally installing that project's libraries. GPUI repositories may need full Xcode and their specified Apple SDK: follow that project's build instructions.

## CKG and MCP

Run these from each actual checkout/worktree:

```sh
ckg index "$PWD"
ckg task-context "$PWD" "fix auth refresh race" --max-tokens 2000 --json
ckg doctor "$PWD"
```

`init-repo.sh` writes this OMP-native schema (with the target path serialized correctly):

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

Launch OrbStack, finish first-run permissions/licensing and start its engine. Then check `docker context ls`, select the intended context when necessary, and run `docker info`. This package installs Docker CLI/Compose/Buildx and appends Homebrew's plugin directory to your Docker CLI config without replacing credentials or contexts. It does not pull images, create containers or start a paid resource.

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
