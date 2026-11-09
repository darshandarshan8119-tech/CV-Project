"""Unit tests for DatabaseManager migrations, indexing, and queries."""
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.db_manager import DatabaseManager


def test_db_lifecycle_and_migration():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.sqlite3"
        db = DatabaseManager(database_path=db_path)

        assert db.count_images() == 0

        # Upsert test images
        rec1 = {
            "path": str(Path(tmpdir) / "photo1.jpg"),
            "folder": str(tmpdir),
            "filename": "photo1.jpg",
            "width": 1920,
            "height": 1080,
            "size_bytes": 204800,
            "modified_at": 1000.0,
        }
        rec2 = {
            "path": str(Path(tmpdir) / "photo2.png"),
            "folder": str(tmpdir),
            "filename": "photo2.png",
            "width": 800,
            "height": 600,
            "size_bytes": 102400,
            "modified_at": 2000.0,
        }
        db.upsert_image(rec1)
        db.upsert_image(rec2)
        db.commit()

        assert db.count_images() == 2

        # Sorting tests
        newest = db.get_images(sort_by="date_desc")
        assert newest[0]["filename"] == "photo2.png"
        oldest = db.get_images(sort_by="date_asc")
        assert oldest[0]["filename"] == "photo1.jpg"

        # Search test
        search_res = db.get_images(search="photo1")
        assert len(search_res) == 1
        assert search_res[0]["filename"] == "photo1.jpg"

        # Category updates
        db.update_category(rec1["path"], "Nature", 0.85, "Green dominant")
        db.commit()
        assert db.count_images(category="Nature") == 1
        assert db.get_category_counts().get("Nature") == 1

        # Duplicate hashes
        db.update_hashes(rec1["path"], "sha_dummy_1", "phash_dummy_1")
        db.update_hashes(rec2["path"], "sha_dummy_1", "phash_dummy_1")
        db.commit()

        exact_dups = db.get_exact_duplicates()
        assert len(exact_dups) == 1
        assert len(exact_dups[0]) == 2

        db.close()
