# Delivery validation

Validated on this Mac on **2026-10-04** using uv-managed Python **3.13.15** and the installed Bun runtime, without running the live workstation bootstrap or changing real account/shell settings.

**33 tests passed**, covering:

- Repeated configuration runs preserve file content and timestamps.
- Existing shell content, permissions, backups and symlink preservation.
- Existing OMP model/provider choices and explicit settings remain authoritative while missing shared defaults are merged.
- Shared user instructions preserve personal text, exclude project-fact placeholders and update idempotently.
- User-level CKG uses the current checkout; existing CKG definitions, other MCP servers and enable/disable choices are preserved.
- Empty/comment-only YAML receives defaults; legacy JSON settings seed global YAML without deleting the legacy file.
- Malformed managed blocks are rejected before affected configuration writes.
- Docker plugin merging keeps existing credentials/context.
- Bash, zsh and Brewfile syntax; root/starter instruction consistency.
- Dry-run behavior without executing installers; rejection of unknown flags.
- Project initialization handles unusual paths and preserves existing instructions/MCP.
- Full output retention and command exit-code preservation in `agent-run`.
- Pet release setup with isolated homes and fake OMP/download commands: fresh install, offline/cache reruns, previews, plugin/download retries, disabled/custom source preservation, latest-release upgrades and query failure handling, legacy checkout preservation, Intel skip, release-cache doctor checks and app overrides. Old ambient OMP, Git, cargo, uv and app-launch commands deliberately fail in these fixtures.
- Latest Python selection ignores prereleases/alternative variants, compares version components numerically, and rejects an empty catalog.
- Full versus CLI-only setup: CLI-only skips Pet and GUI apps, retaining Docker clients.

Historical real checks from the release-installer validation (these are evidence records, not version selectors):

- The published `v0.1.2` app archive matches the release's `SHA256SUMS`.
- Upstream `ensurePetApp()` downloaded/extracted the real release into a temporary cache, verified its bundle identity/version and code signature, then reused it with network access deliberately disabled. No app was launched.
- The installed OMP CLI read `providers.cacheRetention: long` from shared user settings while running in a fresh project without project config. Shared instructions and CKG MCP files were also created in that isolated user directory.
- Bootstrap dry-run and final diff checks passed.

Installation and updates use a Git checkout. Optional archive export is not an installation step. `docs/STACK-ORIGINAL.md` preserves the recovered canonical message; `STACK.md` and the agent starters reflect the current stack.

Not exercised: installation on a wiped Mac, Homebrew/mise package downloads, VM startup, graphical first launches, model sessions, authenticated MCP connections or account/service provisioning. The Pet release currently supports native Apple Silicon; Intel/Rosetta is skipped rather than compiled. Named OMP profiles are isolated and require running configuration for each desired profile. Package/version selectors can change; run the doctor on the target Mac.
