"""Local thumbnail generation and disk caching service."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageOps


def get_thumbnail_dir() -> Path:
    app_data = Path(os.environ.get("PIXORA_DATA_DIR", Path.home() / ".pixora"))
    thumb_dir = app_data / "thumbnails"
    thumb_dir.mkdir(parents=True, exist_ok=True)
    return thumb_dir


def _make_cache_key(image_path: str, size: Tuple[int, int]) -> str:
    path_obj = Path(image_path)
    try:
        mtime = path_obj.stat().st_mtime
    except OSError:
        mtime = 0
    raw = f"{image_path}_{mtime}_{size[0]}x{size[1]}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def get_cached_thumbnail_path(image_path: str, size: Tuple[int, int] = (240, 240)) -> Optional[Path]:
    """Check if a valid cached thumbnail exists on disk."""
    cache_key = _make_cache_key(image_path, size)
    thumb_file = get_thumbnail_dir() / f"{cache_key}.jpg"
    if thumb_file.is_file() and thumb_file.stat().st_size > 0:
        return thumb_file
    return None


def generate_thumbnail(
    image_path: str,
    size: Tuple[int, int] = (240, 240),
) -> Optional[Path]:
    """
    Generate and cache a thumbnail for an image.
    Never modifies the original photo.
    Returns path to the cached JPEG thumbnail, or None if image is unreadable.
    """
    cached = get_cached_thumbnail_path(image_path, size)
    if cached:
        return cached

    src_path = Path(image_path)
    if not src_path.is_file():
        return None

    try:
        with Image.open(src_path) as img:
            # Handle EXIF orientation automatically
            img = ImageOps.exif_transpose(img)
            img.thumbnail(size, Image.Resampling.LANCZOS)
            if img.mode in ("RGBA", "P", "LA"):
                img = img.convert("RGB")

            cache_key = _make_cache_key(image_path, size)
            target = get_thumbnail_dir() / f"{cache_key}.jpg"
            img.save(str(target), "JPEG", quality=85, optimize=True)
            return target
    except Exception:
        return None

