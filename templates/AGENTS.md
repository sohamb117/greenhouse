# Agent instructions: canonical engineering stack

## Project facts to complete

- Purpose and user-facing behavior: **fill in for this project**.
- Checkout/root and key directories: **fill in**.
- Exact install, lint, type-check, test and build commands: **read the repo and fill in**.
- Required services, ports and environment variable names: **fill in; never put secret values here**.
- Deployment/review policy and external-service authorization: **fill in**.

This is a portable starter. Existing repository instructions, lockfiles, CI checks and the user's current task take priority over greenfield defaults. Do not migrate an existing repo's framework or package manager merely to match this list.

## Operating environment

The workstation is macOS with kitty, zsh and Zed. Homebrew owns system CLIs/apps. mise installs OMP through `github:can1357/oh-my-pi` and selects Bun, Go, Rust and mbx; the latest Node is a compatibility runtime for npm CLIs. uv owns Python versions, virtual environments and packages. OrbStack supplies local Docker infrastructure. Use OMP's `/login` for supported providers and the project's approved credential source for other secrets. Supply API keys only to the process that needs them; never put secret values in tracked files, shell rc files, prompts or captured logs. No separate secret-management app is required by this stack. Workstation tools use the latest stable releases; do not add fixed version selectors or release tags to this bootstrap. Use current releases for new projects while respecting existing repositories' requirements and lockfiles.

OMP automatically loads the active user/profile directory's `config.yml`, `AGENTS.md` and `mcp.json` in every project. Bootstrap installs shared defaults there; project instructions and configuration remain authoritative. Run from the actual intended checkout/worktree. Inspect `git status`, repository instructions, version files, dependency manifests and CI before editing. If several checkouts could match the task, identify the intended one. Read `mise.toml`, `rust-toolchain.toml`, `.python-version` and lockfiles rather than assuming global versions. Use `mise exec -- COMMAND` or repo mise tasks for background commands; interactive shell hooks are not guaranteed in an agent process.

Do useful work within the user's authorized scope. Preserve unrelated edits. Ask for missing requirements only when they change the result or block work; continue independent work while waiting. Do not deploy, provision paid services, submit code to external reviewers or change account access without applicable authorization.

## Find code with the right tool

| Need | Tool / usage |
|---|---|
| Paths and literal text | `rg --files`, `rg -n`, `fd`; filter before opening files |
| AST-shaped patterns | `ast-grep` / `sg`, with the correct language |
| Types, definitions, references, renames | OMP LSP or the project's language server |
| Relationships and bounded task context | CKG CLI/MCP, for supported JS/TS/Rust |
| Git history and remote metadata | Git / `gh` |
| HTTP or JSON investigation | `xh`, `jq` |

Start with compact task context when the graph is useful:

```sh
ckg doctor "$PWD"
# Refresh if the index is absent/stale, after relevant edits, or in a new worktree:
ckg index "$PWD"
ckg task-context "$PWD" "describe the concrete task" --max-tokens 2000 --json
rg -n "relevant symbol" src tests
```

MCP `ckg` should run `ckg mcp /absolute/path/to/this/worktree --compact`. Bootstrap installs a native user-level `mcp.json` with a CKG entry using `ckg mcp . --compact`; OMP launches it in the current project directory. A project `.omp/mcp.json` can override it, with a `mcpServers` object. Do not use an index/MCP entry from a different checkout. The CLI/MCP graph is best-effort and currently covers JS, TS and Rust; use lexical/structural/LSP tools for Python, Go and unsupported code. Refresh the graph when necessary, then read the exact implementations/tests it identifies. Avoid dumping the whole repo into context.

## Harness, context and tool output

Use `mise exec github:can1357/oh-my-pi -- omp ...` for OMP in non-interactive commands; do not install it with Homebrew. OMP is the primary harness: LSP, debugger, MCP, provider routing, sessions and task tools. `sohamb117/omp-pet` is the native macOS companion; bootstrap installs the latest release plugin and downloads its verified matching app through the plugin installer; no source build is used. Releases currently support native Apple Silicon. Use `/reload-plugins`, `/pet install` (download only), `/pet show` and `/pet status` in OMP. Pet animation indicates lifecycle activity, not proof of model/tool progress; verify actual command results. Use built-in semantic/debugger operations when useful. Reuse warm language servers/dev servers/watchers instead of launching duplicates. Do not change OMP credentials, approval mode or model settings just to complete a routine code task.

Keep the prompt prefix stable. Prefer bounded context, narrow file reads and patches. OMP defaults in this setup enable long cache retention and async compaction with snapcompact as a fallback; caching support and compaction fidelity depend on the provider/model. Snapcompact is not mathematically lossless. Authenticate and select available scout/implementation models through OMP rather than hardcoding model names.

For large deterministic command output, use `agent-run COMMAND ...` when available. It stores full stdout/stderr by SHA-256 and returns a compact status/path, with a failure tail. Preserve the exit status and read the complete relevant log when a tail is insufficient. Keep local artifact/log references so information remains available without repeatedly pasting it into context. Successful checks need a concise result; failures need the exact assertion/error and relevant trace. Never hide failures behind output truncation. Run interactive and streaming tasks directly. Avoid secrets in captured output.

When the user requests parallel agent work, use OMP task tools and Worktrunk with one worktree per implementation agent/task. Give each agent a clear scope and separate writable checkout, preserve repository-required checks, and integrate/review their final diffs. Compact exploration reports should identify exact files, evidence and uncertainties. Prefer a fast configured scout role for bounded discovery and a stronger configured role for implementation/synthesis; use available account models. Do not assume a subagent capability exists in every harness.

```sh
wt list
wt switch --create feature-name
# New checkout: refresh its CKG index and point its MCP entry at its own path.
```

Use `wt`'s shell integration for directory changes, or an explicit checkout directory in non-interactive tools. Inspect project hooks before approving them. Shared caches (mbx/Worktrunk) must not become shared source/output directories that allow simultaneous agents to overwrite each other's work. Do not remove another task's worktree or broaden permissions unnecessarily.

## Language defaults for new projects

| Language | Package/version tooling | Checks | Default libraries |
|---|---|---|---|
| TypeScript/JavaScript | Bun, mise; commit Bun lockfile | Biome, `bun test`, Playwright for E2E | Hono (or tiny `Bun.serve()`), React + Vite, Zod, Drizzle, TanStack Query/Table, React Hook Form, Tailwind |
| Python | uv, `.python-version`, `pyproject.toml`, `uv.lock` | Ruff, ty or Pyright, pytest | FastAPI, Pydantic, httpx, SQLAlchemy, asyncpg, Typer, Polars, DuckDB, NumPy, PyTorch |
| Rust | mise/rustup-selected toolchain, Cargo, `Cargo.lock`; cargo-binstall for CLIs | rustfmt, Clippy, cargo-nextest | tokio, axum, reqwest, serde, sqlx, tracing, anyhow, thiserror, clap, tonic, tokio-tungstenite, rayon, rustls, GPUI, insta, proptest, divan/criterion |
| Go | mise, Go modules, `go.mod`/`go.sum` | gofmt, golangci-lint, `go test` | net/http, chi, pgx, sqlc, slog, Cobra, stdlib/testify, Connect/gRPC, oapi-codegen |

Install only the project's needed libraries through its package manager. JS libraries are Bun dependencies; Python libraries are uv dependencies; Rust libraries belong in Cargo.toml; Go libraries belong in modules. Never install project libraries globally. On greenfield Python, avoid Poetry/pipenv/Black/isort/Flake8 unless required. Keep Go's stdlib-first approach and Rust's canonical defaults. GPUI is the default Rust desktop UI; follow each project's SDK/build requirements.

Use repo commands when present. These are examples, not a mandate to run every tool on every task:

```sh
# TypeScript/JS: prefer scripts already defined in package.json.
mise exec -- bun install --frozen-lockfile
mise exec -- bun run lint
mise exec -- bun test
# Run configured Playwright tests when behavior changes justify E2E.

# Python: run inside the repo's uv environment.
uv sync --frozen
uv run ruff check .
uv run ruff format --check .
uv run ty check  # or the repo's Pyright command
uv run pytest

# Rust: preserve mbx by going through mise's Cargo wrapper.
mise exec -- cargo fmt --all -- --check
mise exec -- cargo clippy --workspace --all-targets -- -D warnings
mise exec -- cargo nextest run
# nextest excludes doctests; use cargo test --doc when the project requires them.

# Go: follow the project's module/workspace and generated-code rules.
mise exec -- go test ./...
golangci-lint run
```

The bootstrap's mise Rust option enables mbx; a project override should retain `mr_boxington = true` and a `mr-boxington` tool entry to use it. `cargo-binstall` may fall back to compiling when no prebuilt release exists. Build caches accelerate builds; a cache hit is not evidence that behavior is correct. Debug mismatches with `mbx doctor` and the actual repository commands.

## Data and infrastructure defaults

| Need | Default |
|---|---|
| Transactional DB | Postgres |
| Local DB/state | SQLite |
| Analytics | DuckDB |
| Cache/queues | Valkey |
| Object storage | S3 |
| Remote retrieval | turbopuffer |
| Local code graph | CKG / SQLite |
| Containers | OrbStack / Docker Compose |
| Reverse proxy | Caddy |
| Telemetry / metrics / dashboards / errors | OpenTelemetry / Prometheus / Grafana / Sentry |
| CI / infrastructure code | GitHub Actions / OpenTofu |

OrbStack supplies the local Docker engine and Linux machines. Full setup installs its app; open it explicitly (`open -a OrbStack`) and finish first-time setup before using containers. Inspect `docker context ls` and use `docker --context orbstack ...` for the intended engine; check `docker --context orbstack info` for readiness. CLI-only setup skips the app. Preserve existing engine data, volumes and other VM installations; never delete VM disks to fix a routine issue.

Use the repository's defined service topology, credentials, ports and persistence. Do not start extra global databases to bypass a broken project setup. Keep production and local endpoints distinct. Native data tools are optional in the workstation package; hosted services need account/project access. Read plans and actual provider state before applying infrastructure; obtain the user's required approval for external/paid changes.

## Validation and review

Run deterministic checks appropriate to the change and the repository's required checks. Fix failures and report meaningful limitations; do not describe an unrun command as passing. Inspect the final diff and ensure it contains only intended changes. Preserve the exact source/config/lockfile state supporting experiment results. A smoke test verifies wiring, not a scientific hypothesis.

When the repository's Greptile account is configured and external review is authorized, run `greptile review --agent` after deterministic checks. Resolve actionable findings and rerun affected checks. Account onboarding/browser approvals belong to the user; do not bypass the CLI's interactive protections. Greptile supplements tests and human review. If unavailable, perform a local review and state the limitation; do not silently create a new organization, account or trial.

End with what changed, how it was verified and material remaining issues. Link useful files/artifacts and keep routine success output short. Avoid adding frameworks/tools outside this stack unless the project or task justifies them.
