# Canonical LLM-native engineering stack

Based on the final stack message in **GPUI Rewrite Scope** (conversation `6abeed3e-8900-83e9-86a0-5e712b8fc1ca`), updated at the user's request on 2026-10-03: **OrbStack** supplies the VM/container engine for personal use and **sohamb117/omp-pet** supplies the OMP desktop companion. OMP Pet is installed from a published release without compiling, and shared OMP defaults apply through its user-level settings/instructions/MCP files. OMP is installed through mise's `github:can1357/oh-my-pi` backend; bootstrap installation uses a Git checkout. The original recovered message is preserved in `docs/STACK-ORIGINAL.md`; current installation sources live in `docs/SOURCES.md`.

Yes. I’d reduce the whole thing to these lists.

## 1. Core devtools

**Machine/UI**
- macOS
- kitty
- zsh
- Zed

**Environment/tool management**
- Homebrew — system packages
- **mise** — language/tool versions + repo tasks; it can also install missing project tools when running tasks.
- direnv only if mise env handling proves insufficient

**Navigation/search**
- `rg`
- `fd`
- `fzf`
- `zoxide`
- `atuin`
- `bat`
- `jq`
- `xh`
- `ast-grep`

**Feedback/perf**
- `watchexec`
- `hyperfine`
- Lefthook

**Git**
- git
- `gh`
- **Worktrunk** — worktree lifecycle, hooks, parallel-agent workflows, shared COW caches.
- lazygit optional

**Local infra**
- OrbStack
- 1Password CLI

---

# 2. Agent harness

This is the actual LLM-native layer.

### Primary
- **Oh My Pi**
  - agent harness
  - LSP
  - debugger
  - subagents
  - MCP
  - sessions
  - provider/model routing
  - extensions
  - prompt/context machinery

OMP currently ships dozens of tools, LSP/DAP operations and broad provider support.

### Desktop companion
- **[sohamb117/omp-pet](https://github.com/sohamb117/omp-pet)**
  - native macOS companion
  - OMP plugin bridge
  - built from a pinned source revision

### Repo intelligence
- **CKG**
  - local
  - Rust
  - SQLite
  - Tree-sitter
  - MCP
  - task-context generation
  - calls/imports/references/tests/etc.

Its data lives locally under `.ckg/ckg.sqlite`; no graph server is needed.

Then retain:
- `rg` → lexical
- `ast-grep` → structural
- LSP → semantic
- **CKG** → relational/context packing

### Parallelism
- **Worktrunk**
- one worktree per agent/task

```text
OMP
 ├── wt/feature-a
 ├── wt/feature-b
 ├── wt/tests
 └── wt/reviewer
```

### Review
- **Greptile**
- specifically `greptile review --agent`
- independent semantic reviewer after deterministic tests.

### Context/token optimizations
- OMP prompt caching
- OMP async compaction
- OMP snapcompact where useful
- CKG task-context instead of reading entire repos
- truncated success output
- persistent full tool outputs referenced by ID/hash
- patch-based writes rather than whole-file regeneration
- fast scout model + stronger implementation model

---

# 3. TypeScript / JavaScript

### Toolchain
- **Bun** — runtime + package manager + test runner + bundler.
- Biome — lint + format
- mise — Bun version

### Default libraries

```text
Backend       Hono
Frontend      React + Vite
Validation    Zod
Database      Drizzle
Server state  TanStack Query
Tables        TanStack Table
Forms         React Hook Form
Styling       Tailwind
Testing       bun test
E2E           Playwright
```

For tiny backend services, use `Bun.serve()` directly before adding Hono.

---

# 4. Python

### Toolchain

```text
Version/packages   uv
Lint/format        Ruff
Types              ty / Pyright
Tests              pytest
```

### Default libraries

```text
API            FastAPI
Schemas        Pydantic
HTTP           httpx
SQL            SQLAlchemy
Postgres       asyncpg
CLI            Typer
Dataframes     Polars
Analytics      DuckDB
Numerical      NumPy
ML             PyTorch
```

No Poetry/pipenv/Black/isort/Flake8 on greenfield projects unless required by an existing repo.

---

# 5. Rust

### Toolchain

```text
Versions       mise
Dependencies   Cargo
CLI installs   cargo-binstall
Build cache    mbx
Tests          cargo-nextest
```

`cargo-binstall` avoids recompiling CLI tools when prebuilt artifacts exist.

`mbx` provides a content-addressed Rust compilation cache shared across projects/worktrees and integrates directly with mise.

### Default libraries

```text
Async          tokio
HTTP server    axum
HTTP client    reqwest
Serialization  serde
SQL            sqlx
Observability  tracing
App errors     anyhow
Typed errors   thiserror
CLI            clap
gRPC           tonic
WebSockets     tokio-tungstenite
Parallel CPU   rayon
TLS            rustls
Desktop UI     GPUI
Snapshots      insta
Property tests proptest
Benchmarks     divan / criterion
```

This is probably the language where I'd be **most strict about canonical defaults**.

---

# 6. Go

Go already has less tooling nonsense.

### Toolchain

```text
Versions       mise
Packages       go modules
Build          go
Tests          go test
Lint           golangci-lint
Format         gofmt
```

### Default libraries

```text
HTTP           stdlib net/http
Router         chi
Postgres       pgx
SQL generation sqlc
Logging        slog
CLI            Cobra
Testing        stdlib + testify where useful
RPC            Connect / gRPC
OpenAPI        oapi-codegen
```

Don't framework Go to death.

---

# 7. Data / infrastructure defaults

```text
Transactional DB    Postgres
Local DB/state      SQLite
Analytics           DuckDB
Cache/queues        Valkey
Blobs               S3
Remote retrieval    turbopuffer
Local code KG       CKG/SQLite
Containers          OrbStack/Docker
Reverse proxy       Caddy
Telemetry           OpenTelemetry
Metrics             Prometheus
Dashboards          Grafana
Errors              Sentry
CI                   GitHub Actions
IaC                  OpenTofu
```

---

# 8. The canonical stack in one screen

```text
WORKSTATION
macOS
kitty + zsh
Zed
Homebrew
mise

AGENTS
OMP
omp-pet
CKG
Worktrunk
Greptile

CLI
rg
fd
fzf
zoxide
atuin
bat
jq
xh
ast-grep
watchexec
hyperfine
gh
Lefthook

ISOLATION
OrbStack

TS
Bun
Hono
React/Vite
Zod
Drizzle
Biome

PYTHON
uv
Ruff
FastAPI
Pydantic
httpx
SQLAlchemy
pytest

RUST
mise
Cargo
cargo-binstall
mbx
nextest
tokio
axum
reqwest
serde
sqlx
tracing
clap
GPUI

GO
mise
go modules
net/http + chi
pgx + sqlc
slog
golangci-lint

DATA
Postgres
SQLite
DuckDB
Valkey
S3
turbopuffer
```

That’s about where I’d stop. Anything beyond this should have to justify its existence rather than becoming part of the default workstation.
