"""Duplicate and visual similarity detection using SHA-256 and perceptual hashing."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import imagehash
from PIL import Image


def compute_file_sha256(file_path: str) -> Optional[str]:
    """Compute the SHA-256 hash of a file in 64KB chunks."""
    path = Path(file_path)
    if not path.is_file():
        return None
    try:
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return None


def compute_image_phash(file_path: str) -> Optional[str]:
    """Compute perceptual hash using ImageHash (phash)."""
    path = Path(file_path)
    if not path.is_file():
        return None
    try:
        with Image.open(path) as img:
            return str(imagehash.phash(img))
    except Exception:
        return None


def hamming_distance(hash1: str, hash2: str) -> int:
    """Calculate hamming distance between two hex hash strings."""
    try:
        h1 = imagehash.hex_to_hash(hash1)
        h2 = imagehash.hex_to_hash(hash2)
        return int(h1 - h2)
    except Exception:
        return 999


def find_similarity_clusters(
    images_with_phash: List[Dict[str, any]],
    max_distance: int = 8,
) -> Dict[str, str]:
    """
    Cluster images based on perceptual hash Hamming distance.
    Returns a mapping of {image_path: group_id}.
    Only images with at least one similar counterpart receive a group_id.
    """
    valid = [img for img in images_with_phash if img.get("phash")]
    n = len(valid)
    if n < 2:
        return {}

    # Disjoint Set Union (DSU)
    parent = list(range(n))

    def find(i: int) -> int:
        if parent[i] == i:
            return i
        parent[i] = find(parent[i])
        return parent[i]

    def union(i: int, j: int):
        root_i = find(i)
        root_j = find(j)
        if root_i != root_j:
            parent[root_i] = root_j

    for i in range(n):
        for j in range(i + 1, n):
            # Skip if exact same sha256 (they are exact duplicates, not just similar)
            sha_i = valid[i].get("sha256")
            sha_j = valid[j].get("sha256")
            if sha_i and sha_j and sha_i == sha_j:
                continue

            dist = hamming_distance(valid[i]["phash"], valid[j]["phash"])
            if dist <= max_distance:
                union(i, j)

    # Collect clusters of size >= 2
    clusters: Dict[int, List[int]] = {}
    for i in range(n):
        root = find(i)
        clusters.setdefault(root, []).append(i)

    group_mapping: Dict[str, str] = {}
    cluster_idx = 1
    for root, members in clusters.items():
        if len(members) >= 2:
            group_id = f"sim_{cluster_idx:03d}"
            for m in members:
                group_mapping[valid[m]["path"]] = group_id
            cluster_idx += 1

    return group_mapping

