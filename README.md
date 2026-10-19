# eChemTips

Python control and analysis software for custom scanning electrochemical cell
microscopy (SECCM) instruments, built around the **WEC-SPM FPGA protocol**.

[Documentation](https://aalto-ema.github.io/echemtips/) ·
[Installation](docs/INSTALLATION.md) ·
[Report a bug or suggest a feature](https://github.com/aalto-ema/echemtips/issues)

## What can I do?

- Run CV or one-way LSV, approach + voltammetry, scan-rate series and potential-step I–t.
- Acquire hopping maps, with optional conditioning holds and two-speed Z motion.
- Explore combinatorial measurement recipes and experimental adaptive spatial sampling.
- Monitor current/position, move piezos and record full-rate CSV data with JSON metadata.
- Analyze recordings: cycle selection, smoothing, maps, topography, reference conversion,
  quantitative selections, publication figures and map movies.

The **simulator needs no instrument**. Its synthetic contact, redox and transient
signals help test workflows; they are not predictions of experimental performance.

![Control interface](docs/images/control-scan-maps.png)

## Try it

Install Python 3.10+ in an isolated environment, then install this checkout:

```text
python -m pip install -e .
python run_echemtips.py
```

Select **Simulation**, connect and run a small experiment. For first installation,
Windows commands and optional dependencies, follow [Installation](docs/INSTALLATION.md).
Open analysis from **Analysis → Open analysis app** (F6), or run
`python run_analysis.py`.

## Real hardware: compatible interfaces, not a single instrument model

The host communicates through `nifpga` and the native NI driver. It requires a
locally supplied `.lvbitx` compiled for the **exact NI device**, with the supported
register/FIFO contract, channel assignments and execution semantics. Different
NI models are not interchangeable merely because they run FPGA code.

Piezo controllers and current amplifiers need compatible analog interfaces and
independently verified ranges, sensitivities and polarity. There is no requirement
to use a particular amplifier or positioner brand. Support for a new combination
must be established by [commissioning](docs/REAL_HARDWARE_SETUP.md), not assumed.
The [FPGA contract](docs/HARDWARE_INTEGRATION.md) describes the current limits.

**Research software, not a certified safety system.** FPGA initialization can
change physical outputs. Stop does not guarantee zero potential or disable
external amplifiers. Prepare the hardware and physical interlocks before connecting.

## WEC-SPM foundation and acknowledgements

eChemTips is a separate project based on the workflows and FPGA host protocol of
**Warwick Electrochemical Scanning Probe Microscopy (WEC-SPM)**, developed at
the University of Warwick and by its collaborators. It is not an official Warwick
release. Request the original platform through the
[WEC-SPM webpage](https://warwick.ac.uk/fac/sci/chemistry/research/unwin/electrochemistry/wec-spm/).

For the underlying platform: McKelvey et al.,
[A Look inside a Flexible Open-Source Scanning Electrochemical Probe Microscope](https://doi.org/10.1021/acselectrochem.5c00354),
*ACS Electrochemistry* **2026**, *2*, 78–91. Supporting Information S7 explains
software access. Original WEC-SPM sources and FPGA artifacts remain under their
own terms; they are not distributed or relicensed here.

## Development and license

See [Contributing](CONTRIBUTING.md), [Architecture](docs/ARCHITECTURE.md) and
[CHANGELOG](CHANGELOG.md). Run `python -m unittest discover -v` and the control
and analysis smoke tests before proposing changes. Passing simulation/fake-device
tests does not qualify real hardware.

[MIT](LICENSE). Private bitfiles, instrument settings and recordings are excluded.
