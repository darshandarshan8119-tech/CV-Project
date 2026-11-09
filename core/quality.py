"""Image quality, sharpness, blur, and exposure assessment service using OpenCV."""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Optional
import cv2
import numpy as np
from PIL import Image

DEFAULT_BLUR_THRESHOLD = 130.0


def assess_image_quality(
    image_path: str,
    blur_threshold: float = DEFAULT_BLUR_THRESHOLD,
) -> Dict[str, Any]:
    """
    Evaluate sharpness (Laplacian variance), exposure/brightness, and contrast using OpenCV.
    Returns scores scaled from 0.0 to 100.0, blur flag, and explanation.
    Never claims to use AI models; all scores are computed via deterministic CV heuristics.
    """
    path = Path(image_path)
    if not path.is_file():
        return {
            "combined_score": 0.0,
            "blur_score": 0.0,
            "brightness_score": 0.0,
            "contrast_score": 0.0,
            "laplacian_var": 0.0,
            "is_blurry": True,
            "explanation": "File could not be found on disk",
        }

    try:
        with Image.open(path) as pil_img:
            img_small = pil_img.copy()
            img_small.thumbnail((800, 800), Image.Resampling.BILINEAR)
            if img_small.mode != "RGB":
                img_small = img_small.convert("RGB")
            img_rgb = np.array(img_small)
    except Exception as e:
        return {
            "combined_score": 0.0,
            "blur_score": 0.0,
            "brightness_score": 0.0,
            "contrast_score": 0.0,
            "laplacian_var": 0.0,
            "is_blurry": True,
            "explanation": f"Unreadable image data ({e})",
        }

    if img_rgb is None or img_rgb.size == 0:
        return {
            "combined_score": 0.0,
            "blur_score": 0.0,
            "brightness_score": 0.0,
            "contrast_score": 0.0,
            "laplacian_var": 0.0,
            "is_blurry": True,
            "explanation": "Corrupted or empty image array",
        }

    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    total_pixels = gray.size

    # 1. Blur Score using Variance of Laplacian
    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    # Logarithmic normalization: var 50 -> ~25, 130 -> ~45, 500 -> ~70, 1500+ -> 85-100
    blur_score = min(100.0, max(0.0, (math.log10(max(lap_var, 1.0)) / 3.2) * 100.0))
    is_blurry = lap_var < blur_threshold

    # 2. Brightness Score (Luminance Mean & Clipping Penalty)
    mean_lum = float(np.mean(gray))
    # Distance from ideal midtone (~128)
    lum_dist = abs(mean_lum - 128.0) / 128.0  # 0.0 is perfect, 1.0 is extreme dark/white
    base_bright_score = max(0.0, 100.0 * (1.0 - lum_dist))

    # Penalize clipped shadows (<15) and blown highlights (>242)
    underexposed = float(np.sum(gray < 15)) / total_pixels
    overexposed = float(np.sum(gray > 242)) / total_pixels
    clipping_penalty = (underexposed * 1.5 + overexposed * 1.5) * 60.0
    brightness_score = max(0.0, min(100.0, base_bright_score - clipping_penalty))

    # 3. Contrast Score (Standard Deviation of Grayscale Luminance)
    std_dev = float(np.std(gray))
    # Optimal range for rich contrast is roughly 40 to 75
    if std_dev < 15.0:
        contrast_score = (std_dev / 15.0) * 40.0
    elif std_dev <= 75.0:
        contrast_score = 40.0 + ((std_dev - 15.0) / 60.0) * 60.0
    else:
        contrast_score = max(50.0, 100.0 - (std_dev - 75.0))

    # 4. Combined Quality Score (Weighted: Sharpness 45%, Contrast 30%, Brightness 25%)
    combined = (0.45 * blur_score) + (0.30 * contrast_score) + (0.25 * brightness_score)
    combined_score = round(combined, 1)

    # Explanation generator
    reasons = []
    if is_blurry:
        reasons.append(f"Soft/blurry edges (Laplacian var {int(lap_var)} < threshold {int(blur_threshold)})")
    else:
        reasons.append(f"Sharp details (Laplacian var {int(lap_var)})")

    if brightness_score >= 75.0:
        reasons.append("well-balanced exposure")
    elif underexposed > 0.20:
        reasons.append("underexposed shadows")
    elif overexposed > 0.20:
        reasons.append("clipped highlights")

    if contrast_score >= 75.0:
        reasons.append("rich dynamic contrast")
    elif contrast_score < 40.0:
        reasons.append("low contrast / flat tone")

    explanation = "; ".join(reasons)

    return {
        "combined_score": combined_score,
        "blur_score": round(blur_score, 1),
        "brightness_score": round(brightness_score, 1),
        "contrast_score": round(contrast_score, 1),
        "laplacian_var": round(lap_var, 1),
        "is_blurry": is_blurry,
        "explanation": explanation,
    }


def rank_group_photos(
    photos: List[Dict[str, Any]],
    blur_threshold: float = DEFAULT_BLUR_THRESHOLD,
) -> List[Dict[str, Any]]:
    """
    Rank photos within a burst or visually similar group from best to worst.
    Marks the highest quality photo with is_recommended=True and provides score comparison.
    """
    if not photos:
        return []

    ranked = []
    for p in photos:
        # Check if already scored, otherwise compute
        score = p.get("quality_score")
        if score is None or score == 0.0:
            analysis = assess_image_quality(p["path"], blur_threshold)
            p_copy = dict(p)
            p_copy["quality_score"] = analysis["combined_score"]
            p_copy["blur_score"] = analysis["blur_score"]
            p_copy["brightness_score"] = analysis["brightness_score"]
            p_copy["contrast_score"] = analysis["contrast_score"]
            p_copy["laplacian_var"] = analysis["laplacian_var"]
            p_copy["is_blurry"] = analysis["is_blurry"]
            p_copy["quality_explanation"] = analysis["explanation"]
        else:
            p_copy = dict(p)
        ranked.append(p_copy)

    # Sort descending by combined quality score
    ranked.sort(key=lambda x: x.get("quality_score", 0.0), reverse=True)

    for i, item in enumerate(ranked):
        item["rank_in_group"] = i + 1
        item["is_recommended"] = (i == 0)
        if i == 0:
            item["group_recommendation"] = (
                f"★ Recommended Best Shot: Score {int(item.get('quality_score', 0))}/100 "
                f"({item.get('quality_explanation', 'Top sharpness and balance')})"
            )
        else:
            diff = round(ranked[0].get("quality_score", 0.0) - item.get("quality_score", 0.0), 1)
            item["group_recommendation"] = f"Alternative copy ({diff} pts below recommended)"

    return ranked
