"""Unit tests for thumbnail generation and caching."""
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PIL import Image
from core.thumbnails import generate_thumbnail, get_cached_thumbnail_path


def test_thumbnail_generation_and_caching():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "source.jpg"
        img = Image.new("RGB", (800, 600), color=(100, 150, 200))
        img.save(str(src), "JPEG")

        # Initial generation
        thumb = generate_thumbnail(str(src), size=(120, 120))
        assert thumb is not None
        assert thumb.is_file()

        # Cached lookup
        cached = get_cached_thumbnail_path(str(src), size=(120, 120))
        assert cached is not None
        assert cached == thumb

        # Verify source untouched
        assert src.is_file()
        with Image.open(src) as reopened:
            assert reopened.size == (800, 600)
