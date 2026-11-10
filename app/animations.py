"""Pixora animation and micro-interaction utilities for PySide6.

Includes:
- AnimatedStackedWidget: Cross-fade page transition router.
- NumberCounter: Smooth counting animation for numerical stats.
- HoverLiftFilter: Interactive card lift, pointer cursor, and dynamic glow highlight.
- FadeHelper: Smooth opacity animations for dialogs and panels.
"""
from __future__ import annotations

from typing import Callable, Optional
from PySide6.QtCore import (
    QEasingCurve,
    QObject,
    QPropertyAnimation,
    Qt,
    QVariantAnimation,
    Signal,
)
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QLabel,
    QStackedWidget,
    QWidget,
)


class AnimatedStackedWidget(QStackedWidget):
    """QStackedWidget that transitions between pages with a smooth cross-fade animation."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.fade_duration = 180  # ms
        self._is_animating = False

    def slide_to_index(self, target_index: int):
        if target_index == self.currentIndex() or self._is_animating:
            self.setCurrentIndex(target_index)
            return

        current_widget = self.currentWidget()
        target_widget = self.widget(target_index)

        if not current_widget or not target_widget:
            self.setCurrentIndex(target_index)
            return

        self._is_animating = True

        # Setup opacity effect for incoming widget
        target_opacity = QGraphicsOpacityEffect(target_widget)
        target_widget.setGraphicsEffect(target_opacity)
        target_opacity.setOpacity(0.0)

        # Bring target widget to view
        self.setCurrentIndex(target_index)

        # Fade in incoming widget
        anim = QPropertyAnimation(target_opacity, b"opacity")
        anim.setDuration(self.fade_duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)

        def _cleanup():
            target_widget.setGraphicsEffect(None)
            self._is_animating = False

        anim.finished.connect(_cleanup)
        self._current_anim = anim
        anim.start()


class NumberCounter(QObject):
    """Smoothly counts a numeric value from start to target on a QLabel."""
    number_updated = Signal(int)

    def __init__(self, label: QLabel, duration: int = 500, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.label = label
        self.duration = duration
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(duration)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.valueChanged.connect(self._on_value_changed)

    def count_to(self, target_value: int, start_value: Optional[int] = None):
        if start_value is None:
            try:
                curr_text = self.label.text().strip().replace(",", "")
                start_value = int(curr_text) if curr_text.isdigit() else 0
            except Exception:
                start_value = 0

        if start_value == target_value:
            self.label.setText(f"{target_value:,}")
            return

        self.anim.stop()
        self.anim.setStartValue(start_value)
        self.anim.setEndValue(target_value)
        self.anim.start()

    def _on_value_changed(self, val):
        num = int(val)
        self.label.setText(f"{num:,}")
        self.number_updated.emit(num)


class HoverLiftFilter(QObject):
    """Event filter that sets hand pointer cursor and triggers interactive hover glow feedback."""

    def __init__(
        self,
        target_widget: QWidget,
        glow_color: Optional[QColor] = None,
        blur_radius: int = 14,
        glow_name: str = "violet",
    ):
        super().__init__(target_widget)
        self.widget = target_widget
        self.widget.setCursor(Qt.PointingHandCursor)
        self.widget.setAttribute(Qt.WA_Hover, True)
        self.widget.setProperty("glow", glow_name)

        # Soft drop shadow without harsh dark offsets
        self.shadow = QGraphicsDropShadowEffect(self.widget)
        self.shadow.setColor(QColor(0, 0, 0, 0))  # Initially transparent to prevent gray banding boxes
        self.shadow.setBlurRadius(0)
        self.shadow.setOffset(0, 0)
        self.widget.setGraphicsEffect(self.shadow)

        self.glow_color = glow_color or QColor(124, 108, 255, 65)
        self.blur_radius = blur_radius

        self.widget.installEventFilter(self)

    def eventFilter(self, watched: QObject, event) -> bool:
        if watched == self.widget:
            if event.type() == event.Type.Enter:
                self.shadow.setColor(self.glow_color)
                self.shadow.setBlurRadius(self.blur_radius)
                self.shadow.setOffset(0, 2)
            elif event.type() == event.Type.Leave:
                self.shadow.setColor(QColor(0, 0, 0, 0))
                self.shadow.setBlurRadius(0)
                self.shadow.setOffset(0, 0)
        return super().eventFilter(watched, event)


def fade_in_widget(widget: QWidget, duration: int = 180, callback: Optional[Callable[[], None]] = None):
    """Applies a smooth fade-in opacity transition to any widget."""
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    effect.setOpacity(0.0)

    anim = QPropertyAnimation(effect, b"opacity")
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.OutCubic)

    def _done():
        widget.setGraphicsEffect(None)
        if callback:
            callback()

    anim.finished.connect(_done)
    widget._fade_anim = anim
    anim.start()
