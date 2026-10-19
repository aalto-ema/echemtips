# eChemTips documentation

eChemTips provides Python control and analysis for SECCM instruments using a
compatible WEC-SPM FPGA target. Start with the simulator; connect an instrument
only after verifying its interface and calibration.

## Choose your task

| I want to… | Start here |
| --- | --- |
| Install the software or try it without hardware | [Installation and first simulation](INSTALLATION.md) |
| Connect an instrument for the first time | [Hardware setup](REAL_HARDWARE_SETUP.md), then [Calibration](CALIBRATION.md) |
| Run an experiment | [Operator guide](OPERATOR_GUIDE.md) |
| Vary recipes or select locations adaptively | [Advanced scans](ADVANCED_SCANS.md) |
| Process recordings or export results | [Analysis guide](ANALYSIS_GUIDE.md) |
| Understand a setting or file field | [Settings](SETTINGS_REFERENCE.md) or [Recording format](DATA_FORMAT.md) |
| Resolve a problem | [Troubleshooting](TROUBLESHOOTING.md) |
| Extend the software | [Architecture](ARCHITECTURE.md), [FPGA contract](HARDWARE_INTEGRATION.md), [API](API_REFERENCE.md) |

Optional scientific tools have separate references:
[analytical SECCM models](SECCM_MODELS.md) and
[experimental footprint normalization](AREA_NORMALIZATION.md).
The [standalone coarse-positioner tester](PICOMOTOR_TEST.md) is a separate,
controller-specific development tool, not a requirement for standard scans.

## Before using real hardware

Different NI devices require their own compatible compiled targets. Analog
controllers and amplifiers must match the documented electrical interfaces;
software cannot infer wiring, gain, travel direction or safe sample clearance.
FPGA startup can move outputs. Simulation, metadata checks and unit tests do
not replace physical commissioning.

## Origins, support and scope

This is a separate Python host/UI based on Warwick's **WEC-SPM** platform, not an
official Warwick release. Request the original platform at the
[WEC-SPM webpage](https://warwick.ac.uk/fac/sci/chemistry/research/unwin/electrochemistry/wec-spm/);
see McKelvey et al., [ACS Electrochemistry (2026)](https://doi.org/10.1021/acselectrochem.5c00354)
for its description. Original FPGA/software artifacts remain under their own
license terms and are not supplied here.

Use [GitHub issues](https://github.com/aalto-ema/echemtips/issues) for bugs and
feature requests. Include the software revision and a minimal reproduction;
remove private paths, sample details and confidential data.
