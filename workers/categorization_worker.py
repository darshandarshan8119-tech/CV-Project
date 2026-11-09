"""Background worker for local image categorization."""
from __future__ import annotations

from typing import List, Optional
from PySide6.QtCore import QThread, Signal

from core.categorizer import classify_image
from database.db_manager import DatabaseManager


class CategorizationWorker(QThread):
    started_categorization = Signal(int)
    progress = Signal(int, int, str)
    image_categorized = Signal(str, str, float, str)
    completed = Signal(dict)
    failed = Signal(str)

    def __init__(self, force_all: bool = False, database: Optional[DatabaseManager] = None):
        super().__init__()
        self.force_all = force_all
        self.database = database or DatabaseManager()
        self.cancelled = False

    def cancel(self):
        self.cancelled = True

    def run(self):
        try:
            images = self.database.get_images()
            if not self.force_all:
                # Prioritize images that haven't been categorized or are 'Other'
                targets = [img for img in images if not img.get("category_confidence")]
                if not targets:
                    targets = images
            else:
                targets = images

            total = len(targets)
            self.started_categorization.emit(total)

            categorized_count = 0
            for index, img in enumerate(targets, 1):
                if self.cancelled:
                    break

                path = img["path"]
                fname = img.get("filename", "")
                self.progress.emit(index, total, fname)

                category, confidence, reason = classify_image(path)
                self.database.update_category(path, category, confidence, reason)
                self.image_categorized.emit(path, category, confidence, reason)
                categorized_count += 1

                # Periodic commit every 10 images
                if index % 10 == 0:
                    self.database.commit()

            self.database.commit()
            self.completed.emit({
                "total": total,
                "categorized": categorized_count,
                "cancelled": self.cancelled,
            })
        except Exception as e:
            self.failed.emit(str(e))

