"""Unit tests for the virtual keyboard widget and dual English/Pa-O labels."""

from __future__ import annotations

import os
import unittest
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from core.key_mapping import PHYSICAL_LABELS
from gui.virtual_keyboard import VirtualKeyboardWidget


class TestVirtualKeyboard(unittest.TestCase):
    """Verify virtual keyboard layout, dual labels, and state highlighting."""

    @classmethod
    def setUpClass(cls) -> None:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        if QApplication.instance() is None:
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
        cls.font_path = Path("assets/fonts/KhamThaton-Exp-Regular-0.3.ttf").resolve()

    def setUp(self) -> None:
        self.keyboard = VirtualKeyboardWidget(self.font_path, "KhamThaton-Exp")
        self.keyboard.resize(900, 240)

    def test_keys_populated_with_physical_labels(self) -> None:
        """Verify each standard key has an English physical label."""
        for key, button in self.keyboard.keys.items():
            if key == Qt.Key.Key_Space.value:
                self.assertTrue(button.is_spacebar)
            else:
                expected_label = PHYSICAL_LABELS.get(key, "")
                self.assertEqual(button.english_label, expected_label)
                self.assertTrue(len(button.pao_text) > 0)

    def test_shifted_mode_updates_pao_text_retaining_english_label(self) -> None:
        """Switching to shifted mode updates Pa-O characters while keeping English letters."""
        q_key = Qt.Key.Key_Q.value
        button = self.keyboard.keys[q_key]
        self.assertEqual(button.english_label, "Q")
        self.assertEqual(button.pao_text, "ဆ")

        self.keyboard.set_shifted(True)
        self.assertEqual(button.english_label, "Q")
        self.assertEqual(button.pao_text, "ဈ")

        self.keyboard.set_shifted(False)
        self.assertEqual(button.pao_text, "ဆ")

    def test_highlight_target_and_pressed_states(self) -> None:
        """Highlighting targets sets target flags; pressing keys sets pressed flags."""
        q_key = Qt.Key.Key_Q.value
        button = self.keyboard.keys[q_key]

        self.keyboard.highlight_target("ဆ")
        self.assertTrue(button.is_target)
        self.assertFalse(button.is_target_shift)

        self.keyboard.set_pressed_key(q_key)
        self.assertTrue(button.is_pressed)

        self.keyboard.set_pressed_key(None)
        self.assertFalse(button.is_pressed)

    def test_resize_updates_font_sizes(self) -> None:
        """Resizing triggers proportional font size recalculation."""
        self.keyboard.resize(1200, 350)
        self.keyboard._update_font_sizes()
        self.assertGreaterEqual(self.keyboard._current_font_size, 15)
        self.assertGreaterEqual(self.keyboard._current_eng_size, 8)
