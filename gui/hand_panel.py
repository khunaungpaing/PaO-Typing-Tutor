"""Animated hand guidance for touch-typing finger placement.

Renders two stylised hand silhouettes using smooth Bézier curves for a natural
look.  The active finger softly pulses to guide the learner.
"""

from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, Qt, QVariantAnimation
from PyQt6.QtGui import (
    QBrush, QColor, QLinearGradient, QPainter, QPainterPath, QPen,
)
from PyQt6.QtWidgets import QWidget


class HandPositioningPanel(QWidget):
    """Render two vector hand outlines and softly pulse the required finger."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("handPanel")
        self.setMinimumHeight(110)
        self.setMaximumHeight(130)
        self.target_hand: str | None = None
        self.target_finger: str | None = None
        self.shift_hand: str | None = None
        self._pulse = 0.0
        self._animation = QVariantAnimation(self)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.setDuration(1200)
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

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def paintEvent(self, event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        half = self.width() / 2
        gap = 40  # spacing between left and right hand
        self._draw_hand(painter, QRectF(8, 4, half - gap / 2 - 8, self.height() - 8), "left")
        self._draw_hand(painter, QRectF(half + gap / 2, 4, half - gap / 2 - 8, self.height() - 8), "right")

    def _draw_hand(self, painter: QPainter, area: QRectF, hand: str) -> None:
        outline_color = QColor("#3a4d68")
        active_color = QColor("#8e7dff")
        shift_color = QColor("#4cc9f0")
        fill_color = QColor("#0f1e33")
        fill_highlight = QColor("#162640")

        # Layout geometry -- palm and fingers
        palm_w = min(120.0, area.width() * 0.36)
        palm_h = 36.0
        palm_cx = area.center().x()
        palm_x = palm_cx - palm_w / 2
        palm_y = area.bottom() - palm_h - 4
        palm_rect = QRectF(palm_x, palm_y, palm_w, palm_h)

        # Finger dimensions: (relative_height, tip_radius)
        finger_specs = [
            ("Little", 36, 8.5),
            ("Ring", 50, 9.0),
            ("Middle", 58, 9.5),
            ("Index", 48, 9.0),
        ]
        if hand == "right":
            finger_specs = list(reversed(finger_specs))

        finger_w = 17.0
        finger_gap = 5.0
        total_fingers_w = 4 * finger_w + 3 * finger_gap
        fingers_start_x = palm_cx - total_fingers_w / 2

        finger_paths: dict[str, QPainterPath] = {}
        for i, (name, height, tip_r) in enumerate(finger_specs):
            fx = fingers_start_x + i * (finger_w + finger_gap)
            fy = palm_y - height + 12
            path = self._finger_path(fx, fy, finger_w, height, tip_r)
            finger_paths[name] = path

        # Thumb
        thumb_w, thumb_h = 30.0, 20.0
        if hand == "left":
            thumb_x = palm_rect.right() - 2
            thumb_y = palm_y + 10
            thumb_path = self._thumb_path(thumb_x, thumb_y, thumb_w, thumb_h, mirrored=False)
        else:
            thumb_x = palm_rect.left() - thumb_w + 2
            thumb_y = palm_y + 10
            thumb_path = self._thumb_path(thumb_x, thumb_y, thumb_w, thumb_h, mirrored=True)

        # Wrist
        wrist_w, wrist_h = palm_w * 0.55, 10.0
        wrist_rect = QRectF(palm_cx - wrist_w / 2, palm_rect.bottom() - 4, wrist_w, wrist_h)
        wrist_path = QPainterPath()
        wrist_path.addRoundedRect(wrist_rect, 6, 6)

        # Palm path
        palm_path = QPainterPath()
        palm_path.addRoundedRect(palm_rect, 16, 16)

        # Build composite silhouette
        silhouette = palm_path.united(wrist_path).united(thumb_path)
        for fp in finger_paths.values():
            silhouette = silhouette.united(fp)

        # Draw the filled silhouette with a subtle gradient
        gradient = QLinearGradient(
            QPointF(area.center().x(), palm_y - 60),
            QPointF(area.center().x(), area.bottom()),
        )
        gradient.setColorAt(0.0, fill_highlight)
        gradient.setColorAt(1.0, fill_color)
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(outline_color, 1.4))
        painter.drawPath(silhouette)

        # Draw active / shift finger highlights
        for name, path in finger_paths.items():
            is_target = self.target_hand in (hand, "both") and self.target_finger == name
            is_shift = self.shift_hand == hand and name == "Little"
            if is_target or is_shift:
                color = shift_color if is_shift else active_color
                self._draw_glow_finger(painter, path, color)

        # Thumb highlight
        if self.target_hand in (hand, "both") and self.target_finger == "Thumb":
            self._draw_glow_finger(painter, thumb_path, active_color)

    def _draw_glow_finger(self, painter: QPainter, path: QPainterPath,
                          color: QColor) -> None:
        """Draw a glowing highlight around a finger path."""
        # Outer glow
        glow = QColor(color)
        glow.setAlpha(30 + int(self._pulse * 60))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(glow, 6 + self._pulse * 3))
        painter.drawPath(path)
        # Inner fill
        inner = QColor(color)
        inner.setAlpha(40 + int(self._pulse * 25))
        painter.setBrush(inner)
        painter.setPen(QPen(color, 2.2))
        painter.drawPath(path)

    @staticmethod
    def _finger_path(x: float, y: float, w: float, h: float,
                     tip_r: float) -> QPainterPath:
        """Build a smooth finger shape with a rounded tip using Bézier curves."""
        path = QPainterPath()
        r = min(tip_r, w / 2)
        # Start at bottom-left of finger
        path.moveTo(x, y + h)
        # Left side going up
        path.lineTo(x, y + r)
        # Rounded tip
        path.cubicTo(
            QPointF(x, y),
            QPointF(x + w / 2, y - r * 0.3),
            QPointF(x + w / 2, y),
        )
        path.cubicTo(
            QPointF(x + w / 2, y - r * 0.3),
            QPointF(x + w, y),
            QPointF(x + w, y + r),
        )
        # Right side going down
        path.lineTo(x + w, y + h)
        path.closeSubpath()
        return path

    @staticmethod
    def _thumb_path(x: float, y: float, w: float, h: float,
                    mirrored: bool) -> QPainterPath:
        """Build an oval thumb shape angled slightly outward."""
        path = QPainterPath()
        path.addRoundedRect(QRectF(x, y, w, h), h / 2, h / 2)
        return path
