"""Exercise the installer with a real local Git repo and fake build/plugin tools."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.uname().sysname == 'Darwin' and shutil.which('jq'), 'macOS and jq are required')
class PetInstallerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='pet installer ')
        self.root = Path(self.temporary.name)
        self.fixture = self.root / 'bootstrap'
        (self.fixture / 'scripts').mkdir(parents=True)
        (self.fixture / 'config').mkdir()
        shutil.copy2(ROOT / 'scripts/install-omp-pet.sh', self.fixture / 'scripts/install-omp-pet.sh')
        common = (ROOT / 'scripts/common.sh').read_text()
        # Keep the fixture PATH; never discover a real Homebrew install.
        (self.fixture / 'scripts/common.sh').write_text(common.replace('load_brew() {', 'load_brew() {\n  return 0'))
        self.source = self.root / 'managed source with spaces'
        self.upstream = self.root / 'upstream'
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.log = self.root / 'invocations'
        self.plugins = self.root / 'plugins.json'
        self.plugins.write_text('{"npm": []}\n')
        self.env = dict(os.environ, PATH=str(self.bin) + ':' + os.environ['PATH'],
                        OMP_PET_DIR=str(self.source), OMP_PET_GIT_URL=self.upstream.as_uri(),
                        PET_TEST_LOG=str(self.log), PET_TEST_PLUGIN_STATE=str(self.plugins),
                        GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)
        self.upstream.mkdir()
        (self.upstream / 'scripts').mkdir()
        (self.upstream / '.gitignore').write_text('dist/\n')
        (self.upstream / 'scripts/build-app.sh').write_text('''#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
app='dist/OMP Pet.app/Contents/MacOS/omp-pet'
mkdir -p "$(dirname "$app")"
printf '#!/bin/sh\\nexit 0\\n' > "$app"
chmod +x "$app"
printf 'build\\n' >> "$PET_TEST_LOG"
''')
        self.git('init', '-b', 'main')
        self.git('add', '.')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                 '-c', 'commit.gpgsign=false', 'commit', '-m', 'Fixture source')
        self.revision = self.git('rev-parse', 'HEAD').strip()
        (self.fixture / 'config/omp-pet.rev').write_text(self.revision + '\n')
        self.tool('mise', '''#!/bin/bash
set -eu
[[ "$1" == -C ]]; shift 2
[[ "$1" == exec && "$2" == -- ]]; shift 2
exec "$@"
''')
        self.tool('uv', '''#!/bin/bash
set -eu
[[ "$1" == run && "$2" == --no-project && "$3" == --python && "$4" == 3.13 ]]; shift 4
exec "$@"
''')
        self.tool('omp', '''#!/bin/bash
set -eu
case "$1" in
  plugin) [[ "$2" == list && "$3" == --json ]]; cat "$PET_TEST_PLUGIN_STATE" ;;
  install)
    [[ ${PET_TEST_INSTALL_FAIL:-0} == 0 ]] || exit 9
    printf 'install\\n' >> "$PET_TEST_LOG"
    jq -n --arg path "$2" '{npm: [{name: "omp-pet", path: $path, enabled: true}]}' > "$PET_TEST_PLUGIN_STATE" ;;
  *) exit 99 ;;
esac
''')

    def tearDown(self):
        self.temporary.cleanup()

    def tool(self, name, content):
        path = self.bin / name
        path.write_text(content)
        path.chmod(0o755)

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.upstream), *args], env=self.env,
                                       stderr=subprocess.DEVNULL, text=True)

    def run_installer(self, *args, success=True):
        result = subprocess.run([str(self.fixture / 'scripts/install-omp-pet.sh'), *args],
                                env=self.env, capture_output=True, text=True)
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result

    def test_fresh_install_and_repeat_preserve_build_and_link(self):
        self.run_installer()
        self.assertEqual(subprocess.check_output(['git', '-C', str(self.source), 'rev-parse', 'HEAD'], text=True).strip(), self.revision)
        before = (self.source / '.git/mac-dev-bootstrap-built-revision').stat().st_mtime_ns
        self.run_installer()
        self.assertEqual(self.log.read_text(), 'build\ninstall\n')
        self.assertEqual((self.source / '.git/mac-dev-bootstrap-built-revision').stat().st_mtime_ns, before)

    def test_dry_run_leaves_no_checkout_or_plugin_changes(self):
        before = self.plugins.read_bytes()
        result = self.run_installer('--dry-run')
        self.assertFalse(self.source.exists())
        self.assertFalse(self.log.exists())
        self.assertEqual(self.plugins.read_bytes(), before)
        self.assertIn(self.revision, result.stdout)
        self.assertIn('build-app.sh', result.stdout)

    def test_local_source_edits_are_preserved(self):
        self.run_installer()
        path = self.source / 'scripts/build-app.sh'
        path.write_text(path.read_text() + '# personal edit\n')
        before = path.read_bytes()
        self.run_installer(success=False)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(self.log.read_text(), 'build\ninstall\n')

    def test_other_existing_plugin_is_preserved(self):
        existing = {'npm': [{'name': 'omp-pet', 'path': str(self.root / 'personal-plugin'), 'enabled': False}]}
        self.plugins.write_text(json.dumps(existing))
        self.run_installer()
        self.assertEqual(json.loads(self.plugins.read_text()), existing)
        self.assertEqual(self.log.read_text(), 'build\n')

    def test_plugin_failure_can_be_retried_without_rebuilding(self):
        self.env['PET_TEST_INSTALL_FAIL'] = '1'
        self.run_installer(success=False)
        self.env['PET_TEST_INSTALL_FAIL'] = '0'
        self.run_installer()
        self.assertEqual(self.log.read_text(), 'build\ninstall\n')

    def test_existing_non_repository_directory_is_preserved(self):
        self.source.mkdir()
        existing = self.source / 'personal.txt'
        existing.write_text('keep me')
        self.run_installer(success=False)
        self.assertEqual(existing.read_text(), 'keep me')
        self.assertFalse(self.log.exists())
