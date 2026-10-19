# Analysis guide

Analysis is independent of the instrument and never sends FPGA commands or
rewrites original acquisition files. Keep the CSV and matching JSON together.

## Open and select data

Use **Analysis → Open analysis app** (F6), **Analyze last saved recording**, or
`python run_analysis.py`. Drag-and-drop and **Recent recordings** also open files.
Legacy TDMS requires the optional analysis extra; arbitrary legacy columns are
not automatically assumed to be calibrated electrochemical signals.

Imports run in the background. The header shows recording status; partial runs
remain useful for raw inspection but may have fewer complete programs.
**Show / hide file browser** gives plots more width.

Explore **Whole recording**, **Recorded hops** or **Complete CV cycles**, then
choose X/Y channels. Unknown numeric fields retain source names without invented
units. Select a combinatorial **Condition** before processing/comparing protocols.
Marker landings and invalid adaptive results are excluded from derived selections.

Dense traces use display-only extrema-preserving reduction. Quantitative
calculations and exports use full-resolution arrays. Loading is not out-of-core:
large files and processed copies can still exceed available RAM.

## Explore and measure

**Time range / baseline** uses recorded elapsed time, not a clock reset per hop.
Blank bounds select all samples. The baseline is a constant in the native Y
unit (nA for current), regardless of the display unit.

Statistics include sample count, mean, population standard deviation and extrema.
Current charge is signed trapezoidal integration against recorded time:
nA × s = nC. Changing the X plot channel does not change that integration variable.
Invalid data break integration; decreasing timestamps are not silently reordered.

**Compare → Pin this trace as reference** retains a processed snapshot.
References with incompatible channels or potential conversion are hidden.
Reset/clear controls do not alter the recording. Whole-hop current-versus-Z
includes approach, holds and retract; it is not an automatic approach-only selection.

## Voltammetry: cycles, scan rates and branches

The CV tab provides **i vs E**, **E vs t** and **i vs t**. Time starts at zero
for each selected cycle/sweep. Select/overlay cycles within each landing.
Scan-rate-series blocks remain distinct even when rate values repeat.
Only waveform-validated complete programs appear; incomplete data remain in raw views.
Up to 50 curves are displayed at once; bulk export retains all extracted cycles.

For legacy data, **Set CV program** supplies missing waveform parameters in memory.
It does not rewrite JSON and must match the real experiment. LSV is a single
one-way sweep, not an invented reverse cycle.

Potential-dependent maps select channel, potential, **cycle within each hop**
(or explicit cycle average) and chronological leg. For a
−0.2 → +0.6 → −0.4 → −0.2 V CV:

| Leg | Range |
| --- | --- |
| Start → Vertex 1 | −0.2 to +0.6 V |
| Vertex 1 → Vertex 2 | +0.6 to −0.4 V |
| Vertex 2 → Start | −0.4 to −0.2 V |

The first and third legs both increase potential but are different selections.
Interpolation stays within the chosen leg; unavailable potentials/cycles leave
blank cells rather than extrapolated or zero currents.

## Smoothing

Enable **Smooth currents**, select Savitzky–Golay (default) or moving average,
then Apply. For Savitzky–Golay, begin with 5–11 samples and polynomial order 2;
the window must be odd and larger than the order.

Smoothing feeds current traces, tables, summaries, maps and movies. It is temporal,
not spatial smoothing between pixels. Positions, potentials and cycle identification
are not smoothed. Apply always starts from original data; disable to restore it.

Filters do not cross hop/waypoint changes, extracted cycles, sweep reversals or
non-increasing timestamps. Short segments use a smaller valid window or remain
unchanged. Invalid samples stay gaps. The window is in samples, assumes roughly
uniform spacing and can distort peaks or transients; compare against originals.
Exports retain the processing recipe. Processing uses additional RAM.

## Maps, cropping and topography

Maps use recorded physical XY metadata, not acquisition ordering. Serpentine
rows are not mirrored. Unvisited cells remain absent, without interpolation.

- Whole-hop Mean/Min/Max/Std include motion and holds; a Z mean is **not** surface height.
- **CV at potential** uses the selected cycle/leg, as above.
- **Contact Z (surface estimate)** uses available explicit contact metadata or
  validated stationary surface programs. Partial-program fallbacks may recover
  height, but do not certify a complete measurement.
- A “no usable surface Z” result means no trustworthy contact metadata or resolved
  stationary surface program was found. Inspect raw traces, JSON and per-hop recipes;
  apparent scan completion alone is insufficient.
- Commanded contact Z and measured sensor Z have different meanings; do not mix
  their offsets/scales in quantitative interpretation.

Crop X/Y limits to omit boundary rows/columns. Cropping is reversible, keeps original
hop IDs/spacing and does not edit source data. Bounds use original piezo coordinates.

**XY from map corner** puts the lower-left outer cell edge at (0,0), also after
cropping. Cell centres remain half a spacing from the edge; reverse scans are not reflected.
This option applies to other channels and movie maps too.

**Remove tilt** subtracts a plane fitted to usable points within the crop
(at least three noncollinear sites). It can remove real sample shape and is sensitive
to outliers. **Topography height** then computes `max(Z) − Z`: the greatest
contact Z becomes zero height. Cropping/condition selection can change this reference.

**3D view…** opens a rotatable snapshot. Faces connect only complete neighbouring
cells; sparse maps remain points rather than an invented surface. Vertical
exaggeration is for display. Map exports retain origins, plane and height settings.

## Potential-reference conversion

**Potential reference…** optionally transforms E1, not E2 or current signs.
Confirm the recorded potential polarity; control-app settings do not silently
reinterpret old files. The raw table retains original values.

`Eout = sign × Erecorded + Esource(SHE) − Etarget(SHE) + custom offset`

Here sign is +1 for recorded IUPAC potential, −1 for native WEC-SPM potential.
Nominal aqueous references at 25 °C are SHE (0 V), RHE (−0.05915935 × pH V),
saturated-KCl Ag/AgCl (+0.197 V), 3 mol/L-KCl Ag/AgCl (+0.207 V) and SCE (+0.241 V).
A custom additive offset/reference name can be used instead; positive offset adds.

A pipette Ag/AgCl quasi-reference is not automatically a saturated-KCl reference.
Prefer experimental calibration where needed. Junction potentials, temperature
dependence, drift, nonaqueous scales and resistance drop are not corrected.
See [reference-electrode values](https://www.metrohm.cn/content/dam/metrohm/shared/documents/fact-sheets/81098050EN.pdf).

Converted waveform endpoints, map potentials and movie axes remain consistent.
**Set CV program** still edits the original scale. Conversion starts from originals,
not already shifted data. Save an analysis session to retain choices for a file.

## Plot data and figure exports

**Plot → Export plotted data as CSV…** exports full-resolution values for the
displayed series, including visible references/original overlays. Its long-form
columns are series ID/name, sample, x and y; labels/units are in a JSON sidecar.
Panning alone does not select data: use an explicit time interval.

**Export selection…** saves only the active quantitative selection.
**Export map…** saves selected cells and the map recipe.
**Export all separated CVs…** exports every extracted cycle, beyond the display
cap; it is hidden without valid voltammetry programs. These are derived products,
not replacements for acquisition CSV/JSON.

Use **Plot → Export figure…** for traces or the map's **Export figure…**.
The dialog snapshots the selection without changing live formatting:

1. Edit title, axis/colour-bar labels and units (for example pA → nA or V → mV).
   Unit selection rescales values, ticks and limits—not just label text.
2. Set physical width/height in mm, independent of window shape. Start around
   85 × 65 mm for one column, or 150 × 110 mm for a larger panel.
3. Choose fonts, point sizes, line width and legend. Choose an appropriate palette
   and colour limits for maps; viridis/cividis are useful sequential defaults.
4. Preview and export PNG/TIFF (default 300 DPI, up to 1200) or vector PDF/SVG.
   Inspect legibility and the destination journal's requirements.

Maps retain proportional XY geometry, missing cells and crop boundaries. Very long
vector traces can produce large files. Figure sidecars record formatting,
processing, units, source and selection. Source recordings are protected from
being chosen as export targets; inspect both outputs after an export error.

## Map movies

Open **Map movie**, select current channel and frame axis:

- **CV potential:** one chronological leg or **Whole CV**, including both reversals.
- **CV time:** time from selected cycle start.
- **I–t time:** time from the surface program's start.

Choose a per-hop cycle or explicit cycle average for CVs, frame count and
**Every Nth frame** skipping. Whole-CV potential frames retain chronological
branches, even when a potential occurs more than once. Prepare again after
selection/data changes. Preparation is bounded to 20 million hop/frame values.

**Movie options…** controls palette, exclusions, FPS, hold per frame and limits:

| Colour mode | Behaviour |
| --- | --- |
| Auto | One fixed range estimated across prepared data |
| Dynamic | Separate limits per frame |
| Manual | Fixed operator-entered limits |

Automatic range estimation excludes invalid/failed results and uses robust
handling where possible; it cannot identify every bad landing. Inspect exclusions
and the prepared range. Dynamic limits can exaggerate weak variations and prevent
direct colour comparison between frames.

Play/pause, scrub or loop before exporting MP4 (requires `.[movies]`).
Output FPS and hold time control playback, not instrument sampling. Skipping
changes which prepared frames are shown. Export a movie map as a still figure
separately. Movies retain the active crop, processing and coordinate conventions.

## Specialist tools and reproducibility

[Analytical models](SECCM_MODELS.md) provide advisory predicted currents/traces.
[Footprint normalization](AREA_NORMALIZATION.md) provides experimental detachment-
based area estimates, calibrated models and current-density processing.
Neither establishes intrinsic activity or independently validates a landing.

Keep source recordings with derived files and processing recipes. Analysis sessions
retain supported selections/settings, not a replacement raw recording. Full paths
in exports can be sensitive; review before sharing.

For new experiment/provider support, see [Architecture](ARCHITECTURE.md) and
the [API](API_REFERENCE.md). Core analysis must stay independent of Qt and hardware.
