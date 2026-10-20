# Installation and first simulation

## Requirements

- Python **3.10 or newer**; use a 64-bit interpreter for large recordings.
- A desktop environment supported by the installed Qt/PySide6 release.
- Internet during ordinary package installation. Hardware drivers are separate.

The package minimum is not a guarantee that every Python/OS/driver combination
has been hardware-tested. Retain an existing commissioned environment until a
replacement has passed the same checks.

## Choose an installation

### Windows installer previews

The **Windows application preview** GitHub Actions workflow produces a per-user
x64 installer with bundled Python, Control/Analysis Start-menu shortcuts,
optional desktop shortcuts and an optional **Open with** entry for CSV recordings.
It does not take over the default CSV application. No Python or terminal is needed
on the target computer. The initial target is **Windows 11 x64**.

Until a signed release is published, these are **unsigned test artifacts**, not
commissioned instrument distributions. Obtain them only from this repository's
successful workflow runs; compare the supplied SHA-256 checksums. Unsigned builds
can trigger SmartScreen. Do not disable security controls blindly.

Settings in `%APPDATA%\eChemTips` and recordings survive upgrades/uninstall.
New relative data paths resolve under `Documents\eChemTips`, not the application
folder. Existing settings are reused: review relative data-folder paths when moving
from a source checkout, and select an absolute recording directory. Close both apps
before upgrading; the installer will not replace a running installed application.
Updates are manual, never downloaded or applied during an experiment.

NI native drivers/NI MAX and a compatible private bitfile remain separate; see
[hardware setup](REAL_HARDWARE_SETUP.md). MP4 export in this bundle requires an
externally installed FFmpeg executable on `PATH` or `IMAGEIO_FFMPEG_EXE`; no FFmpeg
executable is redistributed. USB picomotor SDK integration is not bundled yet.
Exact versions and dependency licenses are available via **About → Bundled licenses**.
Maintainer build/signing and acceptance checks are in
[Contributing](https://github.com/aalto-ema/echemtips/blob/main/CONTRIBUTING.md#windows-application-builds).

### Source installation (all supported platforms)

Download/extract the repository from
[GitHub](https://github.com/aalto-ema/echemtips), or clone it:

```text
git clone https://github.com/aalto-ema/echemtips.git
cd echemtips
```

Open a terminal **inside the extracted repository**. Create a local environment;
activation is not required.

#### Windows (PowerShell)

Install a supported 64-bit Python from [python.org](https://www.python.org/downloads/).
The following uses the Python launcher; substitute the full path to your
interpreter if the launcher is unavailable.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe run_echemtips.py
```

#### macOS / Linux

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python run_echemtips.py
```

Use that environment's Python for subsequent commands. Avoid installing into
the system interpreter or changing global PowerShell execution policies.

## First run

1. Open Settings and select **Simulation**. Save/apply if needed.
2. Press **Connect**. Choose an experiment from the sidebar or **All experiments…**.
3. Run an approach and a small hopping scan with the default **5 pA magnitude**
   threshold. Synthetic contact signals appear inside the configured approach span.
4. Choose a writable, permanent data folder in Settings. Keep each CSV and JSON together.
5. Open **Analysis → Analyze last saved recording**, or **Open analysis app** (F6).

Simulation demonstrates workflow and recording, not experimental calibration,
noise specifications or collision avoidance. Never connect the real backend
merely to test installation.

## Analysis and optional packages

Run `python run_analysis.py` independently, using the environment's Python.
After installation, `echemtips` and `echemtips-analysis` entry points are also
available when that environment is activated.

| Extra | Purpose | Install command |
| --- | --- | --- |
| FPGA | Python NI communication interface; native drivers still required | `python -m pip install -e ".[fpga]"` |
| Analysis | Import supported legacy TDMS recordings | `python -m pip install -e ".[analysis]"` |
| Movies | Bundled FFmpeg executable for MP4 export | `python -m pip install -e ".[movies]"` |
| Docs | Build the documentation locally | `python -m pip install -e ".[docs]"` |

Extras can be combined, for example `".[fpga,analysis,movies]"`.
No private FPGA bitfile, native NI driver or external controller SDK is included.

## Updates and verification

Finish recordings and close both applications before updating. Preserve
instrument settings and a known-working software revision, update the checkout,
then repeat the relevant install command in the same environment.

```text
python -m unittest discover -v
python run_echemtips.py --smoke-test
python run_analysis.py --smoke-test
```

Smoke tests use simulation, not NI hardware. After an update that affects physical
operation, repeat the relevant [commissioning checks](REAL_HARDWARE_SETUP.md).
