"""Optional pynput bridge for real-time physical-key guidance."""

from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal

from core.key_mapping import PHYSICAL_LABELS, mapped_character

try:
    from pynput import keyboard as pynput_keyboard
except ImportError:
    pynput_keyboard = None


class PhysicalKeyboardListener(QObject):
    """Map global physical events to Qt key codes and emit thread-safe signals."""

    key_pressed = pyqtSignal(int, bool, str)
    key_released = pyqtSignal(int)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._listener: object | None = None
        self._shifted = False
        self._label_to_key = {label.lower(): key for key, label in PHYSICAL_LABELS.items()}
        self._shifted_labels = {
            "!": "1", "@": "2", "#": "3", "$": "4", "%": "5",
            "^": "6", "&": "7", "*": "8", "(": "9", ")": "0",
            "_": "-", "+": "=", "{": "[", "}": "]", "|": "\\",
            ":": ";", '"': "'", "<": ",", ">": ".", "?": "/", "~": "`",
        }

    @property
    def available(self) -> bool:
        return pynput_keyboard is not None

    def start(self) -> bool:
        if pynput_keyboard is None or self._listener is not None:
            return False
        try:
            self._listener = pynput_keyboard.Listener(
                on_press=self._on_press, on_release=self._on_release)
            self._listener.start()
            return True
        except (OSError, RuntimeError):
            self._listener = None
            return False

    def stop(self) -> None:
        if self._listener is not None:
            try:
                self._listener.stop()
            except (OSError, RuntimeError):
                pass
            self._listener = None

    def _qt_key(self, key: object) -> int | None:
        if pynput_keyboard is None:
            return None
        if key == pynput_keyboard.Key.space:
            return self._label_to_key.get("space")
        character = getattr(key, "char", None)
        if isinstance(character, str) and character:
            label = self._shifted_labels.get(character, character).lower()
            return self._label_to_key.get(label)
        return None

    def _on_press(self, key: object) -> None:
        if pynput_keyboard is None:
            return
        if key in (pynput_keyboard.Key.shift, pynput_keyboard.Key.shift_l,
                   pynput_keyboard.Key.shift_r):
            self._shifted = True
            return
        qt_key = self._qt_key(key)
        if qt_key is not None:
            character = mapped_character(qt_key, self._shifted)
            if character is not None:
                self.key_pressed.emit(qt_key, self._shifted, character)

    def _on_release(self, key: object) -> None:
        if pynput_keyboard is None:
            return
        if key in (pynput_keyboard.Key.shift, pynput_keyboard.Key.shift_l,
                   pynput_keyboard.Key.shift_r):
            self._shifted = False
            return
        qt_key = self._qt_key(key)
        if qt_key is not None:
            self.key_released.emit(qt_key)
