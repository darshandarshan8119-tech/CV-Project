# Pixora — AI-Powered Smart Photo Studio

Pixora is a private, local-first desktop photo studio built with **Python** and **PySide6**. All scanning, indexing, categorization, and duplicate detection run 100% locally on your computer. Original images are kept strictly **read-only** and are never modified, moved, or uploaded.

---

## Features (Phases 1–5)

- **Phase 1 — Desktop Foundation & Shell**: Modern dark/light themed native desktop interface with responsive navigation.
- **Phase 2 — Folder Scanning & Import**: Recursive background scanning across subdirectories with non-blocking progress, metadata extraction (dimensions, file size, timestamps), and persistent SQLite indexing.
- **Phase 3 — My Gallery**:
  - Responsive thumbnail grid with on-demand background thumbnail caching (`.pixora/thumbnails/`).
  - Grid View & List View toggling.
  - Real-time search by filename.
  - Multi-criteria sorting (Newest first, Oldest first, Name A–Z / Z–A, Size Largest / Smallest).
  - Modal photo preview dialog with full-resolution display, dimensions, file size, format, full path, and "Reveal in Explorer" shortcut.
  - Professional empty state with direct folder import action.
- **Phase 4 — Smart Categories (Local Heuristics)**:
  - Automated categorization using local computer vision heuristics (OpenCV Haar cascades, color distribution analysis, and geometric aspect ratios).
  - Categories: `Selfies`, `Nature`, `Food`, `Animals`, `Documents`, `Screenshots`, `Travel`, `Objects`, `Other`.
  - Zero external AI model downloads required — runs instantly and offline.
  - Interactive category cards with live counts and one-click photo filtering.
  - Background worker thread with real-time progress and cancellation support.
  - Idempotent SQLite database migration preserving all existing records.
- **Phase 5 — Duplicate Finder & Similar Photos**:
  - **Duplicate Finder**: Cryptographic **SHA-256** checksum matching to detect 100% byte-for-byte exact duplicate photos.
  - **Similar Photos**: Perceptual hashing (**pHash**) with Hamming distance clustering to detect visually similar images, burst shots, and re-encoded copies.
  - Side-by-side duplicate groups with visual similarity badges and "Reveal in Explorer" buttons.
  - Safe read-only architecture: original files are never deleted or modified without explicit consent.

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

## Phase Status

- [x] **Phase 1** — Polished desktop interface and architecture foundation
- [x] **Phase 2** — Recursive folder scanning and local image import
- [x] **Phase 3** — Responsive gallery workspace, lazy thumbnails, search, sort, and preview dialog
- [x] **Phase 4** — Smart Categories with local heuristic classification and background workers
- [x] **Phase 5** — Exact duplicate (SHA-256) and visual similarity (pHash) detection
- [ ] **Phase 6+** — Image enhancements (denoise, auto-levels, contrast), export, and packaging
