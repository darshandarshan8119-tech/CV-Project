"""Non-blocking, local-only folder scanner."""
from pathlib import Path
from PIL import Image, UnidentifiedImageError
from PySide6.QtCore import QThread, Signal

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".gif"}


class ScanningWorker(QThread):
    progress = Signal(int, int)
    image_found = Signal(dict)
    started_scan = Signal(int)
    completed = Signal(dict)
    failed = Signal(str)

    def __init__(self, folder: str):
        super().__init__()
        self.folder = Path(folder)
        self.cancelled = False

    def cancel(self):
        self.cancelled = True

    def run(self):
        try:
            files = [path for path in self.folder.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS]
            self.started_scan.emit(len(files))
            imported = 0
            for index, path in enumerate(files, 1):
                if self.cancelled:
                    break
                try:
                    with Image.open(path) as image:
                        width, height = image.size
                    stat = path.stat()
                    self.image_found.emit({"path": str(path), "folder": str(self.folder), "filename": path.name,
                                           "width": width, "height": height, "size_bytes": stat.st_size, "modified_at": stat.st_mtime})
                    imported += 1
                except (UnidentifiedImageError, OSError):
                    pass
                self.progress.emit(index, len(files))
            self.completed.emit({"discovered": len(files), "imported": imported, "skipped": len(files) - imported, "cancelled": self.cancelled})
        except OSError as error:
            self.failed.emit(str(error))
