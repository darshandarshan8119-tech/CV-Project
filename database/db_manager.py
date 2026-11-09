"""SQLite repository for Pixora's local library index with safe migrations and settings."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.logger import logger


class DatabaseManager:
    def __init__(self, database_path: Path | None = None):
        app_data = Path(os.environ.get("PIXORA_DATA_DIR", Path.home() / ".pixora"))
        app_data.mkdir(parents=True, exist_ok=True)
        self.path = database_path or app_data / "pixora.sqlite3"
        self.connection = sqlite3.connect(str(self.path), check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self._init_tables()
        self._migrate()

    def _init_tables(self):
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS images (
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
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS processed_photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_path TEXT NOT NULL,
                output_path TEXT UNIQUE NOT NULL,
                filename TEXT NOT NULL,
                preset_used TEXT DEFAULT 'Custom',
                width INTEGER DEFAULT 0,
                height INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        self.connection.commit()

    def _migrate(self):
        """Idempotent, safe schema migration adding Phase 4, 5, 6, and 7 columns."""
        cursor = self.connection.execute("PRAGMA table_info(images)")
        existing_cols = {row["name"] for row in cursor.fetchall()}

        new_columns = [
            ("category", "TEXT DEFAULT 'Other'"),
            ("category_confidence", "REAL DEFAULT 0.0"),
            ("category_method", "TEXT DEFAULT 'heuristic'"),
            ("category_reason", "TEXT DEFAULT ''"),
            ("sha256", "TEXT"),
            ("phash", "TEXT"),
            ("exact_dup_group", "TEXT"),
            ("similar_group", "TEXT"),
            ("quality_score", "REAL DEFAULT 0.0"),
            ("blur_score", "REAL DEFAULT 0.0"),
            ("brightness_score", "REAL DEFAULT 0.0"),
            ("contrast_score", "REAL DEFAULT 0.0"),
            ("is_blurry", "INTEGER DEFAULT 0"),
            ("quality_explanation", "TEXT DEFAULT ''"),
        ]

        for col_name, col_def in new_columns:
            if col_name not in existing_cols:
                try:
                    self.connection.execute(f"ALTER TABLE images ADD COLUMN {col_name} {col_def}")
                except sqlite3.OperationalError as e:
                    logger.warning(f"Column migration notice for {col_name}: {e}")

        # Check processed_photos columns as well
        cursor_p = self.connection.execute("PRAGMA table_info(processed_photos)")
        proc_cols = {row["name"] for row in cursor_p.fetchall()}
        for col_name, col_def in [("width", "INTEGER DEFAULT 0"), ("height", "INTEGER DEFAULT 0")]:
            if col_name not in proc_cols:
                try:
                    self.connection.execute(f"ALTER TABLE processed_photos ADD COLUMN {col_name} {col_def}")
                except sqlite3.OperationalError:
                    pass

        # Add indexes for fast querying
        self.connection.execute("CREATE INDEX IF NOT EXISTS idx_img_category ON images(category)")
        self.connection.execute("CREATE INDEX IF NOT EXISTS idx_img_sha256 ON images(sha256)")
        self.connection.execute("CREATE INDEX IF NOT EXISTS idx_img_phash ON images(phash)")
        self.connection.execute("CREATE INDEX IF NOT EXISTS idx_img_exact_group ON images(exact_dup_group)")
        self.connection.execute("CREATE INDEX IF NOT EXISTS idx_img_similar_group ON images(similar_group)")
        self.connection.execute("CREATE INDEX IF NOT EXISTS idx_img_quality ON images(quality_score)")
        self.connection.execute("CREATE INDEX IF NOT EXISTS idx_img_blurry ON images(is_blurry)")
        self.connection.commit()

    def upsert_image(self, record: dict):
        self.connection.execute("""
            INSERT INTO images(path, folder, filename, width, height, size_bytes, modified_at)
            VALUES(:path, :folder, :filename, :width, :height, :size_bytes, :modified_at)
            ON CONFLICT(path) DO UPDATE SET
                width=excluded.width,
                height=excluded.height,
                size_bytes=excluded.size_bytes,
                modified_at=excluded.modified_at
        """, record)

    def count_images(self, category: Optional[str] = None) -> int:
        if category:
            row = self.connection.execute(
                "SELECT COUNT(*) FROM images WHERE category = ?", (category,)
            ).fetchone()
        else:
            row = self.connection.execute("SELECT COUNT(*) FROM images").fetchone()
        return row[0] if row else 0

    def get_images(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        sort_by: str = "date_desc",
        only_blurry: bool = False,
        min_quality: Optional[float] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Retrieve images with optional search, category filter, quality filter, and sorting."""
        query = "SELECT * FROM images WHERE 1=1"
        params: List[Any] = []

        if search:
            query += " AND (filename LIKE ? OR folder LIKE ?)"
            term = f"%{search.strip()}%"
            params.extend([term, term])

        if category and category != "All":
            query += " AND category = ?"
            params.append(category)

        if only_blurry:
            query += " AND is_blurry = 1"

        if min_quality is not None:
            query += " AND quality_score >= ?"
            params.append(min_quality)

        order_clauses = {
            "date_desc": "modified_at DESC",
            "date_asc": "modified_at ASC",
            "name_asc": "filename COLLATE NOCASE ASC",
            "name_desc": "filename COLLATE NOCASE DESC",
            "size_desc": "size_bytes DESC",
            "size_asc": "size_bytes ASC",
            "quality_desc": "quality_score DESC",
            "quality_asc": "quality_score ASC",
        }
        order = order_clauses.get(sort_by, "modified_at DESC")
        query += f" ORDER BY {order}"

        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

        rows = self.connection.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def get_image_by_path(self, path: str) -> Optional[Dict[str, Any]]:
        row = self.connection.execute("SELECT * FROM images WHERE path = ?", (path,)).fetchone()
        return dict(row) if row else None

    def update_category(self, path: str, category: str, confidence: float, reason: str = ""):
        self.connection.execute("""
            UPDATE images
            SET category = ?, category_confidence = ?, category_reason = ?
            WHERE path = ?
        """, (category, round(confidence, 2), reason, path))

    def update_hashes(self, path: str, sha256: str, phash: str):
        self.connection.execute("""
            UPDATE images
            SET sha256 = ?, phash = ?
            WHERE path = ?
        """, (sha256, phash, path))

    def update_groups(self, path: str, exact_group: Optional[str], similar_group: Optional[str]):
        self.connection.execute("""
            UPDATE images
            SET exact_dup_group = ?, similar_group = ?
            WHERE path = ?
        """, (exact_group, similar_group, path))

    def update_quality(
        self,
        path: str,
        combined_score: float,
        blur_score: float,
        brightness_score: float,
        contrast_score: float,
        is_blurry: bool,
        explanation: str,
    ):
        self.connection.execute("""
            UPDATE images
            SET quality_score = ?,
                blur_score = ?,
                brightness_score = ?,
                contrast_score = ?,
                is_blurry = ?,
                quality_explanation = ?
            WHERE path = ?
        """, (
            round(combined_score, 1),
            round(blur_score, 1),
            round(brightness_score, 1),
            round(contrast_score, 1),
            1 if is_blurry else 0,
            explanation,
            path,
        ))

    def get_category_counts(self) -> Dict[str, int]:
        rows = self.connection.execute("""
            SELECT category, COUNT(*) as cnt
            FROM images
            WHERE category IS NOT NULL
            GROUP BY category
        """).fetchall()
        return {row["category"]: row["cnt"] for row in rows}

    def get_exact_duplicates(self) -> List[List[Dict[str, Any]]]:
        groups = self.connection.execute("""
            SELECT sha256 FROM images
            WHERE sha256 IS NOT NULL AND sha256 != ''
            GROUP BY sha256
            HAVING COUNT(*) > 1
        """).fetchall()

        result: List[List[Dict[str, Any]]] = []
        for g in groups:
            rows = self.connection.execute(
                "SELECT * FROM images WHERE sha256 = ? ORDER BY path ASC", (g["sha256"],)
            ).fetchall()
            if len(rows) > 1:
                result.append([dict(r) for r in rows])
        return result

    def get_similar_photos(self) -> List[List[Dict[str, Any]]]:
        groups = self.connection.execute("""
            SELECT similar_group FROM images
            WHERE similar_group IS NOT NULL AND similar_group != ''
            GROUP BY similar_group
            HAVING COUNT(*) > 1
        """).fetchall()

        result: List[List[Dict[str, Any]]] = []
        for g in groups:
            rows = self.connection.execute(
                "SELECT * FROM images WHERE similar_group = ? ORDER BY path ASC", (g["similar_group"],)
            ).fetchall()
            if len(rows) > 1:
                result.append([dict(r) for r in rows])
        return result

    def record_processed_photo(
        self,
        source_path: str,
        output_path: str,
        filename: str,
        preset: str = "Custom",
        width: int = 0,
        height: int = 0,
    ):
        self.connection.execute("""
            INSERT INTO processed_photos(source_path, output_path, filename, preset_used, width, height)
            VALUES(?, ?, ?, ?, ?, ?)
            ON CONFLICT(output_path) DO UPDATE SET
                created_at=CURRENT_TIMESTAMP,
                preset_used=excluded.preset_used,
                width=excluded.width,
                height=excluded.height
        """, (source_path, output_path, filename, preset, width, height))
        self.connection.commit()

    def get_processed_photos(self) -> List[Dict[str, Any]]:
        rows = self.connection.execute("""
            SELECT * FROM processed_photos ORDER BY id DESC
        """).fetchall()
        return [dict(r) for r in rows]

    def count_blurry_images(self) -> int:
        row = self.connection.execute("SELECT COUNT(*) FROM images WHERE is_blurry = 1").fetchone()
        return row[0] if row else 0

    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        row = self.connection.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row[0] if row else default

    def set_setting(self, key: str, value: str):
        self.connection.execute("""
            INSERT INTO settings(key, value) VALUES(?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (key, value))
        self.connection.commit()

    def clear_library(self, delete_processed: bool = False):
        """Reset the local image index while leaving original photos completely untouched."""
        self.connection.execute("DELETE FROM images")
        if delete_processed:
            self.connection.execute("DELETE FROM processed_photos")
        self.connection.commit()
        self.connection.execute("VACUUM")
        logger.info("Library index cleared successfully")

    def commit(self):
        self.connection.commit()

    def close(self):
        self.connection.close()
