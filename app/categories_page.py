"""Smart Categories page powered by local heuristic image analysis."""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.animations import HoverLiftFilter
from app.gallery_page import ImageCard
from app.preview_dialog import PreviewDialog
from core.categorizer import CATEGORIES
from core.thumbnails import get_cached_thumbnail_path
from database.db_manager import DatabaseManager
from workers.categorization_worker import CategorizationWorker
from workers.thumbnail_worker import ThumbnailWorker

CATEGORY_ICONS = {
    "All": "🗂️",
    "Selfies": "🤳",
    "Nature": "🌿",
    "Food": "🍳",
    "Animals": "🐾",
    "Documents": "📄",
    "Screenshots": "🖥️",
    "Travel": "✈️",
    "Objects": "📦",
    "Other": "📁",
}


class CategoryBadge(QFrame):
    clicked = Signal(str)

    def __init__(self, category_name: str, count: int, is_active: bool = False, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.category_name = category_name
        self.setObjectName("featureCard" if is_active else "card")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(86)

        # Micro-interaction hover lift
        self.hover_filter = HoverLiftFilter(
            self,
            glow_color=QColor(124, 108, 255, 60 if is_active else 35),
            blur_radius=16,
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        top_row = QHBoxLayout()
        icon = CATEGORY_ICONS.get(category_name, "📁")
        icon_lbl = QLabel(f"{icon}  {category_name}", objectName="cardTitle")
        if is_active:
            icon_lbl.setStyleSheet("color: #7C6CFF;")
        top_row.addWidget(icon_lbl)
        top_row.addStretch()

        self.count_lbl = QLabel(str(count), objectName="pillActive" if is_active else "pill")
        top_row.addWidget(self.count_lbl)
        layout.addLayout(top_row)

        desc_lbl = QLabel("Local heuristic match", objectName="muted")
        desc_lbl.setStyleSheet("font-size: 11px;")
        layout.addWidget(desc_lbl)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.category_name)
        super().mousePressEvent(event)


class CategoriesPage(QWidget):
    def __init__(
        self,
        database: DatabaseManager,
        on_enhance_callback: Optional[Callable[[str], None]] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.database = database
        self.on_enhance_callback = on_enhance_callback
        self.selected_category = "All"
        self.worker: Optional[CategorizationWorker] = None
        self.thumb_worker: Optional[ThumbnailWorker] = None
        self.cards: List[ImageCard] = []
        self.badge_widgets: Dict[str, CategoryBadge] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(36, 28, 36, 24)
        root.setSpacing(18)

        # Header
        header = QHBoxLayout()
        words = QVBoxLayout()
        words.setSpacing(4)
        title = QLabel("Smart Categories", objectName="pageTitle")
        subtitle = QLabel(
            "Local heuristic organization — analyzed completely on your device with no cloud uploads or model downloads.",
            objectName="pageSub",
        )
        words.addWidget(title)
        words.addWidget(subtitle)
        header.addLayout(words)
        header.addStretch()

        self.btn_run = QPushButton("✦  Run Categorization", objectName="primary")
        self.btn_run.setCursor(Qt.PointingHandCursor)
        self.btn_run.clicked.connect(self.start_categorization)
        header.addWidget(self.btn_run)

        root.addLayout(header)

        # Progress Panel
        self.progress_panel = QFrame(objectName="card")
        self.progress_panel.setVisible(False)
        p_layout = QVBoxLayout(self.progress_panel)
        p_layout.setContentsMargins(18, 14, 18, 14)
        p_layout.setSpacing(10)

        p_top = QHBoxLayout()
        self.progress_status = QLabel("Analyzing image contents with local heuristics…", objectName="cardTitle")
        self.progress_status.setStyleSheet("font-weight: 600; font-size: 13px;")
        p_top.addWidget(self.progress_status)
        p_top.addStretch()

        self.btn_cancel = QPushButton("Cancel", objectName="secondary")
        self.btn_cancel.setFixedWidth(75)
        self.btn_cancel.clicked.connect(self.cancel_categorization)
        p_top.addWidget(self.btn_cancel)
        p_layout.addLayout(p_top)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        p_layout.addWidget(self.progress_bar)

        root.addWidget(self.progress_panel)

        # Category Badges Grid
        self.badges_layout = QGridLayout()
        self.badges_layout.setSpacing(12)
        root.addLayout(self.badges_layout)

        # Filter Subheader
        self.filter_header = QLabel("Showing All Photos", objectName="pageTitle")
        self.filter_header.setStyleSheet("font-size: 16px; margin-top: 6px;")
        root.addWidget(self.filter_header)

        # Filtered Photo Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_content = QWidget()
        self.grid_layout = QGridLayout(self.scroll_content)
        self.grid_layout.setContentsMargins(4, 4, 4, 16)
        self.grid_layout.setSpacing(14)
        self.scroll_area.setWidget(self.scroll_content)
        root.addWidget(self.scroll_area, stretch=1)

        # Render Badges & Photos
        self.refresh_badges()
        self.render_filtered_photos()

    def refresh_badges(self):
        # Clear existing badges
        while self.badges_layout.count():
            item = self.badges_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.badge_widgets.clear()

        counts = self.database.get_category_counts()
        total_photos = self.database.count_images()

        all_cats = ["All"] + CATEGORIES
        cols = 5
        for idx, cat in enumerate(all_cats):
            c_val = total_photos if cat == "All" else counts.get(cat, 0)
            badge = CategoryBadge(cat, c_val, is_active=(cat == self.selected_category))
            badge.clicked.connect(self.select_category)
            row = idx // cols
            col = idx % cols
            self.badges_layout.addWidget(badge, row, col)
            self.badge_widgets[cat] = badge

    def select_category(self, cat_name: str):
        self.selected_category = cat_name
        self.filter_header.setText(f"Showing {cat_name} Photos")
        self.refresh_badges()
        self.render_filtered_photos()

    def render_filtered_photos(self):
        # Cancel any active thumbnail worker
        if self.thumb_worker and self.thumb_worker.isRunning():
            self.thumb_worker.cancel()
            self.thumb_worker.wait(500)

        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.cards.clear()

        images = self.database.get_images(category=self.selected_category)
        if not images:
            empty_lbl = QLabel(f"No photos classified as '{self.selected_category}' yet.\nClick 'Run Categorization' above to analyze your library.")
            empty_lbl.setAlignment(Qt.AlignCenter)
            empty_lbl.setStyleSheet("color: #7C8497; font-size: 14px; margin: 40px;")
            self.grid_layout.addWidget(empty_lbl, 0, 0)
            return

        cols = 4
        paths_needing_thumbs = []
        for index, img in enumerate(images):
            card = ImageCard(img, is_grid=True)
            card.clicked.connect(self.open_preview)
            row = index // cols
            col = index % cols
            self.grid_layout.addWidget(card, row, col)
            self.cards.append(card)

            if not get_cached_thumbnail_path(img["path"]):
                paths_needing_thumbs.append(img["path"])

        self.grid_layout.setRowStretch(len(images) + 1, 1)

        if paths_needing_thumbs:
            self.thumb_worker = ThumbnailWorker(paths_needing_thumbs)
            self.thumb_worker.thumbnail_ready.connect(self._on_thumbnail_ready)
            self.thumb_worker.start()

    def _on_thumbnail_ready(self, img_path: str, thumb_path: str):
        for card in self.cards:
            if card.data.get("path") == img_path:
                card.update_thumbnail(thumb_path)
                break

    def open_preview(self, img_data: Dict[str, Any]):
        dialog = PreviewDialog(img_data, on_enhance_callback=self.on_enhance_callback, parent=self)
        dialog.exec()

    def start_categorization(self):
        if self.worker and self.worker.isRunning():
            return

        self.btn_run.setEnabled(False)
        self.progress_panel.setVisible(True)
        self.progress_bar.setValue(0)

        self.worker = CategorizationWorker(force_all=True, database=self.database)
        self.worker.started_categorization.connect(lambda total: self.progress_bar.setMaximum(max(total, 1)))
        self.worker.progress.connect(self._on_progress)
        self.worker.completed.connect(self._on_completed)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def cancel_categorization(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.progress_status.setText("Cancelling categorization…")

    def _on_progress(self, current: int, total: int, fname: str):
        self.progress_bar.setValue(current)
        self.progress_status.setText(f"Categorizing image {current} of {total}: {fname}…")

    def _on_completed(self, result: dict):
        self.btn_run.setEnabled(True)
        self.progress_panel.setVisible(False)
        self.refresh_badges()
        self.render_filtered_photos()

    def _on_failed(self, error: str):
        self.btn_run.setEnabled(True)
        self.progress_status.setText(f"Categorization error: {error}")
