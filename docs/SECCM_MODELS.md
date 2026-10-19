# SECCM models (advisory)

Open **Analysis → SECCM model calculator** in control or **Models → SECCM models…**
in analysis. The shared nonmodal calculator never sends hardware commands,
changes thresholds, alters instrument defaults or classifies landings.

## Choose the model

| Model | Use | Main limitation |
| --- | --- | --- |
| Analytical · steady-state i–E | Fast limiting-current/kinetic-wave benchmark | No scan-rate or waveform history |
| Analytical · diffusion-limited step i–t | Ideal transport-limited step and optional rectangular averaging | Uniform initial concentration; no previous depletion |
| Transient 1D · diffusion + kinetics | CV/LSV/steps, pre-holds and multiple cycles with concentration memory | Effective spherical sector, not a full meniscus geometry |

The analytical expressions follow Anderson and Edwards,
[Analytical Chemistry (2023)](https://doi.org/10.1021/acs.analchem.3c00216),
equations 1–3, 10–11 and Table 1. The numerical extension uses spherical diffusion
(SI S29) with Butler–Volmer surface kinetics (SI S31); it is a new numerical
implementation, not a published closed-form CV expression.

## Physical inputs and units

Open **Model parameters**. Defaults are illustrative, not your instrument's geometry.

- **Pipette inner radius:** half the opening diameter, in nm.
- **Half-angle:** half the full internal cone angle, in degrees.
- **Meniscus height:** the gap/geometry parameter, not contact Z or piezo displacement.
- **Diffusion coefficient:** enter the coefficient in ×10⁻⁹ m²/s.
  For example, 3 × 10⁻⁶ cm²/s = 0.3 × 10⁻⁹ m²/s: enter **0.3**.
- **Concentration:** mM, numerically equal to mol/m³.
- **Footprint radius:** physical wetted radius; independent of map styling.
  It determines kinetic area, not a directly measured current normalization.
- **k⁰:** cm/s in the UI; converted to m/s internally. Enter E0 on the same
  reference scale as the comparison data, temperature in K, and transfer coefficient α.

Choose R1/R2/R3 for the effective transport radius. R3 accounts approximately for
height: `rp / sin(γ) − h / cos(γ)`; nonpositive radii are rejected. Radius and
angle uncertainty can materially alter limiting currents. No geometry is inferred
from a footprint drawing or contact-height map.

Predictions use IUPAC polarity. In analytical mode, Reduction/Oxidation selects
the reaction direction. In numerical mode it selects the **initial bulk species**:
Ox only for Reduction, Red only for Oxidation. Either current sign can subsequently
occur as the potential reverses.

## First transient CV

1. Select **Transient 1D · diffusion + kinetics** in Calculate / compare.
2. Open **Model parameters**. The numerical waveform section appears only for
   this model. Set CV, Start, Vertex 1, Vertex 2, V/s, cycles and optional pre-hold.
3. Return to Calculate / compare and press **Calculate**. Work runs in a background
   thread. Cancel, edit an input or close the dialog to discard pending results.
   Export stays disabled until a current result is accepted.
4. Switch **i vs E**, **i vs t** or **E vs t** without recalculation.
5. Repeat with **Fine · 480 cells** and compare the curves before quantitative use.

**Load illustrative peak-response example** sets prediction-only parameters
(radius 2 µm, height 1 µm, footprint radius 2.236 µm, D=10⁻⁹ m²/s,
k⁰=1 cm/s, 5 V/s and two CV cycles). It produces a transient peaked response.
It does not load an instrument preset or demonstrate experimental agreement.
Slower scan rates and smaller geometrically similar probes approach steady-state
behaviour; fixed geometry does not describe spreading-induced thin-layer effects.

### Waveforms and history

CV follows **Start → V1 → V2 → Start**, repeated without concentration resets.
LSV runs Start → V1 once; Step uses Start for a pre-hold, a near-instantaneous
explicit ramp to V1, then the chosen hold duration. Pre-holds are real simulated
electrochemistry, not a fresh concentration reset. Step rise duration is tiny but
nonzero to keep timestamps strictly increasing.

The program begins from uniform concentrations, not an automatically equilibrated
electrode or a recovered earlier landing. A finite initial faradaic response can
therefore occur. Only the submitted waveform's history is known.

## Compare recordings

The calculator uses **original** data, irrespective of analysis smoothing.

Analytical calculations accept original recording or extracted-cycle selections.
Select time bounds and confirm recorded polarity. For a step, set the actual onset
as Step origin; bins crossing that origin are excluded.

Transient comparison accepts an **entire extracted CV/LSV cycle**, using its recorded
E(t) and timestamps, not the prediction waveform fields (which become disabled).
Whole-recording transient comparison is rejected because the app cannot infer
approach, retract or multiple-landing concentration resets safely. The selection
starts from uniform bulk concentrations: preceding holds/cycles are unknown.
This is an important limitation when comparing a later experimental cycle.
To study known multicycle history, simulate the complete prediction program.

All timestamps/potentials must be finite and chronological; missing data are not
silently bridged or resampled. Time in the output starts at zero for the selected
program; its source origin is retained in export. Current/potential signs from
native-polarity data are converted together for IUPAC comparison, with explicit
confirmation when metadata are absent. Original files remain unchanged.

## Numerical method and validity

The solver uses radial finite-volume shells in the effective spherical sector.
Integrated shell diffusion resistances preserve the steady-state spherical limit.
Butler–Volmer flux uses physical footprint area mapped onto the sector surface;
this is an effective uniformly accessible electrode approximation.

For **equal Ox/Red diffusivities**, their concentrations sum to the conserved
bulk total, allowing one diffusion field and an exactly complementary product.
The reservoir boundary is at least eight diffusion lengths from the surface over
the full program (and at least 80 effective radii away). Backward Euler uses
bounded time growth and a maximum 1 mV internal potential increment.
Fine mode increases 240 to 480 cells. Python API users can also refine time
growth/potential increments for convergence tests.

Exports include method/version, cells, internal steps, outer radius, timestep
controls, accumulated mass-balance residual, concentration bounds and final
radial concentration profiles. A small conservation residual does **not** prove
grid convergence or experimental validity.

Limits: one dissolved one-electron couple, fixed geometry, equal diffusivities,
excess supporting electrolyte, no homogeneous reactions, adsorption, migration,
iR drop, capacitance, amplifier response or moving wetting boundary. The SI's
migration/HER expressions are chemistry-specific and are not enabled here.
A larger footprint can introduce confined thin-layer transport that this 1D
approximation cannot reproduce reliably; use geometry-resolved modelling for that.

The numerical output is **instantaneous faradaic current**; the analytical step's
averaging control does not apply to it. Do not compare a very early ideal transient
directly with bandwidth-limited experimental samples. Requested programs are bounded
to 100,000 output samples, 50 CV cycles and 200,000 internal steps.

## Exports, presets and checks

**Export result…** saves a separate JSON with SI inputs, DOI, model version,
waveform or source selection, assumptions and predictions. Numerical exports add
E(t), i(t), profiles and solver diagnostics. Residuals are comparisons, not fit
statistics establishing unique parameters or successful contact.

Parameter presets retain model selection, numerical program and resolution.
Old analytical presets remain readable. Radius sensitivity varies only the inner
radius with other inputs fixed; it is not a statistical confidence interval.
Source CSV/JSON paths cannot be used as export destinations.

Automated checks cover the report's R2 analytical benchmark (7.879 pA), ideal
step response, SI Table S2's half-surface-concentration limit, slow-scan S34
kinetic curves at 0.001–1 cm/s, polarity symmetry, concentration conservation,
mesh/time refinement, repeated-cycle memory and fast-scan peaks.
GUI tests cover background/stale-result handling, views, source preservation and
preset/export compatibility. These are numerical limits, not independent full-FEM
or experimental validation. Verify a known redox couple across sizes and scan rates
before using the model for quantitative inference.
