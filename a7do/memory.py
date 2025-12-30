from collections import defaultdict
from datetime import datetime


class Memory:
    """
    Episodic memory with multi-domain tagging.
    """

    def __init__(self):
        self.entries = []

    # --------------------------------------------------
    # Add memory
    # --------------------------------------------------

    def add(self, kind: str, content: str, tags: list | None = None):
        """
        Store a memory entry.

        kind: 'utterance', 'identity', 'event', etc.
        content: raw text
        tags: list of domain labels
        """
        entry = {
            "time": datetime.utcnow().isoformat(),
            "kind": kind,
            "content": content,
            "tags": tags or [],
        }
        self.entries.append(entry)

    # --------------------------------------------------
    # Queries
    # --------------------------------------------------

    def recent(self, n: int = 10):
        return self.entries[-n:]

    def by_tag(self, tag: str):
        return [e for e in self.entries if tag in e["tags"]]

    # --------------------------------------------------
    # Inspection
    # --------------------------------------------------

    def summary(self):
        """
        High-level summary for UI.
        """
        tag_counts = defaultdict(int)
        for e in self.entries:
            for t in e["tags"]:
                tag_counts[t] += 1

        return {
            "total_entries": len(self.entries),
            "by_kind": {
                k: sum(1 for e in self.entries if e["kind"] == k)
                for k in set(e["kind"] for e in self.entries)
            },
            "top_tags": dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
        }