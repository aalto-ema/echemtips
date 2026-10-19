# FPGA contract and extension boundary

For instrument operation use [Hardware setup](REAL_HARDWARE_SETUP.md).
This developer reference explains why hardware-independent documentation does
not mean arbitrary FPGA/DAQ compatibility.

## Device and target requirements

Supply a `.lvbitx` compiled for the exact NI model, preserving the WEC-SPM
interface and execution semantics. No particular filename or compilation
signature is required; retain the signature as provenance. NI-RIO checks whether
the image can open on the device. Model/transport matching alone is insufficient.

The native implementation in `ni_driver.py` requires:

- Register names, datatypes and control/indicator roles in
  `ni_protocol.REGISTER_CONTRACT`.
- `Host_To_FPGA_Positions`: signed I16, host-to-target, depth 8197.
- `FPGA_To_Host_FIFO`: signed I16, target-to-host, depth 32767.
- Fourteen-word waypoint/sample framing, assigned channels, feedback types,
  packed flags, signed line tags and the expected 40 MHz timing/scaling.
- Compatible startup AO writes, applied-output acknowledgement, waiting states,
  operator/feedback pause distinction, contact transitions and stop behaviour.

Depths are checked exactly. Altered framing, channels or semantics require a
reviewed driver/target adaptation, not guessed aliases. Metadata inspection
does not verify analogue conversion, timing or physical response.

## Runtime ownership

- `backends.py` exposes hardware-neutral operations/capabilities to experiments.
- `host.py` owns execution snapshots and framed FIFO streaming/refilling.
- `waypoints.py` compiles physical positions, rates, ramps, jumps, holds and feedback.
- `ni_driver.py` owns one active program, scalers, acknowledgements, refills,
  line/waiting-state completion, contact gating, final drain and cancellation.
- `acquisition.py` drains samples off the GUI thread. Recorder input stays
  full-rate; the UI uses a separate bounded/display-reduced representation.

A feedback-owned pause is not an operator pause. The ordinary approach transition
uses target feedback rather than repeatedly forcing EndCurrentLine. The driver
initializes unused proportional/secondary/running-average controls to neutral
values to avoid inheriting stale target state.

The operator experiments primarily use feedback type 0 for programmed motion
and type 2 for contact-gated advancement. The target's other modes are not
automatically available merely because their enum values exist in Python.

## Logical channels and conversions

| Outputs | Inputs |
| --- | --- |
| AO0/1/2: X/Y/Z command | AI0/1/2: X/Y/Z measured position |
| AO3: E1 command | AI3: Current 1 |
| AO4: E2 command | AI4: Current 2 |
| AO5–7: unused | AI5–7: unused |

AI1 is position readback, not a selectable extra current channel. Reserved
legacy motion flags do not provide general coarse-positioner support.

Position scaling uses per-axis maximum and unipolar/bipolar settings. E1 uses
the selected polarity factor and command ratio; E2 omits that ratio. Current
uses each positive V/nA sensitivity and polarity factor.
[Calibration](CALIBRATION.md) defines how to verify these assumptions physically.

## Wire format and time

A waypoint consists of fourteen signed-I16 words:

1. Line/feedback action word.
2. Five velocity words: X, Y, Z, E1, E2.
3. Five position words: X, Y, Z, E1, E2.
4. Position-loop wait, hold timer and packed flags.

Flag bits 0–8 encode Move X/Y/Z/E1, Jump E1, Hold, Move E2, Jump E2 and
Hold Feedback 1. Reserved bits 9–10 are not set by standard Python programs.
The compiler uses power-of-two velocity scalers and a 40 MHz clock; do not
reimplement quantization separately in experiment pages.

Acquisition also uses fourteen I16 words. Runtime decoding retains position,
potential, current, feedback, line and timing information. Remaining legacy
words are not automatically meaningful analysis channels.

The final two biased I16 words join high-first into a **U32 interval in 40 MHz
ticks**, not an absolute counter. Python accumulates intervals in an unbounded
integer and sets the first accepted frame to zero. Batch boundaries do not reset
time; do not apply absolute-counter unwrapping to these interval words.

CSV is deliberately smaller than the runtime sample: see [Recording format](DATA_FORMAT.md).
Line numbers assist runtime phase/ownership handling but do not universally
classify an experiment's scientific phases.

## Startup, completion and stopping

The [startup outputs](REAL_HARDWARE_SETUP.md#connection-changes-physical-outputs)
are target behaviour, not something External Pause prevents.
The driver verifies readiness before claiming a connection.

Programs can refill beyond initial FIFO capacity. Completion requires the
expected acknowledgement/line/waiting state and final acquisition drain—not an
empty host queue alone. Partial frames, stale/overshot tags and ambiguous target
state must not silently become successful completion.

Controlled cancellation can retire the sample stream, requiring reinitialization.
Emergency Stop does not guarantee zero outputs or physical isolation.
Do not relax these checks to broaden model compatibility.

## Extending a device or host adapter

Implement the backend/driver contract with truthful capabilities and one owner.
An advanced adapter can be selected using `ECHEMTIPS_DRIVER_MODULE`;
`WECSPM_DRIVER_MODULE` is a legacy fallback. The adapter receives the open
session; it must not create a competing session or silently download another target.

A new target profile needs documented registers/types, frame layout, scaling,
startup, feedback/stop/acknowledgement semantics and overflow limits, plus
fake-session tests and physical commissioning. Review channel/voltage differences
before changing the driver; support for one adapter operation does not imply
support for every experiment. See [Architecture](ARCHITECTURE.md) and [API](API_REFERENCE.md).
