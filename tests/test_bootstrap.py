import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('configure', ROOT / 'scripts/configure.py')
configure = importlib.util.module_from_spec(spec)
spec.loader.exec_module(configure)


class ConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='bootstrap test ')
        self.home = Path(self.temporary.name)
        self.config = self.home / '.config'
        self.omp = self.home / '.omp/agent'
        self.env = patch.dict(os.environ, {'DOCKER_CONFIG': str(self.home / '.docker'), 'HOMEBREW_PREFIX': '/opt/homebrew'})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.temporary.cleanup()

    def install(self):
        with contextlib.redirect_stdout(io.StringIO()):
            configure.install(self.home, self.config, self.home, self.omp)

    def snapshot(self):
        return {str(p.relative_to(self.home)): (p.read_bytes(), p.stat().st_mtime_ns)
                for p in self.home.rglob('*') if p.is_file()}

    def test_repeat_run_is_unchanged(self):
        self.install()
        before = self.snapshot()
        self.install()
        self.assertEqual(before, self.snapshot())
        self.assertFalse(list(self.home.rglob('*.mac-dev-backup-*')))
        self.assertTrue((self.home / '.local/bin/agent-run').stat().st_mode & 0o111)
        fragment = self.config / 'mise/conf.d/50-mac-dev-bootstrap.toml'
        self.assertIn('mr-boxington', tomllib.loads(fragment.read_text())['tools'])

    def test_existing_rc_content_and_permissions_survive(self):
        rc = self.home / '.zshrc'
        original = '# My setup\nalias ll="ls -la"'
        rc.write_text(original)
        rc.chmod(0o600)
        self.install()
        self.assertTrue(rc.read_text().startswith(original + '\n'))
        self.assertEqual(rc.stat().st_mode & 0o777, 0o600)
        backups = list(self.home.glob('.zshrc.mac-dev-backup-*'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), original)
        self.install()
        self.assertEqual(len(list(self.home.glob('.zshrc.mac-dev-backup-*'))), 1)

    def test_existing_omp_and_worktrunk_are_preserved(self):
        self.omp.mkdir(parents=True)
        legacy = self.omp / 'config.yaml'
        legacy.write_text('modelRoles:\n  default: personal/model\n')
        wt = self.config / 'worktrunk/config.toml'
        wt.parent.mkdir(parents=True)
        wt.write_text('worktree-path = "custom"\n')
        self.install()
        self.assertFalse((self.omp / 'config.yml').exists())
        self.assertIn('personal/model', legacy.read_text())
        self.assertEqual(configure.yaml_value(legacy.read_text())['providers']['cacheRetention'], 'long')
        self.assertEqual(len(list(self.omp.glob('config.yaml.mac-dev-backup-*'))), 1)
        self.assertEqual(wt.read_text(), 'worktree-path = "custom"\n')

    def test_shared_omp_defaults_preserve_custom_values_and_servers(self):
        self.omp.mkdir(parents=True)
        settings = self.omp / 'config.yml'
        settings.write_text('modelRoles:\n  default: personal/model\ncompaction:\n  enabled: false\n')
        original = settings.read_text()
        mcp = self.omp / 'mcp.json'
        existing = {'mcpServers': {'custom': {'command': 'my-server'}}, 'disabledServers': ['custom']}
        mcp.write_text(json.dumps(existing))
        agents = self.omp / 'AGENTS.md'
        agents.write_text('Keep my personal instructions.\n')
        self.install()
        values = configure.yaml_value(settings.read_text())
        self.assertFalse(values['compaction']['enabled'])
        self.assertTrue(values['compaction']['asyncEnabled'])
        self.assertEqual(values['modelRoles']['default'], 'personal/model')
        backup = list(self.omp.glob('config.yml.mac-dev-backup-*'))
        self.assertEqual(len(backup), 1)
        self.assertEqual(backup[0].read_text(), original)
        servers = json.loads(mcp.read_text())
        self.assertEqual(servers['mcpServers']['custom'], existing['mcpServers']['custom'])
        self.assertEqual(servers['disabledServers'], ['custom'])
        self.assertEqual(servers['mcpServers']['ckg']['args'], ['mcp', '.', '--compact'])
        self.assertTrue(agents.read_text().startswith('Keep my personal instructions.\n'))
        self.assertEqual(agents.read_text().count(configure.MD_START), 1)
        self.assertNotIn('Project facts to complete', agents.read_text())
        before = self.snapshot()
        self.install()
        self.assertEqual(before, self.snapshot())

    def test_empty_global_yaml_receives_defaults(self):
        self.omp.mkdir(parents=True)
        settings = self.omp / 'config.yml'
        settings.write_text('# Empty user settings\n')
        self.install()
        self.assertEqual(configure.yaml_value(settings.read_text())['providers']['cacheRetention'], 'long')

    def test_existing_user_ckg_definition_is_preserved(self):
        self.omp.mkdir(parents=True)
        mcp = self.omp / 'mcp.json'
        original = {'mcpServers': {'ckg': {'command': 'custom-ckg', 'enabled': False}}}
        mcp.write_text(json.dumps(original))
        self.install()
        self.assertEqual(json.loads(mcp.read_text()), original)

    def test_invalid_global_instructions_fail_before_omp_writes(self):
        self.omp.mkdir(parents=True)
        (self.omp / 'AGENTS.md').write_text(configure.MD_START + '\nmissing end\n')
        before = self.snapshot()
        with self.assertRaises(ValueError):
            configure.install_omp(self.omp)
        self.assertEqual(before, self.snapshot())

    def test_legacy_json_settings_seed_global_yaml_without_losing_values(self):
        self.omp.mkdir(parents=True)
        legacy = self.omp / 'settings.json'
        legacy.write_text(json.dumps({'modelRoles': {'default': 'personal/model'}}))
        before = legacy.read_bytes()
        self.install()
        self.assertEqual(legacy.read_bytes(), before)
        values = configure.yaml_value((self.omp / 'config.yml').read_text())
        self.assertEqual(values['modelRoles']['default'], 'personal/model')
        self.assertEqual(values['providers']['cacheRetention'], 'long')

    def test_rc_symlink_is_preserved(self):
        target = self.home / 'my-dotfiles/zshrc'
        target.parent.mkdir()
        target.write_text('# linked settings\n')
        rc = self.home / '.zshrc'
        rc.symlink_to(target)
        self.install()
        self.assertTrue(rc.is_symlink())
        self.assertIn(configure.START, target.read_text())
        self.assertEqual(len(list(target.parent.glob('zshrc.mac-dev-backup-*'))), 1)

    def test_malformed_blocks_fail_before_writes(self):
        (self.home / '.zshrc').write_text(configure.START + '\nmissing end\n')
        before = self.snapshot()
        with self.assertRaises(ValueError):
            self.install()
        self.assertEqual(before, self.snapshot())

    def test_block_replacement_preserves_surrounding_text(self):
        rc = self.home / '.zshrc'
        rc.write_text('before\n' + configure.START + '\nold\n' + configure.END + '\nafter\n')
        self.install()
        text = rc.read_text()
        self.assertTrue(text.startswith('before\n'))
        self.assertTrue(text.endswith('after\n'))
        self.assertEqual(text.count(configure.START), 1)
        self.assertNotIn('\nold\n', text)

    def test_docker_config_is_merged_without_losing_fields(self):
        path = self.home / '.docker/config.json'
        path.parent.mkdir()
        original = {'auths': {'registry.example': {}}, 'currentContext': 'personal', 'cliPluginsExtraDirs': ['/my/plugins']}
        path.write_text(json.dumps(original))
        self.install()
        result = json.loads(path.read_text())
        self.assertEqual(result['auths'], original['auths'])
        self.assertEqual(result['currentContext'], 'personal')
        self.assertEqual(result['cliPluginsExtraDirs'], ['/my/plugins', '/opt/homebrew/lib/docker/cli-plugins'])
        self.install()
        self.assertEqual(len(list(path.parent.glob('config.json.mac-dev-backup-*'))), 1)


class ScriptTests(unittest.TestCase):
    def test_shell_and_brewfile_syntax(self):
        for path in sorted((ROOT / 'scripts').glob('*.sh')):
            subprocess.run(['/bin/bash', '-n', str(path)], check=True, capture_output=True)
        if shutil.which('zsh'):
            for path in sorted((ROOT / 'shell').glob('*.zsh')):
                subprocess.run(['zsh', '-n', str(path)], check=True, capture_output=True)
        if shutil.which('ruby'):
            for path in sorted(ROOT.glob('Brewfile*')):
                subprocess.run(['ruby', '-c', str(path)], check=True, capture_output=True)

    def test_agent_starter_matches_root_shared_instructions(self):
        self.assertTrue((ROOT / 'AGENTS.md').read_text().startswith((ROOT / 'templates/AGENTS.md').read_text()))

    def test_unknown_bootstrap_option_is_rejected(self):
        result = subprocess.run([str(ROOT / 'scripts/bootstrap.sh'), '--invalid'], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Unknown option', result.stderr)

    @unittest.skipUnless(os.uname().sysname == 'Darwin', 'macOS preview')
    def test_dry_run_does_not_execute_installers(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            marker = folder / 'should-not-exist'
            for tool in ('brew', 'mise', 'uv'):
                path = folder / tool
                path.write_text('#!/bin/bash\nif [[ "$1" == shellenv ]]; then exit 0; fi\ntouch "' + str(marker) + '"\n')
                path.chmod(0o755)
            env = dict(os.environ, PATH=str(folder) + ':/usr/bin:/bin:/usr/sbin:/sbin')
            result = subprocess.run([str(ROOT / 'scripts/bootstrap.sh'), '--dry-run', '--extras', '--data-tools'], env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(marker.exists())
            self.assertIn('Brewfile.optional', result.stdout)
            self.assertIn('Brewfile.data', result.stdout)
            self.assertIn('configure.py', result.stdout)
            self.assertIn('install-omp-pet.sh', result.stdout)
            cli = subprocess.run([str(ROOT / 'scripts/bootstrap.sh'), '--dry-run', '--cli-only'], env=env, capture_output=True, text=True)
            self.assertEqual(cli.returncode, 0, cli.stderr)
            self.assertNotIn('install-omp-pet.sh', cli.stdout)
            self.assertNotIn('Brewfile.apps', cli.stdout)
            self.assertFalse(marker.exists())

    @unittest.skipUnless(shutil.which('jq'), 'jq is required')
    def test_project_init_handles_unusual_paths_and_repeat_runs(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'project "quoted" with spaces'
            target.mkdir()
            (target / '.gitignore').write_text('local-original\n')
            cmd = [str(ROOT / 'scripts/init-repo.sh'), str(target)]
            subprocess.run(cmd, check=True, capture_output=True)
            config = json.loads((target / '.omp/mcp.json').read_text())
            self.assertEqual(Path(config['mcpServers']['ckg']['args'][1]).resolve(), target.resolve())
            before = {str(p.relative_to(target)): p.read_bytes() for p in target.rglob('*') if p.is_file()}
            subprocess.run(cmd, check=True, capture_output=True)
            self.assertEqual(before, {str(p.relative_to(target)): p.read_bytes() for p in target.rglob('*') if p.is_file()})
            self.assertEqual((target / '.gitignore').read_text().count('.ckg/'), 1)
            self.assertEqual(len(list(target.glob('.gitignore.mac-dev-backup-*'))), 1)

    @unittest.skipUnless(shutil.which('jq'), 'jq is required')
    def test_project_init_preserves_existing_agent_and_mcp_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            (target / 'AGENTS.md').write_text('Existing instructions\n')
            (target / '.omp').mkdir()
            (target / '.omp/mcp.json').write_text('{"mcpServers": {}}\n')
            subprocess.run([str(ROOT / 'scripts/init-repo.sh'), str(target)], check=True, capture_output=True)
            self.assertEqual((target / 'AGENTS.md').read_text(), 'Existing instructions\n')
            self.assertEqual((target / '.omp/mcp.json').read_text(), '{"mcpServers": {}}\n')

    def test_python_selector_chooses_newest_stable_default_cpython(self):
        with tempfile.TemporaryDirectory() as temporary:
            uv = Path(temporary) / 'uv'
            releases = [
                {'implementation': 'cpython', 'variant': 'default', 'version': '3.9.99'},
                {'implementation': 'cpython', 'variant': 'default', 'version': '3.100.1'},
                {'implementation': 'cpython', 'variant': 'default', 'version': '4.0.0rc1'},
                {'implementation': 'cpython', 'variant': 'freethreaded', 'version': '4.0.0'},
                {'implementation': 'pypy', 'variant': 'default', 'version': '5.0.0'},
            ]
            uv.write_text("#!/bin/sh\ncat <<'JSON'\n" + json.dumps(releases) + '\nJSON\n')
            uv.chmod(0o755)
            env = dict(os.environ, PATH=temporary + ':' + os.environ['PATH'])
            command = ['bash', '-c', 'source "$1"; latest_python', 'bash', str(ROOT / 'scripts/common.sh')]
            result = subprocess.run(command, env=env, capture_output=True, text=True, check=True)
            self.assertEqual(result.stdout.strip(), '3.100.1')
            uv.write_text('#!/bin/sh\necho "[]"\n')
            result = subprocess.run(command, env=env, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)

    def test_capture_preserves_status_and_full_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            env = dict(os.environ, XDG_STATE_HOME=temporary)
            script = ROOT / 'scripts/capture.sh'
            fail = subprocess.run([str(script), '/bin/bash', '-c', 'printf "diagnostic\\n"; exit 7'], env=env, capture_output=True, text=True)
            self.assertEqual(fail.returncode, 7)
            self.assertIn('FAIL', fail.stdout)
            self.assertIn('diagnostic', fail.stdout)
            logs = list(Path(temporary).rglob('*.log'))
            self.assertEqual(len(logs), 1)
            self.assertEqual(logs[0].read_text(), 'diagnostic\n')
            ok = subprocess.run([str(script), '/bin/bash', '-c', 'printf "success detail\\n"'], env=env, capture_output=True, text=True)
            self.assertEqual(ok.returncode, 0)
            self.assertIn('PASS', ok.stdout)
            self.assertNotIn('success detail', ok.stdout)


if __name__ == '__main__':
    unittest.main()
