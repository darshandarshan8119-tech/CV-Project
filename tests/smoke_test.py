"""Comprehensive smoke test suite runner for Pixora production readiness."""
import sys
import traceback
import unittest
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tests.test_categorizer import test_categorizer_heuristics
from tests.test_database import test_db_lifecycle_and_migration
from tests.test_duplicates import test_duplicates_and_similarity
from tests.test_enhancer import (
    test_enhancement_operations_and_scaling,
    test_non_destructive_export_and_non_overwrite,
)
from tests.test_migrations import (
    test_fresh_database_initialization,
    test_migration_from_legacy_phase2_db,
)
from tests.test_quality import (
    test_sharpness_and_blur_detection,
    test_similar_group_ranking,
)
from tests.test_thumbnails import test_thumbnail_generation_and_caching
from tests.test_ui_widgets import TestUIThemeAndWidgets


def run_all_tests() -> int:
    tests = [
        ("Database Lifecycle & Queries", test_db_lifecycle_and_migration),
        ("Legacy Phase 2 Database Migration", test_migration_from_legacy_phase2_db),
        ("Fresh Database Initialization", test_fresh_database_initialization),
        ("Thumbnail Generation & Cache", test_thumbnail_generation_and_caching),
        ("Local Heuristic Categorization", test_categorizer_heuristics),
        ("Exact & Perceptual Duplicate Detection", test_duplicates_and_similarity),
        ("OpenCV Sharpness & Blur Scoring", test_sharpness_and_blur_detection),
        ("Similar Group Best Shot Recommendation", test_similar_group_ranking),
        ("Local Image Enhancements & Scaling", test_enhancement_operations_and_scaling),
        ("Non-Destructive Export & Non-Overwrite", test_non_destructive_export_and_non_overwrite),
        ("UI Theme, Animations & Interactive Slider", lambda: unittest.TextTestRunner(verbosity=0).run(unittest.TestLoader().loadTestsFromTestCase(TestUIThemeAndWidgets))),
    ]

    print("=" * 65)
    print("PIXORA SYSTEM VALIDATION & PRODUCTION SMOKE TEST SUITE")
    print("=" * 65)

    passed = 0
    failed = 0

    for name, func in tests:
        try:
            print(f"[RUNNING] {name:42s} ...", end=" ", flush=True)
            func()
            print("PASSED")
            passed += 1
        except Exception as e:
            print("FAILED")
            traceback.print_exc()
            failed += 1

    print("-" * 65)
    print(f"Summary: {passed} passed, {failed} failed.")
    print("=" * 65)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
