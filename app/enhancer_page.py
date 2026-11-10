"""Local non-destructive photo enhancement studio workspace with interactive before/after split slider."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional
import numpy as np
from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from app.animations import HoverLiftFilter
from app.preview_dialog import reveal_in_explorer
from app.widgets import BeforeAfterSliderWidget, GlowCard
from core.enhancer import apply_preset, enhance_photo
from core.logger import logger
from database.db_manager import DatabaseManager
from workers.enhancement_worker import EnhancementWorker


class EnhancerPage(QWidget):
    def __init__(self, database: DatabaseManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.database = database
        self.current_image_path: Optional[str] = None
        self.original_rgb: Optional[np.ndarray] = None
        self.enhanced_rgb: Optional[np.ndarray] = None
        self.worker: Optional[EnhancementWorker] = None
        self.view_mode = "split"  # "split", "enhanced", "original"

        root = QVBoxLayout(self)
        root.setContentsMargins(36, 28, 36, 24)
        root.setSpacing(16)

        # Header
        header = QHBoxLayout()
        words = QVBoxLayout()
        words.setSpacing(4)
        words.addWidget(QLabel("Image Enhancer Studio", objectName="pageTitle"))
        words.addWidget(
            QLabel(
                "Non-destructive adjustments (CLAHE, bilateral denoising, unsharp masking, and Lanczos scaling).",
                objectName="pageSub",
            )
        )
        header.addLayout(words)
        header.addStretch()

        self.btn_select_file = QPushButton("📁 Choose Photo to Enhance…", objectName="secondary")
        self.btn_select_file.setCursor(Qt.PointingHandCursor)
        self.btn_select_file.clicked.connect(self.choose_file)
        header.addWidget(self.btn_select_file)

        self.btn_save = QPushButton("✦  Export Enhanced Copy", objectName="primary")
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self.export_image)
        header.addWidget(self.btn_save)

        root.addLayout(header)

        # Main Studio Split: Left Interactive Comparison Viewport + Right Control Sidebar
        studio_split = QHBoxLayout()
        studio_split.setSpacing(18)

        # Left Viewport
        viewport_frame = QFrame(objectName="featureCard")
        HoverLiftFilter(viewport_frame, blur_radius=14)
        v_layout = QVBoxLayout(viewport_frame)
        v_layout.setContentsMargins(14, 14, 14, 14)
        v_layout.setSpacing(10)

        # View mode toggle buttons
        mode_bar = QHBoxLayout()
        self.mode_lbl = QLabel("INTERACTIVE BEFORE / AFTER SLIDER")
        self.mode_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #7C8497; letter-spacing: 0.8px;")
        mode_bar.addWidget(self.mode_lbl)
        mode_bar.addStretch()

        self.btn_mode_split = QPushButton("Split Slider", objectName="primary")
        self.btn_mode_split.setCursor(Qt.PointingHandCursor)
        self.btn_mode_split.clicked.connect(lambda: self.set_preview_mode("split"))

        self.btn_mode_enhanced = QPushButton("Enhanced View", objectName="secondary")
        self.btn_mode_enhanced.setCursor(Qt.PointingHandCursor)
        self.btn_mode_enhanced.clicked.connect(lambda: self.set_preview_mode("enhanced"))

        self.btn_mode_original = QPushButton("Original View", objectName="secondary")
        self.btn_mode_original.setCursor(Qt.PointingHandCursor)
        self.btn_mode_original.clicked.connect(lambda: self.set_preview_mode("original"))

        mode_bar.addWidget(self.btn_mode_split)
        mode_bar.addWidget(self.btn_mode_enhanced)
        mode_bar.addWidget(self.btn_mode_original)
        v_layout.addLayout(mode_bar)

        # Interactive split comparison canvas
        self.compare_widget = BeforeAfterSliderWidget()
        self.compare_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        v_layout.addWidget(self.compare_widget, stretch=1)

        # Status & Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        v_layout.addWidget(self.progress_bar)

        self.info_status = QLabel("Ready • Drag the central divider to compare before and after")
        self.info_status.setStyleSheet("font-size: 12px; color: #7C8497;")
        v_layout.addWidget(self.info_status)

        studio_split.addWidget(viewport_frame, stretch=3)

        # Right Controls Sidebar
        sidebar_frame = QFrame(objectName="card")
        sidebar_frame.setFixedWidth(340)
        s_layout = QVBoxLayout(sidebar_frame)
        s_layout.setContentsMargins(20, 18, 20, 18)
        s_layout.setSpacing(12)

        s_layout.addWidget(QLabel("ONE-CLICK PRESETS", objectName="metricLabel"))

        presets_grid = QHBoxLayout()
        presets_grid.setSpacing(6)
        presets_list = [
            ("✨ Auto", "magic_auto"),
            ("🌿 Landscape", "vibrant_landscape"),
            ("👤 Portrait", "portrait_glow"),
            ("🎞️ B&W", "bw_film"),
        ]
        for p_name, p_key in presets_list:
            btn = QPushButton(p_name, objectName="secondary")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("padding: 7px 8px; font-size: 11px;")
            btn.clicked.connect(lambda checked=False, k=p_key: self.apply_preset_filter(k))
            presets_grid.addWidget(btn)
        s_layout.addLayout(presets_grid)

        s_layout.addSpacing(6)
        s_layout.addWidget(QLabel("ADJUSTMENTS", objectName="metricLabel"))

        self.sliders: Dict[str, QSlider] = {}
        self.slider_labels: Dict[str, QLabel] = {}

        slider_defs = [
            ("brightness", "Brightness", -100, 100, 0),
            ("contrast", "Contrast", -100, 100, 0),
            ("saturation", "Saturation", -100, 100, 0),
            ("sharpness", "Sharpening", 0, 100, 0),
            ("denoise", "Denoising", 0, 100, 0),
            ("warmth", "Color Warmth", -100, 100, 0),
        ]

        for key, title, min_val, max_val, def_val in slider_defs:
            row = QHBoxLayout()
            row.addWidget(QLabel(title, styleSheet="font-size: 12px; font-weight: 600;"))
            val_lbl = QLabel(str(def_val), objectName="muted")
            val_lbl.setFixedWidth(35)
            val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row.addWidget(val_lbl)
            s_layout.addLayout(row)

            slider = QSlider(Qt.Horizontal)
            slider.setRange(min_val, max_val)
            slider.setValue(def_val)
            slider.valueChanged.connect(lambda v, k=key, l=val_lbl: self._on_slider_changed(k, v, l))
            slider.sliderReleased.connect(self.trigger_enhancement)
            s_layout.addWidget(slider)

            self.sliders[key] = slider
            self.slider_labels[key] = val_lbl

        s_layout.addSpacing(6)
        s_layout.addWidget(QLabel("RESIZE / UPSCALE", objectName="metricLabel"))
        self.scale_combo = QComboBox()
        self.scale_combo.addItems([
            "Original Size (1.0×)",
            "1.5× Super-Sample (Lanczos)",
            "2.0× High Resolution (Lanczos)",
            "4.0× Ultra Resolution (Lanczos)",
        ])
        s_layout.addWidget(self.scale_combo)

        # Notice distinguishing local CV tools from optional future Real-ESRGAN
        future_note = QLabel(
            "Note: Upscaling uses high-fidelity Lanczos-4 interpolation. Optional generative Real-ESRGAN deep-learning enhancement is planned for a future phase.",
            objectName="muted",
        )
        future_note.setWordWrap(True)
        future_note.setStyleSheet("font-size: 11px; margin-top: 6px; line-height: 1.3;")
        s_layout.addWidget(future_note)

        s_layout.addStretch()

        btn_reset = QPushButton("Reset All Adjustments", objectName="secondary")
        btn_reset.setCursor(Qt.PointingHandCursor)
        btn_reset.clicked.connect(self.reset_adjustments)
        s_layout.addWidget(btn_reset)

        studio_split.addWidget(sidebar_frame)
        root.addLayout(studio_split, stretch=1)

    def load_image(self, file_path: str):
        p = Path(file_path)
        if not p.is_file():
            QMessageBox.warning(self, "File Not Found", f"Could not load image:\n{file_path}")
            return

        self.current_image_path = str(p.resolve())
        self.info_status.setText(f"Loading {p.name}…")

        try:
            with Image.open(p) as img:
                preview = img.copy()
                preview.thumbnail((1200, 1200), Image.Resampling.BILINEAR)
                if preview.mode != "RGB":
                    preview = preview.convert("RGB")
                self.original_rgb = np.array(preview)
                self.enhanced_rgb = self.original_rgb.copy()

            self.reset_adjustments(trigger=False)
            self.btn_save.setEnabled(True)
            self.info_status.setText(f"Loaded {p.name} ({img.size[0]}×{img.size[1]} px). Original file remains read-only.")
            self.update_preview_display()
        except Exception as e:
            logger.error(f"Failed to load image in enhancer: {e}")
            QMessageBox.critical(self, "Load Error", f"Could not decode image:\n{e}")

    def choose_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Photo to Enhance",
            str(Path.home()),
            "Supported Images (*.jpg *.jpeg *.png *.webp *.bmp *.tiff)",
        )
        if path:
            self.load_image(path)

    def _on_slider_changed(self, key: str, value: int, label: QLabel):
        label.setText(str(value))

    def trigger_enhancement(self):
        if self.original_rgb is None or not self.current_image_path:
            return

        params = {k: s.value() for k, s in self.sliders.items()}
        scale_idx = self.scale_combo.currentIndex()
        scale_factors = [1.0, 1.5, 2.0, 4.0]
        params["scale_factor"] = scale_factors[scale_idx]

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate animation

        # Compute on background worker
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(400)

        self.worker = EnhancementWorker(self.current_image_path, params, is_export=False)
        self.worker.preview_ready.connect(self._on_preview_ready)
        self.worker.failed.connect(self._on_worker_failed)
        self.worker.start()

    def _on_preview_ready(self, enhanced_array: np.ndarray):
        self.progress_bar.setVisible(False)
        self.enhanced_rgb = enhanced_array
        self.update_preview_display()

    def _on_worker_failed(self, error: str):
        self.progress_bar.setVisible(False)
        self.info_status.setText(f"Enhancement error: {error}")

    def apply_preset_filter(self, preset_key: str):
        if self.original_rgb is None:
            return
        self.enhanced_rgb = apply_preset(self.original_rgb, preset_key)
        self.update_preview_display()
        self.info_status.setText(f"Applied preset: {preset_key.replace('_', ' ').title()}")

    def set_preview_mode(self, mode: str):
        self.view_mode = mode
        self.btn_mode_split.setObjectName("primary" if mode == "split" else "secondary")
        self.btn_mode_enhanced.setObjectName("primary" if mode == "enhanced" else "secondary")
        self.btn_mode_original.setObjectName("primary" if mode == "original" else "secondary")

        for b in (self.btn_mode_split, self.btn_mode_enhanced, self.btn_mode_original):
            b.style().unpolish(b)
            b.style().polish(b)

        if mode == "split":
            self.compare_widget.set_split_ratio(0.5)
        elif mode == "enhanced":
            self.compare_widget.set_split_ratio(0.0)
        elif mode == "original":
            self.compare_widget.set_split_ratio(1.0)

    def _array_to_pixmap(self, arr: Optional[np.ndarray]) -> Optional[QPixmap]:
        if arr is None:
            return None
        h, w, ch = arr.shape
        bytes_per_line = ch * w
        q_img = QImage(arr.data, w, h, bytes_per_line, QImage.Format_RGB888)
        return QPixmap.fromImage(q_img)

    def update_preview_display(self):
        pm_orig = self._array_to_pixmap(self.original_rgb)
        pm_enh = self._array_to_pixmap(self.enhanced_rgb)
        self.compare_widget.set_images(pm_orig, pm_enh)

    def reset_adjustments(self, trigger: bool = True):
        for s in self.sliders.values():
            s.setValue(0)
        self.scale_combo.setCurrentIndex(0)
        if self.original_rgb is not None:
            self.enhanced_rgb = self.original_rgb.copy()
            self.update_preview_display()
        if trigger:
            self.info_status.setText("All adjustments reset to neutral.")

    def export_image(self):
        if not self.current_image_path or self.enhanced_rgb is None:
            return

        output_dir = self.database.get_setting("processed_dir", "processed")
        params = {k: s.value() for k, s in self.sliders.items()}
        scale_idx = self.scale_combo.currentIndex()
        scale_factors = [1.0, 1.5, 2.0, 4.0]
        params["scale_factor"] = scale_factors[scale_idx]

        self.btn_save.setEnabled(False)
        self.info_status.setText("Exporting full-resolution enhanced photo…")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        # Worker for non-blocking full resolution export
        export_worker = EnhancementWorker(
            self.current_image_path,
            params,
            is_export=True,
            output_dir=output_dir,
        )
        export_worker.export_completed.connect(self._on_export_completed)
        export_worker.failed.connect(self._on_worker_failed)
        export_worker.start()
        self.active_export_worker = export_worker

    def _on_export_completed(self, output_path: str, width: int, height: int):
        self.btn_save.setEnabled(True)
        self.progress_bar.setVisible(False)

        # Record in database
        src_name = Path(self.current_image_path or "").name
        out_name = Path(output_path).name
        self.database.record_processed_photo(
            source_path=self.current_image_path or "",
            output_path=output_path,
            filename=out_name,
            preset="Studio Adjustments",
            width=width,
            height=height,
        )

        msg = QMessageBox(self)
        msg.setWindowTitle("Photo Enhanced Successfully")
        msg.setText(f"Enhanced copy saved safely to:\n{output_path}\n\nResolution: {width} × {height} px\nYour original photo was not changed.")
        btn_open = msg.addButton("Reveal in Explorer", QMessageBox.ActionRole)
        msg.addButton(QMessageBox.Ok)
        msg.exec()

        if msg.clickedButton() == btn_open:
            reveal_in_explorer(output_path)

        self.info_status.setText(f"Exported: {out_name} (original untouched)")
