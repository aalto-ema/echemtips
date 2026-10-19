# Operator guide

For installation, start with [First simulation](INSTALLATION.md).
For real instruments, complete [Hardware setup](REAL_HARDWARE_SETUP.md) and
[Calibration](CALIBRATION.md) before enabling outputs.

## Prepare a session

1. Check the probe, cell, grounding, amplifier gain/filter and mechanical clearance.
2. In Settings, verify backend, bitfile/resource, piezo ranges, current sensitivity,
   polarity, potential scaling, acquisition interval and data folder.
3. Save/apply settings. Hardware-affecting changes require reconnection.
4. Connect only after reading the startup-output warning and preparing for those outputs.
5. Check commanded and measured positions separately; readbacks do not prove calibration.

Opening the application does not connect to hardware. Only one experiment or
recording owns the instrument at a time. Before recording, the optional details
form can capture pipette, electrolyte, electrodes, filter, environment and notes;
blank fields are allowed. Relevant acquisition settings are recorded automatically.

## Navigation and working space

**Move piezo**, monitors and commonly used experiments are in the sidebar.
**All experiments…** searches the complete library, including pinned entries.
Pin/unpin and reorder favorites there; Settings remains accessible.
Presets retain measurement parameters, not permission to reuse another instrument's calibration.

Use **Hide setup** for plot width and **Expand plots** for a larger live view.
Plot controls, buffers and rolling windows affect display only; recording remains
full-rate. The selected current units do not change threshold or saved-data units.
See [Settings](SETTINGS_REFERENCE.md).

## Choose an experiment

| Experiment | Purpose |
| --- | --- |
| Move piezo | Bounded X/Y/Z command at a selected speed; measured and commanded positions remain separate |
| Watch current / position | Explicitly start a live view or recording; opening a page alone does not begin monitoring |
| Guided preflight | Zero-current noise, open-input capacitance and known-resistor checks; prepare each fixture yourself |
| Characterize pipette | Immersed-pipette stability and I–E measurements; model-derived aperture is an estimate |
| CV / LSV | Voltammetry without an automatic approach |
| Approach | Contact-gated approach, settling and optional return |
| Approach + CV / LSV | One landing followed by voltammetry |
| Approach + CV scan-rate series | One landing, multiple ordered scan rates, then one optional return |
| Approach + I–t | One landing followed by a repeated potential-step program |
| Scan hopping + CV / LSV or I–t | Repeat the chosen surface program at grid locations |
| Combinatorial / Adaptive | Recipe assignment or model-guided locations; see [Advanced scans](ADVANCED_SCANS.md) |

## Contact detection

Select **Current 1** or **Current 2** and a threshold in **pA** (default 5 pA).
The experiment UI uses **current magnitude**: contact occurs when
`|i| ≥ |threshold|`, so either a positive or negative excursion can trigger.
This is not a change-from-baseline criterion. A dry offset/noise already above
the threshold can cause false contact; inspect the baseline and gain first.

Low-level Python APIs additionally expose signed and baseline-relative modes.
Do not assume their defaults match the UI's magnitude mode.

After contact, the approach ends and the selected settling/measurement stage
begins. Reaching the approach limit **without** contact does not authorize surface
electrochemistry. **Accept current Z as contact and continue** is an intentional
operator override while approaching, not an automatic quality check.

Contact evidence is electrical, not proof of a particular droplet footprint or
safe physical distance. Confirm behaviour with a controlled signal before a sample.

## CV, LSV and scan-rate series

**CV:** `Start → Vertex 1 → Vertex 2 → Start`, repeated for the chosen cycles.
**LSV:** choose **Waveform → LSV** and set Start, End and scan rate; there is
one sweep, without reverse legs. The endpoint may be above or below Start.

For a scan-rate series, add/remove/reorder rates in V/s. Repeated rates are
allowed and remain separate rate blocks in analysis. One approach precedes the
whole series. In LSV series, E1 jumps back to Start between rates; the optional
reset settling time can reduce—but does not remove—charging effects.

The measurement endpoint remains applied during retraction/completion unless
an enabled post-hold sets another potential. Completion does not imply zero E1.

## I–t

Set initial, pulse and return potentials and their durations, then the cycle count.
A duration may be zero. The current-time measurement begins after confirmed
contact and settling, not when the initial positioning begins.
Inspect the E–t trace when interpreting current transients.

## Hopping scans and return Z

Set the XY grid, serpentine or raster path, initial approach Z, approach limit,
speeds, threshold, settling and electrochemical program. Review the preview and
known-duration estimate; approach times and hardware overhead can vary.

After contact, the requested retract is away from the surface by the configured
distance. **It is bounded at Initial approach Z**: if the full distance would go
past that return boundary, withdrawal stops there rather than failing solely
because the full distance is unavailable. Subsequent landings approach from the
reached retract height. Normal scan completion returns to Initial approach Z.
Single-point methods retain their own retract checkbox.

This bound is not confirmation of droplet detachment or lateral clearance.
You must choose a return height that clears the entire path. Adaptive scans use
their own travel policy described in [Advanced scans](ADVANCED_SCANS.md#adaptive-scanning).
Raster flyback/long-move extra withdrawal does not permit commands outside
configured travel.

### Orientation marker

The optional final orientation landing is on by default. It repeats the last
array measurement recipe at an asymmetric location after successful array completion.
Automatic placement uses the first X position and one Y spacing beyond the last row;
with one Y row it uses X spacing. For a single-point grid, specify coordinates
or disable the marker.

Meniscus footprint diameter does **not** control placement. Check the preview:
the marker must be outside the array and within piezo bounds; coordinates are
not silently clamped. Travel uses the configured long-move extra withdrawal.
The exported `.orientation.svg` shows planned order/orientation; JSON records
actual completion. Marker samples remain in recordings but are excluded from
analysis plots, maps and treatments.

## Optional holds

Expand **Pre/post measurement holds** inside the electrochemistry card; both
default off. Enable each independently and enter E1 and positive duration
(up to 300 s, subject to program/tag limits). Collapse the section without
disabling it; its summary still indicates enabled options.

Order: contact → settling → pre-hold → complete measurement → post-hold → retract.
Holds bracket each landing once; in rate series they bracket the whole series.
Combinatorial recipes share hold settings. No-contact exits do not run holds.
Check availability on the page: standalone CV and adaptive configuration do not
expose the same optional-hold editor.

The post-hold potential persists during withdrawal and completion. Holds are
retained in raw traces; measurement-aware analysis excludes them using
`measurement_phase`. See [Recording format](DATA_FORMAT.md).

## Optional two-speed Z motion

Expand **Z motion profiles** in the motion setup. Approach and retraction can
be enabled separately; both default off. XY motion stays constant-speed.

- **Approach:** enter fast/slow rates. Until a usable contact-height prediction
  exists, motion stays slow. Where available, fast travel ends before predicted
  contact by the configured clearance (default 5 µm). Contact detection stays active.
- **Retraction after a distance:** withdraw slowly for that distance, then fast.
- **Retraction after detected detachment:** remain slow until an attached-current
  contrast collapses toward the dry baseline; continue slowly through the chosen
  buffer, then fast. The fixed switch distance is disabled.

Ambiguous detachment stays slow to the endpoint. Stable potential and measurable
wet/dry contrast are needed; electrical evidence is not a direct footprint
measurement. Automatic withdrawal uses completed waypoint segments, so latency
and stationary gaps can occur. The buffer does not extend the final endpoint.
In adaptive mode without optional tilt fitting, two-speed approach stays slow.

Record profile settings and inspect JSON `motion_events`. Validate rates and
detachment against physical observations before routine use.

## Pause, stop and recovery

| Control | Meaning |
| --- | --- |
| Pause / Resume | Operator pause/resume; not permission to override FPGA feedback-owned pauses |
| End waypoint | Low-level waypoint advance, **not** confirmation of contact; unavailable in adaptive acquisition |
| Stop experiment | Controlled abort; save partial data and follow reported recovery state |
| EMERGENCY STOP | Strong stop/disconnect; not a guarantee of zero AO or de-energized amplifiers |

After hardware cancellation, the current stream may be retired and require
disconnect/reinitialization before another command. The experimental recoverable-stop
branch is not part of main. Do not assume a stopped scan returns Z to initial
position: secure the hardware and inspect the reported state.
Normal completion and stopping are different paths.

Use physical inhibits/interlocks if software cannot establish a safe state.
FPGA reinitialization itself changes outputs; withdraw/prepare safely first.

## Recordings and analysis

Keep the CSV and matching JSON together. Completed, aborted and failed runs
have distinct terminal statuses; partial data are retained for traceability.
Use **Analysis → Open analysis app** (F6) or **Analyze last saved recording**.
Analysis is a separate process and does not operate hardware.
See [Analysis](ANALYSIS_GUIDE.md) and [Troubleshooting](TROUBLESHOOTING.md).
