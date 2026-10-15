"""Cross-platform tests for the Windows offline distribution recipe."""

import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import build_windows_offline as builder


class WindowsDistributionTests(unittest.TestCase):
    def test_existing_destination_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "already exists"):
                builder.build(Path(directory))

    def test_bundle_targets_windows_and_excludes_private_data(self):
        calls = []

        def run(command, **kwargs):
            calls.append(command)
            if "wheel" in command:
                destination = Path(command[command.index("--wheel-dir") + 1])
                (destination / "echemtips-0.1.0-py3-none-any.whl").write_bytes(b"wheel")

        def check_output(command, **kwargs):
            if command[1] == "ls-files":
                return b"README.md\0LICENSE\0pyproject.toml\0echemtips/__init__.py\0"
            if command[1] == "rev-parse":
                return "test-commit\n"
            return b""

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "kit with spaces"
            with patch.object(builder.subprocess, "run", side_effect=run), \
                    patch.object(builder.subprocess, "check_output", side_effect=check_output), \
                    patch.object(builder.urllib.request, "urlopen", return_value=io.BytesIO(b"installer")), \
                    patch.object(builder, "PYTHON_SHA256", hashlib.sha256(b"installer").hexdigest()):
                builder.build(output)
            manifest = json.loads((output / "manifest.json").read_text())
            self.assertEqual("test-commit", manifest["source_commit"])
            self.assertFalse(manifest["source_modified"])
            for entry in manifest["files"]:
                path = output / entry["path"]
                self.assertEqual(entry["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
                self.assertNotIn(".lvbitx", entry["path"])
                self.assertNotIn("data/", entry["path"])
            download = next(command for command in calls if "download" in command)
            self.assertIn("win_amd64", download)
            self.assertIn("313", download)
            self.assertIn("--only-binary=:all:", download)
            self.assertTrue((output / "Start eChemTips.vbs").exists())
            self.assertTrue((output / "run_hardware_check.py").exists())

    def test_setup_is_offline_and_does_not_connect_hardware(self):
        setup = (builder.ROOT / "scripts/Setup-Offline.ps1").read_text()
        self.assertIn("--no-index", setup)
        self.assertIn("Get-FileHash", setup)
        self.assertIn("Get-AuthenticodeSignature", setup)
        self.assertNotIn("--connect", setup)
        for name in ("Start eChemTips.vbs", "Start Analysis.vbs"):
            launcher = (builder.ROOT / name).read_text()
            self.assertIn("pythonw.exe", launcher)
            self.assertIn(".venv", launcher)


if __name__ == "__main__":
    unittest.main()
