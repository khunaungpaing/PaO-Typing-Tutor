"""Live performance metric cards."""

from __future__ import annotations

from typing import Callable, Dict

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class MetricsBar(QFrame):
    """Display elapsed time, WPM, CPM, and accuracy."""

    def __init__(self, localize_digits: Callable[[str], str] | None = None,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.localize_digits = localize_digits or (lambda value: value)
        self.setObjectName("metricsBar")
        self.setFixedHeight(76)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        self.values: Dict[str, QLabel] = {}
        self.headings: Dict[str, QLabel] = {}
        for key, title in (("time", "TIME"), ("wpm", "WPM"), ("cpm", "CPM"), ("accuracy", "ACCURACY")):
            card = QFrame()
            card.setObjectName("metricCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(18, 9, 18, 9)
            card_layout.setSpacing(2)
            heading = QLabel(title)
            heading.setObjectName("metricHeading")
            initial = "00:00" if key == "time" else "0"
            value = QLabel(self.localize_digits(initial))
            value.setObjectName("metricValue")
            value.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            card_layout.addWidget(heading)
            card_layout.addWidget(value)
            layout.addWidget(card)
            self.values[key] = value
            self.headings[key] = heading

    def set_titles(self, titles: Dict[str, str]) -> None:
        """Update metric headings when the application language changes."""
        for key, heading in self.headings.items():
            heading.setText(titles.get(key, key.upper()))

    def update_metrics(self, seconds: int, wpm: float, cpm: float, accuracy: float) -> None:
        """Refresh all displayed values."""
        self.values["time"].setText(self.localize_digits(
            f"{seconds // 60:02d}:{seconds % 60:02d}"))
        self.values["wpm"].setText(self.localize_digits(f"{wpm:.1f}"))
        self.values["cpm"].setText(self.localize_digits(f"{cpm:.0f}"))
        self.values["accuracy"].setText(self.localize_digits(f"{accuracy:.1f}%"))
