"""Source/frozen launch, installer boundaries and reproducible-build contracts."""
import ast
import os
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

from echemtips.desktop_launcher import analysis_command, prepare_runtime
from scripts.build_windows_app import version, write_metadata, validate_payload

ROOT = Path(__file__).resolve().parents[1]


class InstalledDesktopTests(unittest.TestCase):
    def test_source_and_frozen_analysis_launch_preserves_paths(self):
        arguments = ['--data-folder', 'C:/Users/Research User/data', 'C:/Users/Research User/data/test.csv']
        with patch('sys.executable', 'C:/Program Files/eChemTips/eChemTips.exe'), patch('sys.frozen', True, create=True):
            executable, args, cwd = analysis_command(arguments)
            self.assertTrue(executable.endswith('eChemTips.exe'))
            self.assertEqual(args, ['--analysis', *arguments])
            self.assertNotIn('-m', args)
        with patch('sys.frozen', False, create=True):
            executable, args, cwd = analysis_command(arguments)
            self.assertEqual(args, ['-m', 'echemtips.analysis', *arguments])
        self.assertEqual(arguments[0], '--data-folder')

    def test_installed_workspace_is_not_the_application_directory(self):
        from PySide6 import QtCore
        original = Path.cwd()
        with tempfile.TemporaryDirectory() as folder, patch.object(QtCore.QStandardPaths, 'writableLocation', return_value=folder):
            try:
                workspace = prepare_runtime()
                self.assertEqual(workspace, Path(folder)/'eChemTips')
                self.assertEqual(Path.cwd().resolve(), workspace.resolve())
            finally:
                os.chdir(original)

    def test_installer_only_registers_opt_in_open_with_and_preserves_data(self):
        text = (ROOT/'packaging/windows/installer.iss').read_text()
        self.assertIn('PrivilegesRequired=lowest', text)
        self.assertIn('DefaultDirName={localappdata}', text)
        self.assertIn('OpenWithProgids', text)
        self.assertNotIn('UserChoice', text)
        self.assertNotIn('[UninstallDelete]', text)
        self.assertNotIn('[InstallDelete]', text)
        self.assertIn('uninsneveruninstall', text)
        self.assertIn('--analysis', text)
        self.assertIn('SignedUninstaller=yes', text)
        self.assertNotIn('.lvbitx', text)

    def test_dependency_lock_contains_only_exact_hashed_wheels(self):
        lines = (ROOT/'packaging/windows/requirements.lock').read_text().splitlines()
        packages = [line for line in lines if line and not line.startswith('#')]
        self.assertGreater(len(packages), 20)
        for line in packages:
            self.assertRegex(line, r'^[A-Za-z0-9_-]+==[A-Za-z0-9.]+ --hash=sha256:[a-f0-9]{64}$')
        self.assertTrue(any(line.startswith('PySide6==') for line in packages))
        self.assertTrue(any(line.startswith('pyinstaller==') for line in packages))

    def test_release_version_matches_package_and_resource_is_valid_python(self):
        from echemtips import __version__
        self.assertEqual(version(), __version__)
        with tempfile.TemporaryDirectory() as folder, patch('importlib.metadata.distributions', return_value=[]):
            output = Path(folder)/'metadata'
            write_metadata(output, 'example-revision')
            ast.parse((output/'version-info.txt').read_text())
            self.assertTrue((output/'LICENSE-eChemTips.txt').exists())
            self.assertIn('example-revision', (output/'build.json').read_text())

    def test_payload_refuses_private_bitfiles_credentials_and_external_binaries(self):
        with tempfile.TemporaryDirectory() as folder:
            bundle = Path(folder)
            (bundle/'eChemTips.exe').touch()
            validate_payload(bundle)
            for name in ('target.lvbitx', 'key.pfx', 'NiFpga.dll', 'ffmpeg-win64.exe'):
                with self.subTest(name=name):
                    path = bundle/name
                    path.touch()
                    with self.assertRaises(ValueError):
                        validate_payload(bundle)
                    path.unlink()


if __name__ == '__main__':
    unittest.main()
