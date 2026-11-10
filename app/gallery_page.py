"""Polished, responsive My Gallery workspace for Pixora."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.animations import HoverLiftFilter
from app.preview_dialog import PreviewDialog, format_size
from core.thumbnails import get_cached_thumbnail_path
from database.db_manager import DatabaseManager
from workers.thumbnail_worker import ThumbnailWorker


class ImageCard(QFrame):
    clicked = Signal(dict)

    def __init__(self, data: Dict[str, Any], is_grid: bool = True, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.data = data
        self.is_grid = is_grid
        self.setObjectName("card")
        self.setCursor(Qt.PointingHandCursor)

        # Micro-interaction hover lift
        self.hover_filter = HoverLiftFilter(self, glow_color=QColor(124, 108, 255, 45), blur_radius=14)

        if is_grid:
            self.setFixedSize(195, 245)
            layout = QVBoxLayout(self)
            layout.setContentsMargins(8, 8, 8, 8)
            layout.setSpacing(6)

            # Thumbnail container
            self.thumb_label = QLabel()
            self.thumb_label.setAlignment(Qt.AlignCenter)
            self.thumb_label.setFixedSize(179, 150)
            self.thumb_label.setStyleSheet("background: rgba(0,0,0,0.35); border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);")
            layout.addWidget(self.thumb_label)

            # Filename
            self.name_label = QLabel(data.get("filename", "Photo"))
            self.name_label.setStyleSheet("font-weight: 700; font-size: 13px; color: #FFFFFF;")
            self.name_label.setWordWrap(False)
            layout.addWidget(self.name_label)

            # Subtitle (Dimensions & Size)
            w = data.get("width", 0)
            h = data.get("height", 0)
            dim = f"{w}×{h}" if w and h else "—"
            size = format_size(data.get("size_bytes", 0))
            self.meta_label = QLabel(f"{dim} • {size}", objectName="muted")
            self.meta_label.setStyleSheet("font-size: 11px;")
            layout.addWidget(self.meta_label)
        else:
            self.setFixedHeight(68)
            layout = QHBoxLayout(self)
            layout.setContentsMargins(14, 8, 18, 8)
            layout.setSpacing(16)

            self.thumb_label = QLabel()
            self.thumb_label.setAlignment(Qt.AlignCenter)
            self.thumb_label.setFixedSize(52, 52)
            self.thumb_label.setStyleSheet("background: rgba(0,0,0,0.35); border-radius: 6px; border: 1px solid rgba(255,255,255,0.05);")
            layout.addWidget(self.thumb_label)

            info_layout = QVBoxLayout()
            info_layout.setSpacing(2)
            self.name_label = QLabel(data.get("filename", "Photo"))
            self.name_label.setStyleSheet("font-weight: 700; font-size: 14px; color: #FFFFFF;")
            info_layout.addWidget(self.name_label)

            path_lbl = QLabel(data.get("path", ""), objectName="muted")
            path_lbl.setStyleSheet("font-size: 11px;")
            info_layout.addWidget(path_lbl)
            layout.addLayout(info_layout, stretch=1)

            # Category pill
            cat = data.get("category", "Other")
            cat_pill = QLabel(cat, objectName="pill")
            layout.addWidget(cat_pill)

            w = data.get("width", 0)
            h = data.get("height", 0)
            dim = f"{w}×{h} px" if w and h else "—"
            dim_lbl = QLabel(dim, objectName="muted")
            layout.addWidget(dim_lbl)

            size = format_size(data.get("size_bytes", 0))
            size_lbl = QLabel(size, objectName="muted")
            size_lbl.setFixedWidth(75)
            size_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            layout.addWidget(size_lbl)

        # Set cached thumbnail if already present
        self.update_thumbnail()

    def update_thumbnail(self, path: Optional[str] = None):
        if path and Path(path).is_file():
            pm = QPixmap(path)
            target_size = self.thumb_label.size()
            scaled = pm.scaled(target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.thumb_label.setPixmap(scaled)
            return

        # Check disk cache
        img_path = self.data.get("path", "")
        cached = get_cached_thumbnail_path(img_path)
        if cached:
            pm = QPixmap(str(cached))
            scaled = pm.scaled(self.thumb_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.thumb_label.setPixmap(scaled)
        else:
            self.thumb_label.setText("Loading…")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.data)
        super().mousePressEvent(event)


class GalleryPage(QWidget):
    def __init__(
        self,
        database: DatabaseManager,
        import_callback: Optional[Callable[[], None]] = None,
        on_enhance_callback: Optional[Callable[[str], None]] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.database = database
        self.import_callback = import_callback
        self.on_enhance_callback = on_enhance_callback
        self.is_grid_view = True
        self.cards: List[ImageCard] = []
        self.thumb_worker: Optional[ThumbnailWorker] = None

        root = QVBoxLayout(self)
        root.setContentsMargins(36, 28, 36, 24)
        root.setSpacing(18)

        # Top Header Bar
        header = QHBoxLayout()
        words = QVBoxLayout()
        words.setSpacing(4)
        title = QLabel("My Gallery", objectName="pageTitle")
        self.subtitle = QLabel("Browse, search and inspect your indexed photo collection.", objectName="pageSub")
        words.addWidget(title)
        words.addWidget(self.subtitle)
        header.addLayout(words)
        header.addStretch()

        # Search Bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Search by filename…")
        self.search_input.setFixedWidth(250)
        self.search_input.textChanged.connect(self.reload_gallery)
        header.addWidget(self.search_input)

        # Sort Dropdown
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "Newest First",
            "Oldest First",
            "Name (A–Z)",
            "Name (Z–A)",
            "Size (Largest)",
            "Size (Smallest)",
        ])
        self.sort_combo.currentIndexChanged.connect(self.reload_gallery)
        header.addWidget(self.sort_combo)

        # View Toggle Buttons
        self.btn_grid = QPushButton("Grid", objectName="primary")
        self.btn_grid.setCursor(Qt.PointingHandCursor)
        self.btn_grid.setFixedWidth(68)
        self.btn_grid.clicked.connect(lambda: self.set_view_mode(True))

        self.btn_list = QPushButton("List", objectName="secondary")
        self.btn_list.setCursor(Qt.PointingHandCursor)
        self.btn_list.setFixedWidth(68)
        self.btn_list.clicked.connect(lambda: self.set_view_mode(False))

        header.addWidget(self.btn_grid)
        header.addWidget(self.btn_list)

        root.addLayout(header)

        # Content Area: Stacked Widget (Empty State vs. Scroll View)
        self.stack = QStackedWidget()

        # Page 0: Gallery Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_content = QWidget()
        self.grid_layout = QGridLayout(self.scroll_content)
        self.grid_layout.setContentsMargins(4, 8, 4, 16)
        self.grid_layout.setSpacing(14)
        self.scroll_area.setWidget(self.scroll_content)
        self.stack.addWidget(self.scroll_area)

        # Page 1: Empty State
        empty_widget = QWidget()
        empty_layout = QVBoxLayout(empty_widget)
        empty_layout.setAlignment(Qt.AlignCenter)
        empty_layout.setSpacing(14)

        icon_lbl = QLabel("📷")
        icon_lbl.setStyleSheet("font-size: 52px; margin-bottom: 8px;")
        icon_lbl.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(icon_lbl)

        empty_title = QLabel("Your Gallery is Empty", objectName="pageTitle")
        empty_title.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(empty_title)

        empty_desc = QLabel(
            "Import a folder to begin exploring your photos with local privacy and zero original modifications.",
            objectName="muted",
        )
        empty_desc.setAlignment(Qt.AlignCenter)
        empty_desc.setWordWrap(True)
        empty_desc.setStyleSheet("max-width: 480px; line-height: 1.4;")
        empty_layout.addWidget(empty_desc)

        empty_layout.addSpacing(12)
        btn_import = QPushButton("Import Photo Folder", objectName="primary")
        btn_import.setCursor(Qt.PointingHandCursor)
        btn_import.setFixedWidth(210)
        btn_import.setStyleSheet("padding: 10px 20px; font-size: 13px;")
        if self.import_callback:
            btn_import.clicked.connect(self.import_callback)
        empty_layout.addWidget(btn_import, alignment=Qt.AlignCenter)

        self.stack.addWidget(empty_widget)
        root.addWidget(self.stack, stretch=1)

        # Initial load
        self.reload_gallery()

    def set_view_mode(self, is_grid: bool):
        if self.is_grid_view == is_grid:
            return
        self.is_grid_view = is_grid
        self.btn_grid.setObjectName("primary" if is_grid else "secondary")
        self.btn_list.setObjectName("secondary" if is_grid else "primary")
        self.btn_grid.style().unpolish(self.btn_grid)
        self.btn_grid.style().polish(self.btn_grid)
        self.btn_list.style().unpolish(self.btn_list)
        self.btn_list.style().polish(self.btn_list)
        self.reload_gallery()

    def _get_sort_key(self) -> str:
        idx = self.sort_combo.currentIndex()
        mapping = {
            0: "date_desc",
            1: "date_asc",
            2: "name_asc",
            3: "name_desc",
            4: "size_desc",
            5: "size_asc",
        }
        return mapping.get(idx, "date_desc")

    def reload_gallery(self):
        # Cancel any active thumbnail worker
        if self.thumb_worker and self.thumb_worker.isRunning():
            self.thumb_worker.cancel()
            self.thumb_worker.wait(500)

        # Clear layout
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.cards.clear()

        # Query images from db
        search = self.search_input.text().strip()
        sort_by = self._get_sort_key()
        images = self.database.get_images(search=search if search else None, sort_by=sort_by)

        if not images:
            self.stack.setCurrentIndex(1)
            self.subtitle.setText("No photos match your query." if search else "No photos imported yet.")
            return

        self.stack.setCurrentIndex(0)
        self.subtitle.setText(f"Showing {len(images)} photo{'s' if len(images) != 1 else ''} in your library.")

        # Populate cards
        paths_needing_thumbs = []
        if self.is_grid_view:
            cols = 4  # Responsive 4-column layout
            for index, img_data in enumerate(images):
                row = index // cols
                col = index % cols
                card = ImageCard(img_data, is_grid=True)
                card.clicked.connect(self.open_preview)
                self.grid_layout.addWidget(card, row, col)
                self.cards.append(card)

                if not get_cached_thumbnail_path(img_data["path"]):
                    paths_needing_thumbs.append(img_data["path"])
        else:
            for index, img_data in enumerate(images):
                card = ImageCard(img_data, is_grid=False)
                card.clicked.connect(self.open_preview)
                self.grid_layout.addWidget(card, index, 0)
                self.cards.append(card)

                if not get_cached_thumbnail_path(img_data["path"]):
                    paths_needing_thumbs.append(img_data["path"])

        self.grid_layout.setRowStretch(len(images) + 1, 1)

        # Spawn background thumbnail generator for un-cached images
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
