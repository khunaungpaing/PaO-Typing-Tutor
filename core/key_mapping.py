"""Physical QWERTY bindings for the Pa-O Kham Dom keyboard."""

from __future__ import annotations

from typing import Final

from PyQt6.QtCore import Qt


# Base and Shift rules transcribed from pa_o_kham_dom.kmn. Each value is the
# exact Unicode string emitted by that physical key. Supplementary-plane Pa-O
# digits must remain full scalar values and temporary Kham Dom encodings must
# remain multi-codepoint strings so KhamThaton's ss01 feature can shape them.
BUILTIN_LAYOUT_NAME: Final[str] = "Pa-O Kham Dom Experimental"

PAO_KEY_MAP: Final[dict[int, dict[str, str]]] = {
    Qt.Key.Key_QuoteLeft.value: {"normal": "ၐ", "shift": "ဎ"},
    Qt.Key.Key_1.value: {"normal": "\U000116D1", "shift": "ဍ"},
    Qt.Key.Key_2.value: {"normal": "\U000116D2", "shift": "ဠ"},
    Qt.Key.Key_3.value: {"normal": "\U000116D3", "shift": "ဋ"},
    Qt.Key.Key_4.value: {"normal": "\U000116D4", "shift": "ၓ"},
    Qt.Key.Key_5.value: {"normal": "\U000116D5", "shift": "ၔ"},
    Qt.Key.Key_6.value: {"normal": "\U000116D6", "shift": "ၕ"},
    Qt.Key.Key_7.value: {"normal": "\U000116D7", "shift": "ရ"},
    Qt.Key.Key_8.value: {"normal": "\U000116D8", "shift": "*"},
    Qt.Key.Key_9.value: {"normal": "\U000116D9", "shift": "("},
    Qt.Key.Key_0.value: {"normal": "\U000116D0", "shift": ")"},
    Qt.Key.Key_Minus.value: {"normal": "-", "shift": "_"},
    Qt.Key.Key_Equal.value: {"normal": "=", "shift": "+"},
    Qt.Key.Key_Q.value: {"normal": "ဆ", "shift": "ဈ"},
    Qt.Key.Key_W.value: {"normal": "တ", "shift": "ဝ"},
    Qt.Key.Key_E.value: {"normal": "န", "shift": "ဣ"},
    Qt.Key.Key_R.value: {"normal": "မ", "shift": "၎"},
    Qt.Key.Key_T.value: {"normal": "အ", "shift": "ဤ"},
    Qt.Key.Key_Y.value: {"normal": "ပ", "shift": "၌"},
    Qt.Key.Key_U.value: {"normal": "က", "shift": "ဥ"},
    Qt.Key.Key_I.value: {"normal": "င", "shift": "၍"},
    Qt.Key.Key_O.value: {"normal": "သ", "shift": "ဿ"},
    Qt.Key.Key_P.value: {"normal": "စ", "shift": "ဏ"},
    Qt.Key.Key_BracketLeft.value: {"normal": "ဟ", "shift": "ဧ"},
    Qt.Key.Key_BracketRight.value: {"normal": "ဩ", "shift": "ဪ"},
    Qt.Key.Key_Backslash.value: {"normal": "၏", "shift": "ၑ"},
    Qt.Key.Key_A.value: {"normal": "ေ", "shift": "ဗ"},
    Qt.Key.Key_S.value: {"normal": "ျ", "shift": "ှ"},
    Qt.Key.Key_D.value: {"normal": "ိ", "shift": "ီ"},
    Qt.Key.Key_F.value: {"normal": "်", "shift": "္"},
    Qt.Key.Key_G.value: {"normal": "ါ", "shift": "ွ"},
    Qt.Key.Key_H.value: {"normal": "့", "shift": "ံ"},
    Qt.Key.Key_J.value: {"normal": "ြ", "shift": "ဲ"},
    Qt.Key.Key_K.value: {"normal": "ု", "shift": "ဒ"},
    Qt.Key.Key_L.value: {"normal": "ူ", "shift": "ဓ"},
    Qt.Key.Key_Semicolon.value: {"normal": "း", "shift": "ဂ"},
    Qt.Key.Key_Apostrophe.value: {"normal": "'", "shift": "\""},
    Qt.Key.Key_Z.value: {"normal": "ဖ", "shift": "ဇ"},
    Qt.Key.Key_X.value: {"normal": "ထ", "shift": "ဌ"},
    Qt.Key.Key_C.value: {"normal": "ခ", "shift": "ဃ"},
    Qt.Key.Key_V.value: {"normal": "လ", "shift": "္လ"},
    Qt.Key.Key_B.value: {"normal": "ဘ", "shift": "ယ"},
    Qt.Key.Key_N.value: {"normal": "ည", "shift": "ဉ"},
    Qt.Key.Key_M.value: {"normal": "ာ", "shift": "ဦ"},
    Qt.Key.Key_Comma.value: {"normal": "𑛦", "shift": "၊"},
    Qt.Key.Key_Period.value: {"normal": "ႋ", "shift": "။"},
    Qt.Key.Key_Slash.value: {"normal": "/", "shift": "?"},
    Qt.Key.Key_Space.value: {"normal": " ", "shift": " "},
}

# Keep an immutable-in-practice baseline because PAO_KEY_MAP is the active,
# runtime-switchable layout used by the input engine.
DEFAULT_PAO_KEY_MAP: Final[dict[int, dict[str, str]]] = {
    key: states.copy() for key, states in PAO_KEY_MAP.items()
}


PHYSICAL_LABELS: Final[dict[int, str]] = {
    Qt.Key.Key_QuoteLeft.value: "`", **{
        getattr(Qt.Key, f"Key_{digit}").value: digit for digit in "1234567890"
    },
    Qt.Key.Key_Minus.value: "-", Qt.Key.Key_Equal.value: "=",
    **{getattr(Qt.Key, f"Key_{letter}").value: letter for letter in "QWERTYUIOPASDFGHJKLZXCVBNM"},
    Qt.Key.Key_BracketLeft.value: "[", Qt.Key.Key_BracketRight.value: "]",
    Qt.Key.Key_Backslash.value: "\\", Qt.Key.Key_Semicolon.value: ";",
    Qt.Key.Key_Apostrophe.value: "'", Qt.Key.Key_Comma.value: ",",
    Qt.Key.Key_Period.value: ".", Qt.Key.Key_Slash.value: "/",
    Qt.Key.Key_Space.value: "SPACE",
}


def mapped_character(key: int, shifted: bool = False) -> str | None:
    """Return the exact Unicode text emitted by a physical Qt key code."""
    binding = PAO_KEY_MAP.get(key)
    return binding["shift" if shifted else "normal"] if binding else None


def key_for_target(remaining_target: str) -> tuple[int, bool] | None:
    """Find the longest keyboard output matching the remaining lesson text."""
    matches = [
        (len(output), key, state == "shift")
        for key, binding in PAO_KEY_MAP.items()
        for state, output in binding.items()
        if output and remaining_target.startswith(output)
    ]
    if not matches:
        return None
    _, key, shifted = max(matches, key=lambda match: match[0])
    return key, shifted
