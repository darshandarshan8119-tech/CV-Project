"""Modern interactive dashboard workspace with animated stats and motion polish."""
from __future__ import annotations

from typing import Callable, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.animations import HoverLiftFilter
from app.widgets import GlowCard, MetricCard


class Dashboard(QWidget):
    def __init__(self, import_action: Callable[[], None], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.import_action = import_action

        root = QVBoxLayout(self)
        root.setContentsMargins(36, 28, 36, 30)
        root.setSpacing(22)

        # Header hero section
        header = QHBoxLayout()
        words = QVBoxLayout()
        words.setSpacing(6)

        title = QLabel("Library Overview", objectName="pageTitle")
        title.setStyleSheet("font-size: 26px; font-weight: 800; letter-spacing: -0.5px;")
        words.addWidget(title)

        sub = QLabel(
            "Private, on-device photo intelligence — organizing, rating, and enhancing memories with zero cloud transfers.",
            objectName="pageSub",
        )
        words.addWidget(sub)
        header.addLayout(words)
        header.addStretch()

        self.import_button = QPushButton("✦  Import Photo Folder", objectName="primary")
        self.import_button.setCursor(Qt.PointingHandCursor)
        self.import_button.clicked.connect(self.import_action)
        self.import_button.setStyleSheet("font-size: 13px; padding: 11px 22px;")
        header.addWidget(self.import_button)
        root.addLayout(header)

        # Animated Stat Metric Cards Grid
        self.metric_cards = {}
        grid = QGridLayout()
        grid.setSpacing(14)

        metrics_config = [
            ("photos", "Total Indexed Photos", 0, "No images imported yet", "LIVE", "violet"),
            ("last", "Last Imported Batch", 0, "Choose a folder to start", "FOLDER", "cyan"),
            ("duplicates", "Duplicate Groups", 0, "Run Duplicate Finder to detect", "SHA-256", "coral"),
            ("review", "Needs Review (Blurry)", 0, "Evaluate sharpness in Best Shots", "CV SCORED", "emerald"),
        ]

        for col, (key, label, val, sub_text, tag, glow_color) in enumerate(metrics_config):
            card = MetricCard(label, initial_value=val, subtitle=sub_text, tag=tag, glow_name=glow_color)
            grid.addWidget(card, 0, col)
            self.metric_cards[key] = card

        root.addLayout(grid)

        # Import & Scanning Status Feature Card
        self.status_panel = QFrame(objectName="featureCard")
        self.status_panel.setCursor(Qt.PointingHandCursor)
        HoverLiftFilter(self.status_panel, blur_radius=14, glow_name="violet")
        pl = QVBoxLayout(self.status_panel)
        pl.setContentsMargins(24, 20, 24, 20)
        pl.setSpacing(12)

        top_status = QHBoxLayout()
        st_title = QLabel("Engine Activity Status", objectName="cardTitle")
        top_status.addWidget(st_title)
        top_status.addStretch()

        self.status_pill = QLabel("IDLE / READY", objectName="pillSuccess")
        top_status.addWidget(self.status_pill)
        pl.addLayout(top_status)

        self.status_detail = QLabel(
            "Select any local folder. Pixora will index supported images asynchronously while your UI remains fluid.",
            objectName="pageSub",
        )
        self.status_detail.setWordWrap(True)
        pl.addWidget(self.status_detail)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6)
        pl.addWidget(self.progress)

        root.addWidget(self.status_panel)

        # Informational feature cards row
        lower = QHBoxLayout()
        lower.setSpacing(14)

        info_items = [
            (
                "Deterministic Computer Vision",
                "Heuristic classification, Laplacian blur variance, and perceptual hashing run locally via OpenCV and Pillow. No telemetry, no cloud costs.",
                "🔒 PRIVATE",
                "emerald",
            ),
            (
                "Non-Destructive Guarantee",
                "Your original photos are strictly read-only. Enhanced and scaled versions are saved to your chosen output folder with zero risk to originals.",
                "🛡️ PROTECTED",
                "cyan",
            ),
        ]

        for title_text, desc_text, badge_text, glow_name in info_items:
            card = GlowCard(glow_name=glow_name)
            card.setCursor(Qt.PointingHandCursor)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(22, 20, 22, 20)
            cl.setSpacing(8)

            c_top = QHBoxLayout()
            lbl_title = QLabel(title_text, objectName="cardTitle")
            c_top.addWidget(lbl_title)
            c_top.addStretch()

            b_lbl = QLabel(badge_text, objectName="pill")
            c_top.addWidget(b_lbl)
            cl.addLayout(c_top)

            lbl_desc = QLabel(desc_text, objectName="pageSub")
            lbl_desc.setWordWrap(True)
            lbl_desc.setStyleSheet("line-height: 1.4;")
            cl.addWidget(lbl_desc)
            cl.addStretch()
            lower.addWidget(card)

        root.addLayout(lower)
        root.addStretch()

    def begin_scan(self, total: int):
        self.import_button.setEnabled(False)
        self.status_pill.setText("SCANNING")
        self.status_pill.setObjectName("pillActive")
        self.status_pill.style().unpolish(self.status_pill)
        self.status_pill.style().polish(self.status_pill)

        self.status_detail.setText(f"Found {total} supported file{'s' if total != 1 else ''}. Reading image metadata locally…")
        self.progress.setRange(0, max(total, 1))
        self.progress.setValue(0)

    def set_scan_progress(self, current: int, total: int):
        self.progress.setMaximum(max(total, 1))
        self.progress.setValue(current)
        self.status_detail.setText(f"Reading image {current} of {total}…")

    def set_import_summary(self, library_count: int, result: dict, folder: str):
        self.import_button.setEnabled(True)
        self.progress.setValue(self.progress.maximum())
        self.status_pill.setText("COMPLETE")
        self.status_pill.setObjectName("pillSuccess")
        self.status_pill.style().unpolish(self.status_pill)
        self.status_pill.style().polish(self.status_pill)

        imported = result["imported"]
        discovered = result["discovered"]
        skipped = result["skipped"]

        self.status_detail.setText(
            f"Imported {imported} readable image{'s' if imported != 1 else ''} from {discovered} supported file{'s' if discovered != 1 else ''}. {skipped} skipped."
        )

        self.metric_cards["photos"].set_value(library_count)
        self.metric_cards["photos"].set_subtitle("Indexed locally — originals untouched")

        self.metric_cards["last"].set_value(imported)
        self.metric_cards["last"].set_subtitle(f"Imported from {folder}")

    def set_existing_count(self, count: int):
        self.metric_cards["photos"].set_value(count, animate=False)
        self.metric_cards["photos"].set_subtitle("Indexed locally — originals untouched")
