"""Vector icon helpers with native Qt fallbacks."""

from __future__ import annotations

from PyQt6.QtGui import QColor, QIcon
from PyQt6.QtWidgets import QStyle, QWidget

try:
    import qtawesome as qta
except ImportError:  # The application remains usable before optional dependency installation.
    qta = None


_NATIVE = {
    "chevron-left": QStyle.StandardPixmap.SP_ArrowBack,
    "chevron-right": QStyle.StandardPixmap.SP_ArrowForward,
    "undo": QStyle.StandardPixmap.SP_BrowserReload,
    "volume-high": QStyle.StandardPixmap.SP_MediaVolume,
    "volume-off": QStyle.StandardPixmap.SP_MediaVolumeMuted,
    "plus": QStyle.StandardPixmap.SP_FileDialogNewFolder,
    "keyboard": QStyle.StandardPixmap.SP_ComputerIcon,
    "list": QStyle.StandardPixmap.SP_FileDialogListView,
}

_AWESOME = {
    "chevron-left": "fa6s.chevron-left",
    "chevron-right": "fa6s.chevron-right",
    "undo": "fa6s.rotate-left",
    "volume-high": "fa6s.volume-high",
    "volume-off": "fa6s.volume-xmark",
    "globe": "fa6s.globe",
    "book": "fa6s.book-open",
    "keyboard": "fa6s.keyboard",
    "plus": "fa6s.plus",
    "list": "fa6s.list-ul",
}


def icon(widget: QWidget, name: str, color: str = "#b9c7dc") -> QIcon:
    """Return a crisp Font Awesome icon or the closest platform icon."""
    if qta is not None and name in _AWESOME:
        return qta.icon(_AWESOME[name], color=QColor(color))
    standard = _NATIVE.get(name)
    return widget.style().standardIcon(standard) if standard is not None else QIcon()
