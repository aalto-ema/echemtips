"""Offscreen checks of optional, read-only model UI and original-data comparison."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from pathlib import Path
import unittest
from unittest.mock import patch
from tempfile import TemporaryDirectory
import json
import time
import numpy as np
from PySide6 import QtWidgets as Q, QtCore
from echemtips.analysis_core import AnalysisDataset
from echemtips.seccm_model_dialog import ModelDialog


class ModelDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Q.QApplication.instance() or Q.QApplication([])

    def setUp(self):
        self.d = ModelDialog()

    def tearDown(self):
        self.d.close()
        self.app.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)

    def test_modes_and_stale_export(self):
        self.assertIsNotNone(self.d.result)
        self.d.kind.setCurrentIndex(1)
        self.assertIsNone(self.d.result)
        self.d.calculate()
        self.assertEqual(self.d.result['x_unit'], 's')
        self.d.fields['height_m'][0].setValue(1e8)
        self.d.calculate()
        self.assertIsNone(self.d.result)
        self.assertFalse(self.d.export_button.isEnabled())

    def test_original_comparison_and_polarity(self):
        dataset = AnalysisDataset(Path('example.csv'), ('elapsed_s','voltage1_v','current1_na'),
            [{'elapsed_s':i/10, 'voltage1_v':i/10, 'current1_na':i/100} for i in range(11)],
            {'settings':{'polarity_convention':'Instrument-native'}})
        original = dataset.rows.matrix.copy()
        self.d.close(); self.d = ModelDialog(dataset=dataset)
        self.d.source.setCurrentIndex(1); self.d.calculate()
        self.assertIsNotNone(self.d.result)
        self.assertEqual(self.d.result['x'][-1], -1)
        self.assertAlmostEqual(self.d.result['measured_current_a'][-1], -1e-10)
        np.testing.assert_array_equal(original, dataset.rows.matrix)
        self.d.kind.setCurrentIndex(1); self.d.origin.setValue(.5); self.d.calculate()
        self.assertAlmostEqual(self.d.result['x'][0], .1)
        self.assertEqual(len(self.d.result['x']), 5)

    def test_export_and_preset(self):
        with TemporaryDirectory() as folder:
            path = str(Path(folder)/'parameters.json')
            with patch.object(Q.QFileDialog, 'getSaveFileName', return_value=(path,'')):
                self.d.save_parameters()
            self.d.fields['radius_m'][0].setValue(350)
            with patch.object(Q.QFileDialog, 'getOpenFileName', return_value=(path,'')):
                self.d.load_parameters()
            self.assertEqual(self.d.fields['radius_m'][0].value(), 200)
            self.d.calculate()
            with patch.object(Q.QFileDialog, 'getSaveFileName', return_value=(str(Path(folder)/'result.json'),'')):
                self.d.export_result()
            result = json.loads((Path(folder)/'result.json').read_text())
            self.assertEqual(result['output_polarity'], 'IUPAC')
            self.assertEqual(len(result['x']), len(result['predicted_current_a']))

    def test_source_protection(self):
        with TemporaryDirectory() as folder:
            path = Path(folder)/'recording.csv'; path.write_text('original')
            self.d.dataset = AnalysisDataset(path, ('elapsed_s',), [{'elapsed_s':0}], {})
            with patch.object(Q.QFileDialog, 'getSaveFileName', return_value=(str(path),'')), patch.object(Q.QMessageBox, 'warning') as warning:
                self.d.export_result()
            warning.assert_called_once()
            self.assertEqual(path.read_text(), 'original')

    def wait_for_numerical(self):
        """Process queued GUI results without blocking a worker's completion."""
        deadline = time.monotonic() + 5
        while self.d._jobs and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(.005)
        self.app.processEvents()
        self.assertFalse(self.d._jobs, 'Numerical job did not finish')

    def test_transient_example_views_and_export(self):
        self.d.load_peak_example()
        self.assertIsNone(self.d.result)
        self.assertFalse(self.d.export_button.isEnabled())
        self.wait_for_numerical()
        self.assertIsNotNone(self.d.result, self.d.summary.text())
        result = self.d.result
        self.assertIn('Butler–Volmer', result['model'])
        self.assertEqual(result['program']['cycles'], 2)
        self.assertLess(result['transient']['numerics']['relative_mass_balance_error'], 1e-6)
        self.assertGreater(max(result['predicted_current_a']), 0)
        self.d.transient_view.setCurrentIndex(2)
        self.assertEqual(self.d.plot.y_label, 'Potential (V, IUPAC convention)')
        self.assertIs(result, self.d.result)  # View change does not recompute.
        self.d.transient_view.setCurrentIndex(1)
        self.assertEqual(result['x_unit'], 's')
        with TemporaryDirectory() as folder:
            path = str(Path(folder)/'transient.json')
            with patch.object(Q.QFileDialog, 'getSaveFileName', return_value=(path, '')):
                self.d.export_result()
            self.assertEqual(json.loads(Path(path).read_text())['transient_version'], 1)
        self.d.kind.setCurrentIndex(0); self.d.calculate()
        self.assertEqual(self.d.plot.y_label, 'Current (nA)')

    def test_transient_stale_result_and_cancel(self):
        self.d.kind.setCurrentIndex(2); self.d.calculate()
        self.d.fields['radius_m'][0].setValue(250)
        self.wait_for_numerical()
        self.assertIsNone(self.d.result)
        self.assertFalse(self.d.export_button.isEnabled())
        self.d.calculate(); self.d.cancel_calculation()
        self.wait_for_numerical()
        self.assertIsNone(self.d.result)

    def test_transient_and_legacy_presets(self):
        self.d.kind.setCurrentIndex(2)
        self.d.program_fields['scan_rate_v_s'].setValue(2)
        self.d.program_fields['cycles'].setValue(3)
        self.d.resolution.setCurrentIndex(1)
        with TemporaryDirectory() as folder:
            path = str(Path(folder)/'preset.json')
            with patch.object(Q.QFileDialog, 'getSaveFileName', return_value=(path, '')):
                self.d.save_parameters()
            self.d.kind.setCurrentIndex(0)
            with patch.object(Q.QFileDialog, 'getOpenFileName', return_value=(path, '')):
                self.d.load_parameters()
            self.assertEqual(self.d.kind.currentIndex(), 2)
            self.assertEqual(self.d.program_fields['cycles'].value(), 3)
            self.assertEqual(self.d.program_fields['scan_rate_v_s'].value(), 2)
            self.assertEqual(self.d.resolution.currentIndex(), 1)
            old = json.loads(Path(path).read_text())
            old['schema'] = 1
            for field in ('transient_program', 'resolution', 'calculation'): old.pop(field)
            Path(path).write_text(json.dumps(old))
            with patch.object(Q.QFileDialog, 'getOpenFileName', return_value=(path, '')):
                self.d.load_parameters()
            self.assertEqual(self.d.kind.currentIndex(), 0)

    def test_transient_import_preserves_source(self):
        from types import SimpleNamespace
        from echemtips.seccm_transient import potential_program, TransientProgram
        t, e = potential_program(TransientProgram(points_per_leg=30))
        dataset = AnalysisDataset(Path('example.csv'), ('elapsed_s', 'voltage1_v', 'current1_na'),
            [{'elapsed_s':float(ti+10), 'voltage1_v':float(-ei), 'current1_na':.001} for ti, ei in zip(t, e)],
            {'settings': {'polarity_convention': 'Instrument-native'}})
        original = dataset.rows.matrix.copy()
        self.d.close()
        self.d = ModelDialog(dataset=dataset, cycles=[SimpleNamespace(label='cycle 1', rows=dataset.rows)])
        self.d.kind.setCurrentIndex(2); self.d.source.setCurrentIndex(1); self.d.calculate()
        self.assertIsNone(self.d.result)
        self.assertIn('extracted', self.d.summary.text())
        self.d.source.setCurrentIndex(2); self.d.calculate(); self.wait_for_numerical()
        self.assertIsNotNone(self.d.result, self.d.summary.text())
        np.testing.assert_allclose(self.d.result['transient']['potential_v'], e)
        self.assertAlmostEqual(self.d.result['measured_current_a'][0], -1e-12)
        self.assertAlmostEqual(self.d.result['source_time_origin_s'], 10)
        np.testing.assert_array_equal(original, dataset.rows.matrix)
