"""Build a versioned Windows x64 application/installer from a clean commit."""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def version() -> str:
    """Read the canonical application version without importing the GUI."""
    tree = ast.parse((ROOT / 'echemtips/__init__.py').read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == '__version__' for t in node.targets):
            value = ast.literal_eval(node.value)
            if re.fullmatch(r'\d+\.\d+\.\d+', value):
                return value
    raise ValueError('Windows releases require a canonical major.minor.patch version.')


def run(command, **kwargs):
    """Run a build tool without a shell; any failure stops artifact creation."""
    subprocess.run([str(part) for part in command], check=True, cwd=ROOT, **kwargs)


def write_metadata(destination: Path, revision: str) -> None:
    """Preserve exact versions, license texts and build provenance beside the EXE."""
    destination.mkdir(parents=True)
    shutil.copy2(ROOT / 'LICENSE', destination / 'LICENSE-eChemTips.txt')
    shutil.copy2(ROOT / 'packaging/windows/requirements.lock', destination / 'requirements.lock')
    shutil.copy2(ROOT / 'packaging/windows/README.txt', destination / 'README.txt')
    inventory = []
    for dist in sorted(importlib.metadata.distributions(), key=lambda d: d.metadata.get('Name', '').lower()):
        name = dist.metadata.get('Name', 'unknown')
        licenses = []
        for item in dist.files or ():
            lowered = str(item).lower()
            if ('license' not in lowered and 'copying' not in lowered and 'notice' not in lowered) or item.suffix.lower() in {'.py', '.pyc'}:
                continue
            source = Path(dist.locate_file(item))
            if not source.is_file():
                continue
            # No arbitrary absolute paths from a distribution RECORD enter the release.
            relative = Path(*[p for p in item.parts if p not in ('..', '.', '/')])
            target = destination / 'licenses' / re.sub(r'[^A-Za-z0-9_.-]', '_', name) / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            licenses.append(target.relative_to(destination).as_posix())
        inventory.append({'name': name, 'version': dist.version,
                          'license_expression': dist.metadata.get('License-Expression'),
                          'license': dist.metadata.get('License'), 'license_files': licenses,
                          'project_urls': dist.metadata.get_all('Project-URL', [])})
    payload = {'app_version': version(), 'source_commit': revision, 'python': sys.version,
               'created_utc': datetime.now(timezone.utc).isoformat(), 'distributions': inventory,
               'excluded': ['NI native drivers', 'FPGA bitfiles', 'Newport SDK', 'FFmpeg executable'],
               'updates': 'Manual installer replacement; no silent updates during acquisition.'}
    (destination / 'build.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
    # PyInstaller consumes this resource as executable Python, so all strings use repr.
    numbers = tuple(map(int, version().split('.'))) + (0,)
    info = (
        'VSVersionInfo(ffi=FixedFileInfo(filevers={v}, prodvers={v}, mask=0x3f, flags=0, '
        'OS=0x40004, fileType=0x1, subtype=0, date=(0,0)), kids=['
        'StringFileInfo([StringTable("040904B0", ['
        'StringStruct("CompanyName", "eChemTips contributors"),'
        'StringStruct("FileDescription", "eChemTips Control and Analysis"),'
        'StringStruct("FileVersion", {s}), StringStruct("ProductName", "eChemTips"),'
        'StringStruct("ProductVersion", {s}), StringStruct("OriginalFilename", "eChemTips.exe"),'
        'StringStruct("LegalCopyright", "eChemTips contributors; MIT license")])]),'
        'VarFileInfo([VarStruct("Translation", [1033, 1200])])])'
    ).format(v=repr(numbers), s=repr(version()))
    (destination / 'version-info.txt').write_text(info, encoding='utf-8')


def build(output: Path, iscc: str, certificate: str | None = None,
          timestamp_url: str | None = None) -> None:
    """Build only on Windows, preserving user files and refusing stale outputs."""
    if sys.platform != 'win32' or struct.calcsize('P') != 8 or sys.version_info[:3] != (3, 13, 16):
        raise ValueError('Build in a clean Windows x64 CPython 3.13.16 environment using requirements.lock.')
    if certificate and (not re.fullmatch(r'[A-Fa-f0-9]{40}', certificate) or
                        not timestamp_url or not re.fullmatch(r'https://[A-Za-z0-9./:_-]+', timestamp_url)):
        raise ValueError('Signing needs an explicit certificate-store SHA1 thumbprint and HTTPS timestamp URL.')
    if timestamp_url and not certificate:
        raise ValueError('A timestamp URL requires an explicitly selected signing certificate.')
    output = output.resolve()
    if output.exists():
        raise ValueError('Choose a fresh build directory; releases are never overwritten.')
    dirty = subprocess.check_output(['git', 'diff', 'HEAD', '--'], cwd=ROOT)
    if dirty:
        raise ValueError('Commit tracked source changes before building a release.')
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    output.mkdir(parents=True)
    metadata = output / 'metadata'
    write_metadata(metadata, revision)
    environment = dict(os.environ, ECHEMTIPS_RELEASE_METADATA=str(metadata))
    run([sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
         '--distpath', output / 'app', '--workpath', output / 'work',
         ROOT / 'packaging/windows/echemtips.spec'], env=environment)
    bundle = output / 'app/eChemTips'
    executable = bundle / 'eChemTips.exe'
    if certificate:
        run(['signtool', 'sign', '/sha1', certificate, '/fd', 'SHA256',
             '/tr', timestamp_url, '/td', 'SHA256', executable])
        run(['signtool', 'verify', '/pa', executable])
    artifacts = output / 'artifacts'
    artifacts.mkdir()
    run([executable, '--package-check', artifacts / 'package-check.json'], timeout=180)
    report = json.loads((artifacts / 'package-check.json').read_text(encoding='utf-8'))
    if report.get('result') != 'passed' or not report.get('frozen'):
        raise RuntimeError('The frozen application did not pass its package check.')
    command = [iscc, f'/DAppVersion={version()}', f'/DBundleDir={bundle}', f'/DArtifactDir={artifacts}']
    if certificate:
        command += ['/DSignedBuild', f'/Srelease=signtool sign /sha1 {certificate} /fd SHA256 /tr {timestamp_url} /td SHA256 $f']
    command.append(ROOT / 'packaging/windows/installer.iss')
    run(command)
    installer = artifacts / f'eChemTips-{version()}-windows-x64-setup.exe'
    if certificate:
        run(['signtool', 'verify', '/pa', installer])
    # Only Git-tracked sources, never an entire local working tree or personal data.
    run(['git', 'archive', '--format=zip', '--prefix=echemtips-source/',
         f'--output={artifacts / "echemtips-source.zip"}', 'HEAD'])
    shutil.copy2(metadata / 'build.json', artifacts / 'build.json')
    hashes = [f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}'
              for path in sorted(artifacts.iterdir()) if path.is_file()]
    (artifacts / 'SHA256SUMS.txt').write_text('\n'.join(hashes) + '\n', encoding='utf-8')
    print(f'Built {"signed" if certificate else "UNSIGNED preview"}: {installer}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--iscc', default=r'C:\Program Files (x86)\Inno Setup 6\ISCC.exe')
    parser.add_argument('--certificate-thumbprint')
    parser.add_argument('--timestamp-url')
    args = parser.parse_args()
    build(args.output, args.iscc, args.certificate_thumbprint, args.timestamp_url)
