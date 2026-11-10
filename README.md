# Pixora — AI-Powered Smart Photo Studio

Pixora is a private, local-first desktop photo studio built with **Python**, **PySide6 (Qt)**, **OpenCV**, and **Pillow**. All scanning, indexing, categorization, quality scoring, and image enhancements run **100% locally** on your computer. Original images are kept strictly **read-only** and are never modified, overwritten, or uploaded.

---

## Workspaces & Capabilities

### 1. Home (Dashboard)
- Real-time library metric cards (Library Photos, Last Import, Duplicate Sets, Review Needed).
- One-click recursive folder import with live progress feedback.
- Persistent local SQLite index storing photo dimensions, sizes, and timestamps.

### 2. My Gallery
- **Responsive Layout**: High-density grid and clean list view with a live view mode toggle.
- **Lazy Thumbnail Generator & Disk Cache**: Background worker generates and caches thumbnails to `.pixora/thumbnails/`.
- **Search & Filter**: Real-time filename search bar and multi-attribute sorting (Newest, Oldest, Name A–Z / Z–A, Size).
- **Full-Resolution Preview Modal**: Aspect-ratio preserving preview with metadata badges, "Reveal in Explorer", and direct "Enhance in Studio" handoff.

### 3. Smart Categories (Local Heuristics)
- **Zero External AI Downloads**: Classifies photos offline using deterministic computer vision heuristics (OpenCV Haar cascades for faces and pets, HSV color distribution, and aspect ratios).
- **Supported Categories**: `Selfies`, `Nature`, `Food`, `Animals`, `Documents`, `Screenshots`, `Travel`, `Objects`, and `Other`.
- **Interactive Badges**: Category cards with live counts and filtered photo views.
- **Background Worker**: Multi-threaded execution with visible progress and cancel support.

### 4. Duplicate Finder & Similar Photos
- **Duplicate Finder**: Cryptographic **SHA-256** checksum matching to detect 100% byte-for-byte exact duplicate copies.
- **Similar Photos**: Perceptual hashing (**pHash**) with Hamming distance clustering to detect visually similar images, burst photos, and re-encoded copies.
- **Side-by-Side Review**: Group cards with similarity badges, metadata, and safe read-only file handling.

### 5. Best Shots & Blur Detection
- **Deterministic Quality Scoring (OpenCV)**:
  - Sharpness score using variance of Laplacian.
  - Brightness & exposure score evaluating mid-tone balance and clipping penalties.
  - Dynamic contrast score.
  - Combined overall quality score (0–100) with human-readable explanations.
- **Filters**: "All Rated Photos", "Top Picks (Crisp Quality)", and "Needs Review (Blurry / Soft)".
- **Burst / Similar Group Best Shot**: Automatically ranks photos within similar groups and marks the top-recommended shot with score comparisons.

### 6. Image Enhancer Studio
- **Interactive Before/After Split Slider**: Real-time draggable divider overlaying both original and enhanced images for side-by-side comparison.
- **Local Non-Destructive Operations**:
  - Brightness (-100 to +100) & Contrast (-100 to +100).
  - Saturation (-100 to +100) & Color Warmth (-100 to +100).
  - Bilateral edge-preserving denoising (0 to 100).
  - Unsharp masking sharpness (0 to 100).
  - High-fidelity **Lanczos-4** super-sampling upscaling (1.0×, 1.5×, 2.0×, 4.0×).
- **Curated Presets**: "Auto Magic" (CLAHE + vibrance), "Vibrant Landscape", "Portrait Glow", "B&W Film".
- **Interactive Live Preview**: Split view comparing enhanced image against original with smooth handle drag.
- **Safe Export**: Saves copies exclusively to the configured `processed/` directory with collision-resistant naming (original photos are never touched).

---

## Premium UI/UX & Motion Design System
Pixora features a commercial creative-software aesthetic inspired by modern design systems:
- **Obsidian Dark & Titanium Light Themes**: Deep charcoal background (`#090A0F`), translucent glassmorphic panels (`rgba(20,23,34,0.78)`), and electric-violet accents (`#7C6CFF`).
- **Animated Page Transitions**: `AnimatedStackedWidget` with cross-fade opacity and subtle slide easing (`QEasingCurve.OutCubic`, 200ms).
- **Animated Numeric Counters**: `NumberCounter` smoothly counts up dashboard metrics on data import.
- **Micro-Interaction Hover Effects**: `HoverLiftFilter` providing ambient drop shadows and tactile lift on cards, badges, and buttons.
- **Interactive Before/After Split Comparison Slider**: Custom `BeforeAfterSliderWidget` with smooth drag physics, circular glowing thumb, and dynamic label badges.
- **Modern Control Elements**: Slim custom scrollbars, glowing slider thumbs, pill status tags, and segmented filter buttons.

### 7. Recently Processed
- Centralized gallery of all enhanced and exported photos.
- Displays output resolution, size, source file path, and export timestamp.
- Direct "Open Image" and "Reveal in Explorer" actions.

### 8. Settings & Privacy
- Theme toggle: Dark mode & Light mode.
- Configurable processed output folder.
- Configurable blur threshold (Laplacian variance cutoff, default 130).
- "View Application Logs" shortcut (`.pixora/pixora.log`).
- "Clear Local Index" action with confirmation safety dialog.

---

## Supported File Formats

Pixora supports standard local image formats:
- **JPEG / JPG** (`.jpg`, `.jpeg`)
- **PNG** (`.png`)
- **WebP** (`.webp`)
- **Bitmap** (`.bmp`)
- **TIFF** (`.tif`, `.tiff`)
- **GIF** (`.gif`)

---

## Getting Started

### 1. Prerequisites & Virtual Environment

Ensure you have Python 3.10+ installed.

```powershell
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
python -m pip install -r requirements.txt
```

### 2. Launch Pixora

```powershell
python main.py
```

### 3. Run Validation & Smoke Tests

Run the built-in automated test suite:

```powershell
python tests/smoke_test.py
```

---

## Standalone Windows Packaging (PyInstaller)

To build a standalone Windows `.exe` application bundle:

```powershell
# Install PyInstaller
python -m pip install pyinstaller

# Build using the included pixora.spec
pyinstaller --clean pixora.spec
```

The resulting executable will be generated in `dist/Pixora/Pixora.exe`.

---

## Phase Status Summary

- [x] **Phase 1** — Polished desktop interface, semantic tokens, and navigation shell
- [x] **Phase 2** — Recursive folder scanning, SQLite persistence, and import worker
- [x] **Phase 3** — Responsive gallery workspace, lazy thumbnails, search, sort, and preview modal
- [x] **Phase 4** — Smart Categories with local heuristic classification and background workers
- [x] **Phase 5** — Exact duplicate (SHA-256) and visual similarity (pHash) detection
- [x] **Phase 6** — Quality scoring, blur detection, and burst set best shot recommendation
- [x] **Phase 7** — Image Enhancer Studio with local filters, CLAHE, Lanczos scaling, and safe export
- [x] **Production Readiness** — Settings page, logging, migrations, PyInstaller spec, and 100% test pass
