"""Independent analytical limits, history, conservation and convergence checks."""
from dataclasses import replace
import unittest
import numpy as np
from echemtips.seccm_models import ModelParameters, limiting_current, step_current, steady_wave
from echemtips.seccm_transient import TransientProgram, potential_program, transient_current


class TransientModelsTest(unittest.TestCase):
    def test_diffusion_step_matches_published_table_one(self):
        p = replace(ModelParameters(), rate_m_s=1.0)
        times = np.r_[0, np.geomspace(1e-5, 0.1, 80)]
        result = transient_current(p, times, np.full(len(times), -0.8))
        np.testing.assert_allclose(result['current_a'][1:], step_current(p, times[1:]), rtol=0.015, atol=0)
        self.assertLess(result['numerics']['relative_mass_balance_error'], 1e-6)
        self.assertGreaterEqual(result['numerics']['concentration_fraction_min'], -1e-7)
        np.testing.assert_allclose(np.asarray(result['final_ox_mol_m3']) + result['final_red_mol_m3'], p.concentration_mol_m3)

    def test_slow_wave_matches_si_s34_kinetic_rates(self):
        times, potentials = potential_program(TransientProgram(waveform='LSV', scan_rate_v_s=0.002))
        for rate in (1e-5, 1e-4, 1e-3, 1e-2):  # SI S4: 0.001, 0.01, 0.1, 1 cm/s
            p = replace(ModelParameters(), rate_m_s=rate)
            result = transient_current(p, times, potentials)
            error = np.asarray(result['current_a'])[1:] - steady_wave(p, potentials[1:])
            self.assertLess(np.max(abs(error))/abs(limiting_current(p)), 0.01)

    def test_nonzero_surface_concentration_si_table_s2(self):
        # Fast equal-D kinetics at E0 gives cOx,s ≈ cRed,s ≈ cb/2.
        p = replace(ModelParameters(), rate_m_s=1)
        times = np.r_[0, np.geomspace(1e-4, .1, 60)]
        result = transient_current(p, times, np.zeros(len(times)))
        np.testing.assert_allclose(result['current_a'][1:], .5*step_current(p, times[1:]), rtol=.02, atol=0)

    def test_fast_large_probe_forms_peak(self):
        p = replace(ModelParameters(), radius_m=5e-6, height_m=2.5e-6,
                    footprint_radius_m=5.59e-6, rate_m_s=1)
        peaks = []
        for scan_rate in (0.01, 1):
            t, e = potential_program(TransientProgram(start_v=.5, vertex1_v=-.5,
                                                      vertex2_v=.5, scan_rate_v_s=scan_rate))
            current = np.asarray(transient_current(p, t, e)['current_a'])
            vertex = int(np.argmin(e))
            peak = -current[1:vertex+1].min()
            peaks.append(peak)
            if scan_rate == 1:
                self.assertGreater(peak, 1.5*abs(current[vertex]))
                self.assertGreater(current[vertex+1:].max(), 0)
        self.assertGreater(peaks[1], 2*peaks[0])

    def test_oxidation_reduction_symmetry_and_history(self):
        p = replace(ModelParameters(), rate_m_s=0.01)
        t, e = potential_program(TransientProgram(cycles=2, scan_rate_v_s=20))
        reduction = transient_current(p, t, e)
        oxidation = transient_current(replace(p, oxidation=True), t, -e)
        np.testing.assert_allclose(reduction['current_a'], -np.asarray(oxidation['current_a']), rtol=1e-6, atol=1e-20)
        halfway = (len(t)-1)//2
        self.assertFalse(np.allclose(reduction['current_a'][:halfway], reduction['current_a'][halfway:-1], rtol=1e-3, atol=1e-16))

    def test_grid_time_convergence(self):
        p = replace(ModelParameters(), radius_m=2e-6, height_m=1e-6,
                    footprint_radius_m=2.236e-6, rate_m_s=0.01)
        t, e = potential_program(TransientProgram(scan_rate_v_s=5))
        coarse = transient_current(p, t, e)
        fine = transient_current(p, t, e, cells=480, time_fraction=.015, potential_step_v=.0005)
        difference = np.asarray(coarse['current_a']) - fine['current_a']
        self.assertLess(np.max(abs(difference))/max(abs(np.asarray(fine['current_a']))), .02)

    def test_validation_cancellation_and_budgets(self):
        p = ModelParameters()
        for times, potentials in (([0, 0], [0, 1]), ([0, 1], [0, np.nan]), ([0, 1], [0])):
            with self.assertRaises(ValueError): transient_current(p, times, potentials)
        with self.assertRaises(InterruptedError): transient_current(p, [0, 1], [0, 1], cancelled=lambda: True)
        with self.assertRaises(ValueError): transient_current(p, [0, 1], [0, 1], max_steps=1)
        with self.assertRaises(ValueError): transient_current(replace(p, electrons=2), [0, 1], [0, 1])
        with self.assertRaises(ValueError): potential_program(TransientProgram(waveform='LSV', cycles=2))
        with self.assertRaises(ValueError): potential_program(TransientProgram(start_v=0, vertex1_v=0, waveform='LSV'))
        t, e = potential_program(TransientProgram(waveform='Step', prehold_s=10))
        self.assertTrue(np.all(np.diff(t) > 0))
        self.assertEqual(e[-1], -.3)


if __name__ == '__main__':
    unittest.main()
