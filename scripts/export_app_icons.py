"""Render explicit artwork into PNG, Windows ICO and macOS ICNS variants."""
from __future__ import annotations

import argparse
from pathlib import Path
import struct

from PySide6 import QtCore, QtGui, QtSvg

ROOT = Path(__file__).resolve().parents[1]
SIZES = (16, 20, 24, 32, 48, 64, 128, 256, 512, 1024)


def png_bytes(source: Path, size: int) -> bytes:
    """Render SVG or raster artwork without relying on optional image libraries."""
    image = QtGui.QImage(size, size, QtGui.QImage.Format.Format_ARGB32)
    image.fill(QtCore.Qt.GlobalColor.transparent)
    painter = QtGui.QPainter(image)
    painter.setRenderHint(QtGui.QPainter.RenderHint.SmoothPixmapTransform)
    if source.suffix.lower() == '.svg':
        renderer = QtSvg.QSvgRenderer(str(source))
        if not renderer.isValid():
            painter.end()
            raise ValueError(f'Invalid SVG: {source}')
        renderer.render(painter)
    else:
        original = QtGui.QImage(str(source))
        if original.isNull():
            painter.end()
            raise ValueError(f'Invalid image: {source}')
        painter.drawImage(image.rect(), original)
    painter.end()
    buffer = QtCore.QBuffer()
    buffer.open(QtCore.QIODevice.OpenModeFlag.WriteOnly)
    if not image.save(buffer, 'PNG'):
        raise RuntimeError('PNG encoding failed')
    return bytes(buffer.data())


def export_icons(source: Path, output: Path) -> None:
    """Write multi-size icons; never replace the input or existing output files."""
    if output.exists() and any(output.iterdir()):
        raise ValueError('Choose an empty output directory; artwork is never overwritten.')
    output.mkdir(parents=True, exist_ok=True)
    images = {size: png_bytes(source, size) for size in SIZES}
    for size, data in images.items():
        (output / f'echemtips-{size}.png').write_bytes(data)
    ico_images = [(size, images[size]) for size in SIZES if size <= 256]
    offset = 6 + 16 * len(ico_images)
    directory = bytearray(struct.pack('<HHH', 0, 1, len(ico_images)))
    payload = bytearray()
    for size, data in ico_images:
        directory.extend(struct.pack('<BBBBHHII', size % 256, size % 256, 0, 0, 1, 32, len(data), offset))
        payload.extend(data)
        offset += len(data)
    (output / 'echemtips.ico').write_bytes(directory + payload)
    chunks = b''
    for kind, size in ((b'icp4', 16), (b'icp5', 32), (b'icp6', 64),
                       (b'ic07', 128), (b'ic08', 256), (b'ic09', 512), (b'ic10', 1024)):
        data = images[size]
        chunks += kind + struct.pack('>I', len(data) + 8) + data
    (output / 'echemtips.icns').write_bytes(b'icns' + struct.pack('>I', len(chunks) + 8) + chunks)


def main() -> None:
    """Export the existing logo unless an explicit alternative is requested."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'echemtips/assets/echemtips-logo.svg')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    app = QtGui.QGuiApplication.instance() or QtGui.QGuiApplication([])
    export_icons(args.source.resolve(), args.output.resolve())


if __name__ == '__main__':
    main()
