"""Build a local-only Windows x64 offline installation kit, even from macOS.

Requires internet, Git, Python 3.11+ and pip on the build machine. The target
does not require Git, a preinstalled Python, or internet for Python packages.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import urllib.request


ROOT = Path(__file__).resolve().parent.parent
PYTHON_VERSION = "3.13.16"
PYTHON_URL = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/python-{PYTHON_VERSION}-amd64.exe"
PYTHON_SHA256 = "fb4f9f5d438b2396da0086dc70b935c530cb578e37adc6d354f7ad2037fee83b"


def build(output: Path) -> None:
    """Resolve Windows wheels and package only tracked public project files."""
    output = output.resolve()
    if output.exists():
        raise ValueError(f"Output already exists; choose a fresh directory: {output}")
    output.mkdir(parents=True)
    wheels = output / "wheelhouse"
    wheels.mkdir()
    installers = output / "installers"
    installers.mkdir()
    # Never copy recordings, settings, private bitfiles, .git, or a Mac venv.
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    with tempfile.TemporaryDirectory(prefix="echemtips-build-") as temporary:
        source = Path(temporary) / "source"
        source.mkdir()
        for name in tracked:
            if not name or not (name.startswith("echemtips/") or name in ("pyproject.toml", "README.md", "LICENSE")):
                continue
            destination = source / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, destination)
        subprocess.run([sys.executable, "-m", "pip", "wheel", "--no-deps", "--wheel-dir", str(wheels), str(source)], check=True)
    project_wheel, = wheels.glob("echemtips-*.whl")
    subprocess.run([
        sys.executable, "-m", "pip", "download", "--dest", str(wheels),
        "--only-binary=:all:", "--platform", "win_amd64", "--python-version", "313",
        "--implementation", "cp", "--abi", "cp313",
        str(project_wheel) + "[fpga,analysis,movies]",
    ], check=True)
    installer = installers / "python-installer.exe"
    print(f"Downloading Windows Python {PYTHON_VERSION}", flush=True)
    with urllib.request.urlopen(PYTHON_URL, timeout=120) as response, installer.open("wb") as stream:
        shutil.copyfileobj(response, stream)
    if hashlib.sha256(installer.read_bytes()).hexdigest() != PYTHON_SHA256:
        raise ValueError("Python installer SHA-256 mismatch; do not use this kit")
    for name in ("Start eChemTips.vbs", "Start Analysis.vbs", "LICENSE", "run_echemtips.py", "run_analysis.py", "run_hardware_check.py"):
        shutil.copy2(ROOT / name, output / name)
    for name in tracked:
        if name.startswith("docs/") and (ROOT / name).is_file():
            destination = output / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, destination)
    (output / "scripts").mkdir()
    shutil.copy2(ROOT / "scripts/windows_launch.pyw", output / "scripts/windows_launch.pyw")
    for name in ("Setup-Offline.cmd", "Setup-Offline.ps1"):
        shutil.copy2(ROOT / "scripts" / name, output / name)
    (output / "READ-ME-FIRST.md").write_text(
        "# eChemTips offline installation for Windows x64\n\n"
        "Copy this entire folder to a permanent writable local directory, then "
        "double-click **Setup-Offline.cmd**. After setup, use the desktop shortcuts "
        "or **Start eChemTips.vbs** / **Start Analysis.vbs**. Test Simulation first.\n\n"
        "See [the public installation guide](docs/INSTALLATION.md) for "
        "NI driver requirements, private FPGA bitfiles and troubleshooting. "
        "Those hardware components are not included. This kit still needs a "
        "first validation on Windows; it was prepared on the build computer.\n",
        encoding="utf-8",
    )
    (output / "docs").mkdir(exist_ok=True)
    shutil.copy2(ROOT / "docs/INSTALLATION.md", output / "docs/INSTALLATION.md")
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = bool(subprocess.check_output(["git", "diff", "HEAD", "--", "echemtips", "pyproject.toml"], cwd=ROOT))
    payload = sorted(p for p in output.rglob("*") if p.is_file())
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(), "source_commit": revision,
        "source_modified": dirty, "target": "Windows x64 CPython 3.13", "python_version": PYTHON_VERSION,
        "files": [{"path": p.relative_to(output).as_posix(), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in payload],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Offline kit ready: {output}\nCopy the entire folder; double-click Setup-Offline.cmd on Windows.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "offline_windows")
    args = parser.parse_args()
    build(args.output)
