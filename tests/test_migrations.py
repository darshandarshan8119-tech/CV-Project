"""Unit tests for SQLite database migrations from fresh and legacy schemas."""
import sqlite3
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.db_manager import DatabaseManager


def test_migration_from_legacy_phase2_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "legacy_pixora.sqlite3"

        # 1. Create a pure Phase 2 legacy database schema (only 8 columns)
        conn = sqlite3.connect(str(db_file))
        conn.execute("""
            CREATE TABLE images (
                path TEXT PRIMARY KEY,
                folder TEXT NOT NULL,
                filename TEXT NOT NULL,
                width INTEGER,
                height INTEGER,
                size_bytes INTEGER,
                modified_at REAL,
                imported_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            INSERT INTO images (path, folder, filename, width, height, size_bytes, modified_at)
            VALUES ('C:/Photos/legacy1.jpg', 'C:/Photos', 'legacy1.jpg', 1920, 1080, 500000, 123456.0)
        """)
        conn.commit()
        conn.close()

        # 2. Open with modern DatabaseManager -> runs _migrate()
        db = DatabaseManager(database_path=db_file)

        # Verify legacy data preserved
        assert db.count_images() == 1
        img = db.get_images()[0]
        assert img["filename"] == "legacy1.jpg"
        assert img["width"] == 1920

        # Verify new Phase 4-7 columns exist and have safe defaults
        assert img["category"] == "Other"
        assert img["category_confidence"] == 0.0
        assert img["quality_score"] == 0.0
        assert img["is_blurry"] == 0

        # Verify settings table works
        db.set_setting("theme", "dark")
        assert db.get_setting("theme") == "dark"

        # Verify processed_photos table works
        db.record_processed_photo(
            source_path="C:/Photos/legacy1.jpg",
            output_path="C:/Photos/enhanced_legacy1.jpg",
            filename="enhanced_legacy1.jpg",
            preset="Magic",
            width=1920,
            height=1080,
        )
        processed = db.get_processed_photos()
        assert len(processed) == 1
        assert processed[0]["filename"] == "enhanced_legacy1.jpg"

        db.close()


def test_fresh_database_initialization():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "fresh_pixora.sqlite3"
        db = DatabaseManager(database_path=db_file)

        assert db.count_images() == 0
        db.set_setting("blur_threshold", "140.0")
        assert db.get_setting("blur_threshold") == "140.0"

        db.close()

