"""Local image discovery and metadata extraction service."""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Set

import imagehash
from PIL import ExifTags, Image

SUPPORTED_EXTENSIONS: Set[str] = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
    ".tiff",
    ".tif",
    ".gif",
}


def is_supported_image(path: Path | str) -> bool:
    """Check if the file has a supported image extension."""
    return Path(path).suffix.lower() in SUPPORTED_EXTENSIONS


def discover_image_files(root_dir: Path | str) -> List[Path]:
    """Recursively discover all supported image file paths in a directory."""
    root = Path(root_dir)
    if not root.is_dir():
        return []

    discovered: List[Path] = []
    for dirpath, _, filenames in os.walk(root):
        dir_path = Path(dirpath)
        for fname in filenames:
            file_path = dir_path / fname
            if is_supported_image(file_path):
                discovered.append(file_path)

    return sorted(discovered)


def get_exif_date_taken(img: Image.Image) -> Optional[str]:
    """Extract EXIF capture date if present."""
    try:
        exif = img.getexif()
        if not exif:
            return None

        # Tag 36867 is DateTimeOriginal, 306 is DateTime
        for tag_id in (36867, 306):
            if tag_id in exif and exif[tag_id]:
                return str(exif[tag_id]).strip()

        # Check IFD (Exif sub-dictionary)
        if hasattr(exif, "get_ifd"):
            exif_ifd = exif.get_ifd(0x8769)
            if 36867 in exif_ifd and exif_ifd[36867]:
                return str(exif_ifd[36867]).strip()
    except Exception:
        pass
    return None


def extract_metadata(file_path: Path | str, compute_hash: bool = True) -> Optional[Dict[str, Any]]:
    """
    Read an image file and extract dimension, format, EXIF, and perceptual hash.
    Returns None if the image is corrupted or cannot be read.
    """
    path = Path(file_path)
    try:
        stat = path.stat()
        file_size = stat.st_size
        modified_at = stat.st_mtime

        with Image.open(path) as img:
            width, height = img.size
            img_format = img.format or path.suffix.lstrip(".").upper()
            mode = img.mode
            date_taken = get_exif_date_taken(img)

            dhash_str: Optional[str] = None
            if compute_hash:
                try:
                    dhash_str = str(imagehash.dhash(img))
                except Exception:
                    dhash_str = None

        return {
            "path": str(path.resolve()),
            "filename": path.name,
            "size": file_size,
            "width": width,
            "height": height,
            "format": img_format,
            "color_mode": mode,
            "date_taken": date_taken,
            "modified_at": modified_at,
            "imported_at": time.time(),
            "dhash": dhash_str,
        }
    except Exception:
        return None

