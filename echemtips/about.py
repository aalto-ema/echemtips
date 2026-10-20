"""Shared, nonmodal About dialog and help links for both desktop applications."""
import platform
import sys
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from . import __version__
from .branding import logo_label


DOCUMENTATION_URL = "https://aalto-ema.github.io/echemtips/"
SUPPORT_URL = "https://github.com/aalto-ema/echemtips/issues"
REPOSITORY_URL = "https://github.com/aalto-ema/echemtips"
WEC_URL = "https://warwick.ac.uk/fac/sci/chemistry/research/unwin/electrochemistry/wec-spm/"
PAPER_URL = "https://doi.org/10.1021/acselectrochem.5c00354"


def support_details() -> str:
    """Return concise version diagnostics without paths or instrument identifiers."""
    return (f"eChemTips {__version__}\nPython {sys.version.split()[0]}\n"
            f"Qt {QtCore.qVersion()}\nSystem: {platform.system()} {platform.release()} "
            f"({platform.machine()})")


class AboutDialog(QtWidgets.QDialog):
    """Show project identity, attribution and user-initiated help links."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About eChemTips")
        self.setModal(False)
        self.resize(600, 520)
        self.setMinimumSize(440, 380)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(16)
        heading = QtWidgets.QHBoxLayout()
        heading.addWidget(logo_label(64))
        title = QtWidgets.QLabel(f"<h2>eChemTips</h2>Version {__version__}")
        heading.addWidget(title, 1)
        layout.addLayout(heading)
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setAccessibleName("About eChemTips information")
        self.text = QtWidgets.QTextBrowser()
        self.text.setAccessibleName("eChemTips overview and support links")
        self.text.setHtml(
            "<p>Open Python software for instrument control, experiment workflows "
            "and data analysis in scanning electrochemical cell microscopy (SECCM).</p>"
            "<p>Set up measurements, follow live traces and maps, and explore recordings "
            "in the companion analysis app. Workflows include CV/LSV, current–time "
            "measurements, hopping scans, and adaptive and combinatorial experiments. "
            "Simulation lets you explore the software without connecting an instrument.</p>"
            "<p>Developed in the <b>Electrochemical Materials and Applications group "
            "at Aalto University</b>, with contributions and feedback from the community.</p>"
            "<h3>Documentation and community</h3>"
            f'<p><a href="{DOCUMENTATION_URL}">User and developer documentation</a><br>'
            f'<a href="{SUPPORT_URL}">Report a bug or suggest a feature</a><br>'
            f'<a href="{REPOSITORY_URL}">Source code and contributions</a></p>'
            f'<p>Open source under the <a href="{REPOSITORY_URL}/blob/main/LICENSE">MIT license</a>. '
            'See Credits and licenses for acknowledgements and dependency information.</p>'
        )
        self.credits = QtWidgets.QTextBrowser()
        self.credits.setAccessibleName("Acknowledgements, references and licenses")
        self.credits.setHtml(
            "<h3>Acknowledgements</h3>"
            "<p>The FPGA host protocol and workflows build on WEC-SPM "
            "(Warwick Electrochemical Scanning Probe Microscopy, University of Warwick "
            "and collaborators). We thank its developers. "
            "eChemTips is an independent project, not an official Warwick release.</p>"
            f'<p><a href="{WEC_URL}">WEC-SPM and original software requests</a><br>'
            f'<a href="{PAPER_URL}">A Look inside a Flexible Open-Source Scanning '
            'Electrochemical Probe Microscope</a></p>'
            "<p>Made possible by the Python, NumPy, SciPy, PySide6, PyQtGraph and "
            "NI FPGA Python communities, and everyone testing and contributing to eChemTips.</p>"
            "<h3>Licensing</h3>"
            f'<p>eChemTips is released under the <a href="{REPOSITORY_URL}/blob/main/LICENSE">'
            'MIT license</a>. Dependencies and the original platform software have separate licenses.</p>'
            '<p>Qt/PySide6 is used under its open-source license terms. '
            '<a href="https://www.qt.io/development/open-source-lgpl-obligations">Qt licensing and library replacement</a>.</p>'
        )
        for browser, caption in ((self.text, "Overview"), (self.credits, "Credits and licenses")):
            browser.setOpenExternalLinks(True)
            browser.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
            self.tabs.addTab(browser, caption)
        layout.addWidget(self.tabs, 1)
        actions = QtWidgets.QHBoxLayout()
        self.copy_button = QtWidgets.QPushButton("Copy version details")
        self.copy_button.setToolTip("Copy app, Python, Qt and operating-system versions for a support report.")
        self.copy_button.clicked.connect(self.copy_details)
        actions.addWidget(self.copy_button)
        licenses = Path(__file__).resolve().parent.parent / 'release-metadata'
        if licenses.is_dir():
            license_button = QtWidgets.QPushButton('Bundled licenses')
            license_button.setToolTip('Open local dependency license texts and exact build versions.')
            license_button.clicked.connect(lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(licenses))))
            actions.addWidget(license_button)
        actions.addStretch(1)
        close = QtWidgets.QPushButton("Close")
        close.setDefault(True)
        close.clicked.connect(self.close)
        actions.addWidget(close)
        layout.addLayout(actions)

    def copy_details(self):
        """Copy a minimal support summary only when explicitly requested."""
        QtWidgets.QApplication.clipboard().setText(support_details())
        self.copy_button.setText("Copied")


def install_help_menu(window):
    """Install consistent Help actions without interrupting acquisition or analysis."""
    menu = window.menuBar().addMenu("Help")
    for title, url in (("Documentation", DOCUMENTATION_URL), ("Report an issue…", SUPPORT_URL)):
        action = menu.addAction(title)
        action.triggered.connect(lambda _checked=False, target=url: QtGui.QDesktopServices.openUrl(QtCore.QUrl(target)))
    menu.addSeparator()
    about = menu.addAction("About eChemTips…")
    about.setMenuRole(QtGui.QAction.MenuRole.AboutRole)

    def show_about():
        """Reuse a single nonmodal dialog per application window."""
        dialog = getattr(window, "_about_dialog", None)
        if dialog is None:
            dialog = AboutDialog(window)
            window._about_dialog = dialog
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    about.triggered.connect(show_about)
    return menu
