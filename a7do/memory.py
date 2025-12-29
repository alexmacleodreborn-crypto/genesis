"""
A7DO Memory System

This module provides:
- A structured memory entry format
- A MemorySystem class for storing, tagging, and retrieving memories
- Emotional integration (valence + label)
- Hooks for consolidation and long-term pruning (added later)
- Export helpers for timeline and mind-map visualisation

The memory system is intentionally transparent and auditable.
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any


# -----------------------------------------------------------------------------
# Memory Entry
# -----------------------------------------------------------------------------

@dataclass
class MemoryEntry:
    """
    A single memory record.

    Fields:
    - kind:            category of memory ("dialogue", "identity", "emotion", etc.)
    - content:         the text content of the memory
    - source:          where it came from ("user", "system", "development")
    - tags:            list of semantic tags
    - emotion_valence: float in [-1.0, 1.0]
    - emotion_label:   coarse label ("curious", "neutral", "reflective", etc.)
    - step_index:      chronological index assigned by MemorySystem
    - compressed:      whether this memory has been summarised by consolidation
    """

    kind: str
    content: str
    source: str
    tags: List[str]
    emotion_valence: float
    emotion_label: str
    step_index: int
    compressed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """
        Export a dictionary representation for timeline logging or debugging.
        """
        return asdict(self)


# -----------------------------------------------------------------------------
# Memory System
# -----------------------------------------------------------------------------

class MemorySystem:
    """
    Central memory store for A7DO.

    Responsibilities:
    - Store chronological memory entries
    - Provide search/filter utilities
    - Integrate emotional valence into memory
    - Support consolidation (added later)
    - Provide export for timeline and mind-map
    """

    def __init__(self):
        self._entries: List[MemoryEntry] = []
        self._step_counter: int = 0

    # -------------------------------------------------------------------------
    # Core API
    # -------------------------------------------------------------------------

    def add_memory(
        self,
        kind: str,
        content: str,
        source: str = "system",
        tags: Optional[List[str]] = None,
        emotion_valence: float = 0.0,
        emotion_label: str = "neutral",
    ) -> int:
        """
        Add a new memory entry and return its index.
        """

        if tags is None:
            tags = []

        # Clamp valence
        v = max(-1.0, min(1.0, float(emotion_valence)))

        entry = MemoryEntry(
            kind=kind,
            content=content,
            source=source,
            tags=list(tags),
            emotion_valence=v,
            emotion_label=emotion_label,
            step_index=self._step_counter,
        )

        self._entries.append(entry)
        self._step_counter += 1

        return entry.step_index

    # -------------------------------------------------------------------------
    # Retrieval
    # -------------------------------------------------------------------------

    def get(self, index: int) -> Optional[MemoryEntry]:
        """
        Retrieve a memory by index.
        """
        if 0 <= index < len(self._entries):
            return self._entries[index]
        return None

    def all(self) -> List[MemoryEntry]:
        """
        Return all memory entries.
        """
        return list(self._entries)

    # -------------------------------------------------------------------------
    # Search utilities
    # -------------------------------------------------------------------------

    def search_by_tag(self, tag: str) -> List[MemoryEntry]:
        """
        Return all memories containing a given tag.
        """
        return [m for m in self._entries if tag in m.tags]

    def search_by_kind(self, kind: str) -> List[MemoryEntry]:
        """
        Return all memories of a given kind.
        """
        return [m for m in self._entries if m.kind == kind]

    def search_text(self, substring: str) -> List[MemoryEntry]:
        """
        Return all memories whose content contains the substring.
        """
        s = substring.lower()
        return [m for m in self._entries if s in m.content.lower()]

    # -------------------------------------------------------------------------
    # Emotional integration
    # -------------------------------------------------------------------------

    def recent_emotions(self, n: int = 20) -> List[float]:
        """
        Return the last N emotional valence values.
        """
        vals = [m.emotion_valence for m in self._entries]
        return vals[-n:]

    # -------------------------------------------------------------------------
    # Consolidation hooks (implemented later)
    # -------------------------------------------------------------------------

    def mark_compressed(self, indices: List[int]) -> None:
        """
        Mark a set of memories as compressed.
        """
        for idx in indices:
            m = self.get(idx)
            if m:
                m.compressed = True

    # -------------------------------------------------------------------------
    # Export for timeline / mind-map
    # -------------------------------------------------------------------------

    def export_all(self) -> List[Dict[str, Any]]:
        """
        Export all memories as dictionaries.
        """
        return [m.to_dict() for m in self._entries]

    def export_recent(self, n: int = 50) -> List[Dict[str, Any]]:
        """
        Export the last N memories.
        """
        return [m.to_dict() for m in self._entries[-n:]]

    # -------------------------------------------------------------------------
    # Character-panel helper
    # -------------------------------------------------------------------------

    def build_memory_summary(self) -> str:
        """
        Build a short descriptive summary of memory activity for the
        character panel. This is intentionally simple and narrative.
        """
        total = len(self._entries)
        if total == 0:
            return "I haven't formed any memories yet."

        identity_count = len(self.search_by_kind("identity"))
        dialogue_count = len(self.search_by_kind("dialogue"))
        compressed_count = sum(1 for m in self._entries if m.compressed)

        return (
            f"I currently hold {total} memories. "
            f"{identity_count} relate to my identity, "
            f"{dialogue_count} come from our conversations, "
            f"and {compressed_count} have been summarised through consolidation."
        )
