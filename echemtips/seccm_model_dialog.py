"""Opt-in, nonmodal analytical calculator shared by control and analysis.

No backend reference or acquisition subscription: results are advisory only.
Explicit presets and exports never modify application defaults or recordings.
"""
from dataclasses import asdict, replace
import json
from pathlib import Path
import numpy as np
from PySide6 import QtCore, QtWidgets as Q
from .qt_common import XYPlot, label, button, scroll_area
from .seccm_models import ModelParameters, limiting_current, step_current, steady_wave, model_warnings, DOI, MODEL_VERSION
from .seccm_transient import TransientProgram, potential_program, TRANSIENT_VERSION
from .seccm_model_jobs import TransientModelJob

class CompactNumber(Q.QDoubleSpinBox):
    """Show significant digits without eight distracting trailing zeroes."""
    def textFromValue(self, value):
        """Format a value with the active locale and compact significant digits."""
        return self.locale().toString(value, 'g', 8)



class ModelDialog(Q.QDialog):
    """Calculate curves or compare a frozen original-data selection in IUPAC units."""
    def __init__(self, parent=None, dataset=None, cycles=()):
        super().__init__(parent)
        self.setWindowTitle("SECCM models — analytical and transient 1D")
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        self.resize(1050, 760)
        self.dataset = dataset
        self.result = None
        self.fields = {}
        self._calculation_token = 0
        self._jobs = {}
        self._pending_snapshot = None
        self.setMinimumSize(820, 600)
        root = Q.QVBoxLayout(self)
        root.addWidget(label("Predictions only · no instrument settings or landing decisions are changed", word_wrap=True))
        self.tabs = Q.QTabWidget(); root.addWidget(self.tabs, 1)
        results = Q.QWidget(); body = Q.QVBoxLayout(results)
        if dataset is not None:
            root.addWidget(label("Source snapshot: " + dataset.path.name + " · close and reopen to change recording", word_wrap=True))
        self.tabs.addTab(results, "Calculate / compare")
        controls = Q.QGridLayout(); body.addLayout(controls)
        self.kind = Q.QComboBox(); self.kind.addItems(["Analytical · steady-state i–E", "Analytical · diffusion-limited step i–t", "Transient 1D · diffusion + kinetics"])
        self.source = Q.QComboBox(); self.source.addItem("Prediction only", None)
        self.source.setMinimumContentsLength(16)
        self.source.setSizeAdjustPolicy(Q.QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        if dataset is not None:
            self.source.addItem("Original recording — choose time bounds", dataset.rows)
            for cycle in cycles:
                self.source.addItem("Original " + cycle.label, cycle.rows)
        self.channel = Q.QComboBox(); self.channel.addItems(["current1_na", "current2_na"])
        for col, (caption, widget) in enumerate((("Model", self.kind), ("Compare with", self.source), ("Current channel", self.channel))):
            controls.addWidget(label(caption), 0, col); controls.addWidget(widget, 1, col)
        self.e_start = self.number(-100, 100, -0.3)
        self.e_end = self.number(-100, 100, 0.3)
        self.t_start = self.number(0, 1e9, 0)
        self.t_end = self.number(0, 1e9, 1)
        self.origin = self.number(0, 1e9, 0)
        self.interval = self.number(0, 1e6, 0)
        options = Q.QWidget(); form = Q.QFormLayout(options)
        self.options_form = form
        form.addRow("Prediction E start / end (V)", self.pair(self.e_start, self.e_end))
        form.addRow("Recording time bounds / step preview bounds (s)", self.pair(self.t_start, self.t_end))
        form.addRow("Step origin in recording time (s)", self.origin)
        form.addRow("Step averaging interval (ms; 0 = instantaneous)", self.interval)
        self.recording_sign = Q.QComboBox(); self.recording_sign.addItems(["Select recording polarity…", "IUPAC", "Opposite to IUPAC"])
        if dataset is not None:
            convention = dataset.metadata.get("settings", {}).get("polarity_convention")
            if convention == "IUPAC": self.recording_sign.setCurrentIndex(1)
            elif convention == "Instrument-native": self.recording_sign.setCurrentIndex(2)
        form.addRow("Recorded E and i convention", self.recording_sign)
        body.addWidget(options)
        self.plot = XYPlot("Potential (V)", "Current (nA)")
        body.addWidget(self.plot, 1)
        self.summary = label("", word_wrap=True); body.addWidget(self.summary)
        actions = Q.QHBoxLayout(); body.addLayout(actions)
        self.calculate_button = button("Calculate", self.calculate, "primary")
        actions.addWidget(self.calculate_button)
        self.cancel_button = button("Cancel", self.cancel_calculation)
        self.cancel_button.hide(); actions.addWidget(self.cancel_button)
        self.transient_view = Q.QComboBox(); self.transient_view.addItems(["i vs E", "i vs t", "E vs t"])
        self.transient_view.hide(); actions.addWidget(self.transient_view)
        self.plot.current_display_unit = "pA"
        self.export_button = button("Export result…", self.export_result); self.export_button.setEnabled(False)
        actions.addWidget(self.export_button)
        actions.addWidget(button("Model parameters…", lambda: self.tabs.setCurrentIndex(1)))
        parameters = Q.QWidget(); outer = Q.QVBoxLayout(parameters)
        outer.addWidget(label("Physical inputs — illustrative defaults, not measured instrument geometry", word_wrap=True))
        outer.addWidget(label("Enter radius, not diameter, and half-angle, not full cone angle. The D field is a coefficient: 3 × 10⁻⁶ cm²/s means 0.3 here. Concentration is in mM (= mol/m³).", word_wrap=True))
        self.transient_group = Q.QGroupBox("Transient waveform and numerical resolution")
        tf = Q.QFormLayout(self.transient_group)
        self.waveform = Q.QComboBox(); self.waveform.addItems(["CV", "LSV", "Step"])
        tf.addRow("Waveform", self.waveform)
        self.program_fields = {}
        for key, caption, value in (
            ("start_v", "Start / pre-hold potential (V)", 0.3),
            ("vertex1_v", "Vertex 1 / LSV end / step potential (V)", -0.3),
            ("vertex2_v", "Vertex 2 (V; CV only)", 0.3),
            ("scan_rate_v_s", "Scan rate (V/s)", 0.25),
            ("cycles", "CV cycles", 1),
            ("prehold_s", "Pre-hold at Start (s)", 0),
            ("step_duration_s", "Step duration (s)", 1)):
            widget = self.number(-100 if key.endswith("_v") else 0, 100 if key.endswith("_v") else 1e5, value)
            if key == "cycles": widget.setDecimals(0); widget.setRange(1, 50)
            self.program_fields[key] = widget
            tf.addRow(caption, widget)
        self.resolution = Q.QComboBox(); self.resolution.addItems(["Standard · 240 cells", "Fine · 480 cells"])
        tf.addRow("Radial grid", self.resolution)
        tf.addRow(label("CV: Start → V1 → V2 → Start, without concentration resets. Reduction starts with Ox only; Oxidation with Red only. Both current signs can occur. Imported comparison uses an entire extracted cycle; its prior history is unknown.", word_wrap=True))
        tf.addRow(button("Load illustrative peak-response example", self.load_peak_example))
        outer.addWidget(self.transient_group)
        pf = Q.QFormLayout(); outer.addLayout(pf)
        specs = [
            ("radius_m", "Pipette inner radius (nm)", 200, 1e-9),
            ("half_angle_deg", "Pipette half-angle (°)", 7.5, 1),
            ("height_m", "Meniscus height (nm; not contact Z)", 100, 1e-9),
            ("footprint_radius_m", "Physical footprint radius (nm; kinetics only)", 224, 1e-9),
            ("diffusion_m2_s", "Diffusion coefficient (×10⁻⁹ m²/s)", 1, 1e-9),
            ("concentration_mol_m3", "Reactant concentration (mM)", 1, 1),
            ("electrons", "Electrons per reactant (kinetic model: 1)", 1, 1),
            ("formal_potential_v", "Formal potential (V; same reference as data)", 0, 1),
            ("temperature_k", "Temperature (K)", 298.15, 1),
            ("rate_m_s", "Standard rate constant k⁰ (cm/s)", 0.001, 0.01),
            ("alpha", "Transfer coefficient α", 0.5, 1)]
        for key, caption, value, factor in specs:
            widget = self.number(-1e9, 1e9, value)
            if key == "electrons": widget.setDecimals(0)
            self.fields[key] = (widget, factor); pf.addRow(caption, widget)
        self.radius_model = Q.QComboBox(); self.radius_model.addItems(["R3", "R2", "R1"])
        pf.addRow("Equivalent radius approximation", self.radius_model)
        self.reaction = Q.QComboBox(); self.reaction.addItems(["Reduction (negative current)", "Oxidation (positive current)"])
        pf.addRow("Reaction / IUPAC polarity", self.reaction)
        self.spread = self.number(0, 90, 0)
        pf.addRow("Pipette-radius sensitivity ± (%)", self.spread)
        outer.addWidget(label("Radius sensitivity varies only inner radius, with other inputs fixed; it is not a confidence interval. Footprint radius is independent of the map display setting.", word_wrap=True))
        outer.addWidget(label("Analytical expressions are the fast benchmark. Transient 1D adds waveform history with equal Ox/Red diffusivities and Butler–Volmer kinetics. Neither includes capacitance, migration/HER, iR, amplifier filtering or changing wetting geometry. Footprint area maps kinetics onto an effective spherical sector, not a full meniscus mesh.", word_wrap=True))
        row = Q.QHBoxLayout(); outer.addLayout(row)
        row.addWidget(button("Load parameters…", self.load_parameters))
        row.addWidget(button("Save parameters…", self.save_parameters))
        row.addWidget(button("Calculate / compare", lambda: self.tabs.setCurrentIndex(0)))
        outer.addStretch()
        self.tabs.addTab(scroll_area(parameters), "Model parameters")
        close = Q.QDialogButtonBox(Q.QDialogButtonBox.StandardButton.Close)
        close.rejected.connect(self.close); root.addWidget(close)
        for widget in self.findChildren(Q.QDoubleSpinBox): widget.valueChanged.connect(self.invalidate)
        for widget in self.findChildren(Q.QComboBox):
            if widget is not self.transient_view: widget.currentIndexChanged.connect(self.invalidate)
        self.transient_view.currentIndexChanged.connect(self.show_transient_result)
        self.waveform.currentIndexChanged.connect(self.mode_changed)
        self.source.currentIndexChanged.connect(self.select_source)
        self.kind.currentIndexChanged.connect(self.mode_changed)
        self.mode_changed()
        self.calculate()

        self.select_source()
    @staticmethod
    def number(low, high, value):
        """Consistent editable scientific inputs, with explicit units in labels."""
        w = CompactNumber(); w.setDecimals(8); w.setRange(low, high); w.setValue(value)
        w.setKeyboardTracking(False); return w

    @staticmethod
    def pair(a, b):
        """Group two related bounds without widening the entire dialog."""
        w = Q.QWidget(); layout = Q.QHBoxLayout(w); layout.setContentsMargins(0,0,0,0)
        layout.addWidget(a); layout.addWidget(b); return w

    def parameters(self):
        """Translate explicitly entered display units into validated SI parameters."""
        values = {k: w.value()*factor for k, (w, factor) in self.fields.items()}
        values['electrons'] = int(values['electrons'])
        p = ModelParameters(**values, radius_model=self.radius_model.currentText(), oxidation=bool(self.reaction.currentIndex()))
        p.validate(); return p

    def invalidate(self, *_):
        """Never export stale curves under newly edited model settings."""
        self._calculation_token += 1
        for job in self._jobs.values(): job.cancelled.set()
        self.result = None; self.export_button.setEnabled(False)
        self.calculate_button.setEnabled(True); self.cancel_button.hide()
        self.summary.setText("Inputs changed — press Calculate to update.")

    def mode_changed(self, *_):
        """Disable irrelevant controls while keeping the layout stable."""
        step = self.kind.currentIndex() == 1
        numerical = self.kind.currentIndex() == 2
        self.origin.setEnabled(step); self.interval.setEnabled(step)
        self.e_start.setEnabled(not step); self.e_end.setEnabled(not step)
        rows = self.source.currentData() is not None
        self.options_form.setRowVisible(0, not numerical and not step and not rows)
        self.options_form.setRowVisible(1, not numerical and (step or rows))
        self.options_form.setRowVisible(2, step and rows)
        self.options_form.setRowVisible(3, step)
        self.options_form.setRowVisible(4, rows)
        self.channel.setEnabled(rows)
        self.transient_group.setVisible(numerical)
        self.transient_view.setVisible(numerical)
        waveform = self.waveform.currentText()
        self.waveform.setEnabled(not rows)
        for widget in self.program_fields.values(): widget.setEnabled(not rows)
        self.program_fields['cycles'].setEnabled(not rows and waveform == 'CV')
        self.program_fields['vertex2_v'].setEnabled(not rows and waveform == 'CV')
        self.program_fields['scan_rate_v_s'].setEnabled(not rows and waveform != 'Step')
        self.program_fields['step_duration_s'].setEnabled(not rows and waveform == 'Step')

    def select_source(self, *_):
        """Default bounds to the explicit selected original-data scope."""
        rows = self.source.currentData()
        if rows is not None:
            t = rows.matrix[:, rows.columns.index('elapsed_s')]
            finite = t[np.isfinite(t)]
            if len(finite): self.t_start.setValue(float(finite.min())); self.t_end.setValue(float(finite.max()))
        self.recording_sign.setEnabled(rows is not None)
        self.mode_changed()

    def calculate(self):
        """Evaluate selected full-resolution samples; plot reduction is display-only."""
        self.invalidate()
        try:
            if self.kind.currentIndex() == 2:
                self.calculate_transient()
                return
            p = self.parameters(); step = self.kind.currentIndex() == 1
            lo, hi = self.t_start.value(), self.t_end.value()
            if hi <= lo: raise ValueError("End time must exceed start time.")
            dt = self.interval.value()/1000
            rows = self.source.currentData(); measured = None
            if rows is not None:
                if self.recording_sign.currentIndex() == 0: raise ValueError("Confirm the recording's polarity convention before comparing.")
                t = rows.matrix[:, rows.columns.index('elapsed_s')]
                mask = np.isfinite(t) & (t >= lo) & (t <= hi)
                if step: mask &= (t - self.origin.value() > 0) & (t - self.origin.value() >= dt)
                factor = 1 if self.recording_sign.currentIndex() == 1 else -1
                measured = factor * rows.matrix[mask, rows.columns.index(self.channel.currentText())] * 1e-9
                x = t[mask] - self.origin.value() if step else factor * rows.matrix[mask, rows.columns.index('voltage1_v')]
                valid = np.isfinite(x) & np.isfinite(measured); x, measured = x[valid], measured[valid]
                if not len(x): raise ValueError("No valid samples in this interval; review step origin and bounds.")
            elif step:
                low = max(lo, dt, 1e-5)
                if hi <= low: raise ValueError("Step end time must exceed the averaging interval and start time.")
                x = np.geomspace(low, hi, 800)
            else:
                if self.e_end.value() <= self.e_start.value(): raise ValueError("End potential must exceed start potential.")
                x = np.linspace(self.e_start.value(), self.e_end.value(), 800)
            evaluate = lambda params: step_current(params, x, interval_s=dt) if step else steady_wave(params, x)
            predicted = evaluate(p)
            series = [("Model", x, predicted*1e9, "#008c87")]
            radius_curves = []
            if self.spread.value():
                for sign in (-1, 1):
                    varied = replace(p, radius_m=p.radius_m*(1+sign*self.spread.value()/100))
                    y = evaluate(varied); radius_curves.append(y.tolist())
                    series.append((f"Radius {sign*self.spread.value():+g}%", x, y*1e9, "#a1a8bc"))
            residual = None
            if measured is not None:
                series.insert(0, ("Original data (IUPAC)", x, measured*1e9, "#304d79"))
                residual = measured - predicted
            self.plot.x_label = "Time since step (s)" if step else "Potential (V, IUPAC convention)"
            self.plot.y_label = "Current (nA)"
            self.plot.set_data(series)
            message = f"Predicted steady limiting current: {limiting_current(p)*1e12:.4g} pA. "
            if residual is not None: message += f"RMS residual: {np.sqrt(np.mean(residual**2))*1e12:.4g} pA ({len(x)} original samples). "
            if step and np.min(x) < 1e-5: message += "Very early times: meniscus geometry and instrument response can dominate. "
            self.summary.setText(message + "Approximation only; not a landing-quality score.")
            self.result = dict(schema=1, model_version=MODEL_VERSION, doi=DOI, model=self.kind.currentText(),
                parameters_si=asdict(p), assumptions=model_warnings(p), source=str(self.dataset.path) if rows is not None else None,
                selection=self.source.currentText(), channel=self.channel.currentText(),
                recording_polarity=self.recording_sign.currentText(), output_polarity="IUPAC",
                time_bounds_s=[lo,hi], step_origin_s=self.origin.value(), averaging_interval_s=dt if step else 0,
                radius_sensitivity_percent=self.spread.value(), radius_sensitivity_current_a=radius_curves,
                x_unit="s" if step else "V", x=x.tolist(), predicted_current_a=predicted.tolist(),
                measured_current_a=None if measured is None else measured.tolist(),
                residual_current_a=None if residual is None else residual.tolist())
            self.export_button.setEnabled(True)
        except (ValueError, KeyError, OverflowError) as exc:
            self.plot.set_message("Review model inputs")
            self.summary.setText(str(exc))

    def program(self):
        """Read the explicit numerical waveform without changing instrument settings."""
        values = {key: widget.value() for key, widget in self.program_fields.items()}
        values['cycles'] = int(values['cycles']) if self.waveform.currentText() == 'CV' else 1
        program = TransientProgram(waveform=self.waveform.currentText(), **values)
        program.validate()
        return program

    def load_peak_example(self):
        """Load illustrative numerical inputs only; never configure an instrument."""
        p = replace(ModelParameters(), radius_m=2e-6, height_m=1e-6,
                    footprint_radius_m=2.236e-6, rate_m_s=0.01)
        for key, (widget, factor) in self.fields.items(): widget.setValue(getattr(p, key)/factor)
        program = TransientProgram(start_v=.4, vertex1_v=-.4, vertex2_v=.4,
                                   scan_rate_v_s=5, cycles=2, prehold_s=.01)
        for key, widget in self.program_fields.items(): widget.setValue(getattr(program, key))
        self.waveform.setCurrentText('CV'); self.radius_model.setCurrentText('R3')
        self.reaction.setCurrentIndex(0); self.source.setCurrentIndex(0)
        self.kind.setCurrentIndex(2); self.spread.setValue(0)
        self.transient_view.setCurrentIndex(0)
        self.tabs.setCurrentIndex(0)
        self.calculate()

    def calculate_transient(self):
        """Snapshot input and launch a cancellable numerical calculation."""
        p = self.parameters()
        measured, origin = None, None
        rows = self.source.currentData()
        if rows is None:
            program = self.program()
            times, potentials = potential_program(program)
        else:
            if self.source.currentIndex() == 1:
                raise ValueError("For transient comparison select an extracted CV/LSV cycle, not the whole recording. Prior approach/hold history is not inferred.")
            if self.recording_sign.currentIndex() == 0:
                raise ValueError("Confirm the recording polarity before comparison.")
            sign = 1 if self.recording_sign.currentIndex() == 1 else -1
            times = rows.matrix[:, rows.columns.index('elapsed_s')].copy()
            potentials = sign*rows.matrix[:, rows.columns.index('voltage1_v')].copy()
            measured = sign*rows.matrix[:, rows.columns.index(self.channel.currentText())].copy()*1e-9
            if len(times) < 2 or not np.isfinite(measured).all():
                raise ValueError("The cycle must contain at least two finite current samples.")
            origin = float(times[0]); times -= times[0]
        token = self._calculation_token
        job = TransientModelJob(token, p, times, potentials, 480 if self.resolution.currentIndex() else 240, self.spread.value())
        self._pending_snapshot = dict(schema=2, model_version=MODEL_VERSION, transient_version=TRANSIENT_VERSION,
            doi=DOI, model="Transient 1D diffusion + Butler–Volmer", parameters_si=asdict(p),
            program=None if rows is not None else asdict(program),
            source=str(self.dataset.path) if rows is not None else None, selection=self.source.currentText(),
            source_time_origin_s=origin, channel=self.channel.currentText(),
            recording_polarity=self.recording_sign.currentText(), output_polarity="IUPAC",
            radius_sensitivity_percent=self.spread.value(), measured_current_a=None if measured is None else measured.tolist())
        job.signals.finished.connect(self.transient_finished)
        self._jobs[token] = job
        self.calculate_button.setEnabled(False); self.cancel_button.show()
        self.summary.setText("Calculating transient diffusion in background… Cancel or change inputs to discard it.")
        QtCore.QThreadPool.globalInstance().start(job)

    def cancel_calculation(self):
        """Cancel numerical work and discard any pending export snapshot."""
        self.invalidate()
        self.summary.setText("Calculation cancelled; no source data changed.")

    def transient_finished(self, token, payload, error):
        """Accept only the current request; never publish stale predictions."""
        self._jobs.pop(token, None)
        if token != self._calculation_token: return
        self.calculate_button.setEnabled(True); self.cancel_button.hide()
        if error:
            self.summary.setText(error); self.plot.set_message("Review transient inputs")
            return
        result, variants = payload
        self.result = {**self._pending_snapshot, 'transient': result,
                       'radius_sensitivity_current_a': variants,
                       'predicted_current_a': result['current_a'], 'assumptions': result['assumptions']}
        measured = self.result['measured_current_a']
        if measured is not None:
            self.result['residual_current_a'] = (np.asarray(measured)-np.asarray(result['current_a'])).tolist()
        else: self.result['residual_current_a'] = None
        numerical = result['numerics']
        message = f"Transient 1D · {numerical['cells']} cells · {numerical['steps']} steps. "
        message += f"Steady limiting-current benchmark: {limiting_current(ModelParameters(**self.result['parameters_si']))*1e12:.4g} pA. "
        if measured is not None:
            message += f"RMS residual: {np.sqrt(np.mean(np.asarray(self.result['residual_current_a'])**2))*1e12:.4g} pA. "
        self.summary.setText(message + "Uniform initial concentration; no capacitance/iR. Check grid convergence. Not a landing-quality score.")
        self.export_button.setEnabled(True)
        self.show_transient_result()

    def show_transient_result(self, *_):
        """Switch numerical i–E/i–t/E–t without recomputing the transport solution."""
        if self.result is None or 'transient' not in self.result: return
        r = self.result['transient']; view = self.transient_view.currentIndex()
        x = r['potential_v'] if view == 0 else r['time_s']
        self.plot.x_label = "Potential (V, IUPAC convention)" if view == 0 else "Time from program start (s)"
        self.plot.y_label = "Potential (V, IUPAC convention)" if view == 2 else "Current (nA)"
        if view == 2:
            series = [("Applied waveform", x, r['potential_v'], "#008c87")]
        else:
            series = [("Transient 1D", x, np.asarray(r['current_a'])*1e9, "#008c87")]
            if self.result['measured_current_a'] is not None:
                series.insert(0, ("Original data (IUPAC)", x, np.asarray(self.result['measured_current_a'])*1e9, "#304d79"))
            for sign, currents in zip((-1, 1), self.result['radius_sensitivity_current_a']):
                series.append((f"Radius {sign*self.result['radius_sensitivity_percent']:+g}%", x, np.asarray(currents)*1e9, "#a1a8bc"))
        self.plot.set_data(series)
        self.result.update(view=self.transient_view.currentText(), x=x, x_unit='V' if view == 0 else 's',
                           display_y_quantity='potential' if view == 2 else 'current')

    def closeEvent(self, event):
        """Stop background work without blocking instrument/UI event processing."""
        for job in self._jobs.values(): job.cancelled.set()
        super().closeEvent(event)

    def write_json(self, payload, title):
        """Atomic, explicit JSON export with source-file protection."""
        path, _ = Q.QFileDialog.getSaveFileName(self, title, "seccm-model.json", "JSON (*.json)")
        if not path: return
        try:
            target = Path(path).resolve()
            if self.dataset is not None and target in (self.dataset.path.resolve(), self.dataset.path.with_suffix('.json').resolve()):
                raise ValueError("Choose a different path; source recordings are protected.")
            data = json.dumps(payload, indent=2, allow_nan=False).encode()
            out = QtCore.QSaveFile(str(target))
            if not out.open(QtCore.QIODevice.OpenModeFlag.WriteOnly): raise OSError(out.errorString())
            if out.write(data) != len(data) or not out.commit(): raise OSError(out.errorString())
        except (OSError, ValueError) as exc: Q.QMessageBox.warning(self, "Not saved", str(exc))

    def export_result(self):
        """Save predictions, residuals and all assumptions without touching data."""
        if self.result is not None: self.write_json(self.result, "Export model result")

    def save_parameters(self):
        """Save an explicitly named preset; never replace instrument defaults."""
        try:
            payload = dict(schema=2, kind="seccm-model-parameters", parameters=asdict(self.parameters()),
                           radius_sensitivity_percent=self.spread.value(), calculation=self.kind.currentIndex(),
                           resolution=self.resolution.currentIndex())
            if self.kind.currentIndex() == 2:
                payload['transient_program'] = asdict(self.program())
            self.write_json(payload, "Save model parameters")
        except ValueError as exc: Q.QMessageBox.warning(self, "Invalid parameters", str(exc))

    def load_parameters(self):
        """Validate a complete preset before changing any widgets."""
        path, _ = Q.QFileDialog.getOpenFileName(self, "Load model parameters", "", "JSON (*.json)")
        if not path: return
        try:
            payload = json.loads(Path(path).read_text())
            if payload.get('schema') not in (1, 2) or payload.get('kind') != 'seccm-model-parameters': raise ValueError("Not a supported model preset.")
            p = ModelParameters(**payload['parameters']); p.validate()
            program = TransientProgram(**payload.get('transient_program', {})); program.validate()
            calculation, resolution = payload.get('calculation', 0), payload.get('resolution', 0)
            spread = float(payload.get('radius_sensitivity_percent', 0))
            if calculation not in (0, 1, 2) or resolution not in (0, 1) or not np.isfinite(spread) or not 0 <= spread <= 90:
                raise ValueError("Invalid calculation, resolution or radius sensitivity.")
            for k, (w, factor) in self.fields.items():
                value = getattr(p, k)/factor
                if not w.minimum() <= value <= w.maximum(): raise ValueError("Preset value exceeds UI range.")
            for key, widget in self.program_fields.items():
                if not widget.minimum() <= getattr(program, key) <= widget.maximum():
                    raise ValueError("Preset waveform exceeds the UI range.")
            if program.points_per_leg != 300:
                raise ValueError("This UI preset requires 300 output points per leg.")
            for k, (w, factor) in self.fields.items(): w.setValue(getattr(p, k)/factor)
            self.radius_model.setCurrentText(p.radius_model); self.reaction.setCurrentIndex(int(p.oxidation))
            for k, widget in self.program_fields.items(): widget.setValue(getattr(program, k))
            self.waveform.setCurrentText(program.waveform)
            self.kind.setCurrentIndex(calculation); self.resolution.setCurrentIndex(resolution)
            self.spread.setValue(spread)
        except (OSError, ValueError, KeyError, TypeError) as exc: Q.QMessageBox.warning(self, "Preset not loaded", str(exc))


def open_model_dialog(parent, dataset=None, cycles=()):
    """Reuse a visible dialog; data are snapshotted when it is first opened."""
    old = getattr(parent, '_seccm_model_dialog', None)
    if old is not None:
        old.raise_(); old.activateWindow(); return old
    dialog = ModelDialog(parent, dataset, cycles)
    parent._seccm_model_dialog = dialog
    dialog.destroyed.connect(lambda: setattr(parent, '_seccm_model_dialog', None))
    dialog.show(); return dialog
