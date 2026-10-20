"""Small-size, vector-source and OS icon contracts for original MIT artwork."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from pathlib import Path
import struct
import tempfile
import unittest

from PySide6 import QtCore, QtGui, QtSvg, QtWidgets
from echemtips.branding import application_icon, logo_label
from echemtips.navigation import EXPERIMENTS
from echemtips.navigation_icons import navigation_icon, navigation_svg, CONTENT_COLOR, SIDEBAR_COLOR
from scripts.export_app_icons import export_icons

ROOT = Path(__file__).resolve().parents[1]


def contrast(a, b):
    """WCAG luminance ratio for a pair of RGB hex colours."""
    def luminance(color):
        values = [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)]
        return sum(w * (v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4)
                   for w, v in zip((.2126, .7152, .0722), values))
    x, y = sorted((luminance(a), luminance(b)))
    return (y+.05)/(x+.05)


class BrandingAssetsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def test_approved_logo_and_icon_variants(self):
        assets = ROOT / 'echemtips/assets'
        renderer = QtSvg.QSvgRenderer(str(assets/'echemtips-logo.svg'))
        self.assertTrue(renderer.isValid())
        self.assertIn('electrochemical response', logo_label().accessibleName())
        for size in (16, 20, 24, 32, 48, 256):
            self.assertFalse(application_icon().pixmap(size).isNull())
        ico = (assets/'echemtips.ico').read_bytes()
        reserved, kind, count = struct.unpack('<HHH', ico[:6])
        self.assertEqual((reserved, kind), (0, 1))
        self.assertGreaterEqual(count, 7)
        for index in range(count):
            w, h, _, _, _, _, length, offset = struct.unpack('<BBBBHHII', ico[6+16*index:22+16*index])
            image = QtGui.QImage.fromData(ico[offset:offset+length], 'PNG')
            self.assertEqual(image.width(), w or 256)
            self.assertEqual(image.height(), h or 256)
        icns = (assets/'echemtips.icns').read_bytes()
        self.assertEqual(icns[:4], b'icns')
        self.assertEqual(struct.unpack('>I', icns[4:8])[0], len(icns))

    def test_every_catalog_icon_is_distinct_at_navigation_size(self):
        for sidebar in (False, True):
            seen = []
            for entry in EXPERIMENTS:
                self.assertTrue(QtSvg.QSvgRenderer(navigation_svg(entry.name, sidebar).encode()).isValid())
                image = navigation_icon(entry.name, sidebar).pixmap(20).toImage()
                self.assertFalse(image.isNull())
                self.assertNotIn(image, seen, entry.name)
                seen.append(image)
        self.assertGreater(contrast(CONTENT_COLOR, '#ffffff'), 3)
        self.assertGreater(contrast(SIDEBAR_COLOR, '#17324d'), 3)
        self.assertGreater(contrast('#6fe0c9', '#17324d'), 3)

    def test_exporter_does_not_overwrite_existing_artwork(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)/'icons'
            export_icons(ROOT/'echemtips/assets/echemtips-logo.svg', output)
            self.assertTrue((output/'echemtips.icns').exists())
            with self.assertRaises(ValueError):
                export_icons(ROOT/'echemtips/assets/echemtips-logo.svg', output)


if __name__ == '__main__':
    unittest.main()
