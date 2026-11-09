"""Unit tests for exact duplicate and similarity grouping."""
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PIL import Image
from core.duplicates import (
    compute_file_sha256,
    compute_image_phash,
    find_similarity_clusters,
    hamming_distance,
)


def test_duplicates_and_similarity():
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Exact duplicate files
        f1 = Path(tmpdir) / "original.jpg"
        f2 = Path(tmpdir) / "copy.jpg"
        img = Image.new("RGB", (200, 200), color=(120, 100, 80))
        img.save(str(f1), "JPEG")

        # Copy byte-for-byte
        with open(f1, "rb") as src, open(f2, "wb") as dst:
            dst.write(src.read())

        sha1 = compute_file_sha256(str(f1))
        sha2 = compute_file_sha256(str(f2))
        assert sha1 is not None and sha2 is not None
        assert sha1 == sha2

        # 2. Similar image (slightly changed pixel)
        f3 = Path(tmpdir) / "similar.jpg"
        img3 = Image.new("RGB", (200, 200), color=(122, 100, 80))
        img3.save(str(f3), "JPEG")

        ph1 = compute_image_phash(str(f1))
        ph3 = compute_image_phash(str(f3))
        assert ph1 is not None and ph3 is not None

        dist = hamming_distance(ph1, ph3)
        assert dist <= 4  # Very close perceptual hash

        # 3. Test cluster assignment
        items = [
            {"path": str(f1), "sha256": sha1, "phash": ph1},
            {"path": str(f3), "sha256": "different_sha", "phash": ph3},
        ]
        clusters = find_similarity_clusters(items, max_distance=6)
        assert len(clusters) == 2
        assert clusters[str(f1)] == clusters[str(f3)]
