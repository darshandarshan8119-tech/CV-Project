"""Background worker for image quality and blur scoring."""
from __future__ import annotations

from typing import Optional
from PySide6.QtCore import QThread, Signal

from core.logger import logger
from core.quality import assess_image_quality
from database.db_manager import DatabaseManager


class QualityWorker(QThread):
    started_analysis = Signal(int)
    progress = Signal(int, int, str)
    image_analyzed = Signal(str, dict)
    completed = Signal(dict)
    failed = Signal(str)

    def __init__(
        self,
        force_all: bool = False,
        blur_threshold: Optional[float] = None,
        database: Optional[DatabaseManager] = None,
    ):
        super().__init__()
        self.force_all = force_all
        self.database = database or DatabaseManager()
        if blur_threshold is not None:
            self.blur_threshold = blur_threshold
        else:
            val = self.database.get_setting("blur_threshold", "130.0")
            try:
                self.blur_threshold = float(val)
            except ValueError:
                self.blur_threshold = 130.0
        self.cancelled = False

    def cancel(self):
        self.cancelled = True

    def run(self):
        try:
            images = self.database.get_images()
            if not self.force_all:
                targets = [img for img in images if not img.get("quality_score")]
                if not targets:
                    targets = images
            else:
                targets = images

            total = len(targets)
            self.started_analysis.emit(total)

            blurry_count = 0
            crisp_count = 0

            for index, img in enumerate(targets, 1):
                if self.cancelled:
                    break

                path = img["path"]
                fname = img.get("filename", "")
                self.progress.emit(index, total, f"Evaluating {fname}…")

                res = assess_image_quality(path, self.blur_threshold)
                self.database.update_quality(
                    path,
                    res["combined_score"],
                    res["blur_score"],
                    res["brightness_score"],
                    res["contrast_score"],
                    res["is_blurry"],
                    res["explanation"],
                )
                self.image_analyzed.emit(path, res)

                if res["is_blurry"]:
                    blurry_count += 1
                elif res["combined_score"] >= 75.0:
                    crisp_count += 1

                if index % 10 == 0:
                    self.database.commit()

            self.database.commit()
            logger.info(f"Quality analysis complete: {total} scanned, {crisp_count} crisp, {blurry_count} blurry")

            self.completed.emit({
                "total": total,
                "blurry": blurry_count,
                "crisp": crisp_count,
                "cancelled": self.cancelled,
            })
        except Exception as e:
            logger.error(f"Quality worker failed: {e}")
            self.failed.emit(str(e))
