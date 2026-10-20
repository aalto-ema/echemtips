# Contributing to eChemTips

eChemTips controls research hardware. Changes should remain easy to review,
reproduce in Simulation, and commission deliberately on the instrument. A unit
test passing against a fake FPGA session is necessary evidence, not permission
to energize real outputs.

## Development setup

Use a supported 64-bit CPython meeting the package minimum. Keep a commissioned
hardware environment pinned until a replacement has passed physical verification.
The [installation guide](docs/INSTALLATION.md) includes Windows commands.

```bash
git clone https://github.com/aalto-ema/echemtips.git
cd echemtips
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[analysis]"
python -m unittest discover -s tests -v
python run_echemtips.py --smoke-test
python run_analysis.py --smoke-test
```

Install `.[fpga]` only on a system with the required NI runtime when working on
the real backend. Normal tests must not require an NI device, private bitfile,
or legacy LabVIEW checkout.

## Repository boundaries

Never commit:

- LabVIEW `.vi`, `.lvproj`, or related private legacy sources;
- compiled `.lvbitx` images or FPGA binaries;
- local settings, calibration records, experimental data, or patient/sample
  identifiers;
- virtual environments, caches, generated build products, or editor state.

The `.gitignore` is a guard, not authorization to place sensitive material in
the working tree. Check `git status --short` and the staged diff before every
commit.

## Change workflow

1. Start from a clean branch based on the latest `main`.
2. Reproduce the behavior in Simulation or a fake-session test.
3. Make one coherent change. Preserve unrelated user changes.
4. Add tests at the lowest useful boundary: pure calculation, state machine,
   protocol/fake session, recording, or Qt smoke/layout.
5. Update operator, data, settings, integration, or commissioning documentation
   when behavior or semantics change.
6. Run the complete test and smoke-test commands.
7. Review the diff for unsafe output changes, stale names/units, private files,
   and unbounded recording/rendering behavior.
8. Use a focused commit message that describes the outcome.

## Design rules

- Keep experiment policy in `experiments.py` and parameter validation in
  `models.py`; do not duplicate protocol conversion in UI pages.
- Keep deterministic target framing/scaling in `ni_protocol.py`, common
  physical plans in `waypoints.py`, and NI execution ownership in
  `ni_driver.py`.
- Access hardware through `InstrumentBackend`. UI code must not open NI
  sessions or read/write registers directly.
- Preserve one owner per program, complete 14-word FIFO framing, final
  acquisition drain, and explicit terminal recording state.
- Full-rate recording and display decimation are separate responsibilities.
  Never improve plot responsiveness by dropping recorder input silently.
- Keep simulator and hardware stage semantics aligned, particularly contact,
  end-of-travel, settling, retract, cancellation, and completion.
- Treat Current 1/2, E1/E2, and commanded/measured position terminology and
  units consistently.
- Do not broaden hardware support by guessing register names or bitfile
  compatibility. Add a target profile only with its independently verified
  contract and commissioning plan.

## Safety review for hardware-affecting changes

Call out changes to startup, motion, voltage conversion, feedback, pause, stop,
watchdog, FIFO framing, or completion semantics in the pull request. Include:

- the old and new physical behavior;
- limits and failure state;
- simulator and fake-session evidence;
- whether the bitfile changes (normally it must not);
- the smallest staged hardware test required;
- rollback and recovery steps.

Do not make automated tests connect to `RIO0` by default. A physical test must
require an explicit operator action, exact target/resource, prepared hardware,
and the procedure in `docs/REAL_HARDWARE_SETUP.md`.

## Tests and evidence

| Area | Preferred evidence | What it does not prove |
| --- | --- | --- |
| Models/calculations | focused `unittest` cases | physical calibration |
| Experiment state machines | deterministic `SimulationBackend` tests | FPGA timing or wiring |
| NI protocol/driver | fake registers/FIFOs and `.lvbitx` inspection | NI driver compatibility or analog response |
| Acquisition/recording | backlog, drain, failure, round-trip tests | storage reliability for a particular long run |
| Qt UI | offscreen layout and smoke tests | every screen/DPI combination or operator comprehension |
| Physical commissioning | signed instrument record and saved traces | behavior after an unreviewed hardware/software change |

When fixing a bug, add a test that fails for the original behavior whenever it
can be expressed safely without hardware.

## Documentation style

Write for one of four audiences: simulator user, instrument operator, data
analyst, or developer. Lead with the action or contract, give every physical
quantity a unit, and label unverified hardware statements explicitly. Prefer
links to source definitions over copying values into multiple documents.

Keep public instructions hardware-brand-independent while stating exact protocol
constraints. Instrument-specific worksheets, historical audits and local installer
notes belong in ignored local documentation, not the published site. Keep one
canonical explanation per topic and link to it instead of adding a page for
each small feature. Every public documentation page must appear in the navigation;
merely removing a page from the menu does not prevent publication or search.

Install `.[docs]` and run `python -m mkdocs build --strict` when changing the site.
Update the operator guide, recording format or hardware contract when semantics
change. Do not describe planned capabilities as implemented features.

## Issues and pull requests

Bug reports should include the eChemTips commit, platform and Python version,
backend, experiment, exact message, minimal reproduction, and recording status.
For hardware reports use the template in `docs/TROUBLESHOOTING.md`, removing
private paths and data before posting publicly.

## Windows application builds

The repository has a separate **Windows application preview** workflow.
It builds on Windows, not by cross-compiling a macOS environment. Runtime/build
wheels are pinned with SHA-256 hashes in `packaging/windows/requirements.lock`;
GitHub Actions are pinned to release commits. This fixes dependency inputs, not
byte-for-byte executable reproducibility (timestamps and code signing vary).

Build in a clean Windows 11 x64 CPython **3.13.16** virtual environment:

```powershell
python -m pip install --require-hashes --only-binary=:all: -r packaging/windows/requirements.lock
python -m pip install --no-deps --no-build-isolation .
python -m pip check
python scripts/build_windows_app.py --output build/windows-preview
```

Inno Setup 6 (`ISCC.exe`, default standard installation path) is required to build
the installer. GitHub's Windows runner provides it; install it separately for a
local build, or pass `--iscc` with its full path. A clean committed tree is required;
artifacts go to a fresh output directory. No local data, bitfiles or SDKs are copied.
The artifact contains the installer, exact Git source archive, version/license
inventory, frozen simulation check and checksums. PyInstaller uses one-folder
deployment with replaceable Qt DLLs, not static Qt linkage. Both shortcuts use the
same executable, with `--analysis` dispatch; recording paths with spaces remain
separate arguments. There are no silent automatic updates.

Signing is **not configured in CI**. A release maintainer with a suitable trusted
code-signing certificate in the Windows certificate store and `signtool` on PATH
can explicitly add:

```powershell
python scripts/build_windows_app.py --output build/windows-signed --certificate-thumbprint CERTIFICATE_SHA1_THUMBPRINT --timestamp-url https://YOUR_CERTIFICATE_AUTHORITY_TIMESTAMP_SERVICE
```

This signs/verifies the app and requests signed installer/uninstaller generation.
Never commit certificates, PFX files or passwords. Choose certificate ownership,
protected signing infrastructure and release hosting separately. Public release
publication is intentionally manual. Do not describe unsigned previews as signed.
Before distributing, review third-party notices, LGPL library-replacement and
corresponding-source obligations for the precise versions in `build.json`.
FFmpeg executables, proprietary drivers, FPGA images and controller SDKs are excluded.

### Windows acceptance checklist

CI checks frozen imports, all pages, a two-landing simulation, the transient solver,
per-user install/upgrade/uninstall with spaces, shortcuts, opt-in file association,
high-DPI offscreen rendering and preservation of an existing settings-file sentinel.
These automated checks do **not** replace clean physical Windows validation:

- Install without Python/LabVIEW/NI present; run Control and Analysis from shortcuts.
- Use 100%, 150% and 200% scaling; inspect plots, dialogs and icons on a laptop.
- Record a small simulated scan in a path with spaces; open its CSV via **Open with**,
  drag/drop, and F6 from Control, then export a figure and reopen the recording.
- Upgrade with an existing real settings/navigation profile; compare values and data.
- Confirm installer refuses replacement while either installed app is running.
- Uninstall; verify settings/calibration/recordings remain and shortcuts/association go.
- Verify signatures and publisher for a signed build; test offline installation.
- Only after NI drivers and a compatible private bitfile are commissioned, perform
  the separate hardware checks. CI never opens NI sessions.

Keep issue #14 open until signing and clean-host operator checks have evidence.
