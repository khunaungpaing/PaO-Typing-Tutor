"""Responsive Pa-O on-screen keyboard."""

from __future__ import annotations

from pathlib import Path
from typing import Final

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, Qt, pyqtProperty
from PyQt6.QtGui import QColor, QFont, QFontDatabase
from PyQt6.QtWidgets import (
    QGraphicsDropShadowEffect, QGridLayout, QPushButton, QSizePolicy, QWidget,
)

from core.font_features import pao_font
from core.key_mapping import PAO_KEY_MAP, key_for_target
from gui.hand_panel import HandPositioningPanel


KEY_ROWS: Final[list[list[int]]] = [
    [Qt.Key.Key_QuoteLeft.value, *range(Qt.Key.Key_1.value, Qt.Key.Key_9.value + 1),
     Qt.Key.Key_0.value, Qt.Key.Key_Minus.value, Qt.Key.Key_Equal.value],
    [getattr(Qt.Key, f"Key_{letter}").value for letter in "QWERTYUIOP"]
    + [Qt.Key.Key_BracketLeft.value, Qt.Key.Key_BracketRight.value, Qt.Key.Key_Backslash.value],
    [getattr(Qt.Key, f"Key_{letter}").value for letter in "ASDFGHJKL"]
    + [Qt.Key.Key_Semicolon.value, Qt.Key.Key_Apostrophe.value],
    [getattr(Qt.Key, f"Key_{letter}").value for letter in "ZXCVBNM"]
    + [Qt.Key.Key_Comma.value, Qt.Key.Key_Period.value, Qt.Key.Key_Slash.value],
    [Qt.Key.Key_Space.value],
]

# Pa-O Kham Dom Experimental visual keyboard source mapping.
# Dotted circles (U+25CC) are added to combining marks so their relative positioning is clear.
VISUAL_KEY_MAP: Final[dict[int, dict[str, str]]] = {
    Qt.Key.Key_QuoteLeft.value: {"normal": "\u1050", "shift": "\u100E"},
    Qt.Key.Key_1.value: {"normal": "\U000116D1", "shift": "\u100D"},
    Qt.Key.Key_2.value: {"normal": "\U000116D2", "shift": "\u1020"},
    Qt.Key.Key_3.value: {"normal": "\U000116D3", "shift": "\u100B"},
    Qt.Key.Key_4.value: {"normal": "\U000116D4", "shift": "\u1053"},
    Qt.Key.Key_5.value: {"normal": "\U000116D5", "shift": "\u1054"},
    Qt.Key.Key_6.value: {"normal": "\U000116D6", "shift": "\u1055"},
    Qt.Key.Key_7.value: {"normal": "\U000116D7", "shift": "\u101B"},
    Qt.Key.Key_8.value: {"normal": "\U000116D8", "shift": "*"},
    Qt.Key.Key_9.value: {"normal": "\U000116D9", "shift": "("},
    Qt.Key.Key_0.value: {"normal": "\U000116D0", "shift": ")"},
    Qt.Key.Key_Minus.value: {"normal": "-", "shift": "_"},
    Qt.Key.Key_Equal.value: {"normal": "=", "shift": "+"},
    Qt.Key.Key_Q.value: {"normal": "\u1006", "shift": "\u1008"},
    Qt.Key.Key_W.value: {"normal": "\u1010", "shift": "\u101D"},
    Qt.Key.Key_E.value: {"normal": "\u1014", "shift": "\u1023"},
    Qt.Key.Key_R.value: {"normal": "\u1019", "shift": "\u104E"},
    Qt.Key.Key_T.value: {"normal": "\u1021", "shift": "\u1024"},
    Qt.Key.Key_Y.value: {"normal": "\u1015", "shift": "\u104C"},
    Qt.Key.Key_U.value: {"normal": "\u1000", "shift": "\u1025"},
    Qt.Key.Key_I.value: {"normal": "\u1004", "shift": "\u104D"},
    Qt.Key.Key_O.value: {"normal": "\u101E", "shift": "\u103F"},
    Qt.Key.Key_P.value: {"normal": "\u1005", "shift": "\u100F"},
    Qt.Key.Key_BracketLeft.value: {"normal": "\u101F", "shift": "\u1027"},
    Qt.Key.Key_BracketRight.value: {"normal": "\u1029", "shift": "\u102A"},
    Qt.Key.Key_Backslash.value: {"normal": "\u104F", "shift": "\u1051"},
    Qt.Key.Key_A.value: {"normal": "\u25CC\u1031", "shift": "\u1017"},
    Qt.Key.Key_S.value: {"normal": "\u25CC\u103B", "shift": "\u25CC\u103E"},
    Qt.Key.Key_D.value: {"normal": "\u25CC\u102D", "shift": "\u25CC\u102E"},
    Qt.Key.Key_F.value: {"normal": "\u25CC\u103A", "shift": "\u25CC\u1039"},
    Qt.Key.Key_G.value: {"normal": "\u102B", "shift": "\u25CC\u103D"},
    Qt.Key.Key_H.value: {"normal": "\u1037", "shift": "\u25CC\u1036"},
    Qt.Key.Key_J.value: {"normal": "\u25CC\u103C", "shift": "\u25CC\u1032"},
    Qt.Key.Key_K.value: {"normal": "\u25CC\u102F", "shift": "\u1012"},
    Qt.Key.Key_L.value: {"normal": "\u25CC\u1030", "shift": "\u1013"},
    Qt.Key.Key_Semicolon.value: {"normal": "\u25CC\u1038", "shift": "\u1002"},
    Qt.Key.Key_Apostrophe.value: {"normal": "'", "shift": '"'},
    Qt.Key.Key_Z.value: {"normal": "\u1016", "shift": "\u1007"},
    Qt.Key.Key_X.value: {"normal": "\u1011", "shift": "\u100C"},
    Qt.Key.Key_C.value: {"normal": "\u1001", "shift": "\u1003"},
    Qt.Key.Key_V.value: {"normal": "\u101C", "shift": "\u105E"},
    Qt.Key.Key_B.value: {"normal": "\u1018", "shift": "\u101A"},
    Qt.Key.Key_N.value: {"normal": "\u100A", "shift": "\u1009"},
    Qt.Key.Key_M.value: {"normal": "\u102C", "shift": "\u1026"},
    Qt.Key.Key_Comma.value: {"normal": "\u108F", "shift": "\u104A"},
    Qt.Key.Key_Period.value: {"normal": "\u108B", "shift": "\u104B"},
    Qt.Key.Key_Slash.value: {"normal": "/", "shift": "?"},
    Qt.Key.Key_Space.value: {"normal": " ", "shift": " "},
}

COMBINING_DISPLAY_MAP: Final[dict[str, str]] = {
    "\u1031": "\u25CC\u1031",  # ◌ေ
    "\u103B": "\u25CC\u103B",  # ◌ျ
    "\u102D": "\u25CC\u102D",  # ◌ိ
    "\u103A": "\u25CC\u103A",  # ◌်
    "\u103C": "\u25CC\u103C",  # ◌ြ
    "\u102F": "\u25CC\u102F",  # ◌ု
    "\u1030": "\u25CC\u1030",  # ◌ူ
    "\u1038": "\u25CC\u1038",  # ◌း
    "\u103E": "\u25CC\u103E",  # ◌ှ
    "\u102E": "\u25CC\u102E",  # ◌ီ
    "\u1039": "\u25CC\u1039",  # ◌္
    "\u103D": "\u25CC\u103D",  # ◌ွ
    "\u1036": "\u25CC\u1036",  # ◌ံ
    "\u1032": "\u25CC\u1032",  # ◌ဲ
}


def _keys(characters: str) -> set[int]:
    """Return Qt physical key values for an alphanumeric group."""
    return {getattr(Qt.Key, f"Key_{character.upper()}").value for character in characters}


LEFT_LITTLE = _keys("1qaz") | {Qt.Key.Key_QuoteLeft.value}
LEFT_RING = _keys("2wsx")
LEFT_MIDDLE = _keys("3edc")
LEFT_INDEX = _keys("45rtfgvb")
RIGHT_INDEX = _keys("67yuhjnm")
RIGHT_MIDDLE = _keys("8ik") | {Qt.Key.Key_Comma.value}
RIGHT_RING = _keys("9ol") | {Qt.Key.Key_Period.value}
RIGHT_LITTLE = _keys("0p") | {
    Qt.Key.Key_Minus.value, Qt.Key.Key_Equal.value, Qt.Key.Key_BracketLeft.value,
    Qt.Key.Key_BracketRight.value, Qt.Key.Key_Backslash.value,
    Qt.Key.Key_Semicolon.value, Qt.Key.Key_Apostrophe.value, Qt.Key.Key_Slash.value,
}
LEFT_KEYS = LEFT_LITTLE | LEFT_RING | LEFT_MIDDLE | LEFT_INDEX
FINGER_BY_KEY: Final[dict[int, str]] = {}
for finger, keys in (("Little", LEFT_LITTLE | RIGHT_LITTLE),
                     ("Ring", LEFT_RING | RIGHT_RING),
                     ("Middle", LEFT_MIDDLE | RIGHT_MIDDLE),
                     ("Index", LEFT_INDEX | RIGHT_INDEX)):
    FINGER_BY_KEY.update({key: finger for key in keys})
FINGER_BY_KEY[Qt.Key.Key_Space.value] = "Thumb"


class GlowKeyButton(QPushButton):
    """Keyboard key with an animated, soft target halo."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._glow = 0.0
        self._effect = QGraphicsDropShadowEffect(self)
        self._effect.setOffset(0, 0)
        self._effect.setEnabled(False)
        self.setGraphicsEffect(self._effect)
        self._animation = QPropertyAnimation(self, b"glow", self)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.setDuration(950)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._animation.setLoopCount(-1)
        self._animation.setKeyValueAt(0.5, 1.0)
        self._animation.setEndValue(0.0)

    @pyqtProperty(float)
    def glow(self) -> float:
        return self._glow

    @glow.setter
    def glow(self, value: float) -> None:
        self._glow = value
        color = QColor("#7867ff")
        color.setAlpha(115 + int(value * 110))
        self._effect.setColor(color)
        self._effect.setBlurRadius(16 + value * 13)

    def set_guided(self, guided: bool) -> None:
        if guided and not self._effect.isEnabled():
            self._effect.setEnabled(True)
            self._animation.start()
        elif not guided and self._effect.isEnabled():
            self._animation.stop()
            self._effect.setEnabled(False)


class VirtualKeyboardWidget(QWidget):
    """Keyboard whose labels and highlights follow the Pa-O bindings."""

    def __init__(self, font_path: Path, fallback_family: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(230)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._shifted = False
        self._pressed_key: int | None = None
        self._target_key: int | None = None
        self._target_shifted = False
        self.keys: dict[int, GlowKeyButton] = {}
        self.shift_keys: list[QPushButton] = []
        self.hand_overlay = HandPositioningPanel()
        self._key_font = self._load_font(font_path, fallback_family)

        grid = QGridLayout(self)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(4)
        grid.setVerticalSpacing(4)
        for row_index, row in enumerate(KEY_ROWS):
            offset = row_index if row_index < 4 else 4
            for column, key in enumerate(row):
                button = GlowKeyButton()
                button.setObjectName("keyboardKey")
                button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                button.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
                button.setFont(self._key_font)
                button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                button.setMinimumHeight(38)
                button.setMaximumHeight(42)
                span = 18 if key == Qt.Key.Key_Space.value else 2
                grid.addWidget(button, row_index, offset + column * 2, 1, span)
                self.keys[key] = button
        for column, span in ((0, 4), (22, 4)):
            shift = QPushButton("⇧  Shift")
            shift.setObjectName("modifierKey")
            shift.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            shift.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            shift.setMinimumHeight(38)
            shift.setMaximumHeight(42)
            grid.addWidget(shift, 4, column, 1, span)
            self.shift_keys.append(shift)
        grid.addWidget(self.hand_overlay, 5, 0, 1, 26)
        self._refresh()

    @staticmethod
    def _load_font(font_path: Path, fallback_family: str) -> QFont:
        family = fallback_family
        if font_path.is_file():
            font_id = QFontDatabase.addApplicationFont(str(font_path))
            families = QFontDatabase.applicationFontFamilies(font_id) if font_id >= 0 else []
            if families:
                family = families[0]
        return pao_font(family, 15)

    @property
    def font_family(self) -> str:
        """Family loaded specifically for the Pa-O key caps."""
        return self._key_font.family()

    def set_shifted(self, shifted: bool) -> None:
        """Show normal or Shift Pa-O labels."""
        if self._shifted != shifted:
            self._shifted = shifted
            self._refresh()

    def reload_layout(self) -> None:
        """Refresh key legends after an external layout is activated."""
        self._refresh()

    def set_pressed_key(self, key: int | None) -> None:
        """Highlight the physical key currently held down."""
        self._pressed_key = key if key in self.keys else None
        self._refresh_styles()

    def highlight_target(self, remaining_target: str) -> str | None:
        """Highlight and describe the binding for the next required text."""
        match = key_for_target(remaining_target)
        self._target_key, self._target_shifted = match if match else (None, False)
        self._refresh_styles()
        if match is None:
            return None
        key, shifted = match
        state = "shift" if shifted else "normal"
        visual = VISUAL_KEY_MAP.get(key, {}).get(state)
        if visual:
            return visual
        return PAO_KEY_MAP[key][state]

    def _refresh(self) -> None:
        state = "shift" if self._shifted else "normal"
        for key, button in self.keys.items():
            if key == Qt.Key.Key_Space.value:
                button.setText("Spacebar")
                continue

            character = PAO_KEY_MAP.get(key, {}).get(state, "")
            visual = VISUAL_KEY_MAP.get(key, {}).get(state)

            if visual and (character == "" or character == visual.replace("\u25CC", "")):
                display_text = visual
            else:
                display_text = COMBINING_DISPLAY_MAP.get(character, character)

            button.setText("U+200B" if display_text == "\u200b" else display_text)
        self._refresh_styles()

    def _refresh_styles(self) -> None:
        if self._target_key is None:
            hand = finger = shift_hand = None
        elif self._target_key == Qt.Key.Key_Space.value:
            hand, finger, shift_hand = "both", "Thumb", None
        else:
            hand = "left" if self._target_key in LEFT_KEYS else "right"
            finger = FINGER_BY_KEY.get(self._target_key)
            shift_hand = ("right" if hand == "left" else "left") if self._target_shifted else None
        self.hand_overlay.set_target(hand, finger, shift_hand)
        shift_active = self._shifted or self._target_shifted
        for shift in self.shift_keys:
            shift.setProperty("active", shift_active)
            shift.style().unpolish(shift)
            shift.style().polish(shift)
        for key, button in self.keys.items():
            button.set_guided(key == self._target_key)
            button.setProperty("pressed", key == self._pressed_key)
            button.setProperty("target", key == self._target_key)
            button.setProperty("targetShift", key == self._target_key and self._target_shifted)
            button.style().unpolish(button)
            button.style().polish(button)


# Backwards-compatible name for existing imports.
VirtualKeyboard = VirtualKeyboardWidget
