"""Recently Processed workspace showing all enhanced and exported photos."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.preview_dialog import format_size, reveal_in_explorer
from core.thumbnails import generate_thumbnail, get_cached_thumbnail_path
from database.db_manager import DatabaseManager


class ProcessedItemCard(QFrame):
    def __init__(self, record: Dict[str, Any], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.record = record
        self.setObjectName("card")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(16)

        # Thumbnail
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(68, 68)
        self.thumb_label.setAlignment(Qt.AlignCenter)
        self.thumb_label.setStyleSheet("background: rgba(0,0,0,0.25); border-radius: 8px;")
        layout.addWidget(self.thumb_label)

        # Metadata Details
        info = QVBoxLayout()
        info.setSpacing(3)
        name_lbl = QLabel(record.get("filename", "Enhanced Photo"))
        name_lbl.setStyleSheet("font-size: 14px; font-weight: 700;")
        info.addWidget(name_lbl)

        src_lbl = QLabel(f"Source: {Path(record.get('source_path', '')).name}", objectName="muted")
        src_lbl.setStyleSheet("font-size: 11px;")
        info.addWidget(src_lbl)

        date_lbl = QLabel(f"Exported: {record.get('created_at', '')}", objectName="muted")
        date_lbl.setStyleSheet("font-size: 11px;")
        info.addWidget(date_lbl)
        layout.addLayout(info, stretch=1)

        # Resolution & Size
        w = record.get("width", 0)
        h = record.get("height", 0)
        dim_str = f"{w} × {h} px" if w and h else "—"
        dim_lbl = QLabel(dim_str, objectName="muted")
        layout.addWidget(dim_lbl)

        p = Path(record.get("output_path", ""))
        size_str = format_size(p.stat().st_size) if p.is_file() else "—"
        size_lbl = QLabel(size_str, objectName="muted")
        size_lbl.setFixedWidth(75)
        size_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(size_lbl)

        # Actions
        btn_open = QPushButton("Open", objectName="secondary")
        btn_open.setCursor(Qt.PointingHandCursor)
        btn_open.clicked.connect(self._open_file)
        layout.addWidget(btn_open)

        btn_reveal = QPushButton("Reveal", objectName="primary")
        btn_reveal.setCursor(Qt.PointingHandCursor)
        btn_reveal.clicked.connect(lambda: reveal_in_explorer(record.get("output_path", "")))
        layout.addWidget(btn_reveal)

        self._load_thumbnail()

    def _open_file(self):
        p = Path(self.record.get("output_path", ""))
        if p.is_file():
            if sys.platform == "win32":
                os.startfile(str(p))
            elif sys.platform == "darwin":
                subprocess.run(["open", str(p)])
            else:
                subprocess.run(["xdg-open", str(p)])

    def _load_thumbnail(self):
        out_p = self.record.get("output_path", "")
        if not Path(out_p).is_file():
            self.thumb_label.setText("Deleted")
            return

        cached = get_cached_thumbnail_path(out_p)
        if not cached:
            cached = generate_thumbnail(out_p)

        if cached and Path(cached).is_file():
            pm = QPixmap(str(cached))
            scaled = pm.scaled(self.thumb_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.thumb_label.setPixmap(scaled)
        else:
            self.thumb_label.setText("No Preview")


class ProcessedPage(QWidget):
    def __init__(self, database: DatabaseManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.database = database

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 26, 32, 24)
        root.setSpacing(16)

        # Header
        header = QHBoxLayout()
        words = QVBoxLayout()
        words.setSpacing(4)
        words.addWidget(QLabel("Recently Processed", objectName="pageTitle"))
        words.addWidget(
            QLabel(
                "Exported, enhanced, and scaled copies. All originals remain safely untouched.",
                objectName="pageSub",
            )
        )
        header.addLayout(words)
        header.addStretch()

        btn_refresh = QPushButton("Refresh List", objectName="secondary")
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.clicked.connect(self.reload_list)
        header.addWidget(btn_refresh)

        root.addLayout(header)

        # Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_content = QWidget()
        self.list_layout = QVBoxLayout(self.scroll_content)
        self.list_layout.setContentsMargins(4, 4, 4, 16)
        self.list_layout.setSpacing(12)
        self.scroll_area.setWidget(self.scroll_content)
        root.addWidget(self.scroll_area, stretch=1)

        self.reload_list()

    def reload_list(self):
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        items = self.database.get_processed_photos()
        if not items:
            empty_card = QFrame(objectName="card")
            el = QVBoxLayout(empty_card)
            el.setAlignment(Qt.AlignCenter)
            el.setContentsMargins(30, 40, 30, 40)
            el.setSpacing(8)
            el.addWidget(QLabel("No Processed Photos Yet", objectName="pageTitle"))
            el.addWidget(
                QLabel(
                    "Photos you enhance and export in the Image Enhancer Studio will appear here.",
                    objectName="muted",
                )
            )
            self.list_layout.addWidget(empty_card)
            return

        for rec in items:
            card = ProcessedItemCard(rec)
            self.list_layout.addWidget(card)

        self.list_layout.addStretch()

