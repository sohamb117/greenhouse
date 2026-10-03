#!/usr/bin/env python3
"""Own narrow config fragments; preserve unrelated settings and backup edits."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
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


MD_START = '<!-- >>> mac-dev-bootstrap >>> -->'
MD_END = '<!-- <<< mac-dev-bootstrap <<< -->'


def yaml_value(text):
    # Bun ships with the stack; parse YAML without a separate global Python package.
    result = subprocess.run(['bun', '-e',
        'console.log(JSON.stringify(Bun.YAML.parse(await Bun.stdin.text()) ?? null));'],
        input=text, text=True, capture_output=True, check=True)
    value = json.loads(result.stdout)
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError('OMP settings must contain a mapping.')
    return value


def merge_missing(current, defaults):
    changed = False
    for key, value in defaults.items():
        if key not in current:
            current[key] = value
            changed = True
        elif isinstance(current[key], dict) and isinstance(value, dict):
            changed = merge_missing(current[key], value) or changed
    return changed


def install_omp(omp_dir):
    defaults_text = (ROOT / 'config/omp.yml').read_text()
    defaults = yaml_value(defaults_text)
    settings = next((omp_dir / name for name in ('config.yml', 'config.yaml')
                     if (omp_dir / name).exists()), omp_dir / 'config.yml')
    legacy = omp_dir / 'settings.json'
    if settings.exists():
        current = yaml_value(settings.read_text())
    elif legacy.exists():
        current = json.loads(legacy.read_text())
        if not isinstance(current, dict):
            raise ValueError('OMP settings.json must contain an object.')
    else:
        current = {}
    settings_changed = merge_missing(current, defaults)
    mcp = omp_dir / 'mcp.json'
    servers = json.loads(mcp.read_text()) if mcp.exists() else {}
    if not isinstance(servers, dict) or not isinstance(servers.get('mcpServers', {}), dict):
        raise ValueError('OMP mcp.json and mcpServers must contain objects.')
    # CKG resolves '.' against the stdio transport's session/project cwd.
    mcp_changed = 'ckg' not in servers.get('mcpServers', {})
    if mcp_changed:
        servers.setdefault('mcpServers', {})['ckg'] = {
            'type': 'stdio', 'command': 'ckg', 'args': ['mcp', '.', '--compact']}
    agents = omp_dir / 'AGENTS.md'
    original = agents.read_text() if agents.exists() else ''
    markers = [line.strip() for line in original.splitlines() if line.strip() in (MD_START, MD_END)]
    if markers not in ([], [MD_START, MD_END]):
        raise ValueError('Malformed managed block in ' + str(agents))
    if settings_changed or not settings.exists():
        if not settings.exists() and not legacy.exists():
            content = defaults_text
        else:
            result = subprocess.run(['bun', '-e',
                'console.log(Bun.YAML.stringify(JSON.parse(await Bun.stdin.text())));'],
                input=json.dumps(current), text=True, capture_output=True, check=True)
            content = result.stdout
        write_changed(settings, content)
    if mcp_changed:
        write_changed(mcp, json.dumps(servers, indent=2) + '\n')
    starter = (ROOT / 'templates/AGENTS.md').read_text()
    shared = '# Shared engineering defaults\n\n' + starter[starter.index('This is a portable starter.'):]
    block = MD_START + '\n' + shared.rstrip() + '\n' + MD_END + '\n'
    if markers:
        begin = original.index(MD_START)
        end = original.index(MD_END, begin) + len(MD_END)
        suffix = original[end:]
        content = original[:begin] + block.rstrip('\n') + suffix
    else:
        content = original + ('\n\n' if original and not original.endswith('\n') else '\n' if original else '') + block
    write_changed(agents, content)


def install(home, config_home, zsh_dir, omp_dir, skip_omp=False):
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
    if not skip_omp:
        install_omp(omp_dir)
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
    parser.add_argument('--skip-omp', action='store_true', help='Stage mise configuration before Bun is installed.')
    parser.add_argument('--omp-only', action='store_true', help='Install only shared OMP defaults after runtimes are available.')
    args = parser.parse_args()
    home = args.target_home.expanduser().resolve() if args.target_home else Path.home()
    if args.target_home:
        config_home, zsh_dir, omp_dir = home / '.config', home, home / '.omp/agent'
    else:
        config_home = Path(os.environ.get('XDG_CONFIG_HOME', str(home / '.config')))
        zsh_dir = Path(os.environ.get('ZDOTDIR', str(home)))
        omp_root = Path(os.environ.get('PI_CONFIG_DIR', str(home / '.omp')))
        profile = os.environ.get('OMP_PROFILE') or os.environ.get('PI_PROFILE') or 'default'
        omp_dir = (Path(os.environ.get('PI_CODING_AGENT_DIR', str(omp_root / 'agent')))
                   if profile == 'default' else omp_root / 'profiles' / profile / 'agent')
    if args.omp_only:
        install_omp(omp_dir)
    else:
        install(home, config_home, zsh_dir, omp_dir, skip_omp=args.skip_omp)


if __name__ == '__main__':
    main()
