"""
A7DO Memory Consolidation Module

This module performs:
- Clustering of related memories
- Summary-memory creation
- Marking originals as compressed
- Optional pruning of old compressed memories

The goal is to keep A7DO's memory:
- compact
- concept-driven
- efficient to search
- psychologically plausible

This module does NOT delete important memories (identity, development, etc.).
"""

from __future__ import annotations
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

# MemorySystem will call into this module
# from .memory import MemorySystem, MemoryEntry


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

DEFAULT_MIN_CLUSTER_SIZE = 4
DEFAULT_SIMILARITY_THRESHOLD = 0.65
DEFAULT_MAX_MEMORY = 2000


# -----------------------------------------------------------------------------
# Utility: simple semantic similarity
# -----------------------------------------------------------------------------

def simple_similarity(a: str, b: str) -> float:
    """
    A deliberately simple similarity metric.

    - Token overlap
    - Lowercased
    - No embeddings (keeps it transparent)

    Returns a float in [0, 1].
    """
    if not a or not b:
        return 0.0

    A = set(a.lower().split())
    B = set(b.lower().split())

    if not A or not B:
        return 0.0

    overlap = len(A.intersection(B))
    union = len(A.union(B))

    return overlap / union


# -----------------------------------------------------------------------------
# Clustering
# -----------------------------------------------------------------------------

def cluster_memories(memories, similarity_threshold=DEFAULT_SIMILARITY_THRESHOLD):
    """
    Group memories into clusters based on simple semantic similarity.

    Returns:
        List[List[int]] where each inner list is a cluster of memory indices.
    """
    clusters: List[List[int]] = []
    used = set()

    for i, m in enumerate(memories):
        if i in used:
            continue

        cluster = [i]
        used.add(i)

        for j in range(i + 1, len(memories)):
            if j in used:
                continue

            sim = simple_similarity(m.content, memories[j].content)
            if sim >= similarity_threshold:
                cluster.append(j)
                used.add(j)

        clusters.append(cluster)

    return clusters


# -----------------------------------------------------------------------------
# Summary memory creation
# -----------------------------------------------------------------------------

def create_summary_memory(memory_system, cluster_indices: List[int]) -> int:
    """
    Create a summary memory for a cluster of related memories.

    The summary is a simple narrative description of what the cluster is about.
    """
    if not cluster_indices:
        return -1

    entries = [memory_system.get(i) for i in cluster_indices]
    entries = [e for e in entries if e is not None]

    if not entries:
        return -1

    # Extract dominant tag
    tag_counts = defaultdict(int)
    for e in entries:
        for t in e.tags:
            tag_counts[t] += 1

    if tag_counts:
        dominant_tag = max(tag_counts, key=tag_counts.get)
    else:
        dominant_tag = "general"

    # Build summary text
    contents = [e.content for e in entries]
    joined = " ".join(contents)

    summary_text = (
        f"Summary of {len(entries)} related memories "
        f"(dominant tag: '{dominant_tag}'): "
        f"{joined[:400]}..."
    )

    # Add summary memory
    summary_index = memory_system.add_memory(
        kind="summary",
        content=summary_text,
        source="consolidation",
        tags=["summary", dominant_tag],
        emotion_valence=0.05,
        emotion_label="reflective",
    )

    return summary_index


# -----------------------------------------------------------------------------
# Consolidation pipeline
# -----------------------------------------------------------------------------

def run_consolidation(memory_system,
                      min_cluster_size=DEFAULT_MIN_CLUSTER_SIZE,
                      similarity_threshold=DEFAULT_SIMILARITY_THRESHOLD,
                      max_memory=DEFAULT_MAX_MEMORY):
    """
    Main consolidation routine.

    Steps:
    1. Cluster memories
    2. For each cluster >= min_cluster_size:
         - Create summary memory
         - Mark originals as compressed
    3. If memory > max_memory:
         - prune old compressed memories
    """

    all_entries = memory_system.all()
    if not all_entries:
        return

    # 1. Cluster
    clusters = cluster_memories(all_entries, similarity_threshold)

    # 2. Summaries
    for cluster in clusters:
        if len(cluster) >= min_cluster_size:
            summary_idx = create_summary_memory(memory_system, cluster)
            memory_system.mark_compressed(cluster)

    # 3. Pruning
    if len(all_entries) > max_memory:
        prune_old_compressed(memory_system)


# -----------------------------------------------------------------------------
# Pruning
# -----------------------------------------------------------------------------

def prune_old_compressed(memory_system, keep_recent=1500):
    """
    Remove old compressed memories to keep memory size manageable.

    Does NOT remove:
    - identity memories
    - development memories
    - summary memories
    """

    entries = memory_system.all()

    # Identify candidates
    candidates = [
        m for m in entries
        if m.compressed
        and m.kind not in ("identity", "development", "summary")
    ]

    # Sort by age (oldest first)
    candidates.sort(key=lambda m: m.step_index)

    # Determine how many to remove
    excess = len(entries) - keep_recent
    if excess <= 0:
        return

    to_remove = candidates[:excess]

    # Remove by rebuilding the list
    remaining = [
        m for m in entries
        if m not in to_remove
    ]

    # Replace internal memory list
    memory_system._entries = remaining

    # Reassign step indices
    for i, m in enumerate(memory_system._entries):
        m.step_index = i

    memory_system._step_counter = len(memory_system._entries)
