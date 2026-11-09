"""Local non-destructive photo enhancement and upscaling engine using OpenCV and NumPy."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import cv2
import numpy as np
from PIL import Image

from core.logger import logger


def enhance_photo(
    image_rgb: np.ndarray,
    brightness: int = 0,    # -100 to 100
    contrast: int = 0,      # -100 to 100
    saturation: int = 0,    # -100 to 100
    sharpness: int = 0,     # 0 to 100
    denoise: int = 0,       # 0 to 100
    warmth: int = 0,        # -100 to 100
    scale_factor: float = 1.0,  # 1.0, 1.5, 2.0, 4.0
) -> np.ndarray:
    """Apply non-destructive image enhancements and optional Lanczos scaling."""
    res = image_rgb.copy()

    # 1. Denoising (Bilateral filtering for edge-preserving smoothness)
    if denoise > 0:
        d = int(5 + (denoise / 100.0) * 8)
        sigma = 15 + (denoise / 100.0) * 45
        res = cv2.bilateralFilter(res, d, sigma, sigma)

    # 2. Brightness & Contrast
    if brightness != 0 or contrast != 0:
        alpha = 1.0 + (contrast / 100.0) * 0.8
        beta = (brightness / 100.0) * 70.0
        res = cv2.convertScaleAbs(res, alpha=alpha, beta=beta)

    # 3. Saturation & Warmth
    if saturation != 0 or warmth != 0:
        hsv = cv2.cvtColor(res, cv2.COLOR_RGB2HSV).astype(np.float32)
        if saturation != 0:
            sat_factor = 1.0 + (saturation / 100.0) * 0.9
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * sat_factor, 0, 255)

        res = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)

        if warmth != 0:
            shift = int((warmth / 100.0) * 35.0)
            r = np.clip(res[:, :, 0].astype(np.int16) + shift, 0, 255).astype(np.uint8)
            b = np.clip(res[:, :, 2].astype(np.int16) - shift, 0, 255).astype(np.uint8)
            res[:, :, 0] = r
            res[:, :, 2] = b

    # 4. Sharpening (Unsharp masking)
    if sharpness > 0:
        amount = (sharpness / 100.0) * 1.5
        gaussian = cv2.GaussianBlur(res, (0, 0), 2.0)
        sharpened = cv2.addWeighted(res, 1.0 + amount, gaussian, -amount, 0)
        res = np.clip(sharpened, 0, 255).astype(np.uint8)

    # 5. Scaling / Super-sampling using Lanczos
    if scale_factor > 1.0:
        new_w = int(res.shape[1] * scale_factor)
        new_h = int(res.shape[0] * scale_factor)
        res = cv2.resize(res, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

    return res


def apply_preset(image_rgb: np.ndarray, preset_name: str) -> np.ndarray:
    """Apply a curated local enhancement style preset."""
    name = preset_name.lower().replace(" ", "_")

    if name in ("magic_auto", "magic", "auto_magic"):
        lab = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl, a, b))
        enhanced = cv2.cvtColor(limg, cv2.COLOR_LAB2RGB)
        return enhance_photo(enhanced, brightness=5, contrast=10, saturation=15, sharpness=25)

    if name in ("vibrant_landscape", "landscape"):
        return enhance_photo(image_rgb, brightness=5, contrast=20, saturation=35, sharpness=30, warmth=5)

    if name in ("portrait_glow", "portrait"):
        return enhance_photo(image_rgb, brightness=10, contrast=5, saturation=10, denoise=30, warmth=15)

    if name in ("crisp_details", "crisp"):
        return enhance_photo(image_rgb, brightness=0, contrast=25, saturation=5, sharpness=60, denoise=15)

    if name in ("bw_film", "black_and_white"):
        gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        eq = clahe.apply(gray)
        return cv2.cvtColor(eq, cv2.COLOR_GRAY2RGB)

    return image_rgb


def save_enhanced_image(
    source_path: str,
    enhanced_rgb: np.ndarray,
    output_dir: str = "processed",
    custom_filename: Optional[str] = None,
) -> Path:
    """
    Save enhanced image to the processed output directory.
    Original source photo is NEVER modified or overwritten.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    src = Path(source_path)
    if custom_filename:
        base_name = custom_filename if custom_filename.lower().endswith((".jpg", ".jpeg", ".png")) else f"{custom_filename}.jpg"
    else:
        base_name = f"enhanced_{src.stem}.jpg"

    target_path = out_dir / base_name

    # If target already exists, append unique counter to prevent overwriting
    counter = 1
    stem = Path(base_name).stem
    suffix = Path(base_name).suffix or ".jpg"
    while target_path.exists():
        target_path = out_dir / f"{stem}_{counter}{suffix}"
        counter += 1

    # Save via Pillow with high quality
    pil_img = Image.fromarray(enhanced_rgb)
    format_name = "PNG" if target_path.suffix.lower() == ".png" else "JPEG"
    if format_name == "JPEG":
        pil_img.save(str(target_path), format_name, quality=94, optimize=True)
    else:
        pil_img.save(str(target_path), format_name, optimize=True)

    logger.info(f"Enhanced image saved safely to: {target_path} (original untouched)")
    return target_path
