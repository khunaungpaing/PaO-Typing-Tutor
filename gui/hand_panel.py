"""Animated outline hand guidance for touch-typing finger placement."""

from __future__ import annotations

from PyQt6.QtCore import QRectF, Qt, QVariantAnimation
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QWidget


class HandPositioningPanel(QWidget):
    """Render two vector hand outlines and softly pulse the required finger."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("handPanel")
        self.setMinimumHeight(118)
        self.setMaximumHeight(136)
        self.target_hand: str | None = None
        self.target_finger: str | None = None
        self.shift_hand: str | None = None
        self._pulse = 0.0
        self._animation = QVariantAnimation(self)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.setDuration(1100)
        self._animation.setLoopCount(-1)
        self._animation.setKeyValueAt(0.5, 1.0)
        self._animation.setEndValue(0.0)
        self._animation.valueChanged.connect(self._set_pulse)
        self._animation.start()

    def _set_pulse(self, value: object) -> None:
        self._pulse = float(value)
        if self.target_finger or self.shift_hand:
            self.update()

    def set_target(self, hand: str | None, finger: str | None,
                   shift_hand: str | None = None) -> None:
        self.target_hand = hand
        self.target_finger = finger
        self.shift_hand = shift_hand
        self.update()

    def paintEvent(self, event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        half = self.width() / 2
        self._draw_hand(painter, QRectF(8, 4, half - 16, self.height() - 8), "left")
        self._draw_hand(painter, QRectF(half + 8, 4, half - 16, self.height() - 8), "right")

    def _draw_hand(self, painter: QPainter, area: QRectF, hand: str) -> None:
        outline = QColor("#435571")
        active = QColor("#8e7dff")
        shift = QColor("#4cc9f0")
        fill = QColor("#142238")
        palm_width = min(132.0, area.width() * .3)
        palm_x = area.center().x() - palm_width / 2
        palm = QRectF(palm_x, area.bottom() - 48, palm_width, 42)
        wrist = QRectF(palm.center().x() - 34, palm.bottom() - 6, 68, 12)

        finger_width, gap = 21.0, 7.0
        heights = (43, 61, 70, 63)
        if hand == "right":
            heights = tuple(reversed(heights))
        names = (("Little", "Ring", "Middle", "Index") if hand == "left"
                 else ("Index", "Middle", "Ring", "Little"))
        start_x = palm_x + 14
        finger_paths: dict[str, QPainterPath] = {}
        for index, (height, name) in enumerate(zip(heights, names)):
            rect = QRectF(start_x + index * (finger_width + gap),
                          palm.top() - height + 16, finger_width, height)
            path = QPainterPath()
            path.addRoundedRect(rect, 10, 10)
            finger_paths[name] = path

        thumb_x = palm.right() - 5 if hand == "left" else palm.left() - 35
        thumb_rect = QRectF(thumb_x, palm.top() + 15, 40, 23)
        thumb_path = QPainterPath()
        thumb_path.addRoundedRect(thumb_rect, 11, 11)
        silhouette = QPainterPath()
        silhouette.addRoundedRect(palm, 20, 20)
        wrist_path = QPainterPath()
        wrist_path.addRoundedRect(wrist, 9, 9)
        silhouette = silhouette.united(wrist_path).united(thumb_path)
        for path in finger_paths.values():
            silhouette = silhouette.united(path)
        painter.setBrush(fill)
        painter.setPen(QPen(outline, 1.8))
        painter.drawPath(silhouette)

        for name, path in finger_paths.items():
            is_target = self.target_hand in (hand, "both") and self.target_finger == name
            is_shift = self.shift_hand == hand and name == "Little"
            color = shift if is_shift else active if is_target else outline
            if is_target or is_shift:
                glow = QColor(color)
                glow.setAlpha(45 + int(self._pulse * 75))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QPen(glow, 8 + self._pulse * 4))
                painter.drawPath(path)
                highlight_fill = QColor(color)
                highlight_fill.setAlpha(45)
                painter.setBrush(highlight_fill)
                painter.setPen(QPen(color, 2.8))
                painter.drawPath(path)

        thumb_active = self.target_hand in (hand, "both") and self.target_finger == "Thumb"
        if thumb_active:
            glow = QColor(active)
            glow.setAlpha(45 + int(self._pulse * 75))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(glow, 8 + self._pulse * 4))
            painter.drawPath(thumb_path)
            thumb_fill = QColor(active)
            thumb_fill.setAlpha(45)
            painter.setBrush(thumb_fill)
            painter.setPen(QPen(active, 2.8))
            painter.drawPath(thumb_path)
