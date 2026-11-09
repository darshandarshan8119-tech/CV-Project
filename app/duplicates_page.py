"""Duplicate Finder and Similar Photos pages powered by SHA-256 and perceptual hashing."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.preview_dialog import PreviewDialog, format_size, reveal_in_explorer
from core.duplicates import hamming_distance
from core.thumbnails import generate_thumbnail, get_cached_thumbnail_path
from database.db_manager import DatabaseManager
from workers.duplicate_worker import DuplicateWorker


class DuplicateItemRow(QFrame):
    clicked = Signal(dict)

    def __init__(self, data: Dict[str, Any], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.data = data
        self.setObjectName("card")
        self.setCursor(Qt.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(14)

        # Thumbnail
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(60, 60)
        self.thumb_label.setAlignment(Qt.AlignCenter)
        self.thumb_label.setStyleSheet("background: rgba(0,0,0,0.25); border-radius: 6px;")
        layout.addWidget(self.thumb_label)

        # Metadata
        info_col = QVBoxLayout()
        info_col.setSpacing(3)
        name_lbl = QLabel(data.get("filename", "Photo"))
        name_lbl.setStyleSheet("font-weight: 700; font-size: 14px;")
        info_col.addWidget(name_lbl)

        path_lbl = QLabel(data.get("path", ""), objectName="muted")
        path_lbl.setStyleSheet("font-size: 11px;")
        info_col.addWidget(path_lbl)
        layout.addLayout(info_col, stretch=1)

        # Dimensions & Size
        w = data.get("width", 0)
        h = data.get("height", 0)
        dim_lbl = QLabel(f"{w}×{h} px" if w and h else "—", objectName="muted")
        layout.addWidget(dim_lbl)

        size_lbl = QLabel(format_size(data.get("size_bytes", 0)), objectName="muted")
        size_lbl.setFixedWidth(75)
        size_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(size_lbl)

        # Actions
        btn_reveal = QPushButton("Reveal", objectName="secondary")
        btn_reveal.setCursor(Qt.PointingHandCursor)
        btn_reveal.clicked.connect(lambda: reveal_in_explorer(data.get("path", "")))
        layout.addWidget(btn_reveal)

        # Safe disabled delete action
        btn_del = QPushButton("Delete", objectName="secondary")
        btn_del.setEnabled(False)
        btn_del.setToolTip("Deletion is disabled: Pixora preserves all original files in read-only mode.")
        btn_del.setStyleSheet("opacity: 0.5;")
        layout.addWidget(btn_del)

        self.load_thumbnail()

    def load_thumbnail(self):
        img_path = self.data.get("path", "")
        cached = get_cached_thumbnail_path(img_path)
        if not cached:
            cached = generate_thumbnail(img_path)

        if cached and Path(cached).is_file():
            pm = QPixmap(str(cached))
            scaled = pm.scaled(self.thumb_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.thumb_label.setPixmap(scaled)
        else:
            self.thumb_label.setText("No Preview")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.data)
        super().mousePressEvent(event)


class DuplicateGroupCard(QFrame):
    image_clicked = Signal(dict)

    def __init__(
        self,
        group_id: str,
        images: List[Dict[str, Any]],
        is_exact: bool = True,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.setObjectName("featureCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        # Group header
        top = QHBoxLayout()
        if is_exact:
            title = QLabel(f"Exact Duplicate Group — {len(images)} copies")
            title.setStyleSheet("font-weight: 700; font-size: 15px;")
            top.addWidget(title)
            top.addStretch()
            badge = QLabel("100% BYTE-FOR-BYTE (SHA-256)", objectName="pill")
            badge.setStyleSheet("color: #E27D60; font-weight: 700; font-size: 11px;")
            top.addWidget(badge)
        else:
            title = QLabel(f"Visually Similar Group — {len(images)} photos")
            title.setStyleSheet("font-weight: 700; font-size: 15px;")
            top.addWidget(title)
            top.addStretch()

            # Calculate similarity % between first two
            sim_pct = 90
            if len(images) >= 2 and images[0].get("phash") and images[1].get("phash"):
                dist = hamming_distance(images[0]["phash"], images[1]["phash"])
                sim_pct = max(50, int((1.0 - dist / 64.0) * 100))

            badge = QLabel(f"~{sim_pct}% VISUAL SIMILARITY (PERCEPTUAL HASH)", objectName="pill")
            badge.setStyleSheet("color: #7C6CFF; font-weight: 700; font-size: 11px;")
            top.addWidget(badge)

        layout.addLayout(top)

        # Items
        for img in images:
            row = DuplicateItemRow(img)
            row.clicked.connect(self.image_clicked.emit)
            layout.addWidget(row)


class DuplicatesPage(QWidget):
    def __init__(
        self,
        database: DatabaseManager,
        mode: str = "exact",  # "exact" or "similar"
        on_enhance_callback: Optional[Callable[[str], None]] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.database = database
        self.mode = mode
        self.on_enhance_callback = on_enhance_callback
        self.worker: Optional[DuplicateWorker] = None

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 26, 32, 24)
        root.setSpacing(16)

        # Header
        header = QHBoxLayout()
        words = QVBoxLayout()
        words.setSpacing(4)

        if self.mode == "exact":
            title_text = "Duplicate Finder"
            desc_text = "Detect exact byte-for-byte duplicate photos using cryptographic SHA-256 hashes."
            btn_text = "Scan for Duplicates"
        else:
            title_text = "Similar Photos"
            desc_text = "Detect visually similar, burst, or edited photos using perceptual hashing (pHash)."
            btn_text = "Scan Similar Photos"

        words.addWidget(QLabel(title_text, objectName="pageTitle"))
        words.addWidget(QLabel(desc_text, objectName="pageSub"))
        header.addLayout(words)
        header.addStretch()

        self.btn_scan = QPushButton(btn_text, objectName="primary")
        self.btn_scan.setCursor(Qt.PointingHandCursor)
        self.btn_scan.clicked.connect(self.start_scan)
        header.addWidget(self.btn_scan)

        root.addLayout(header)

        # Progress Panel
        self.progress_panel = QFrame(objectName="card")
        self.progress_panel.setVisible(False)
        p_layout = QVBoxLayout(self.progress_panel)
        p_layout.setContentsMargins(16, 12, 16, 12)
        p_layout.setSpacing(8)

        p_top = QHBoxLayout()
        self.progress_status = QLabel("Analyzing cryptographic & perceptual hashes…", styleSheet="font-weight: 600;")
        p_top.addWidget(self.progress_status)
        p_top.addStretch()

        self.btn_cancel = QPushButton("Cancel", objectName="secondary")
        self.btn_cancel.setFixedWidth(75)
        self.btn_cancel.clicked.connect(self.cancel_scan)
        p_top.addWidget(self.btn_cancel)
        p_layout.addLayout(p_top)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        p_layout.addWidget(self.progress_bar)

        root.addWidget(self.progress_panel)

        # Groups Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_content = QWidget()
        self.groups_layout = QVBoxLayout(self.scroll_content)
        self.groups_layout.setContentsMargins(4, 4, 4, 16)
        self.groups_layout.setSpacing(16)
        self.scroll_area.setWidget(self.scroll_content)
        root.addWidget(self.scroll_area, stretch=1)

        self.reload_groups()

    def reload_groups(self):
        while self.groups_layout.count():
            item = self.groups_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if self.mode == "exact":
            groups = self.database.get_exact_duplicates()
            is_exact = True
            empty_title = "No Exact Duplicates Found"
            empty_desc = "All photos in your library appear to have unique byte content."
        else:
            groups = self.database.get_similar_photos()
            is_exact = False
            empty_title = "No Visually Similar Photos Found"
            empty_desc = "No photos with close perceptual hash distances were clustered."

        if not groups:
            empty_card = QFrame(objectName="card")
            el = QVBoxLayout(empty_card)
            el.setAlignment(Qt.AlignCenter)
            el.setContentsMargins(30, 40, 30, 40)
            el.setSpacing(8)

            t = QLabel(empty_title, objectName="pageTitle")
            t.setAlignment(Qt.AlignCenter)
            d = QLabel(f"{empty_desc}\nClick '{'Scan for Duplicates' if is_exact else 'Scan Similar Photos'}' above to analyze your images.", objectName="muted")
            d.setAlignment(Qt.AlignCenter)
            el.addWidget(t)
            el.addWidget(d)
            self.groups_layout.addWidget(empty_card)
            return

        for idx, grp in enumerate(groups, 1):
            gid = f"Group #{idx}"
            card = DuplicateGroupCard(gid, grp, is_exact=is_exact)
            card.image_clicked.connect(self.open_preview)
            self.groups_layout.addWidget(card)

        self.groups_layout.addStretch()

    def open_preview(self, img_data: Dict[str, Any]):
        dialog = PreviewDialog(img_data, on_enhance_callback=self.on_enhance_callback, parent=self)
        dialog.exec()

    def start_scan(self):
        if self.worker and self.worker.isRunning():
            return

        self.btn_scan.setEnabled(False)
        self.progress_panel.setVisible(True)
        self.progress_bar.setValue(0)

        self.worker = DuplicateWorker(force_all=False, database=self.database)
        self.worker.started_scan.connect(lambda total: self.progress_bar.setMaximum(max(total, 1)))
        self.worker.progress.connect(self._on_progress)
        self.worker.completed.connect(self._on_completed)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def cancel_scan(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.progress_status.setText("Cancelling scan…")

    def _on_progress(self, current: int, total: int, status_msg: str):
        self.progress_bar.setValue(current)
        self.progress_status.setText(f"Processing ({current}/{total}): {status_msg}")

    def _on_completed(self, result: dict):
        self.btn_scan.setEnabled(True)
        self.progress_panel.setVisible(False)
        self.reload_groups()

    def _on_failed(self, error: str):
        self.btn_scan.setEnabled(True)
        self.progress_status.setText(f"Scan error: {error}")

