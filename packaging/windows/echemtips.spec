# One-folder build: replaceable dynamic Qt DLLs, shared Control/Analysis runtime.
from pathlib import Path
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

root = Path(SPECPATH).parents[1]
release = Path(os.environ['ECHEMTIPS_RELEASE_METADATA'])
datas = [(str(root / 'echemtips/assets'), 'echemtips/assets'),
         (str(release), 'release-metadata')]
for package in ('echemtips', 'nifpga', 'nptdms', 'imageio_ffmpeg'):
    datas += copy_metadata(package)
datas += collect_data_files('nifpga')
hidden = collect_submodules('echemtips') + collect_submodules('nptdms') + ['imageio_ffmpeg', 'nifpga']
a = Analysis([str(root / 'packaging/windows/entry.py')], pathex=[str(root)],
             binaries=[], datas=datas, hiddenimports=hidden,
             excludes=['PyQt5', 'PyQt6', 'PySide2', 'tkinter', 'pytest'], noarchive=False)
# FFmpeg is an external optional executable, not a silently redistributed GPL binary.
a.datas = [item for item in a.datas if not ('imageio_ffmpeg' in item[0] and 'binaries' in item[0])]
a.binaries = [item for item in a.binaries if not ('imageio_ffmpeg' in item[0] and 'binaries' in item[0])]
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='eChemTips',
          debug=False, strip=False, upx=False, console=False,
          icon=str(root / 'echemtips/assets/echemtips.ico'),
          version=str(release / 'version-info.txt'))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='eChemTips')
