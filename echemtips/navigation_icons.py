"""Original MIT vector icons: workflow at left, measurement at right."""
from functools import lru_cache
from PySide6 import QtCore, QtGui, QtSvg


ICON_FAMILIES = {
    'Settings': 'settings', 'Move piezo': 'move', 'All experiments': 'library',
    'Watch current': 'current', 'Watch position': 'position', 'Preflight': 'check',
    'Characterize pipette': 'pipette', 'CV': 'cv', 'Approach': 'approach',
    'Approach + CV': 'cv', 'Approach + CV scan-rate series': 'cv_series',
    'Approach + I-t': 'current', 'Scan hopping + CV': 'scan',
    'Scan hopping + I-t': 'scan', 'Adaptive hopping + CV / LSV': 'adaptive',
    'Adaptive hopping + I-t': 'adaptive', 'Combinatorial scan + CV / LSV': 'combinatorial',
    'Combinatorial scan + I-t': 'combinatorial',
}
WORKFLOWS = {
    'Approach + CV': 'approach', 'Approach + CV scan-rate series': 'approach',
    'Approach + I-t': 'approach', 'Scan hopping + CV': 'scan', 'Scan hopping + I-t': 'scan',
    'Adaptive hopping + CV / LSV': 'adaptive', 'Adaptive hopping + I-t': 'adaptive',
    'Combinatorial scan + CV / LSV': 'combinatorial', 'Combinatorial scan + I-t': 'combinatorial',
}
MEASUREMENTS = {name: ('series' if 'scan-rate' in name else 'pulse' if 'I-t' in name else 'cv')
                for name in WORKFLOWS}
CONTENT_COLOR, SIDEBAR_COLOR = '#176c78', '#bad2e3'


def navigation_svg(name: str, sidebar: bool = False) -> str:
    """Return vector source with shared strokes, not colour-only badges."""
    name = name.replace('I–t', 'I-t')
    family = ICON_FAMILIES.get(name, 'library')
    paths, circles = [], []
    workflow = WORKFLOWS.get(name)
    if workflow:
        if workflow == 'approach':
            paths += ['M5 3v13m-3-3 3 3 3-3M2 21h6']
        elif workflow == 'scan':
            paths += ['M2 4h7v7H2v8h7']
        elif workflow == 'adaptive':
            paths += ['M2 4 8 10 3 19M5 5h4V1']
            circles += [(8, 10, 1.5), (3, 19, 1.5)]
        else:
            paths += ['M2 3h6v5H2ZM2 11h6v5H2ZM5 19l3 3H2Z']
        measurement = MEASUREMENTS[name]
        if measurement == 'cv':
            paths += ['M13 18 16 5 18 4 22 13 20 20 17 19 13 10']
        elif measurement == 'series':
            paths += ['M13 20 16 5 19 3 22 14 20 21', 'M13 16 16 9 18 8 21 15 19 18']
        else:
            paths += ['M13 19h2V5h3v8h4v6']
    elif family == 'settings':
        paths += ['M5 3v4m0 4v10M12 3v12m0 4v2M19 3v6m0 4v8']
        circles += [(5, 9, 2), (12, 17, 2), (19, 11, 2)]
    elif family == 'move':
        paths += ['M3 12h18M12 3v18M6 9l-3 3 3 3M18 9l3 3-3 3M9 6l3-3 3 3M9 18l3 3 3-3']
    elif family == 'library':
        paths += ['M3 3h7v7H3ZM14 3h7v7h-7ZM3 14h7v7H3ZM14 14h7v7h-7Z']
    elif family == 'cv':
        paths += ['M3 18 6 7 12 4 19 10 21 17 15 20 8 15 3 18']
    elif family == 'current':
        paths += ['M2 16h4l2-10 3 14 3-10 3 6h5']
    elif family == 'position':
        paths += ['M3 3v18h19M6 17h4v-5h5V7h6']
    elif family in {'approach', 'pipette'}:
        paths += ['M7 3h10l-5 12ZM12 16v3M5 22h14']
        if family == 'pipette':
            paths += ['M19 4h3v13h-3']
    else:
        circles += [(12, 12, 9)]
        paths += ['M7 12l3 4 7-8']
    color = SIDEBAR_COLOR if sidebar else CONTENT_COLOR
    strokes = ''.join(f'<path d="{path}"/>' for path in paths)
    strokes += ''.join(f'<circle cx="{x}" cy="{y}" r="{r}"/>' for x, y, r in circles)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
            f'<title>eChemTips navigation</title><g fill="none" stroke="{color}" '
            f'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{strokes}</g></svg>')


@lru_cache(maxsize=96)
def navigation_icon(name, sidebar=False):
    """Render the same vector grammar for sidebar, library and favourites."""
    renderer = QtSvg.QSvgRenderer(navigation_svg(name, sidebar).encode())
    icon = QtGui.QIcon()
    for size in (20, 24, 40, 48, 96):
        pixmap = QtGui.QPixmap(size, size)
        pixmap.fill(QtCore.Qt.GlobalColor.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        renderer.render(painter)
        painter.end()
        icon.addPixmap(pixmap)
    return icon
