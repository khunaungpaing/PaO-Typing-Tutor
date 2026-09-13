"""Focused lesson practice surface."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget,
)


class TypingArea(QFrame):
    """Own the primary target, entry, hint, and compact practice actions."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("practiceCard")
        self.setMaximumHeight(360)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 16)
        layout.setSpacing(12)

        self.target_label = QLabel()
        self.target_label.setObjectName("targetText")
        self.target_label.setWordWrap(True)
        self.target_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.target_label.setMinimumHeight(150)
        self.target_label.setMaximumHeight(205)
        layout.addWidget(self.target_label, 1)

        self.input_edit = QLineEdit()
        self.input_edit.setObjectName("typingInput")
        self.input_edit.setClearButtonEnabled(True)
        layout.addWidget(self.input_edit)

        footer = QHBoxLayout()
        footer.setSpacing(10)
        self.hint_label = QLabel()
        self.hint_label.setObjectName("hintText")
        self.sound_button = QPushButton()
        self.sound_button.setObjectName("iconButton")
        self.sound_button.setCheckable(True)
        self.sound_button.setFixedSize(42, 42)
        self.restart_button = QPushButton()
        self.restart_button.setObjectName("iconButton")
        self.restart_button.setFixedSize(42, 42)
        footer.addWidget(self.hint_label)
        footer.addStretch()
        footer.addWidget(self.sound_button)
        footer.addWidget(self.restart_button)
        layout.addLayout(footer)
