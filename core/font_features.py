"""Font configuration shared by every Pa-O text surface."""

from __future__ import annotations

from PyQt6.QtGui import QFont


def enable_pao_shaping(font: QFont) -> QFont:
    """Return font configured for native Pa-O rendering without enabling ss01.

    In KhamThaton-Exp font, native Pa-O Kham Dom glyphs are displayed by default.
    OpenType ss01 is NOT enabled, as it would revert to original base glyphs.
    """
    return QFont(font)


def pao_font(family: str, point_size: int) -> QFont:
    """Build a font configured for native Pa-O text rendering."""
    return QFont(family, point_size)
