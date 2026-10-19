# Troubleshooting

Secure the instrument before diagnosing physical faults. Keep the original
recording and complete error text. Simulation and software checks cannot prove
that a stage, amplifier or cell is safe.

| Symptom | Check / next action |
| --- | --- |
| Application or dependency import fails | Use the same isolated Python environment used for installation; repeat its install command and report the traceback |
| NI resource cannot open | Check native driver/device/OS compatibility and NI MAX resource; close competing control software |
| Bitfile or register/FIFO contract rejected | Check exact model, transport and target contract; do not rename a binary or guess register aliases |
| Connection causes an unexpected move | Startup AO writes are part of the target; physically inhibit/secure the setup and verify conversion before reconnecting |
| Commanded and measured position differ | Check the actual command and sensor voltages, scaling, offset, saturation and controller feedback state separately |
| Current scale/sign is wrong | Verify active amplifier gain/output connector, V/nA sensitivity, polarity and electrode wiring using a controlled load |
| Current clips near a fixed limit | Amplifier/headstage or NI input may be saturated; reduce the stimulus/gain safely and compare raw voltage independently |
| Approach declares contact immediately | UI detection is magnitude-based; inspect dry offset/noise, transients and threshold units before changing settings |
| Approach reaches its limit without contact | Verify selected channel, threshold, wiring, travel direction and actual surface location; no-contact must not start electrochemistry |
| Contact transition stalls or program is paused | Distinguish operator pause from feedback-owned pause; do not repeatedly force Resume or End waypoint |
| Another command is rejected after Stop | Cancellation may retire the acquisition stream; prepare for startup outputs before disconnect/reinitialization |
| Emergency Stop leaves an output applied | Stop is not electrical isolation or guaranteed zero AO; use the physical inhibit/interlock procedure |
| Adaptive scan rejects a site / stops on tilt tolerance | Check conditioning and quality log; optional tilt checks are stricter than default mode. Do not treat false contacts as verified geometry |
| Plots lag | Reduce unnecessary live views and rolling windows; close heavy analysis. Display reduction does not reduce recorder input |
| Surface Z map is blank | Check contact metadata and stationary surface-program recognition, per-hop recipes and partial waveforms; completion alone does not guarantee usable height |
| Few cycles/hops appear in analysis | Keep JSON with CSV; inspect waveform/cycle/condition selection and incomplete programs. Do not replace missing cycles with zeros |
| Disk/backlog error or JSON remains running after a crash | Preserve both files as partial, check storage and permissions; never manually relabel a failed run complete |

## Retest after a correction or update

1. Reproduce in Simulation or a fake-device test where possible.
2. With outputs safely prepared, check stationary signals and independent calibration.
3. Use a small controlled-signal approach: verify both current signs, no-contact
   end-of-travel, manual acceptance and post-contact transitions.
4. Test a short single landing, then a small scan and a second normal completion.
5. Test pause/stop and recovery with safe mechanical/electrical clearance.
   Do not extend watchdogs or repeatedly resume to conceal an unexplained target state.

## Minimal issue report

Use [GitHub issues](https://github.com/aalto-ema/echemtips/issues).
Remove private paths, sample identifiers and confidential data before posting.

```text
Software commit:
OS, Python version and architecture:
Backend and experiment:
Native NI driver / NI MAX / nifpga versions (if relevant):
Device model, resource, target signature:
Exact error and last known physical state:
Minimal reproduction, preferably in Simulation:
Recording status and available CSV/JSON:
Hardware-check output (if relevant):
```

See [Hardware setup](REAL_HARDWARE_SETUP.md),
[Calibration](CALIBRATION.md) and [FPGA contract](HARDWARE_INTEGRATION.md)
for the checks behind these symptoms.
