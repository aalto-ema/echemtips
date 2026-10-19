# Advanced scans

Commission an ordinary single-landing experiment and a small regular scan first.
These methods reuse the same contact-gated hardware programs; they do not remove
the need to verify clearance, signal quality and final potential.

## Combinatorial scanning

Choose **Combinatorial scan + CV / LSV** or **Combinatorial scan + I–t** from
**All experiments…**. Regular scans remain single-program workflows.

1. Configure the grid and shared motion, contact, settling and marker settings.
2. Open **Plan recipes and assignments…**. Duplicate/name recipes and edit their
   complete electrochemical programs.
3. In **Assignment preview**, choose Row blocks, Interleaved or Randomized.
   Check the programs, replicate counts and grid positions, then **Use this plan**.
4. Start the scan. Inspect the active recipe name and saved per-hop waveform.
5. In analysis, select **Condition** before comparing traces, maps or movies.

**CV/LSV recipe fields:** start, vertex/end potentials, scan rate, cycles and waveform.
**I–t fields:** initial/pulse/return potentials and times, and cycles.
Motion, feedback, settling, calibration, acquisition and pre/post holds remain shared.
CV/LSV and I–t are separate recipe families, not arbitrary mixed sequences.

Row blocks repeat recipes in physical row blocks. Interleaving repeats the recipe
list across the row-major grid. Randomization shuffles a balanced assignment using
the displayed seed; it does not randomize travel. Serpentine acquisition does not
reverse recipe-to-coordinate assignment. Each recipe needs at least one fresh site.

**Two-factor matrix…** creates combinations of two numerical parameter lists
(up to 64 combinations). Saved recipe libraries omit instrument settings and
assignments; each recording retains its actual plan. After changing grid dimensions,
reopen the planner to confirm it. A marker repeats the last array recipe and is
excluded from analysis.

Row assignment can confound material heterogeneity with condition effects.
Use randomized/interleaved fresh-site replicates and reference conditions where
appropriate. A live current map may mix protocols; unavailable sampling potentials
leave cells blank. Use analysis condition filters for meaningful comparisons.

## Adaptive scanning

Choose **Adaptive hopping + CV / LSV** or **Adaptive hopping + I–t**. Begin with
approval enabled, a small inspected region and a modest landing budget.

### Initial points and travel

Start with corners + center or a 3 × 3 grid. These are ordinary measurements
that seed the spatial model—not mandatory tilt calibration.

By default, **surface tilt checks are off**. The operator confirms that Initial Z
clears the full region and entry path. The supervisor withdraws to its safe travel
height before XY movement. Retraction/normal completion use Initial Z as the
return boundary; a shorter available retract is not by itself a failed landing.

Optional tilt checks fit a plane to **commanded** contact Z, not sensor readback.
They require explicit plane approval and add travel-clearance, relief and
deviation checks. An inconsistent later contact can stop proposals in that mode.
A sparse plane cannot detect particles, steps or drift; it is not collision avoidance.

Decreasing Z must move away from the sample for this adaptive workflow.
Verify that physical direction before use. Piezo-range validity alone does not
establish sample clearance.

### Approach conditioning and quality

At safe travel height, the approach potential is applied and acknowledged before
feedback is armed. **Settling before approach** defaults to 0.25 s (minimum 0.05 s).
Three fresh final current samples must lie below the contact-magnitude threshold.

In default mode, an unsettled/above-threshold site is rejected without approaching,
returns to initial Z and gives way to a fresh location. Missing fresh data still
stops the run; optional tilt mode is more restrictive. Invalid/noisy electrochemistry
is logged but does not train the model. A no-contact approach stops the scan and
hardware cancellation may require reconnection.

Quality filters require confirmed complete finite non-clipped measurements and
sufficient objective samples. Low current alone is not failure. These tests do not
establish constant area, intrinsic activity, or eliminate all false contacts.

### Objective and selection

The objective is **absolute median signed current** in the selected window:
`|median(i)|`, not `median(|i|)`. Both signs can therefore be optimal without
artificially rewarding zero-mean noise.

- **CV/LSV:** choose current channel, potential window, cycle and chronological leg.
  The full window must fit inside that leg; at least three samples are needed.
- **I–t:** select cycle and time window from that cycle's start, not from pulse start.
  The window must remain within one potential hold.
- **Hotspots:** maximize predicted mean + two posterior standard deviations.
- **Mapping:** choose greatest posterior uncertainty.
- **Balanced:** alternate hotspot and uncertainty selection.

The model is a Gaussian process on a bounded 31 × 31 candidate grid, with an
isotropic squared-exponential kernel, five candidate length scales and a fixed
regularizing noise term. SciPy linear algebra implements its inference; it is
already a simple Bayesian optimization/active-learning workflow, not a generic
materials-discovery engine. With fewer than three usable results, space-filling
fresh locations are used until fitting is possible.

Minimum separation excludes **every attempted** landing, including rejected ones.
Choose it yourself for footprint/residue clearance. Count/time budgets include
initial points; approval waits and pauses count toward wall time. The supervisor
does not deliberately cut an active landing short to meet a time budget.

### Displays, records and limitations

Tabs show measured/predicted objective, uncertainty, commanded contact Z, waveform,
traces and the decision log. The red cross marks a proposal; grey lines show order.
Predictions need sufficient usable measurements and are not measured activity.

CSV/JSON retain measurements and location/validity metadata.
A flushed `.decisions.jsonl` journal and final `.report.md` explain proposals and
results. Invalid data remain available for raw inspection but are excluded from
derived selections. Adaptive locations are nonuniform: do not treat missing
locations as zero or regular rendered cells as measured footprint areas.

This version does not add automatic retries, crash resume, drift correction,
contact-area-aware objectives, obstacle navigation, long-range positioning or
orientation-marker landings. Ordinary Stop/Emergency Stop behaviour is unchanged;
End waypoint cannot bypass adaptive gates.

## A small verification sequence

1. In simulation, test two recipes on a 2 × 2 combinatorial scan and inspect
   condition assignments in analysis.
2. Run adaptive CV with two cycles, objective cycle 2 and leg 2; then repeat LSV
   and I–t with a valid cycle-relative window.
3. Use 7–10 total landings with approval enabled. Check initial points, fresh-site
   proposals, maps, quality states, report and return Z.
4. Before autonomous hardware work, repeat on a prepared controlled setup.
   Verify potential conditioning, actual movement, return height, contact gating
   and recovery. Simulated hotspots are not evidence of hardware performance.
