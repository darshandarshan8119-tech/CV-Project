"""Best Shots workspace: AI/CV Quality, Sharpness, and Blur Analysis."""
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
from core.quality import rank_group_photos
from core.thumbnails import get_cached_thumbnail_path
from database.db_manager import DatabaseManager
from workers.quality_worker import QualityWorker
from workers.thumbnail_worker import ThumbnailWorker


class SimilarGroupRankCard(QFrame):
    image_clicked = Signal(dict)

    def __init__(
        self,
        group_id: str,
        ranked_images: List[Dict[str, Any]],
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.setObjectName("featureCard")
        self.hover_filter = HoverLiftFilter(self, glow_color=QColor(16, 185, 129, 45), blur_radius=16)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        # Header
        top = QHBoxLayout()
        title = QLabel(f"Similar Photo Set ({len(ranked_images)} variations)", objectName="cardTitle")
        title.setStyleSheet("font-size: 15px;")
        top.addWidget(title)
        top.addStretch()

        badge = QLabel("DETERMINISTIC QUALITY RANKING (OPENCV)", objectName="pill")
        badge.setStyleSheet("color: #9487FF; font-weight: 700; font-size: 11px;")
        top.addWidget(badge)
        layout.addLayout(top)

        # Best pick callout banner
        if ranked_images:
            best = ranked_images[0]
            callout = QFrame(objectName="card")
            callout.setStyleSheet("background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 10px;")
            cl = QHBoxLayout(callout)
            cl.setContentsMargins(14, 12, 14, 12)
            cl.setSpacing(12)

            rec_icon = QLabel("★ BEST PICK")
            rec_icon.setStyleSheet("color: #10B981; font-weight: 800; font-size: 11px; background: rgba(16, 185, 129, 0.15); padding: 5px 10px; border-radius: 8px;")
            cl.addWidget(rec_icon)

            rec_text = QVBoxLayout()
            rec_text.setSpacing(2)
            lbl1 = QLabel(f"Recommended Best Shot: {best.get('filename')}", styleSheet="font-weight: 700; font-size: 13px; color: #10B981;")
            lbl2 = QLabel(
                f"Score: {int(best.get('quality_score', 0))}/100 — {best.get('quality_explanation', 'Top sharpness and dynamic range')}",
                objectName="muted",
            )
            lbl2.setStyleSheet("font-size: 12px;")
            rec_text.addWidget(lbl1)
            rec_text.addWidget(lbl2)
            cl.addLayout(rec_text, stretch=1)
            layout.addWidget(callout)

        # Grid of images in this group
        grid = QGridLayout()
        grid.setSpacing(12)
        for idx, img in enumerate(ranked_images):
            card = ImageCard(img, is_grid=True)
            # Add ranking badge
            if img.get("is_recommended"):
                card.meta_label.setText(f"★ BEST ({int(img.get('quality_score', 0))}/100)")
                card.meta_label.setStyleSheet("color: #10B981; font-weight: 700; font-size: 11px;")
            else:
                card.meta_label.setText(f"#{img.get('rank_in_group')} ({int(img.get('quality_score', 0))}/100)")

            card.clicked.connect(self.image_clicked.emit)
            grid.addWidget(card, 0, idx)

        layout.addLayout(grid)


class BestShotsPage(QWidget):
    def __init__(
        self,
        database: DatabaseManager,
        on_enhance_callback: Optional[Callable[[str], None]] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.database = database
        self.on_enhance_callback = on_enhance_callback
        self.filter_mode = "all"  # "all", "top", "blurry", "bursts"
        self.worker: Optional[QualityWorker] = None
        self.thumb_worker: Optional[ThumbnailWorker] = None
        self.cards: List[ImageCard] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(36, 28, 36, 24)
        root.setSpacing(18)

        # Header
        header = QHBoxLayout()
        words = QVBoxLayout()
        words.setSpacing(4)
        title = QLabel("Best Shots", objectName="pageTitle")
        subtitle = QLabel(
            "Find your sharpest, highest-quality memories and identify blurry or sub-optimal shots for review.",
            objectName="pageSub",
        )
        words.addWidget(title)
        words.addWidget(subtitle)
        header.addLayout(words)
        header.addStretch()

        self.btn_analyze = QPushButton("✦  Analyze Library Quality", objectName="primary")
        self.btn_analyze.setCursor(Qt.PointingHandCursor)
        self.btn_analyze.clicked.connect(self.start_analysis)
        header.addWidget(self.btn_analyze)

        root.addLayout(header)

        # Progress Panel
        self.progress_panel = QFrame(objectName="card")
        self.progress_panel.setVisible(False)
        p_layout = QVBoxLayout(self.progress_panel)
        p_layout.setContentsMargins(18, 14, 18, 14)
        p_layout.setSpacing(10)

        p_top = QHBoxLayout()
        self.progress_status = QLabel("Evaluating sharpness and exposure metrics…", objectName="cardTitle")
        self.progress_status.setStyleSheet("font-weight: 600; font-size: 13px;")
        p_top.addWidget(self.progress_status)
        p_top.addStretch()

        self.btn_cancel = QPushButton("Cancel", objectName="secondary")
        self.btn_cancel.setFixedWidth(75)
        self.btn_cancel.clicked.connect(self.cancel_analysis)
        p_top.addWidget(self.btn_cancel)
        p_layout.addLayout(p_top)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        p_layout.addWidget(self.progress_bar)

        root.addWidget(self.progress_panel)

        # Filter Segmented Bar
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)

        self.btn_filter_all = QPushButton("All Ranked Photos", objectName="primary")
        self.btn_filter_all.setCursor(Qt.PointingHandCursor)
        self.btn_filter_all.clicked.connect(lambda: self.set_filter("all"))

        self.btn_filter_top = QPushButton("Top Picks (Crisp Quality)", objectName="secondary")
        self.btn_filter_top.setCursor(Qt.PointingHandCursor)
        self.btn_filter_top.clicked.connect(lambda: self.set_filter("top"))

        self.btn_filter_blurry = QPushButton("Needs Review (Blurry / Soft)", objectName="secondary")
        self.btn_filter_blurry.setCursor(Qt.PointingHandCursor)
        self.btn_filter_blurry.clicked.connect(lambda: self.set_filter("blurry"))

        self.btn_filter_bursts = QPushButton("Burst & Similar Best Picks", objectName="secondary")
        self.btn_filter_bursts.setCursor(Qt.PointingHandCursor)
        self.btn_filter_bursts.clicked.connect(lambda: self.set_filter("bursts"))

        filter_bar.addWidget(self.btn_filter_all)
        filter_bar.addWidget(self.btn_filter_top)
        filter_bar.addWidget(self.btn_filter_blurry)
        filter_bar.addWidget(self.btn_filter_bursts)
        filter_bar.addStretch()

        root.addLayout(filter_bar)

        # Photo Grid Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_content = QWidget()
        self.content_layout = QVBoxLayout(self.scroll_content)
        self.content_layout.setContentsMargins(4, 4, 4, 16)
        self.content_layout.setSpacing(16)
        self.scroll_area.setWidget(self.scroll_content)
        root.addWidget(self.scroll_area, stretch=1)

        self.reload_photos()

    def set_filter(self, mode: str):
        self.filter_mode = mode
        self.btn_filter_all.setObjectName("primary" if mode == "all" else "secondary")
        self.btn_filter_top.setObjectName("primary" if mode == "top" else "secondary")
        self.btn_filter_blurry.setObjectName("primary" if mode == "blurry" else "secondary")
        self.btn_filter_bursts.setObjectName("primary" if mode == "bursts" else "secondary")

        for b in (self.btn_filter_all, self.btn_filter_top, self.btn_filter_blurry, self.btn_filter_bursts):
            b.style().unpolish(b)
            b.style().polish(b)

        self.reload_photos()

    def reload_photos(self):
        if self.thumb_worker and self.thumb_worker.isRunning():
            self.thumb_worker.cancel()
            self.thumb_worker.wait(500)

        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.cards.clear()

        # Handle burst / similar grouped mode
        if self.filter_mode == "bursts":
            sim_groups = self.database.get_similar_photos()
            if not sim_groups:
                empty_card = QFrame(objectName="card")
                el = QVBoxLayout(empty_card)
                el.setAlignment(Qt.AlignCenter)
                el.setContentsMargins(30, 48, 30, 48)
                el.addWidget(QLabel("No Similar or Burst Photo Groups Found", objectName="pageTitle"))
                el.addWidget(QLabel("Scan for similar photos in the Similar Photos workspace first.", objectName="muted"))
                self.content_layout.addWidget(empty_card)
                return

            blur_th = float(self.database.get_setting("blur_threshold", "130.0"))
            for idx, grp in enumerate(sim_groups, 1):
                ranked = rank_group_photos(grp, blur_th)
                card = SimilarGroupRankCard(f"Group #{idx}", ranked)
                card.image_clicked.connect(self.open_preview)
                self.content_layout.addWidget(card)

            self.content_layout.addStretch()
            return

        # Otherwise grid mode
        grid_container = QWidget()
        grid = QGridLayout(grid_container)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(14)

        if self.filter_mode == "all":
            images = self.database.get_images(sort_by="quality_desc")
        elif self.filter_mode == "top":
            min_q = float(self.database.get_setting("min_quality", "70.0"))
            images = self.database.get_images(sort_by="quality_desc", min_quality=min_q)
        else:
            images = self.database.get_images(only_blurry=True, sort_by="quality_asc")

        if not images:
            empty_lbl = QLabel(
                "No photos match the selected quality filter.\nClick 'Analyze Library Quality' above to evaluate your photos."
            )
            empty_lbl.setAlignment(Qt.AlignCenter)
            empty_lbl.setStyleSheet("color: #7C8497; font-size: 14px; margin: 40px;")
            self.content_layout.addWidget(empty_lbl)
            return

        cols = 4
        paths_needing_thumbs = []
        for index, img in enumerate(images):
            card = ImageCard(img, is_grid=True)
            q_score = img.get("quality_score", 0.0)
            if q_score:
                is_b = img.get("is_blurry", 0)
                tag = "Needs review" if is_b else f"Quality {int(q_score)}/100"
                card.meta_label.setText(f"{tag} • {card.meta_label.text()}")

            card.clicked.connect(self.open_preview)
            row = index // cols
            col = index % cols
            grid.addWidget(card, row, col)
            self.cards.append(card)

            if not get_cached_thumbnail_path(img["path"]):
                paths_needing_thumbs.append(img["path"])

        grid.setRowStretch(len(images) + 1, 1)
        self.content_layout.addWidget(grid_container)

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

    def start_analysis(self):
        if self.worker and self.worker.isRunning():
            return

        self.btn_analyze.setEnabled(False)
        self.progress_panel.setVisible(True)
        self.progress_bar.setValue(0)

        blur_th = float(self.database.get_setting("blur_threshold", "130.0"))
        self.worker = QualityWorker(force_all=True, blur_threshold=blur_th, database=self.database)
        self.worker.started_analysis.connect(lambda total: self.progress_bar.setMaximum(max(total, 1)))
        self.worker.progress.connect(self._on_progress)
        self.worker.completed.connect(self._on_completed)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def cancel_analysis(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.progress_status.setText("Cancelling analysis…")

    def _on_progress(self, current: int, total: int, status_msg: str):
        self.progress_bar.setValue(current)
        self.progress_status.setText(f"Analyzing ({current}/{total}): {status_msg}")

    def _on_completed(self, result: dict):
        self.btn_analyze.setEnabled(True)
        self.progress_panel.setVisible(False)
        self.reload_photos()

    def _on_failed(self, error: str):
        self.btn_analyze.setEnabled(True)
        self.progress_status.setText(f"Analysis error: {error}")
