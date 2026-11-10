"""Unit tests for non-destructive local image enhancer and upscaler."""
import hashlib
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
from PIL import Image

from core.enhancer import apply_preset, enhance_photo, save_enhanced_image


def test_enhancement_operations_and_scaling():
    # Create test 100x100 RGB image array
    test_arr = np.full((100, 100, 3), 128, dtype=np.uint8)

    # 1. Adjustments
    enhanced = enhance_photo(
        test_arr,
        brightness=20,
        contrast=10,
        saturation=15,
        sharpness=30,
        denoise=10,
        warmth=10,
        scale_factor=1.0,
    )
    assert enhanced.shape == (100, 100, 3)
    assert not np.array_equal(enhanced, test_arr)

    # 2. Lanczos super-sampling scaling (2.0x)
    scaled_2x = enhance_photo(test_arr, scale_factor=2.0)
    assert scaled_2x.shape == (200, 200, 3)

    # 3. Presets
    preset_arr = apply_preset(test_arr, "magic_auto")
    assert preset_arr.shape == (100, 100, 3)


def test_non_destructive_export_and_non_overwrite():
    with tempfile.TemporaryDirectory() as tmpdir:
        src_path = Path(tmpdir) / "original_photo.jpg"
        img = Image.new("RGB", (250, 200), color=(100, 150, 200))
        img.save(str(src_path), "JPEG")

        # Record hash of original
        with open(src_path, "rb") as f:
            orig_hash = hashlib.sha256(f.read()).hexdigest()

        # Perform enhancement export
        out_dir = Path(tmpdir) / "output"
        enhanced_data = np.full((200, 250, 3), 180, dtype=np.uint8)

        out_1 = save_enhanced_image(str(src_path), enhanced_data, output_dir=str(out_dir))
        assert out_1.is_file()
        assert out_1.name == "enhanced_original_photo.jpg"

        # Export again -> must not overwrite, must append counter
        out_2 = save_enhanced_image(str(src_path), enhanced_data, output_dir=str(out_dir))
        assert out_2.is_file()
        assert out_2.name == "enhanced_original_photo_1.jpg"
        assert out_1 != out_2

        # Verify original source photo is 100% untouched
        with open(src_path, "rb") as f:
            final_hash = hashlib.sha256(f.read()).hexdigest()
        assert orig_hash == final_hash

