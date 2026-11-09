"""Background worker for non-blocking photo enhancement and file exporting."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional
import numpy as np
from PIL import Image
from PySide6.QtCore import QThread, Signal

from core.enhancer import apply_preset, enhance_photo, save_enhanced_image
from core.logger import logger


class EnhancementWorker(QThread):
    preview_ready = Signal(object)      # Emits RGB numpy array preview
    export_completed = Signal(str, int, int)  # Emits (output_path, width, height)
    failed = Signal(str)

    def __init__(
        self,
        source_path: str,
        params: Dict[str, Any],
        is_export: bool = False,
        output_dir: str = "processed",
        preset_name: Optional[str] = None,
    ):
        super().__init__()
        self.source_path = source_path
        self.params = params
        self.is_export = is_export
        self.output_dir = output_dir
        self.preset_name = preset_name
        self.cancelled = False

    def cancel(self):
        self.cancelled = True

    def run(self):
        try:
            p = Path(self.source_path)
            if not p.is_file():
                self.failed.emit("Source image file not found")
                return

            with Image.open(p) as img:
                if self.is_export:
                    # Full resolution for export
                    full_img = img.copy()
                    if full_img.mode != "RGB":
                        full_img = full_img.convert("RGB")
                    img_rgb = np.array(full_img)
                else:
                    # Bounded resolution (max 1024) for instant live preview
                    preview_img = img.copy()
                    preview_img.thumbnail((1024, 1024), Image.Resampling.BILINEAR)
                    if preview_img.mode != "RGB":
                        preview_img = preview_img.convert("RGB")
                    img_rgb = np.array(preview_img)

            if self.cancelled:
                return

            if self.preset_name:
                enhanced = apply_preset(img_rgb, self.preset_name)
            else:
                enhanced = enhance_photo(
                    img_rgb,
                    brightness=self.params.get("brightness", 0),
                    contrast=self.params.get("contrast", 0),
                    saturation=self.params.get("saturation", 0),
                    sharpness=self.params.get("sharpness", 0),
                    denoise=self.params.get("denoise", 0),
                    warmth=self.params.get("warmth", 0),
                    scale_factor=self.params.get("scale_factor", 1.0) if self.is_export else 1.0,
                )

            if self.cancelled:
                return

            if self.is_export:
                saved_path = save_enhanced_image(
                    self.source_path,
                    enhanced,
                    output_dir=self.output_dir,
                    custom_filename=self.params.get("custom_filename"),
                )
                self.export_completed.emit(str(saved_path), enhanced.shape[1], enhanced.shape[0])
            else:
                self.preview_ready.emit(enhanced)

        except Exception as e:
            logger.error(f"Enhancement worker error: {e}")
            self.failed.emit(str(e))

