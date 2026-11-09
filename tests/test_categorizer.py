"""Unit tests for local heuristic categorizer."""
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PIL import Image, ImageDraw
from core.categorizer import classify_image


def test_categorizer_heuristics():
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Document canvas (high white area with black text lines)
        doc_path = Path(tmpdir) / "doc_test.png"
        doc_img = Image.new("RGB", (600, 800), color=(250, 250, 250))
        draw = ImageDraw.Draw(doc_img)
        for y in range(80, 720, 25):
            draw.line([(60, y), (540, y)], fill=(20, 20, 20), width=3)
        doc_img.save(str(doc_path))

        cat, conf, reason = classify_image(str(doc_path))
        assert cat in ("Documents", "Screenshots")
        assert conf > 0.6

        # 2. Nature canvas (Green bottom half, blue top half)
        nat_path = Path(tmpdir) / "nature_test.jpg"
        nat_img = Image.new("RGB", (800, 500), color=(34, 139, 34))  # Forest green
        draw = ImageDraw.Draw(nat_img)
        draw.rectangle([(0, 0), (800, 200)], fill=(70, 130, 180))  # Steel blue sky
        nat_img.save(str(nat_path))

        cat, conf, reason = classify_image(str(nat_path))
        assert cat == "Nature"
        assert conf >= 0.7

        # 3. Screenshot filename heuristic
        scr_path = Path(tmpdir) / "Screenshot_2026-11-09.png"
        Image.new("RGB", (100, 100), color=(50, 50, 50)).save(str(scr_path))
        cat, conf, reason = classify_image(str(scr_path))
        assert cat == "Screenshots"
        assert conf >= 0.9

        # 4. Food filename heuristic
        food_path = Path(tmpdir) / "delicious_recipe_dinner.jpg"
        Image.new("RGB", (100, 100), color=(200, 80, 30)).save(str(food_path))
        cat, conf, reason = classify_image(str(food_path))
        assert cat == "Food"
        assert conf >= 0.8
