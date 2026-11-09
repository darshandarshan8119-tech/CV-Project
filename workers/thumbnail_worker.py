"""Background thread for lazy generation of image thumbnails."""
from __future__ import annotations

import queue
from pathlib import Path
from typing import List, Optional
from PySide6.QtCore import QThread, Signal

from core.thumbnails import generate_thumbnail, get_cached_thumbnail_path


class ThumbnailWorker(QThread):
    thumbnail_ready = Signal(str, str)  # (original_path, cached_thumbnail_path)
    finished = Signal()

    def __init__(self, paths: Optional[List[str]] = None):
        super().__init__()
        self.queue: queue.Queue[str] = queue.Queue()
        self.cancelled = False
        if paths:
            for p in paths:
                self.queue.put(p)

    def add_path(self, path: str):
        self.queue.put(path)

    def cancel(self):
        self.cancelled = True

    def run(self):
        while not self.queue.empty() and not self.cancelled:
            try:
                img_path = self.queue.get_nowait()
            except queue.Empty:
                break

            # Check if cached first without re-generating
            thumb = get_cached_thumbnail_path(img_path)
            if not thumb:
                thumb = generate_thumbnail(img_path)

            if thumb:
                self.thumbnail_ready.emit(img_path, str(thumb))

        self.finished.emit()

