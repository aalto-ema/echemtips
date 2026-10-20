eChemTips Windows preview
========================

This is research software. Validate in Simulation before configuring real hardware.
No Python installation is needed. Use the Control and Analysis Start-menu shortcuts.
Control also opens Analysis with F6 without disturbing acquisition.

The installer runs per user. Settings remain in %APPDATA%\eChemTips. New relative
recording paths resolve under Documents\eChemTips, not the installation directory.
Existing settings are reused; review any relative data paths after moving from a
source checkout. Choose an absolute data folder for reproducible operation.
Updates are manual: finish recordings, disconnect deliberately, close both apps,
back up settings/calibration, then install the new version. Uninstall preserves data.

The native NI runtime/NI MAX for the exact device/OS and a compatible privately
obtained FPGA bitfile are separate prerequisites. The nifpga Python interface is
included, but no proprietary NI drivers, bitfiles, LabVIEW or controller SDKs are
distributed. Installing this app does not establish target compatibility.

MP4 export requires a separately installed FFmpeg executable. Add it to PATH or
set IMAGEIO_FFMPEG_EXE to its full path before starting the app. The GPL FFmpeg
binary shipped in some Python wheels is deliberately excluded from this bundle.
Picomotor USB SDK integration is not included in this first Windows bundle.

Licenses and exact versions are under this folder's licenses/ and build.json.
eChemTips source is MIT licensed; libraries retain their own licenses. Qt/PySide6
is dynamically linked under LGPL terms. Compatible library replacements may be
placed in the bundle's _internal folder; no integrity restriction prevents this.
Rebuild instructions and source accompany the artifact. Obtain the corresponding
Qt/PySide source release matching build.json from https://download.qt.io/archive/
and https://code.qt.io/cgit/pyside/pyside-setup.git/ . Release maintainers must
verify complete corresponding-source and license obligations before redistribution.
FFmpeg, NI and externally installed software have separate terms.

Unsigned preview installers can raise Windows SmartScreen warnings. Do not disable
system protection blindly: verify the source, SHA256SUMS and publisher. The build
supports a deliberately chosen code-signing certificate; no certificate is included.

Documentation: https://aalto-ema.github.io/echemtips/
Support: https://github.com/aalto-ema/echemtips/issues
