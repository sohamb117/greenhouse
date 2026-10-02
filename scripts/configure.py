#!/usr/bin/env python3
"""Own narrow config fragments; preserve unrelated settings and backup edits."""
import argparse
import json
import os
from pathlib import Path
import shutil
import tempfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
START = '# >>> mac-dev-bootstrap >>>'
END = '# <<< mac-dev-bootstrap <<<'


def backup(path):
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    destination = path.with_name(path.name + '.mac-dev-backup-' + stamp)
    shutil.copy2(path, destination)
    return destination


def write_changed(path, content):
    path = Path(path).expanduser()
    # Resolve an existing symlink so atomic writes preserve the link itself.
    if path.is_symlink():
        path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text() == content:
        print('Unchanged:', path)
        return False
    previous_mode = path.stat().st_mode & 0o777 if path.exists() else 0o644
    if path.exists():
        print('Backup:', backup(path))
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as handle:
            handle.write(content)
        os.chmod(temporary, previous_mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print('Wrote:', path)
    return True


def add_block(path, body):
    text = path.read_text() if path.exists() else ''
    lines = text.splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines) if line.strip() == START]
    ends = [i for i, line in enumerate(lines) if line.strip() == END]
    if starts or ends:
        if len(starts) != 1 or len(ends) != 1 or starts[0] >= ends[0]:
            raise ValueError('Malformed managed block in ' + str(path) + '; fix it before rerunning.')
        before = ''.join(lines[:starts[0]])
        after = ''.join(lines[ends[0] + 1:])
    else:
        before = text + ('\n' if text and not text.endswith('\n') else '')
        after = ''
    return write_changed(path, before + START + '\n' + body + '\n' + END + '\n' + after)


def install(home, config_home, zsh_dir, omp_dir):
    # Validate both rc files before any writes.
    for name in ('.zprofile', '.zshrc'):
        path = zsh_dir / name
        text = path.read_text() if path.exists() else ''
        markers = [line.strip() for line in text.splitlines() if line.strip() in (START, END)]
        if markers not in ([], [START, END]):
            raise ValueError('Malformed managed block in ' + str(path))
    managed = config_home / 'mac-dev-bootstrap'
    for name in ('zprofile.zsh', 'zshrc.zsh'):
        write_changed(managed / name, (ROOT / 'shell' / name).read_text())
    helper = home / '.local/bin/agent-run'
    write_changed(helper, (ROOT / 'scripts/capture.sh').read_text())
    helper.chmod(0o755)
    write_changed(config_home / 'mise/conf.d/50-mac-dev-bootstrap.toml', (ROOT / 'mise.toml').read_text())
    for rc, fragment in (('.zprofile', 'zprofile.zsh'), ('.zshrc', 'zshrc.zsh')):
        source = '${XDG_CONFIG_HOME:-$HOME/.config}/mac-dev-bootstrap/' + fragment
        add_block(zsh_dir / rc, '[[ -r "' + source + '" ]] && source "' + source + '"')
    wt = config_home / 'worktrunk/config.toml'
    if wt.exists():
        print('Preserved existing Worktrunk config:', wt)
    else:
        write_changed(wt, (ROOT / 'config/worktrunk.toml').read_text())
    legacy = [omp_dir / name for name in ('config.yml', 'config.yaml', 'settings.json')]
    if any(path.exists() for path in legacy):
        print('Preserved existing OMP settings. Compare config/omp.yml manually.')
    else:
        write_changed(omp_dir / 'config.yml', (ROOT / 'config/omp.yml').read_text())
    # Docker uses DOCKER_CONFIG, not XDG.
    docker = Path(os.environ.get('DOCKER_CONFIG', str(home / '.docker')))
    path = docker / 'config.json'
    config = json.loads(path.read_text()) if path.exists() else {}
    if not isinstance(config, dict):
        raise ValueError('Docker config.json must contain an object.')
    brew_prefix = os.environ.get('HOMEBREW_PREFIX')
    if brew_prefix:
        plugin_dir = str(Path(brew_prefix) / 'lib/docker/cli-plugins')
        plugin_dirs = config.setdefault('cliPluginsExtraDirs', [])
        if not isinstance(plugin_dirs, list):
            raise ValueError('Docker cliPluginsExtraDirs must be an array.')
        if plugin_dir not in plugin_dirs:
            plugin_dirs.append(plugin_dir)
            write_changed(path, json.dumps(config, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--target-home', type=Path, help='Use an isolated home directory for configuration tests.')
    args = parser.parse_args()
    home = args.target_home.expanduser().resolve() if args.target_home else Path.home()
    if args.target_home:
        config_home, zsh_dir, omp_dir = home / '.config', home, home / '.omp/agent'
    else:
        config_home = Path(os.environ.get('XDG_CONFIG_HOME', str(home / '.config')))
        zsh_dir = Path(os.environ.get('ZDOTDIR', str(home)))
        omp_dir = Path(os.environ.get('PI_CODING_AGENT_DIR', str(home / '.omp/agent')))
    install(home, config_home, zsh_dir, omp_dir)


if __name__ == '__main__':
    main()
