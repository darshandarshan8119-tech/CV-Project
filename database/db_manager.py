"""SQLite repository for Pixora's local library index with safe migrations."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


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
        self.connection.commit()

    def _migrate(self):
        """Idempotent, safe schema migration adding Phase 4 and Phase 5 columns."""
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
        ]

        for col_name, col_def in new_columns:
            if col_name not in existing_cols:
                try:
                    self.connection.execute(f"ALTER TABLE images ADD COLUMN {col_name} {col_def}")
                except sqlite3.OperationalError:
                    pass

        # Add indexes for fast querying
        self.connection.execute("CREATE INDEX IF NOT EXISTS idx_img_category ON images(category)")
        self.connection.execute("CREATE INDEX IF NOT EXISTS idx_img_sha256 ON images(sha256)")
        self.connection.execute("CREATE INDEX IF NOT EXISTS idx_img_phash ON images(phash)")
        self.connection.execute("CREATE INDEX IF NOT EXISTS idx_img_exact_group ON images(exact_dup_group)")
        self.connection.execute("CREATE INDEX IF NOT EXISTS idx_img_similar_group ON images(similar_group)")
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
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Retrieve images with optional search, category filter, and sorting."""
        query = "SELECT * FROM images WHERE 1=1"
        params: List[Any] = []

        if search:
            query += " AND (filename LIKE ? OR folder LIKE ?)"
            term = f"%{search.strip()}%"
            params.extend([term, term])

        if category and category != "All":
            query += " AND category = ?"
            params.append(category)

        order_clauses = {
            "date_desc": "modified_at DESC",
            "date_asc": "modified_at ASC",
            "name_asc": "filename COLLATE NOCASE ASC",
            "name_desc": "filename COLLATE NOCASE DESC",
            "size_desc": "size_bytes DESC",
            "size_asc": "size_bytes ASC",
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

    def get_category_counts(self) -> Dict[str, int]:
        rows = self.connection.execute("""
            SELECT category, COUNT(*) as cnt
            FROM images
            WHERE category IS NOT NULL
            GROUP BY category
        """).fetchall()
        return {row["category"]: row["cnt"] for row in rows}

    def get_exact_duplicates(self) -> List[List[Dict[str, Any]]]:
        """Return groups of images that share the exact same sha256 hash."""
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
        """Return groups of images sharing a similar_group identifier."""
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

    def commit(self):
        self.connection.commit()

    def close(self):
        self.connection.close()
