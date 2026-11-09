"""Unit tests for OpenCV quality, sharpness, blur, and group ranking."""
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from core.quality import assess_image_quality, rank_group_photos


def test_sharpness_and_blur_detection():
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Create artificial high-contrast sharp checkerboard
        sharp_path = Path(tmpdir) / "sharp.jpg"
        sharp_img = Image.new("RGB", (400, 400), color=(255, 255, 255))
        draw = ImageDraw.Draw(sharp_img)
        for y in range(0, 400, 20):
            for x in range(0, 400, 20):
                if (x + y) % 40 == 0:
                    draw.rectangle([x, y, x + 20, y + 20], fill=(0, 0, 0))
        sharp_img.save(str(sharp_path), "JPEG")

        # 2. Create heavy blurred copy
        blur_path = Path(tmpdir) / "blurry.jpg"
        blur_img = sharp_img.filter(ImageFilter.GaussianBlur(radius=10))
        blur_img.save(str(blur_path), "JPEG")

        # Evaluate quality
        sharp_res = assess_image_quality(str(sharp_path), blur_threshold=130.0)
        blur_res = assess_image_quality(str(blur_path), blur_threshold=130.0)

        assert sharp_res["is_blurry"] is False
        assert sharp_res["laplacian_var"] > 500.0
        assert sharp_res["combined_score"] > 60.0

        assert blur_res["is_blurry"] is True
        assert blur_res["laplacian_var"] < 50.0
        assert blur_res["combined_score"] < sharp_res["combined_score"]


def test_similar_group_ranking():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create 3 variation images with different blur radii
        base = Image.new("RGB", (300, 300), color=(200, 200, 200))
        draw = ImageDraw.Draw(base)
        for i in range(20, 280, 20):
            draw.line([(i, 20), (i, 280)], fill=(10, 10, 10), width=4)

        paths = []
        for idx, radius in enumerate([0, 4, 8]):
            p = Path(tmpdir) / f"var_{idx}.jpg"
            img = base if radius == 0 else base.filter(ImageFilter.GaussianBlur(radius))
            img.save(str(p), "JPEG")
            paths.append(str(p))

        mock_group = [
            {"path": paths[1], "filename": "var_1.jpg"},
            {"path": paths[0], "filename": "var_0.jpg"},
            {"path": paths[2], "filename": "var_2.jpg"},
        ]

        ranked = rank_group_photos(mock_group, blur_threshold=130.0)
        assert len(ranked) == 3
        # var_0 (unblurred) should be #1 recommended
        assert ranked[0]["path"] == paths[0]
        assert ranked[0]["is_recommended"] is True
        assert "Recommended Best Shot" in ranked[0]["group_recommendation"]
        assert ranked[1]["is_recommended"] is False
        assert ranked[2]["is_recommended"] is False
