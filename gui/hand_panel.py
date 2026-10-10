"""Animated hand guidance panel for touch-typing finger placement.

Renders two stylised hand silhouettes using smooth Bézier curves with:
- Anatomically proportioned finger widths and heights
- Individual fingernail highlights
- Subtle knuckle shading for depth
- Per-finger glow + pulse animation on the active finger
- Clean palm gradient with wrist taper
"""

from __future__ import annotations
import math

from PyQt6.QtCore import QPointF, QRectF, Qt, QVariantAnimation
from PyQt6.QtGui import (
    QBrush, QColor, QLinearGradient, QPainter, QPainterPath,
    QPen, QRadialGradient,
)
from PyQt6.QtWidgets import QWidget


# ── Palette ────────────────────────────────────────────────────────────────
SKIN_DARK   = QColor("#1a2b44")
SKIN_MID    = QColor("#1e3252")
SKIN_LIGHT  = QColor("#243d61")
SKIN_EDGE   = QColor("#2c4a72")
OUTLINE     = QColor("#3a5275")
NAIL_FILL   = QColor("#2e4a6a")
NAIL_SHINE  = QColor("#5a7fa8")
ACTIVE_CLR  = QColor("#a78bfa")   # violet-400
SHIFT_CLR   = QColor("#38bdf8")   # sky-400
GLOW_ACTIVE = QColor("#7c5cf6")
GLOW_SHIFT  = QColor("#0ea5e9")


class HandPositioningPanel(QWidget):
    """Render two vector hand outlines and softly pulse the required finger."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("handPanel")
        self.setMinimumHeight(130)
        self.setMaximumHeight(160)

        self.target_hand:   str | None = None
        self.target_finger: str | None = None
        self.shift_hand:    str | None = None

        self._pulse = 0.0
        self._animation = QVariantAnimation(self)
        self._animation.setStartValue(0.0)
        self._animation.setKeyValueAt(0.5, 1.0)
        self._animation.setEndValue(0.0)
        self._animation.setDuration(1400)
        self._animation.setLoopCount(-1)
        self._animation.valueChanged.connect(self._set_pulse)
        self._animation.start()

    def _set_pulse(self, value: object) -> None:
        self._pulse = float(value)
        if self.target_finger or self.shift_hand:
            self.update()

    def set_target(self, hand: str | None, finger: str | None,
                   shift_hand: str | None = None) -> None:
        self.target_hand   = hand
        self.target_finger = finger
        self.shift_hand    = shift_hand
        self.update()

    # ── Paint ─────────────────────────────────────────────────────────────

    def paintEvent(self, _event: object) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        w = self.width()
        h = self.height()
        cx = w / 2
        gap = 44  # gap between the two hands

        lw = cx - gap / 2 - 10        # width available for one hand
        self._draw_hand(p, QRectF(10,      6, lw, h - 10), "left")
        self._draw_hand(p, QRectF(cx + gap / 2, 6, lw, h - 10), "right")

    def _draw_hand(self, p: QPainter, area: QRectF, hand: str) -> None:
        # ── Geometry ──────────────────────────────────────────────────────
        AW, AH = area.width(), area.height()
        cx = area.center().x()

        # Palm
        palm_w  = min(AW * 0.82, 115.0)
        palm_h  = max(AH * 0.30, 30.0)
        palm_x  = cx - palm_w / 2
        palm_y  = area.bottom() - palm_h - 2
        palm_r  = QRectF(palm_x, palm_y, palm_w, palm_h)

        # Wrist — slightly narrower, merges smoothly below palm
        wrist_w = palm_w * 0.62
        wrist_h = palm_h * 0.50
        wrist_r = QRectF(cx - wrist_w / 2, palm_r.bottom() - 5, wrist_w, wrist_h + 5)

        # Fingers: (name, rel_height_fraction, width_fraction, tip_radius)
        # heights as fraction of (AH - palm_h)
        avail_h = AH - palm_h - 10
        specs = [
            ("Little", 0.56, 0.85, 6.0),
            ("Ring",   0.78, 1.00, 7.0),
            ("Middle", 0.95, 1.00, 7.5),
            ("Index",  0.74, 1.00, 7.0),
        ]
        if hand == "right":
            specs = list(reversed(specs))

        # Finger widths and gaps
        n_fingers  = 4
        # Total fingers width ≈ palm_w * 0.88
        total_fw   = palm_w * 0.88
        finger_w   = total_fw / (n_fingers + (n_fingers - 1) * 0.22)
        finger_gap = finger_w * 0.22
        start_x    = cx - (total_fw) / 2

        # Build per-finger geometry
        finger_geom: list[tuple[str, float, float, float, float, float]] = []
        for i, (name, hfrac, wfrac, tip_r) in enumerate(specs):
            fw = finger_w * wfrac
            fh = avail_h * hfrac
            fx = start_x + i * (finger_w + finger_gap) + (finger_w - fw) / 2
            fy = palm_y - fh + palm_h * 0.18   # fingers emerge from upper palm
            finger_geom.append((name, fx, fy, fw, fh, tip_r))

        # Thumb
        thumb_w = palm_w * 0.22
        thumb_h = avail_h * 0.44
        if hand == "left":
            tx = palm_r.right() - 4
            ty = palm_y + palm_h * 0.15
            thumb_path = self._thumb_path(tx, ty, thumb_w, thumb_h, right_facing=False)
        else:
            tx = palm_r.left() - thumb_w + 4
            ty = palm_y + palm_h * 0.15
            thumb_path = self._thumb_path(tx, ty, thumb_w, thumb_h, right_facing=True)

        # ── Build silhouette paths ─────────────────────────────────────────
        finger_paths: dict[str, QPainterPath] = {}
        for name, fx, fy, fw, fh, tip_r in finger_geom:
            finger_paths[name] = self._finger_path(fx, fy, fw, fh, tip_r)

        palm_path = QPainterPath()
        palm_path.addRoundedRect(palm_r, 14, 14)

        wrist_path = QPainterPath()
        wrist_path.addRoundedRect(wrist_r, 10, 10)

        silhouette = palm_path.united(wrist_path).united(thumb_path)
        for fp in finger_paths.values():
            silhouette = silhouette.united(fp)

        # ── Draw shadow (depth illusion) ───────────────────────────────────
        shadow_path = QPainterPath(silhouette)
        p.save()
        p.translate(0, 3)
        p.setBrush(QColor(0, 0, 0, 55))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPath(shadow_path)
        p.restore()

        # ── Fill silhouette with gradient ─────────────────────────────────
        top_y    = area.top()
        bottom_y = area.bottom()
        grad = QLinearGradient(QPointF(cx, top_y), QPointF(cx, bottom_y))
        grad.setColorAt(0.00, SKIN_LIGHT)
        grad.setColorAt(0.40, SKIN_MID)
        grad.setColorAt(1.00, SKIN_DARK)

        p.setBrush(QBrush(grad))
        p.setPen(QPen(OUTLINE, 1.2))
        p.drawPath(silhouette)

        # ── Inner palm sheen ──────────────────────────────────────────────
        # A small radial highlight near the top of the palm for depth
        sheen = QRadialGradient(QPointF(cx, palm_y + 6), palm_w * 0.4)
        sheen.setColorAt(0.0, QColor(255, 255, 255, 16))
        sheen.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(QBrush(sheen))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPath(silhouette)

        # ── Draw individual fingers with knuckle / nail details ────────────
        for name, fx, fy, fw, fh, tip_r in finger_geom:
            self._draw_finger_details(p, fx, fy, fw, fh, tip_r)

        # ── Highlight active / shift fingers ──────────────────────────────
        for name, fp in finger_paths.items():
            is_target = self.target_hand in (hand, "both") and self.target_finger == name
            is_shift  = self.shift_hand == hand and name == "Little"
            if is_target or is_shift:
                color     = SHIFT_CLR  if is_shift  else ACTIVE_CLR
                glow_clr  = GLOW_SHIFT if is_shift  else GLOW_ACTIVE
                self._draw_active_finger(p, fp, color, glow_clr)

        if self.target_hand in (hand, "both") and self.target_finger == "Thumb":
            self._draw_active_finger(p, thumb_path, ACTIVE_CLR, GLOW_ACTIVE)

        # ── Labels below each finger (tiny dots instead of text) ──────────
        # Small colored dots at the base of each finger for visual clarity
        dot_y = palm_y + palm_h * 0.72
        for i, (name, fx, fy, fw, fh, tip_r) in enumerate(finger_geom):
            dot_x = fx + fw / 2
            is_target = self.target_hand in (hand, "both") and self.target_finger == name
            is_shift  = self.shift_hand == hand and name == "Little"
            if is_target:
                color = ACTIVE_CLR
                alpha = 180 + int(self._pulse * 75)
            elif is_shift:
                color = SHIFT_CLR
                alpha = 180 + int(self._pulse * 75)
            else:
                color = OUTLINE
                alpha = 80
            c = QColor(color)
            c.setAlpha(alpha)
            p.setBrush(c)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(dot_x, dot_y), 3.5, 3.5)

    # ── Glow helper ───────────────────────────────────────────────────────

    def _draw_active_finger(self, p: QPainter, path: QPainterPath,
                             color: QColor, glow: QColor) -> None:
        pulse = self._pulse

        # Outer soft corona (multi-layer)
        for radius, alpha_base, alpha_pulse in [
            (12, 18, 28),
            (7,  35, 45),
            (4,  55, 55),
        ]:
            c = QColor(glow)
            c.setAlpha(alpha_base + int(pulse * alpha_pulse))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(c, radius))
            p.drawPath(path)

        # Inner fill
        fill = QColor(color)
        fill.setAlpha(38 + int(pulse * 40))
        p.setBrush(fill)
        # Crisp colored outline
        outline = QColor(color)
        outline.setAlpha(200 + int(pulse * 55))
        p.setPen(QPen(outline, 2.0))
        p.drawPath(path)

    # ── Finger detail: nail + knuckle ──────────────────────────────────────

    def _draw_finger_details(self, p: QPainter,
                              fx: float, fy: float, fw: float, fh: float,
                              tip_r: float) -> None:
        """Draw small fingernail and knuckle line inside a finger shape."""
        # Fingernail — small oval near the tip
        nail_w = fw * 0.55
        nail_h = min(tip_r * 0.9, fh * 0.18)
        nail_x = fx + (fw - nail_w) / 2
        nail_y = fy + 3

        nail_grad = QLinearGradient(QPointF(fx + fw / 2, nail_y),
                                    QPointF(fx + fw / 2, nail_y + nail_h))
        nail_grad.setColorAt(0.0, NAIL_SHINE)
        nail_grad.setColorAt(1.0, NAIL_FILL)
        p.setBrush(QBrush(nail_grad))
        p.setPen(QPen(QColor("#4a6888"), 0.7))
        p.drawRoundedRect(QRectF(nail_x, nail_y, nail_w, nail_h),
                          nail_h / 2, nail_h / 2)

        # Knuckle line — subtle horizontal arc ~1/3 up the finger
        knuckle_y  = fy + fh * 0.34
        knuckle_x0 = fx + fw * 0.12
        knuckle_x1 = fx + fw * 0.88
        knuckle_mid = knuckle_y - 2.0   # slight upward bow

        kpath = QPainterPath()
        kpath.moveTo(knuckle_x0, knuckle_y)
        kpath.cubicTo(
            QPointF(knuckle_x0 + (knuckle_x1 - knuckle_x0) * 0.33, knuckle_mid),
            QPointF(knuckle_x0 + (knuckle_x1 - knuckle_x0) * 0.67, knuckle_mid),
            QPointF(knuckle_x1, knuckle_y),
        )
        kc = QColor("#4a6888")
        kc.setAlpha(70)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(kc, 0.9))
        p.drawPath(kpath)

    # ── Shape builders ────────────────────────────────────────────────────

    @staticmethod
    def _finger_path(x: float, y: float, w: float, h: float,
                     tip_r: float) -> QPainterPath:
        """Smooth finger rectangle with a capsule top (rounded tip)."""
        r = min(tip_r, w / 2)
        path = QPainterPath()
        # Bottom edge — straight (merges with palm)
        path.moveTo(x,     y + h)
        path.lineTo(x + w, y + h)
        # Right side up
        path.lineTo(x + w, y + r)
        # Rounded tip — three-point quadratic via cubicTo
        path.cubicTo(
            QPointF(x + w,     y - r * 0.15),
            QPointF(x + w / 2, y - r * 0.35),
            QPointF(x + w / 2, y),
        )
        path.cubicTo(
            QPointF(x + w / 2, y - r * 0.35),
            QPointF(x,         y - r * 0.15),
            QPointF(x,         y + r),
        )
        # Left side down
        path.lineTo(x, y + h)
        path.closeSubpath()
        return path

    @staticmethod
    def _thumb_path(x: float, y: float, w: float, h: float,
                    right_facing: bool) -> QPainterPath:
        """Angled rounded thumb that tapers toward the tip."""
        # We draw it as a rounded parallelogram leaning outward
        angle_offset = w * 0.30
        path = QPainterPath()
        if not right_facing:
            # Left hand: thumb points right
            path.moveTo(x, y + h)
            path.lineTo(x + w, y + h)
            path.cubicTo(
                QPointF(x + w + angle_offset, y + h * 0.5),
                QPointF(x + w + angle_offset, y),
                QPointF(x + w / 2 + angle_offset, y),
            )
            path.cubicTo(
                QPointF(x + angle_offset * 0.4, y),
                QPointF(x - 2, y + h * 0.3),
                QPointF(x, y + h),
            )
        else:
            # Right hand: thumb points left
            path.moveTo(x + w, y + h)
            path.lineTo(x, y + h)
            path.cubicTo(
                QPointF(x - angle_offset, y + h * 0.5),
                QPointF(x - angle_offset, y),
                QPointF(x + w / 2 - angle_offset, y),
            )
            path.cubicTo(
                QPointF(x + w - angle_offset * 0.4, y),
                QPointF(x + w + 2, y + h * 0.3),
                QPointF(x + w, y + h),
            )
        path.closeSubpath()
        return path
