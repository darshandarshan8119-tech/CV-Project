"""Background worker for SHA-256 exact duplicates and perceptual similarity scanning."""
from __future__ import annotations

from typing import List, Optional
from PySide6.QtCore import QThread, Signal

from core.duplicates import (
    compute_file_sha256,
    compute_image_phash,
    find_similarity_clusters,
)
from database.db_manager import DatabaseManager


class DuplicateWorker(QThread):
    started_scan = Signal(int)
    progress = Signal(int, int, str)
    completed = Signal(dict)
    failed = Signal(str)

    def __init__(self, force_all: bool = False, database: Optional[DatabaseManager] = None):
        super().__init__()
        self.force_all = force_all
        self.database = database or DatabaseManager()
        self.cancelled = False

    def cancel(self):
        self.cancelled = True

    def run(self):
        try:
            images = self.database.get_images()
            total = len(images)
            self.started_scan.emit(total)

            # Step 1: Compute hashes for unhashed files
            for index, img in enumerate(images, 1):
                if self.cancelled:
                    break

                path = img["path"]
                fname = img.get("filename", "")
                self.progress.emit(index, total, f"Analyzing {fname}…")

                sha256 = img.get("sha256")
                phash = img.get("phash")

                need_update = False
                if self.force_all or not sha256:
                    sha256 = compute_file_sha256(path)
                    need_update = True

                if self.force_all or not phash:
                    phash = compute_image_phash(path)
                    need_update = True

                if need_update and (sha256 or phash):
                    self.database.update_hashes(path, sha256 or "", phash or "")
                    img["sha256"] = sha256
                    img["phash"] = phash

                if index % 10 == 0:
                    self.database.commit()

            self.database.commit()

            if self.cancelled:
                self.completed.emit({"cancelled": True})
                return

            # Step 2: Assign exact duplicate groups
            refreshed_images = self.database.get_images()
            sha_map: dict[str, list[dict]] = {}
            for img in refreshed_images:
                s = img.get("sha256")
                if s:
                    sha_map.setdefault(s, []).append(img)

            exact_count = 0
            for s, group in sha_map.items():
                if len(group) >= 2:
                    exact_count += 1
                    gid = f"exact_{s[:12]}"
                    for img in group:
                        self.database.update_groups(img["path"], gid, None)
                else:
                    for img in group:
                        # Clear old exact group if no longer duplicate
                        self.database.update_groups(img["path"], None, None)

            # Step 3: Find similarity clusters
            sim_mapping = find_similarity_clusters(refreshed_images, max_distance=8)
            for path, gid in sim_mapping.items():
                # Preserve exact group if present
                img_record = self.database.get_image_by_path(path)
                exact_gid = img_record.get("exact_dup_group") if img_record else None
                self.database.update_groups(path, exact_gid, gid)

            self.database.commit()

            # Count groups
            exact_groups = self.database.get_exact_duplicates()
            sim_groups = self.database.get_similar_photos()

            self.completed.emit({
                "exact_groups": len(exact_groups),
                "similar_groups": len(sim_groups),
                "total_images": total,
                "cancelled": False,
            })
        except Exception as e:
            self.failed.emit(str(e))

