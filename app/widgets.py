"""Custom interactive components for Pixora.

Features:
- BeforeAfterSliderWidget: Interactive split-view comparison with draggable divider handle.
- MetricCard: Stat card with animated counting number and trend pill.
- GlowCard: Modern glassmorphism card with ambient glow and hover feedback.
- NavButton: Sidebar navigation button with smooth active indicator.
"""
from __future__ import annotations

from typing import Any, Optional
from PySide6.QtCore import QPoint, QRect, QRectF, QSize, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QCursor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPolygonF,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.animations import HoverLiftFilter, NumberCounter


class GlowCard(QFrame):
    """Glassmorphism card with responsive hover lighting."""

    def __init__(self, parent: Optional[QWidget] = None, glow_color: Optional[QColor] = None):
        super().__init__(parent)
        self.setObjectName("card")
        self.hover_filter = HoverLiftFilter(
            self,
            glow_color=glow_color or QColor(124, 108, 255, 55),
            blur_radius=18,
        )


class MetricCard(QFrame):
    """Dashboard statistic card with animated numeric counter."""

    def __init__(
        self,
        title: str,
        initial_value: int = 0,
        subtitle: str = "",
        tag: str = "",
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.setObjectName("card")
        self.setCursor(Qt.PointingHandCursor)
        self.hover_filter = HoverLiftFilter(self, glow_color=QColor(124, 108, 255, 45), blur_radius=14)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(6)

        # Header row with title & optional tag
        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        self.title_lbl = QLabel(title.upper(), objectName="metricLabel")
        top_row.addWidget(self.title_lbl)
        top_row.addStretch()

        if tag:
            self.tag_lbl = QLabel(tag, objectName="pill")
            top_row.addWidget(self.tag_lbl)
        else:
            self.tag_lbl = None

        layout.addLayout(top_row)

        # Number display with animated counter
        self.number_lbl = QLabel(str(initial_value), objectName="metric")
        self.counter = NumberCounter(self.number_lbl, duration=550)
        layout.addWidget(self.number_lbl)

        # Subtitle
        self.sub_lbl = QLabel(subtitle, objectName="muted")
        self.sub_lbl.setWordWrap(True)
        layout.addWidget(self.sub_lbl)

    def set_value(self, val: int, animate: bool = True):
        if animate:
            self.counter.count_to(val)
        else:
            self.number_lbl.setText(f"{val:,}")

    def set_subtitle(self, text: str):
        self.sub_lbl.setText(text)


class BeforeAfterSliderWidget(QWidget):
    """Interactive split-view comparison widget with draggable divider handle.
    
    Allows user to slide horizontally to dynamically reveal Before vs After enhancement.
    """
    split_changed = Signal(float)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setMinimumSize(320, 240)

        self._pixmap_before: Optional[QPixmap] = None
        self._pixmap_after: Optional[QPixmap] = None
        self._split_pos: float = 0.5  # 0.0 (all after) to 1.0 (all before)
        self._is_dragging: bool = False
        self._hover_handle: bool = False

        self.label_before_text: str = "ORIGINAL"
        self.label_after_text: str = "ENHANCED"

    def set_images(self, pixmap_before: Optional[QPixmap], pixmap_after: Optional[QPixmap]):
        self._pixmap_before = pixmap_before
        self._pixmap_after = pixmap_after
        self.update()

    def set_split_ratio(self, ratio: float):
        self._split_pos = max(0.0, min(1.0, ratio))
        self.split_changed.emit(self._split_pos)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        w = self.width()
        h = self.height()

        # Fill neutral dark backdrop
        painter.fillRect(self.rect(), QColor(14, 16, 24))

        if not self._pixmap_before and not self._pixmap_after:
            # Empty placeholder state
            painter.setPen(QColor(120, 130, 150))
            font = QFont("Segoe UI", 12)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignCenter, "No photo loaded.\nChoose a photo to begin interactive comparison.")
            return

        # Determine scaled destination rectangle preserving aspect ratio
        ref_pixmap = self._pixmap_before or self._pixmap_after
        pm_w = ref_pixmap.width()
        pm_h = ref_pixmap.height()

        aspect = pm_w / max(pm_h, 1)
        widget_aspect = w / max(h, 1)

        if widget_aspect > aspect:
            target_h = h
            target_w = int(h * aspect)
            target_x = (w - target_w) // 2
            target_y = 0
        else:
            target_w = w
            target_h = int(w / aspect)
            target_x = 0
            target_y = (h - target_h) // 2

        img_rect = QRect(target_x, target_y, target_w, target_h)

        # Split x coordinate inside the image rect
        split_x = int(img_rect.left() + img_rect.width() * self._split_pos)

        # 1. Draw "Before" image on the left clipped region
        if self._pixmap_before:
            painter.save()
            clip_left = QRect(0, 0, split_x, h)
            painter.setClipRect(clip_left)
            painter.drawPixmap(img_rect, self._pixmap_before)
            painter.restore()

        # 2. Draw "After" image on the right clipped region
        if self._pixmap_after:
            painter.save()
            clip_right = QRect(split_x, 0, w - split_x, h)
            painter.setClipRect(clip_right)
            painter.drawPixmap(img_rect, self._pixmap_after)
            painter.restore()

        # 3. Draw divider line
        divider_pen = QPen(QColor(255, 255, 255, 220), 2)
        painter.setPen(divider_pen)
        painter.drawLine(split_x, img_rect.top(), split_x, img_rect.bottom())

        # 4. Draw circular handle at center of divider
        handle_y = img_rect.top() + img_rect.height() // 2
        handle_radius = 18 if self._hover_handle or self._is_dragging else 16

        # Ambient glow behind handle
        painter.setBrush(QBrush(QColor(124, 108, 255, 120)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPoint(split_x, handle_y), handle_radius + 4, handle_radius + 4)

        # Main handle circle
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(QPen(QColor(124, 108, 255), 2))
        painter.drawEllipse(QPoint(split_x, handle_y), handle_radius, handle_radius)

        # Arrows inside handle (◀ ▶)
        painter.setPen(QPen(QColor(40, 45, 60), 2))
        font = QFont("Segoe UI", 9, QFont.Bold)
        painter.setFont(font)
        painter.drawText(
            QRect(split_x - handle_radius, handle_y - handle_radius, handle_radius * 2, handle_radius * 2),
            Qt.AlignCenter,
            "◀ ▶",
        )

        # 5. Badges for "ORIGINAL" and "ENHANCED"
        badge_font = QFont("Segoe UI", 9, QFont.Bold)
        painter.setFont(badge_font)

        # Left badge (Before)
        if split_x > img_rect.left() + 90:
            b_rect = QRect(img_rect.left() + 14, img_rect.top() + 14, 86, 26)
            painter.setBrush(QBrush(QColor(15, 18, 28, 190)))
            painter.setPen(QPen(QColor(255, 255, 255, 40), 1))
            painter.drawRoundedRect(b_rect, 6, 6)
            painter.setPen(QColor(220, 225, 240))
            painter.drawText(b_rect, Qt.AlignCenter, self.label_before_text)

        # Right badge (After)
        if split_x < img_rect.right() - 90:
            a_rect = QRect(img_rect.right() - 100, img_rect.top() + 14, 86, 26)
            painter.setBrush(QBrush(QColor(124, 108, 255, 210)))
            painter.setPen(QPen(QColor(255, 255, 255, 80), 1))
            painter.drawRoundedRect(a_rect, 6, 6)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(a_rect, Qt.AlignCenter, self.label_after_text)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_dragging = True
            self._update_split_from_x(event.pos().x())

    def mouseMoveEvent(self, event):
        x = event.pos().x()
        if self._is_dragging:
            self._update_split_from_x(x)
        else:
            # Check if mouse is hovering near handle
            curr_split_x = int(self.width() * self._split_pos)
            near_handle = abs(x - curr_split_x) < 22
            if near_handle != self._hover_handle:
                self._hover_handle = near_handle
                self.setCursor(Qt.SplitHCursor if near_handle else Qt.ArrowCursor)
                self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_dragging = False
            self.setCursor(Qt.ArrowCursor)
            self.update()

    def _update_split_from_x(self, x: int):
        w = max(self.width(), 1)
        ratio = max(0.02, min(0.98, x / w))
        self.set_split_ratio(ratio)
