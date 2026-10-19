# Hardware setup and commissioning

eChemTips is not tied to an amplifier or piezo-controller brand. It **is** tied
to a defined FPGA protocol and analog interface. A device with a similar connector
or a bitfile with similar metadata is not automatically compatible.

## Required interfaces

| Component | Requirement |
| --- | --- |
| NI FPGA device | Supported by the chosen native NI driver and a target compiled for that exact model |
| Compiled target | WEC-SPM-compatible registers, FIFOs, framing, scaling, startup and execution behaviour |
| Piezo controller/stage | Compatible command inputs and position-monitor outputs; known calibrated ranges/directions |
| Current amplifier | Analog current output with known V/nA sensitivity, bandwidth, offset and saturation limits |
| Potential control | Compatible E1/E2 command interface, reference arrangement and independently verified polarity/scaling |
| Host computer | Supported OS/driver/interpreter combination, adequate RAM and reliable local recording storage |
| Physical protection | Site-appropriate motion/output inhibits, travel limits and independent emergency procedure |

The Python host does not supply the compiled target, control electronics or
an arbitrary-channel device abstraction. Another NI model needs its own compatible
target and staged verification; a USB image cannot simply be reused on PCIe/PXI.
See the exact [FPGA contract](HARDWARE_INTEGRATION.md).

## Prepare the computer

Follow [Installation](INSTALLATION.md), then install the Python FPGA extra:

```text
python -m pip install -e ".[fpga]"
```

Separately install the native NI-RIO/R Series driver release supported by the exact
device and OS, including NI MAX and FPGA Interface support. Reboot if requested.
The Python package cannot replace that driver. Obtain installers through
[NI support](https://www.ni.com/en/support/downloads.html); offline machines need
the vendor's complete offline installation media, not just a web downloader.

In NI MAX, confirm the device and its resource name (often `RIO0`). Obtain a
private `.lvbitx` from the instrument owner, compiled for that device and contract.
Its filename is arbitrary. Select it in Settings; no private archive is searched.

Use the environment's Python for these checks:

```text
python run_hardware_check.py --bitfile "PATH/target.lvbitx"
python run_hardware_check.py --bitfile "PATH/target.lvbitx" --connect --resource RIO0
```

The first command checks metadata without hardware. `--connect` explicitly opens
the target with `no_run=True`; it does not execute a waypoint. Neither proves
analog behaviour or permission to operate near a sample. Do not run other host
applications against the same device simultaneously.

## Channel and wiring worksheet

These are the **current logical assignments**, not universal NI terminal numbers.
Use the exact device/breakout manuals to identify connectors, terminal numbers,
grounds, input topology and allowable voltage/current. Check AO/AI capabilities
for the selected model; do not assume every NI device supports the same ranges.

| Channel | Role | Terminal / destination / signal reference |
| --- | --- | --- |
| AO0 / AO1 / AO2 | X / Y / Z piezo command | Record locally |
| AO3 | E1 potential command; configured command ratio applies | Record locally |
| AO4 | E2 potential command; no E1 ratio | Record locally |
| AI0 / AI1 / AI2 | X / Y / Z position-monitor inputs | Record locally |
| AI3 / AI4 | Current 1 / Current 2 amplifier outputs | Record locally |
| AO5–AO7 / AI5–AI7 | Unused by the standard experiment interface | Leave unused unless a reviewed extension requires them |

Never connect piezo high voltage directly to NI analog inputs.
Confirm signal grounds and protective-earth bonding according to each device's
manual and laboratory electrical procedure. Do not lift protective earth to
reduce noise, or create unplanned return paths through USB/coax shields.

## Connection changes physical outputs

The compatible target executes startup writes before pause-controlled loops:
AO0/X and AO1/Y become raw `0x3FFF` (about +5 V under this target's conversion),
AO2/Z becomes 0 V, and AO3/E1 plus AO4/E2 become 0 V. Physical position depends
on controller mapping and configured ranges; measured position can differ.

**External Pause cannot suppress these startup writes.** Prepare mechanical
clearance before connection/reinitialization, and inhibit downstream outputs
where appropriate. The UI requires acknowledgement; programmatic callers must
explicitly allow startup actuation. Applied-output/readiness checks precede a
reported connection; mismatch stops/rejects it.

Do not infer “safe” from zero voltage: some stages use midrange or reverse mappings.
A driver stop also does not promise zero AO or an electrically open cell.

## Staged commissioning

Keep evidence for each stage. Use a probe safely clear of a surface, physical
inhibits and appropriate dummy loads; only proceed when independent observations
agree with commands and configured tolerances.

1. Back up the known-working instrument configuration. Record software, driver,
   bitfile and electronics versions; close competing device hosts.
2. Test installation and simulation without real outputs. Check the bitfile
   contract offline, then resource opening with outputs inhibited.
3. With downstream command inputs disconnected/inhibited, connect the application
   and independently measure the stated startup AO levels.
4. Check E1/E2 command sign, ratio, offsets and limits using appropriate loads.
   Check current sensitivity/sign, zero offset, noise and clipping independently.
5. Enable one piezo axis at a time. Test small slow commands with a physical/voltage
   reference; confirm range, position monitor, direction and endpoints. Test Z last.
6. Run Guided preflight with correctly prepared open/resistor fixtures. Test both
   current channels if used. Record gain, filter and acquisition timing.
7. With safe travel and a controlled contact signal, test Approach, no-contact
   end-of-travel, manual contact acceptance, settling, pause/resume and stop.
   Test positive and negative excursions for UI magnitude detection.
8. Test a short Approach + CV/LSV or I–t, then 1 × 1 and 2 × 2 hopping scans.
   Verify contact gating, physical return Z, XY clearance, potentials, marker
   placement, saved timestamps and pixel metadata.
9. Test partial recordings, fault/recovery and physical emergency procedures.
   Reinitialization changes outputs; demonstrate recovery before routine work.
10. Add advanced profiles, recipes or adaptive selection only after ordinary
    workflows pass. Simulation/fake-session tests do not replace this process.

For conversion equations and sign migration see [Calibration](CALIBRATION.md).
For failure symptoms see [Troubleshooting](TROUBLESHOOTING.md).

## Keep a local instrument record

Record at least: date/operator, software commit, OS/Python/driver versions,
device model/serial/resource, target signature and source, connector worksheet,
piezo/controller ranges and direction, amplifier/headstage gain/filter and command
span, polarity convention, acquisition interval, ground/reference arrangement,
startup observations, stop/recovery checks, tolerances and representative traces.

Do not commit identifying calibration records, private binaries or sample data.
Recheck affected stages after wiring, gain, driver, firmware, target or physical
scaling changes. Compatibility is a property of the verified combination, not
a promise made by choosing a hardware name in Settings.
