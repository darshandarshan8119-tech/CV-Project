"""Smoke test suite runner for Pixora Phase 1–5 validation."""
import sys
import traceback
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tests.test_database import test_db_lifecycle_and_migration
from tests.test_thumbnails import test_thumbnail_generation_and_caching
from tests.test_categorizer import test_categorizer_heuristics
from tests.test_duplicates import test_duplicates_and_similarity


def run_all_tests() -> int:
    tests = [
        ("Database Migrations & Operations", test_db_lifecycle_and_migration),
        ("Thumbnail Generation & Caching", test_thumbnail_generation_and_caching),
        ("Local Heuristic Categorization", test_categorizer_heuristics),
        ("Exact & Perceptual Duplicate Detection", test_duplicates_and_similarity),
    ]

    print("=" * 60)
    print("PIXORA SYSTEM VALIDATION & SMOKE TEST SUITE")
    print("=" * 60)

    passed = 0
    failed = 0

    for name, func in tests:
        try:
            print(f"[RUNNING] {name}...", end=" ", flush=True)
            func()
            print("PASSED")
            passed += 1
        except Exception as e:
            print("FAILED")
            traceback.print_exc()
            failed += 1

    print("-" * 60)
    print(f"Summary: {passed} passed, {failed} failed.")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
