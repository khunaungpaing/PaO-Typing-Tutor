"""Font configuration shared by every Pa-O text surface."""

from __future__ import annotations

from PyQt6.QtGui import QFont


PAO_STYLISTIC_SET = "ss01"


def enable_pao_shaping(font: QFont) -> QFont:
    """Return a copy of ``font`` with KhamThaton's Pa-O forms enabled."""
    configured = QFont(font)
    configured.setFeature(QFont.Tag.fromString(PAO_STYLISTIC_SET), 1)
    return configured


def pao_font(family: str, point_size: int) -> QFont:
    """Build a font that renders temporary Kham Dom sequences correctly."""
    return enable_pao_shaping(QFont(family, point_size))
