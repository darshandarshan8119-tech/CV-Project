"""Unit tests for Pixora's modern UI widgets, animations, and theme system."""
from __future__ import annotations

import sys
from pathlib import Path
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QWidget

from app.animations import AnimatedStackedWidget, HoverLiftFilter, NumberCounter
from app.theme import DARK, LIGHT, stylesheet
from app.widgets import BeforeAfterSliderWidget, GlowCard, MetricCard

# Ensure QApplication exists for widget testing
_app = QApplication.instance() or QApplication(sys.argv)


class TestUIThemeAndWidgets(unittest.TestCase):
    def test_theme_tokens_and_stylesheet(self):
        """Theme stylesheet must produce valid CSS with Obsidian tokens."""
        dark_qss = stylesheet(DARK)
        self.assertIn("#090A0F", dark_qss)
        self.assertIn("#7C6CFF", dark_qss)
        self.assertIn("QFrame#card", dark_qss)

        light_qss = stylesheet(LIGHT)
        self.assertIn("#F5F7FB", light_qss)
        self.assertIn("#6355FF", light_qss)

    def test_animated_stacked_widget(self):
        """AnimatedStackedWidget should support adding pages and slide transitions."""
        stack = AnimatedStackedWidget()
        w1 = QLabel("Page 1")
        w2 = QLabel("Page 2")
        stack.addWidget(w1)
        stack.addWidget(w2)

        self.assertEqual(stack.currentIndex(), 0)
        stack.slide_to_index(1)
        self.assertEqual(stack.currentIndex(), 1)

    def test_metric_card_and_counter(self):
        """MetricCard should display titles, initial values, and update numbers."""
        card = MetricCard("Total Photos", initial_value=12, subtitle="Test Subtitle", tag="LIVE")
        self.assertEqual(card.title_lbl.text(), "TOTAL PHOTOS")
        self.assertEqual(card.number_lbl.text(), "12")

        card.set_value(45, animate=False)
        self.assertEqual(card.number_lbl.text(), "45")

    def test_hover_lift_filter(self):
        """HoverLiftFilter should attach a QGraphicsDropShadowEffect."""
        widget = QWidget()
        filter_obj = HoverLiftFilter(widget, glow_color=QColor(124, 108, 255, 50))
        self.assertIsNotNone(widget.graphicsEffect())

    def test_before_after_slider_widget(self):
        """BeforeAfterSliderWidget should correctly compute split coordinates and update."""
        slider = BeforeAfterSliderWidget()
        slider.resize(800, 600)

        # Create two sample pixmaps
        pm1 = QPixmap(100, 100)
        pm1.fill(Qt.red)
        pm2 = QPixmap(100, 100)
        pm2.fill(Qt.blue)

        slider.set_images(pm1, pm2)
        slider.set_split_ratio(0.4)
        self.assertAlmostEqual(slider._split_pos, 0.4, places=2)

        # Bounds clamping
        slider.set_split_ratio(1.5)
        self.assertEqual(slider._split_pos, 1.0)
        slider.set_split_ratio(-0.5)
        self.assertEqual(slider._split_pos, 0.0)


if __name__ == "__main__":
    unittest.main()
