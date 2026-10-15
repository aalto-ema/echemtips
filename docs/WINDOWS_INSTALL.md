# First installation on Windows (including offline computers)

## Recommended: offline installation kit

The kit targets **64-bit Intel/AMD Windows 10/11**. Check separately that your
Windows release is supported by the NI driver for your exact device. This is
an offline **installation kit**, not a portable installed environment: copy it
to a permanent writable local directory **before** setup. Do not run from a
USB drive, network share or synced laboratory folder. No Git, system Python,
PowerShell activation or internet connection is needed on the destination for
the Python application installation. Drivers remain separate.

1. Copy the whole `offline_windows` directory to, for example,
   `C:\Users\YOURNAME\Applications\eChemTips`. Keep all its subdirectories.
2. Double-click **Setup-Offline.cmd**. It verifies payload checksums, runs the
   signed Python installer, installs the bundled wheels without contacting
   PyPI, checks imports and creates desktop shortcuts for control and analysis.
   Keep the setup window open if an error occurs and save the message.
3. Double-click **eChemTips** on the desktop (or **Start eChemTips.vbs** in
   the folder). **Start Analysis.vbs** launches analysis independently. These
   launchers do not leave a command window open.
4. Select **Simulation**, connect, and test an approach and a short scan.
   Choose a permanent **data folder** in Settings and save defaults. Operator
   settings are per-user; they are not copied from the build computer.
5. For real hardware, complete the NI and instrument steps below before
   connecting. Successful installation is not hardware commissioning.

The kit uses CPython 3.13.16 and includes FPGA communication, TDMS analysis,
and MP4 export dependencies. The older commissioning guide recommends Python
3.11; **this newer Windows runtime still requires Windows/hardware validation**.
No claim of hardware qualification follows from a successful package download
or a simulation test on macOS. The kit is not a signed Windows application
installer and may need approval from institutional IT. Do not disable antivirus
or organization policies. VBScript/Windows Script Host and PowerShell must be
allowed; if they are blocked, ask IT to approve a launcher or use
`runtime\python.exe -m echemtips.app` temporarily.

Python is installed for the current user into `runtime`, without changing PATH.
The official installer may require additional handling if the same Python
release is already installed elsewhere; ask IT rather than uninstalling an
existing interpreter. Do not move an installed kit or copy its `runtime` to a
second PC. Use the original, uninstalled kit on each PC. Keep the original kit
as a reproducibility snapshot; rebuild a fresh kit for updates, not a mixture
of old and new wheels.

Startup errors are saved under `%LOCALAPPDATA%\eChemTips\logs` as
`control.log` and `analysis.log`. Setup checks neither connect to NI hardware
nor run FPGA outputs. The normal application connection procedure still applies.

## Prepare a kit on an internet-connected computer

From an up-to-date checkout on macOS, Linux or Windows, using Python 3.11+
with pip:

```text
python scripts/build_windows_offline.py
```

On this project's Mac virtual environment, use
`.venv/bin/python scripts/build_windows_offline.py` instead. The builder
downloads **Windows** wheels, not Mac packages. It refuses to overwrite an
existing output folder. Use `--output ANOTHER_NEW_FOLDER` for later builds;
keep such custom destinations outside Git or explicitly ignore them.

The default `offline_windows/` is Git-ignored. It includes the current tracked
application source in an installable wheel, Windows dependency wheels, the
official Python installer, local launchers, instructions and a SHA-256 manifest
with source commit and modification status. The build needs internet, pip and
Git; the target needs none of those preinstalled. The manifest detects accidental
corruption, not malicious replacement of the entire kit. Preserve third-party
licenses included in the wheels and installer. Allow hundreds of MB of space
for the kit and more for the installed environment.

No recordings, saved settings, private FPGA bitfiles, NI drivers or Newport SDK
are included. Build dependencies are only needed on the connected build machine.
Newport/pythonnet is not part of this initial kit; use the separate
[picomotor guide](PICOMOTOR_TEST.md) when commissioning that hardware.

## NI hardware: additional steps

1. Obtain the **full offline installer** for the NI-RIO/R Series driver release
   supported by your NI device and Windows version, including NI MAX and FPGA
   Interface support. A small web installer is not sufficient offline.
   NI describes [individual offline installers](https://knowledge.ni.com/KnowledgeArticleDetails?id=kA03q000000YGjPCAW)
   and [offline feeds](https://knowledge.ni.com/KnowledgeArticleDetails?id=kA03q000000YGejCAG).
   Installing drivers can require administrator privileges and a restart.
2. Verify the NI device appears in **NI MAX**, and note its resource (often
   `RIO0`). Python packages cannot replace native NI drivers.
3. Copy your private, device-compatible `.lvbitx` through your laboratory's
   approved process. Select it in Settings. It is deliberately not in the kit
   or GitHub; no LabVIEW source/compiler is bundled.
4. Enter and independently check piezo ranges, amplifier sensitivity, polarity,
   command ratio and acquisition settings. Do not copy another instrument's
   calibration without verification.
5. Follow the staged [real-hardware setup](REAL_HARDWARE_SETUP.md), starting
   with the probe away from the surface. **FPGA initialization can change
   physical outputs**, so installing the app is not permission to connect
   near a sample. For commands in that guide, use `runtime\python.exe` in
   place of its virtual-environment Python.

## Alternative: ordinary online source installation

Install 64-bit Python and Git, clone
`https://github.com/aalto-ema/echemtips.git`, and open a terminal once:

```powershell
cd C:\path\to\echemtips
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[fpga,analysis,movies]"
```

Then double-click **Start eChemTips.vbs** or **Start Analysis.vbs**. You can
create Windows shortcuts to those files. No environment activation is needed.
For an existing commissioned 3.11 setup, retain that tested interpreter rather
than upgrading the instrument during an experiment.

Python installer reference:
[Python 3.13.16](https://www.python.org/downloads/release/python-31316/).
