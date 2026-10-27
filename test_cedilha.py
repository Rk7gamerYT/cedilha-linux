import json
import os
from pathlib import Path
import subprocess
import shutil
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('cedilha.py')


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.env = {**os.environ, 'HOME': str(self.home),
                    'XDG_CONFIG_HOME': str(self.home / '.config'),
                    'XDG_DATA_HOME': str(self.home / '.local/share'),
                    'XDG_STATE_HOME': str(self.home / '.local/state')}

    def run_script(self, *args, ok=True):
        r = subprocess.run([sys.executable, str(SCRIPT), *args], env=self.env,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode == 0, ok, r.stdout + r.stderr)
        return r

    def test_preserve_idempotent_restore(self):
        compose = self.home / '.XCompose'
        compose.write_text('include "%L"\n# regra pessoal\n')
        profile = self.home / '.profile'
        profile.write_text('export TESTE=1\n')
        before = {p: p.read_bytes() for p in [compose, profile]}
        self.run_script('install', '--no-flatpak')
        after = compose.read_bytes()
        self.assertIn(b'# regra pessoal', after)
        self.run_script('install', '--no-flatpak')
        self.assertEqual(after, compose.read_bytes())
        self.run_script('uninstall')
        for path, data in before.items():
            self.assertEqual(path.read_bytes(), data)
        self.assertFalse((self.home / '.config/environment.d/99-cedilha-linux.conf').exists())

    def test_refuse_to_erase_later_edits(self):
        self.run_script('install', '--no-flatpak')
        p = self.home / '.profile'
        p.write_text(p.read_text() + '# alteração posterior\n')
        self.run_script('uninstall', ok=False)
        self.assertIn('alteração posterior', p.read_text())
        self.assertTrue((self.home / '.XCompose').exists())

    def test_input_methods_opt_in(self):
        self.run_script('install', '--no-flatpak')
        p = self.home / '.config/environment.d/99-cedilha-linux.conf'
        self.assertNotIn('GTK_IM_MODULE', p.read_text())
        self.run_script('uninstall')
        self.run_script('install', '--no-flatpak', '--force-input-methods')
        self.assertIn('GTK_IM_MODULE="cedilla"', p.read_text())
        self.assertIn('QT_IM_MODULE="compose"', p.read_text())

    @unittest.skipUnless(shutil.which('flatpak'), 'Flatpak não instalado')
    def test_real_flatpak_override_preserves_and_restores(self):
        override = self.home / '.local/share/flatpak/overrides/global'
        override.parent.mkdir(parents=True)
        original = '[Environment]\nTEST_CEDILHA=preservar\n'
        override.write_text(original)
        self.run_script('install')
        content = override.read_text()
        self.assertIn('TEST_CEDILHA=preservar', content)
        self.assertIn('XCOMPOSEFILE=', content)
        self.assertIn('.XCompose:ro', content)
        self.run_script('uninstall')
        self.assertEqual(override.read_text(), original)

    def test_flatpak_args_and_rollback_on_failure(self):
        binpath = self.home / 'bin'
        binpath.mkdir()
        fake = binpath / 'flatpak'
        fake.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "$HOME/args"\nexit 1\n')
        fake.chmod(0o755)
        self.env['PATH'] = str(binpath) + ':' + self.env['PATH']
        self.run_script('install', ok=False)
        self.assertIn('--user', (self.home / 'args').read_text())
        self.assertIn('--filesystem=', (self.home / 'args').read_text())
        self.assertFalse((self.home / '.XCompose').exists())
        self.assertFalse((self.home / '.profile').exists())


if __name__ == '__main__':
    unittest.main()
