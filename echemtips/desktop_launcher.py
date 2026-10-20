"""Frozen desktop entry point and source/frozen analysis-process launch contract."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile
import traceback


def analysis_command(arguments: list[str]) -> tuple[str, list[str], str]:
    """Use the bundled dispatcher, never ask a frozen EXE to run Python -m."""
    executable = Path(sys.executable)
    if getattr(sys, 'frozen', False):
        return str(executable), ['--analysis', *arguments], str(Path.cwd())
    if sys.platform == 'win32' and executable.with_name('pythonw.exe').exists():
        executable = executable.with_name('pythonw.exe')
    return str(executable), ['-m', 'echemtips.analysis', *arguments], str(Path(__file__).resolve().parent.parent)


def prepare_runtime() -> Path:
    """Keep installed app data outside its replaceable installation directory."""
    from PySide6 import QtCore
    documents = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.StandardLocation.DocumentsLocation)
    workspace = (Path(documents) if documents else Path.home()) / 'eChemTips'
    workspace.mkdir(parents=True, exist_ok=True)
    os.chdir(workspace)
    return workspace


def installation_lock():
    """Keep a named Windows mutex alive so installers cannot replace a running app."""
    if sys.platform != 'win32':
        return None
    import ctypes
    from ctypes import wintypes
    create = ctypes.windll.kernel32.CreateMutexW
    create.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
    create.restype = wintypes.HANDLE
    handle = create(None, False, 'Local\\eChemTipsDesktop')
    if not handle:
        raise ctypes.WinError()
    return handle


def package_check(output: Path) -> None:
    """Exercise installed imports, pages and a small simulated scan, never NI."""
    from unittest.mock import patch
    import numpy as np
    import scipy.linalg
    import matplotlib
    import nptdms
    import nifpga  # Native NI driver/session is deliberately not opened.
    from PySide6 import QtCore, QtWidgets
    from . import __version__
    from .ui import create_application, EChemTipsApp
    from .analysis_window import AnalysisWindow
    from .backends import SimulationBackend
    from .experiments import ScanHoppingCVExperiment, ExperimentState
    from .models import AppSettings, ScanHoppingCVParameters
    from .seccm_models import ModelParameters
    from .seccm_transient import transient_current

    with tempfile.TemporaryDirectory(prefix='echemtips package check ') as folder:
        with patch.dict(os.environ, {'ECHEMTIPS_SETTINGS_PATH': str(Path(folder) / 'settings.json')}):
            app = create_application()
            control = EChemTipsApp()
            control.poll_timer.stop()
            analysis = AnalysisWindow(data_folder=folder)
            try:
                if control.settings.mode != 'Simulation' or control.backend.connected:
                    raise RuntimeError('Package check must start disconnected in Simulation.')
                control.resize(1280, 800)
                control.show()
                for name in control.PAGE_NAMES:
                    control.show_page(name)
                    app.processEvents()
                    if control.nav_buttons[name].icon().isNull():
                        raise RuntimeError(f'Missing packaged navigation icon: {name}')
                analysis.show()
                for index in range(analysis.tabs.count()):
                    analysis.tabs.setCurrentIndex(index)
                    app.processEvents()
                now = [1000.0]
                with patch('time.monotonic', side_effect=lambda: now[0]):
                    settings = AppSettings()
                    backend = SimulationBackend(settings)
                    backend.connect()
                    parameters = ScanHoppingCVParameters(x_points=2, y_points=1,
                        marker_enabled=False, start_z_um=10, end_z_um=90,
                        lateral_rate_um_s=100, approach_rate_um_s=20,
                        retract_rate_um_s=100, cv_scan_rate_v_s=5,
                        settling_time_s=.02, feedback_mode='magnitude', feedback_threshold_na=.005)
                    experiment = ScanHoppingCVExperiment(backend, settings)
                    experiment.start(parameters)
                    for _ in range(20_000):
                        now[0] += .02
                        experiment.tick_samples([backend.read_sample()])
                        if not experiment.active:
                            break
                    if experiment.state != ExperimentState.COMPLETE or len(experiment.contact_z) != 2:
                        raise RuntimeError(f'Packaged simulated scan failed: {experiment.detail}')
                    backend.disconnect()
                result = transient_current(ModelParameters(), [0, .001, .01], [.3, -.3, -.3])
                if not np.isfinite(result['current_a']).all():
                    raise RuntimeError('Packaged SciPy transient solver failed.')
                report = {'version': __version__, 'python': sys.version, 'qt': QtCore.qVersion(),
                          'device_pixel_ratio': app.primaryScreen().devicePixelRatio(),
                          'frozen': bool(getattr(sys, 'frozen', False)),
                          'pages': len(control.PAGE_NAMES), 'simulation_landings': 2,
                          'hardware_opened': False, 'result': 'passed'}
            finally:
                control.close()
                analysis.close()
                QtWidgets.QApplication.processEvents()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)


def main() -> None:
    """Dispatch installed Control/Analysis shortcuts and report startup failures."""
    if sys.argv[1:2] == ['--package-check']:
        if len(sys.argv) != 3:
            raise SystemExit('Usage: eChemTips --package-check RESULT.json')
        output = Path(sys.argv[2]).resolve()
        try:
            package_check(output)
        except Exception:
            output.parent.mkdir(parents=True, exist_ok=True)
            if not output.exists():
                output.write_text(json.dumps({'result': 'failed', 'traceback': traceback.format_exc()}), encoding='utf-8')
            raise SystemExit(1)
        return
    try:
        if getattr(sys, 'frozen', False):
            mutex = installation_lock()
            prepare_runtime()
        if sys.argv[1:2] == ['--analysis']:
            del sys.argv[1]
            from .analysis import main as run
        else:
            from .app import main as run
        run()
    except Exception:
        if not getattr(sys, 'frozen', False):
            raise
        from .models import default_settings_path
        from PySide6 import QtWidgets
        log = default_settings_path().parent / 'logs' / 'startup.log'
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(traceback.format_exc(), encoding='utf-8')
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        QtWidgets.QMessageBox.critical(None, 'eChemTips could not start',
            f'Please report this error with the diagnostic log:\n{log}\n\n'
            'Your settings and recordings have not been deleted.')
        raise SystemExit(1)


if __name__ == '__main__':
    main()
