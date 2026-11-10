"""Full-resolution photo preview dialog with metadata and Explorer integration."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.animations import HoverLiftFilter, fade_in_widget


def format_size(bytes_num: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_num < 1024.0:
            return f"{bytes_num:.1f} {unit}"
        bytes_num /= 1024.0
    return f"{bytes_num:.1f} TB"


def reveal_in_explorer(file_path: str):
    """Reveal file in OS file explorer (Windows Explorer, macOS Finder, Linux file manager)."""
    p = Path(file_path).resolve()
    if sys.platform == "win32":
        subprocess.run(["explorer", f"/select,{str(p)}"])
    elif sys.platform == "darwin":
        subprocess.run(["open", "-R", str(p)])
    else:
        subprocess.run(["xdg-open", str(p.parent)])


class PreviewDialog(QDialog):
    def __init__(
        self,
        image_data: Dict[str, Any],
        on_enhance_callback: Optional[Callable[[str], None]] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.image_data = image_data
        self.on_enhance_callback = on_enhance_callback
        self.setWindowTitle(f"Pixora Preview — {image_data.get('filename', 'Photo')}")
        self.resize(1060, 720)
        self.setMinimumSize(820, 540)
        self.setModal(True)

        # Outer layout
        outer = QHBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(18)

        # Left / Center: Image viewport
        img_container = QFrame(objectName="featureCard")
        HoverLiftFilter(img_container, blur_radius=20)
        img_layout = QVBoxLayout(img_container)
        img_layout.setContentsMargins(12, 12, 12, 12)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image_label.setStyleSheet("background: rgba(0,0,0,0.4); border-radius: 10px;")
        img_layout.addWidget(self.image_label)
        outer.addWidget(img_container, stretch=3)

        # Right sidebar: Metadata card
        meta_card = QFrame(objectName="card")
        meta_card.setFixedWidth(320)
        HoverLiftFilter(meta_card, blur_radius=14)
        meta_layout = QVBoxLayout(meta_card)
        meta_layout.setContentsMargins(22, 20, 22, 20)
        meta_layout.setSpacing(10)

        meta_layout.addWidget(QLabel("PHOTO DETAILS", objectName="metricLabel"))

        name_lbl = QLabel(image_data.get("filename", "Unknown"), objectName="cardTitle")
        name_lbl.setStyleSheet("font-size: 17px;")
        name_lbl.setWordWrap(True)
        meta_layout.addWidget(name_lbl)

        # Badge pill
        read_only_pill = QLabel("● READ-ONLY (ORIGINAL UNTOUCHED)", objectName="pillSuccess")
        meta_layout.addWidget(read_only_pill)

        meta_layout.addSpacing(6)

        # Info items
        w = image_data.get("width", 0)
        h = image_data.get("height", 0)
        dim_str = f"{w} × {h} px" if w and h else "—"
        size_str = format_size(image_data.get("size_bytes", 0))
        cat_str = image_data.get("category", "Uncategorized")
        conf = image_data.get("category_confidence", 0.0)
        conf_str = f" ({int(conf * 100)}%)" if conf else ""

        q_score = image_data.get("quality_score", 0.0)
        q_str = f"{int(q_score)}/100" if q_score else "Not rated yet"
        if image_data.get("is_blurry"):
            q_str += " (Soft / blurry)"
        elif q_score >= 75.0:
            q_str += " (Crisp quality)"

        for lbl, val in [
            ("Dimensions", dim_str),
            ("File Size", size_str),
            ("Quality Rating", q_str),
            ("Category", f"{cat_str}{conf_str}"),
            ("Location", image_data.get("folder", "—")),
        ]:
            meta_layout.addWidget(QLabel(lbl.upper(), objectName="metricLabel"))
            val_lbl = QLabel(str(val), objectName="muted")
            val_lbl.setWordWrap(True)
            meta_layout.addWidget(val_lbl)

        # File path box
        meta_layout.addWidget(QLabel("FULL PATH", objectName="metricLabel"))
        path_box = QLabel(image_data.get("path", ""))
        path_box.setTextInteractionFlags(Qt.TextSelectableByMouse)
        path_box.setWordWrap(True)
        path_box.setStyleSheet(
            "font-size: 11px; color: #8F97AA; background: rgba(0,0,0,0.25); padding: 8px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.06);"
        )
        meta_layout.addWidget(path_box)

        meta_layout.addStretch()

        # Action buttons
        if self.on_enhance_callback:
            btn_enhance = QPushButton("✦  Enhance in Studio", objectName="primary")
            btn_enhance.setCursor(Qt.PointingHandCursor)
            btn_enhance.clicked.connect(self._handle_enhance)
            meta_layout.addWidget(btn_enhance)

        btn_reveal = QPushButton("Reveal in Explorer", objectName="secondary")
        btn_reveal.setCursor(Qt.PointingHandCursor)
        btn_reveal.clicked.connect(lambda: reveal_in_explorer(image_data.get("path", "")))
        meta_layout.addWidget(btn_reveal)

        btn_close = QPushButton("Close Preview", objectName="secondary")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(self.accept)
        meta_layout.addWidget(btn_close)

        outer.addWidget(meta_card)

        # Escape shortcut
        QShortcut(QKeySequence("Escape"), self, self.accept)

        # Load image safely
        self._load_pixmap()

    def showEvent(self, event):
        super().showEvent(event)
        fade_in_widget(self, duration=180)

    def _handle_enhance(self):
        self.accept()
        if self.on_enhance_callback:
            self.on_enhance_callback(self.image_data.get("path", ""))

    def _load_pixmap(self):
        path = self.image_data.get("path", "")
        if path and Path(path).is_file():
            pm = QPixmap(path)
            if not pm.isNull():
                self.pixmap_orig = pm
                self._update_scaled_pixmap()
                return

        self.image_label.setText("Could not display full image.")

    def _update_scaled_pixmap(self):
        if hasattr(self, "pixmap_orig") and not self.pixmap_orig.isNull():
            target_size = self.image_label.size()
            if target_size.width() > 50 and target_size.height() > 50:
                scaled = self.pixmap_orig.scaled(
                    target_size,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                self.image_label.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_scaled_pixmap()
