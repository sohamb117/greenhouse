# Delivery validation

Validated on this Mac on **2026-10-02** using the existing Python **3.14.6**, without running the live installer or changing real account/shell settings.

**14 tests passed**, covering:

- Identical configuration and file timestamps after a repeated run.
- Existing shell content, permissions, backups and symlink preservation.
- Existing OMP/Worktrunk settings preservation.
- Managed-block updates and rejection of malformed blocks before writes.
- Docker plugin configuration merging with existing credentials/context retained.
- Bash, zsh and Brewfile syntax.
- Starter/root agent instruction consistency.
- Dry-run behavior without executing installers and rejection of unknown flags.
- Repo initialization with spaces/quotes in paths, repeat runs and existing instruction/MCP preservation.
- Full output retention and command exit-code preservation in `agent-run`.

The ZIP was checked for integrity, matching source bytes, expected contents and executable script permissions. `STACK.md` was checked against the recovered full canonical message.

Not exercised: installation on a wiped Mac, Homebrew/mise package downloads, Intel binary/source installation, graphical app first launches, authenticated OMP/MCP sessions or any account/service provisioning. The delivered install commands were checked against linked primary documentation. Rolling package/version selectors and vendor requirements can change; rerun the doctor on the actual target Mac.
