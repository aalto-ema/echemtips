"""Cancellable numerical model work; no widgets or hardware in the worker."""
from dataclasses import replace
from threading import Event
from PySide6 import QtCore
from .seccm_transient import transient_current


class ModelSignals(QtCore.QObject):
    """Deliver one numerical result to the GUI thread with its request token."""
    finished = QtCore.Signal(int, object, str)


class TransientModelJob(QtCore.QRunnable):
    """Evaluate immutable model/waveform snapshots outside the event loop."""
    def __init__(self, token, parameters, times, potentials, cells, spread):
        super().__init__()
        self.token, self.parameters = token, parameters
        self.times, self.potentials, self.cells, self.spread = times.copy(), potentials.copy(), cells, spread
        self.cancelled = Event()
        self.signals = ModelSignals()

    def run(self):
        """Report cancellation/errors without touching the dialog or source data."""
        try:
            result = transient_current(self.parameters, self.times, self.potentials,
                                       cells=self.cells, cancelled=self.cancelled.is_set)
            variants = []
            if self.spread:
                for sign in (-1, 1):
                    p = replace(self.parameters, radius_m=self.parameters.radius_m*(1+sign*self.spread/100))
                    variant = transient_current(p, self.times, self.potentials,
                                                cells=self.cells, cancelled=self.cancelled.is_set)
                    variants.append(variant["current_a"])
            self.signals.finished.emit(self.token, (result, variants), "")
        except InterruptedError:
            self.signals.finished.emit(self.token, None, "Cancelled")
        except Exception as exc:
            self.signals.finished.emit(self.token, None, str(exc))
