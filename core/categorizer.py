"""Local heuristic image categorizer using OpenCV, Pillow, and color/geometry rules."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional, Tuple
import cv2
import numpy as np
from PIL import Image

CATEGORIES = [
    "Selfies",
    "Nature",
    "Food",
    "Animals",
    "Documents",
    "Screenshots",
    "Travel",
    "Objects",
    "Other",
]

# Load built-in OpenCV Haar cascades
FACE_CASCADE: Optional[cv2.CascadeClassifier] = None
CAT_CASCADE: Optional[cv2.CascadeClassifier] = None

try:
    face_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    if os.path.exists(face_path):
        FACE_CASCADE = cv2.CascadeClassifier(face_path)
except Exception:
    FACE_CASCADE = None

try:
    cat_path = cv2.data.haarcascades + "haarcascade_frontalcatface.xml"
    if os.path.exists(cat_path):
        CAT_CASCADE = cv2.CascadeClassifier(cat_path)
except Exception:
    CAT_CASCADE = None


def classify_image(image_path: str) -> Tuple[str, float, str]:
    """
    Classify an image using local heuristics (color histograms, geometry, edges, Haar cascades).
    Returns (category, confidence, explanation).
    Never raises an uncaught exception on corrupt/unreadable files.
    """
    path = Path(image_path)
    if not path.is_file():
        return "Other", 0.0, "File not found"

    fname_lower = path.name.lower()

    # 1. Filename heuristic shortcuts
    if any(k in fname_lower for k in ["screenshot", "screen shot", "snip", "scr_"]):
        return "Screenshots", 0.95, "Filename indicates a captured screenshot"

    if any(k in fname_lower for k in ["receipt", "invoice", "scan", "document", "doc_"]):
        return "Documents", 0.92, "Filename indicates scanned document or receipt"

    if any(k in fname_lower for k in ["selfie", "portrait"]):
        return "Selfies", 0.90, "Filename indicates selfie or portrait"

    if any(k in fname_lower for k in ["food", "meal", "dinner", "lunch", "breakfast", "dish", "cake", "recipe"]):
        return "Food", 0.88, "Filename indicates food or culinary photo"

    if any(k in fname_lower for k in ["pet", "cat", "dog", "puppy", "kitten", "bird", "animal"]):
        return "Animals", 0.88, "Filename indicates animal or pet"

    if any(k in fname_lower for k in ["travel", "trip", "vacation", "holiday", "beach", "mountain"]):
        return "Travel", 0.85, "Filename indicates travel or landmark"

    # 2. Read image with OpenCV for visual analysis
    try:
        # Read as small resolution for lightning-fast analysis (max 640px)
        with Image.open(path) as pil_img:
            w, h = pil_img.size
            # Convert to small RGB array
            pil_small = pil_img.copy()
            pil_small.thumbnail((640, 640), Image.Resampling.BILINEAR)
            if pil_small.mode != "RGB":
                pil_small = pil_small.convert("RGB")
            img_rgb = np.array(pil_small)
    except Exception as e:
        return "Other", 0.0, f"Unreadable image: {e}"

    if img_rgb is None or img_rgb.size == 0:
        return "Other", 0.0, "Empty image data"

    aspect_ratio = w / max(h, 1)
    img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
    img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    img_hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)

    total_pixels = img_rgb.shape[0] * img_rgb.shape[1]

    # Check 1: Document Heuristic (Bimodal grayscale, high white background, low saturation)
    mean_val = float(np.mean(img_gray))
    std_val = float(np.std(img_gray))
    mean_sat = float(np.mean(img_hsv[:, :, 1]))
    white_fraction = float(np.sum(img_gray > 200)) / total_pixels

    if white_fraction > 0.45 and mean_sat < 40 and 0.65 < aspect_ratio < 1.6:
        # Likely a document, paper, or text scan
        return "Documents", 0.82, "High white-background ratio with low color saturation"

    # Check 2: Screenshot Heuristic (Standard aspect ratio, sharp line UI, PNG/uniform areas)
    is_standard_display = any(
        abs(aspect_ratio - target) < 0.05
        for target in [16 / 9, 16 / 10, 4 / 3, 9 / 16, 9 / 19.5, 9 / 20]
    )
    if is_standard_display and (path.suffix.lower() == ".png" or "trashed" in fname_lower):
        # Measure edges: screenshots typically have sharp horizontal & vertical UI elements
        edges = cv2.Canny(img_gray, 50, 150)
        edge_density = float(np.sum(edges > 0)) / total_pixels
        if 0.03 < edge_density < 0.25 and (white_fraction > 0.35 or mean_sat < 65):
            return "Screenshots", 0.78, "Display aspect ratio with UI edge profile"

    # Check 3: Face / Selfie Detection via OpenCV Haar Cascade
    if FACE_CASCADE is not None:
        faces = FACE_CASCADE.detectMultiScale(img_gray, scaleFactor=1.15, minNeighbors=5, minSize=(60, 60))
        if len(faces) > 0:
            # Check if face is prominent
            largest_face = max(faces, key=lambda f: f[2] * f[3])
            face_area_ratio = (largest_face[2] * largest_face[3]) / total_pixels
            if face_area_ratio >= 0.08:
                return "Selfies", min(0.92, 0.70 + face_area_ratio), f"Frontal face detected ({int(face_area_ratio*100)}% of frame)"

    # Check 4: Cat / Pet Detection via Haar Cascade
    if CAT_CASCADE is not None:
        cats = CAT_CASCADE.detectMultiScale(img_gray, scaleFactor=1.2, minNeighbors=4, minSize=(50, 50))
        if len(cats) > 0:
            return "Animals", 0.75, "Pet facial features detected"

    # Check 5: Nature Heuristic (Green vegetation + Blue sky)
    # Hue ranges in OpenCV: 0-180. Green is approx 35-85, Blue is 90-130
    h_channel = img_hsv[:, :, 0]
    s_channel = img_hsv[:, :, 1]
    green_mask = (h_channel >= 35) & (h_channel <= 85) & (s_channel >= 40)
    green_ratio = float(np.sum(green_mask)) / total_pixels

    # Upper 40% for sky
    upper_h = int(img_hsv.shape[0] * 0.4)
    sky_mask = (
        (h_channel[:upper_h, :] >= 90)
        & (h_channel[:upper_h, :] <= 135)
        & (s_channel[:upper_h, :] >= 30)
    )
    sky_ratio = float(np.sum(sky_mask)) / (upper_h * img_hsv.shape[1])

    if green_ratio > 0.25:
        confidence = min(0.90, 0.65 + green_ratio)
        return "Nature", confidence, f"Vegetation/greenery dominant ({int(green_ratio*100)}% coverage)"

    if green_ratio > 0.12 and sky_ratio > 0.20:
        return "Nature", 0.80, f"Outdoor greenery ({int(green_ratio*100)}%) and sky detected"

    # Check 6: Food Heuristic (Warm appetizing colors: Red, Orange, Yellow + high saturation)
    warm_mask = ((h_channel <= 25) | (h_channel >= 165)) & (s_channel >= 70)
    warm_ratio = float(np.sum(warm_mask)) / total_pixels

    if warm_ratio > 0.35 and mean_sat > 80:
        return "Food", 0.76, f"Warm culinary color palette ({int(warm_ratio*100)}% warm hues)"

    # Check 7: Travel / Landscapes (Wide ratio, sky, structures)
    if aspect_ratio >= 1.3 and sky_ratio > 0.25:
        return "Travel", 0.72, "Wide scenic horizon with open sky"

    # Check 8: Objects (Centered subject with distinct background contrast)
    center_y, center_x = img_gray.shape[0] // 2, img_gray.shape[1] // 2
    box_h, box_w = img_gray.shape[0] // 4, img_gray.shape[1] // 4
    center_roi = img_gray[center_y - box_h : center_y + box_h, center_x - box_w : center_x + box_w]
    if center_roi.size > 0:
        center_std = float(np.std(center_roi))
        border_std = (float(np.std(img_gray[:30, :])) + float(np.std(img_gray[-30:, :]))) / 2.0
        if center_std > 40 and border_std < 25:
            return "Objects", 0.68, "Centered subject with uniform background"

    return "Other", 0.50, "General image, no dominant heuristic match"

