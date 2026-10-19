"""Advisory transient spherical-sector diffusion with Butler–Volmer kinetics.

Extends the effective geometry of Anderson & Edwards (2023), DOI
10.1021/acs.analchem.3c00216, using SI S29/S31 rather than treating Table S2
as an instantaneous CV formula. Equal diffusivities imply cOx+cRed=constant.
Finite-volume shell resistances are integrated exactly; backward Euler preserves
concentration history across the complete waveform. No hardware dependencies.
"""
from dataclasses import dataclass
import math
import numpy as np
from scipy.linalg import solve_banded
from scipy.special import expit

from .seccm_models import ModelParameters, F, RGAS, limiting_current

TRANSIENT_VERSION = 1


@dataclass(frozen=True)
class TransientProgram:
    """Prediction waveform in IUPAC volts, seconds and V/s; no implicit resets."""
    waveform: str = "CV"
    start_v: float = 0.3
    vertex1_v: float = -0.3
    vertex2_v: float = 0.3
    scan_rate_v_s: float = 0.25
    cycles: int = 1
    prehold_s: float = 0.0
    step_duration_s: float = 1.0
    points_per_leg: int = 300

    def validate(self):
        """Reject invalid or excessive programs before allocating arrays."""
        if self.waveform not in ("CV", "LSV", "Step"):
            raise ValueError("Select CV, LSV or Step.")
        if not all(math.isfinite(v) for v in (self.start_v, self.vertex1_v, self.vertex2_v,
                                              self.scan_rate_v_s, self.prehold_s, self.step_duration_s)):
            raise ValueError("Waveform values must be finite.")
        if self.scan_rate_v_s <= 0 or self.prehold_s < 0 or self.step_duration_s <= 0:
            raise ValueError("Scan rate and step duration must be positive; pre-hold cannot be negative.")
        if not isinstance(self.cycles, int) or not 1 <= self.cycles <= 50:
            raise ValueError("Use 1–50 CV cycles.")
        if not isinstance(self.points_per_leg, int) or not 30 <= self.points_per_leg <= 1000:
            raise ValueError("Use 30–1000 output points per leg.")
        if self.waveform != "CV" and self.cycles != 1:
            raise ValueError("LSV and Step use one program, not CV cycles.")


def potential_program(program: TransientProgram):
    """Build strictly chronological samples, retaining vertices and pre-hold."""
    program.validate()
    times, potentials = [0.0], [program.start_v]

    def append(duration, target, count):
        """Append a ramp/hold without duplicating a shared time endpoint."""
        if not math.isfinite(duration):
            raise ValueError("Waveform duration exceeds numerical range.")
        if duration <= 0:
            return
        if len(times)+count > 100_000:
            raise ValueError("Reduce cycles or output points (maximum 100,000 samples).")
        start_t, start_e = times[-1], potentials[-1]
        times.extend((start_t + np.linspace(0, duration, count + 1)[1:]).tolist())
        potentials.extend(np.linspace(start_e, target, count + 1)[1:].tolist())

    append(program.prehold_s, program.start_v, 30)
    if program.waveform == "Step":
        # A near-instantaneous ramp makes the discontinuity explicit in E(t).
        # Keep it far shorter than the earliest reported post-step sample.
        jump = max(min(1e-9, program.step_duration_s * 1e-6),
                   float(np.spacing(max(times[-1], 1.0))) * 4096)
        if jump > program.step_duration_s * 0.01:
            raise ValueError("Step duration is too short relative to the pre-hold's timestamp precision.")
        append(jump, program.vertex1_v, 1)
        append(program.step_duration_s, program.vertex1_v, program.points_per_leg)
    else:
        for _ in range(program.cycles):
            targets = (program.vertex1_v, program.vertex2_v, program.start_v) if program.waveform == "CV" else (program.vertex1_v,)
            for target in targets:
                append(abs(target - potentials[-1]) / program.scan_rate_v_s,
                       target, program.points_per_leg)
    if len(times) < 2 or times[-1] <= 0:
        raise ValueError("The waveform needs a nonzero potential sweep or a step duration.")
    if len(times) > 100_000:
        raise ValueError("Reduce cycles or output points (maximum 100,000 samples).")
    return np.asarray(times), np.asarray(potentials)


def transient_current(p: ModelParameters, time_s, potential_v, *, cells=240,
                      time_fraction=0.03, potential_step_v=0.001,
                      cancelled=None, max_steps=200_000):
    """Return i(t) and reproducible diagnostics for a complete sampled E(t).

    Concentrations start uniform: Ox only for Reduction, Red only for Oxidation.
    E(t) is piecewise linear between strictly increasing sample times. Both
    species have p.diffusion_m2_s; cRed follows from conservation, not a reset.
    Surface kinetics use physical footprint area mapped to the spherical sector.
    Output is instantaneous faradaic current in A, not filtered/averaged current.
    """
    p.validate()
    if p.electrons != 1:
        raise ValueError("Transient kinetics currently supports one-electron couples only.")
    t, e = np.asarray(time_s, dtype=float), np.asarray(potential_v, dtype=float)
    if t.ndim != 1 or e.shape != t.shape or not 2 <= len(t) <= 100_000:
        raise ValueError("Provide matching 1D time/potential arrays with 2–100,000 samples.")
    if not np.isfinite(t).all() or not np.isfinite(e).all() or np.any(np.diff(t) <= 0):
        raise ValueError("Finite data and strictly increasing timestamps are required; gaps are not silently repaired.")
    if not isinstance(cells, int) or not 80 <= cells <= 1000:
        raise ValueError("Use 80–1000 radial cells.")
    if not math.isfinite(time_fraction) or not 0 < time_fraction <= 0.1:
        raise ValueError("Time-growth fraction must be in (0, 0.1].")
    if not math.isfinite(potential_step_v) or not 0 < potential_step_v <= 0.005:
        raise ValueError("Maximum potential increment must be in (0, 5 mV].")
    radius = p.equivalent_radius_m
    diffusion_time = radius**2 / p.diffusion_m2_s
    if not math.isfinite(diffusion_time) or diffusion_time <= 0:
        raise ValueError("Geometry/diffusion timescale is outside numerical range.")
    tau = (t - t[0]) / diffusion_time
    if not np.isfinite(tau).all() or tau[-1] > 1e10:
        raise ValueError("Program timescale exceeds the supported numerical domain.")
    # Bulk boundary is >=8 diffusion lengths away over the entire program.
    extent = max(80.0, 8 * math.sqrt(tau[-1]))
    edges = 1 + np.r_[0.0, np.geomspace(1e-5, extent, cells)]
    centers = (edges[:-1] + edges[1:]) / 2
    volumes = np.diff(edges) * (edges[1:]**2 + edges[:-1]*edges[1:] + edges[:-1]**2) / 3
    conductance = centers[:-1]*centers[1:] / np.diff(centers)
    left, right = np.zeros(cells), np.zeros(cells)
    right[:-1], left[1:] = conductance / volumes[:-1], conductance / volumes[1:]
    outer_g = centers[-1]*edges[-1] / (edges[-1]-centers[-1])
    right[-1] = outer_g / volumes[-1]
    surface_g = centers[0] / (centers[0]-1)
    omega = 4 * math.pi * math.sin(math.radians(p.half_angle_deg)/2)**2
    beta = math.pi*p.footprint_radius_m**2 * p.rate_m_s / (omega*radius*p.diffusion_m2_s)
    if not math.isfinite(beta) or beta <= 0:
        raise ValueError("Geometry/kinetic boundary coefficient is outside numerical range.")
    bulk = 0.0 if p.oxidation else 1.0
    # Evolve deviation from bulk so the far field is identically zero initially.
    state = np.zeros(cells)
    scale = abs(limiting_current(p))
    thermal = F / (RGAS*p.temperature_k)

    def boundary(voltage):
        """Eliminate the surface concentration using stable kinetic resistances."""
        eta = thermal * (voltage-p.formal_potential_v)
        log_rate = math.log(beta) + float(np.logaddexp(-p.alpha*eta, (1-p.alpha)*eta))
        effective = surface_g * float(expit(log_rate-math.log(surface_g)))
        return effective, float(expit(eta))

    def flux(voltage):
        """Return net inward Ox flux in dimensionless transport units."""
        effective, equilibrium = boundary(voltage)
        return effective*(state[0]+bulk-equilibrium)

    current = np.empty(len(t)); current[0] = -scale*flux(e[0])
    steps, integrated_flux, balance_error = 0, 0.0, 0.0
    minimum, maximum = bulk, bulk
    for point in range(1, len(t)):
        position = tau[point-1]
        interval = tau[point]-position
        slope = (e[point]-e[point-1]) / interval
        while position < tau[point]:
            if cancelled is not None and cancelled():
                raise InterruptedError("Transient calculation cancelled.")
            steps += 1
            if steps > max_steps:
                raise ValueError("Numerical step budget exceeded; reduce cycles/time span or use a simpler selection.")
            dt = min(tau[point]-position, max(position*time_fraction, 1e-5))
            if slope:
                dt = min(dt, potential_step_v/abs(slope))
            if dt <= 0 or position+dt == position:
                raise ValueError("Waveform time increments are below numerical precision.")
            voltage = e[point-1] + slope*(position+dt-tau[point-1])
            effective, equilibrium = boundary(voltage)
            band = np.zeros((3, cells))
            band[0, 1:], band[2, :-1] = -dt*right[:-1], -dt*left[1:]
            band[1] = 1 + dt*(left+right)
            band[1, 0] += dt*effective/volumes[0]
            rhs = state.copy()
            rhs[0] += dt*effective*(equilibrium-bulk)/volumes[0]
            updated = solve_banded((1, 1), band, rhs, check_finite=False)
            low, high = float(updated.min()+bulk), float(updated.max()+bulk)
            if not np.isfinite(updated).all() or low < -1e-7 or high > 1+1e-7:
                raise ValueError("Nonphysical concentration encountered; refine the numerical settings.")
            surface_flux = effective*(updated[0]+bulk-equilibrium)
            outer_flux = -outer_g*updated[-1]
            balance_error += abs(float(np.dot(volumes, updated-state)) - dt*(outer_flux-surface_flux))
            integrated_flux += abs(dt*surface_flux)
            minimum, maximum = min(minimum, low), max(maximum, high)
            state = updated
            position = min(position+dt, tau[point])
        current[point] = -scale*flux(e[point])
    return {
        "time_s": (t-t[0]).tolist(), "potential_v": e.tolist(), "current_a": current.tolist(),
        "radial_position_m": (centers*radius).tolist(),
        "final_ox_mol_m3": ((state+bulk)*p.concentration_mol_m3).tolist(),
        "final_red_mol_m3": ((1-bulk-state)*p.concentration_mol_m3).tolist(),
        "numerics": {"version": TRANSIENT_VERSION, "method": "spherical finite volume / backward Euler",
                     "cells": cells, "steps": steps, "outer_radius_m": float(edges[-1]*radius),
                     "time_fraction": time_fraction, "max_potential_increment_v": potential_step_v,
                     "concentration_fraction_min": minimum, "concentration_fraction_max": maximum,
                     "relative_mass_balance_error": float(abs(balance_error)/max(integrated_flux, 1e-15))},
        "assumptions": ["Fixed effective spherical-sector geometry; not a full pipette/meniscus mesh.",
                        "One dissolved one-electron couple; equal Ox/Red diffusivities; excess supporting electrolyte.",
                        "Uniform initial reactant, zero initial product; history retained only within this submitted program.",
                        "Butler–Volmer kinetics over the entered footprint area; no migration, iR, capacitance, filtering or moving wetting boundary.",
                        "Instantaneous faradaic output; validate grid/time convergence and geometry before quantitative use."],
    }
