"""Exercise release setup with isolated homes and fake OMP/app-download commands."""
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
        self.temporary = tempfile.TemporaryDirectory(prefix='pet release installer ')
        self.root = Path(self.temporary.name)
        self.fixture = self.root / 'bootstrap'
        (self.fixture / 'scripts').mkdir(parents=True)
        (self.fixture / 'config').mkdir()
        for name in ('install-omp-pet.sh', 'doctor-omp-pet.sh'):
            shutil.copy2(ROOT / 'scripts' / name, self.fixture / 'scripts' / name)
        common = (ROOT / 'scripts/common.sh').read_text()
        (self.fixture / 'scripts/common.sh').write_text(common.replace('load_brew() {', 'load_brew() {\n  return 0'))
        (self.fixture / 'config/omp-pet.release').write_text('v0.1.2\n')
        self.home = self.root / 'home with spaces'
        self.home.mkdir()
        self.plugin = self.root / 'plugin with spaces'
        self.app = self.home / 'Library/Application Support/OMP Pet/apps/0.1.2/OMP Pet.app'
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.log = self.root / 'invocations'
        self.plugins = self.root / 'plugins.json'
        self.plugins.write_text('{"npm": []}\n')
        self.env = dict(os.environ, HOME=str(self.home), PATH=str(self.bin) + ':' + os.environ['PATH'],
                        PET_TEST_LOG=str(self.log), PET_TEST_PLUGIN_STATE=str(self.plugins),
                        PET_TEST_PLUGIN_DIR=str(self.plugin), PET_TEST_APP=str(self.app))
        for key in ('OMP_PET_APP', 'OMP_PET_DIR', 'OMP_PET_GIT_URL'):
            self.env.pop(key, None)
        self.tool('uname', '''#!/bin/sh
case "$1" in
  -s) echo Darwin ;;
  -m) echo "${PET_TEST_ARCH:-arm64}" ;;
  *) exit 99 ;;
esac
''')
        self.tool('sysctl', '#!/bin/sh\necho 0\n')
        self.tool('mise', '''#!/bin/bash
set -eu
[[ "$1" == -C ]]; shift 2
[[ "$1" == exec ]]; shift
if [[ "$1" == github:can1357/oh-my-pi ]]; then
  shift
  [[ "$1" == -- && "$2" == omp ]]; shift 2
  exec "$(dirname "$0")/managed-omp" "$@"
fi
[[ "$1" == -- && "$2" == bun ]]; shift 2
exec "$(dirname "$0")/bun" "$@"
''')
        self.tool('managed-omp', '''#!/bin/bash
set -eu
case "$1" in
  --version) printf '18.5.1\\n' ;;
  plugin)
    case "$2" in
      list) [[ "$3" == --json ]]; cat "$PET_TEST_PLUGIN_STATE" ;;
      install)
        [[ "$3" == github:sohamb117/omp-pet#v0.1.2 ]]
        [[ ${PET_TEST_INSTALL_FAIL:-0} == 0 ]] || exit 9
        printf 'install\\n' >> "$PET_TEST_LOG"
        mkdir -p "$PET_TEST_PLUGIN_DIR/extension"
        touch "$PET_TEST_PLUGIN_DIR/extension/installer.ts"
        jq -n --arg path "$PET_TEST_PLUGIN_DIR" '{npm: [{name: "omp-pet", version: "0.1.2", path: $path, enabled: true}]}' > "$PET_TEST_PLUGIN_STATE" ;;
      *) exit 99 ;;
    esac ;;
  *) exit 99 ;;
esac
''')
        self.tool('bun', '''#!/bin/bash
set -eu
[[ "$1" == -e && "$2" == *ensurePetApp* && "$3" == "$PET_TEST_PLUGIN_DIR/extension/installer.ts" ]]
[[ ${PET_TEST_DOWNLOAD_FAIL:-0} == 0 ]] || exit 8
if [[ ! -x "$PET_TEST_APP/Contents/MacOS/omp-pet" ]]; then
  printf 'download\\n' >> "$PET_TEST_LOG"
  mkdir -p "$PET_TEST_APP/Contents/MacOS"
  printf '#!/bin/sh\\nexit 0\\n' > "$PET_TEST_APP/Contents/MacOS/omp-pet"
  chmod +x "$PET_TEST_APP/Contents/MacOS/omp-pet"
fi
printf '%s\\n' "$PET_TEST_APP"
''')
        # No ambient OMP, Git/source build or app launch may be used.
        for name in ('omp', 'git', 'cargo', 'uv', 'open'):
            self.tool(name, '#!/bin/sh\necho "unexpected command" >&2\nexit 88\n')

    def tearDown(self):
        self.temporary.cleanup()

    def tool(self, name, content):
        path = self.bin / name
        path.write_text(content)
        path.chmod(0o755)

    def run_script(self, name='install-omp-pet.sh', *args, success=True):
        result = subprocess.run([str(self.fixture / 'scripts' / name), *args],
                                env=self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)
        return result

    def test_fresh_install_and_repeat_reuse_plugin_and_app(self):
        self.run_script()
        executable = self.app / 'Contents/MacOS/omp-pet'
        before = executable.stat().st_mtime_ns
        self.run_script()
        self.assertEqual(self.log.read_text(), 'install\ndownload\n')
        self.assertEqual(executable.stat().st_mtime_ns, before)
        self.run_script('doctor-omp-pet.sh')

    def test_dry_run_leaves_no_plugin_or_app_changes(self):
        before = self.plugins.read_bytes()
        result = self.run_script('install-omp-pet.sh', '--dry-run')
        self.assertFalse(self.plugin.exists())
        self.assertFalse(self.app.exists())
        self.assertFalse(self.log.exists())
        self.assertEqual(self.plugins.read_bytes(), before)
        self.assertIn('github:sohamb117/omp-pet#v0.1.2', result.stdout)
        self.assertNotIn('cargo', result.stdout)

    def test_existing_other_version_is_preserved(self):
        existing = {'npm': [{'name': 'omp-pet', 'version': '0.0.9', 'path': str(self.root / 'personal-plugin'), 'enabled': True}]}
        self.plugins.write_text(json.dumps(existing))
        self.run_script()
        self.assertEqual(json.loads(self.plugins.read_text()), existing)
        self.assertFalse(self.log.exists())

    def test_disabled_plugin_is_preserved(self):
        self.run_script()
        existing = json.loads(self.plugins.read_text())
        existing['npm'][0]['enabled'] = False
        self.plugins.write_text(json.dumps(existing))
        self.run_script()
        self.assertEqual(json.loads(self.plugins.read_text()), existing)
        self.assertEqual(self.log.read_text(), 'install\ndownload\n')
        self.run_script('doctor-omp-pet.sh', success=False)

    def test_plugin_failure_is_retryable(self):
        self.env['PET_TEST_INSTALL_FAIL'] = '1'
        self.run_script(success=False)
        self.assertFalse(self.app.exists())
        self.env['PET_TEST_INSTALL_FAIL'] = '0'
        self.run_script()
        self.assertEqual(self.log.read_text(), 'install\ndownload\n')

    def test_download_failure_reuses_installed_plugin_on_retry(self):
        self.env['PET_TEST_DOWNLOAD_FAIL'] = '1'
        self.run_script(success=False)
        self.assertFalse(self.app.exists())
        self.env['PET_TEST_DOWNLOAD_FAIL'] = '0'
        self.run_script()
        self.assertEqual(self.log.read_text(), 'install\ndownload\n')

    def test_legacy_checkout_is_untouched(self):
        legacy = self.home / '.local/share/mac-dev-bootstrap/omp-pet'
        legacy.mkdir(parents=True)
        source = legacy / 'personal.txt'
        source.write_text('keep my old checkout')
        self.run_script()
        self.assertEqual(source.read_text(), 'keep my old checkout')
        self.assertEqual(list(legacy.iterdir()), [source])

    def test_intel_skips_without_source_fallback(self):
        self.env['PET_TEST_ARCH'] = 'x86_64'
        self.run_script()
        self.run_script('doctor-omp-pet.sh')
        self.assertFalse(self.plugin.exists())
        self.assertFalse(self.log.exists())

    def test_doctor_checks_release_cache_and_reports_missing_app(self):
        self.run_script()
        self.run_script('doctor-omp-pet.sh')
        (self.app / 'Contents/MacOS/omp-pet').unlink()
        self.run_script('doctor-omp-pet.sh', success=False)

    def test_doctor_honors_app_override(self):
        self.run_script()
        alternate = self.root / 'custom app/Contents/MacOS/omp-pet'
        alternate.parent.mkdir(parents=True)
        shutil.copy2(self.app / 'Contents/MacOS/omp-pet', alternate)
        (self.app / 'Contents/MacOS/omp-pet').unlink()
        self.env['OMP_PET_APP'] = str(alternate.parents[2])
        self.run_script('doctor-omp-pet.sh')
