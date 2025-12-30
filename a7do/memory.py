from collections import defaultdict
from datetime import datetime


class Memory:
    """
    Episodic memory + confidence-based promotion into stable facts.
    """

    def __init__(self):
        self.entries = []

        # candidate beliefs waiting to be confirmed
        # key -> {"score": float, "count": int, "last_time": "...", "example": "..."}
        self.candidates = {}

        # stable promoted facts
        # key -> {"score": float, "count": int, "promoted_time": "..."}
        self.facts = {}

    # --------------------------------------------------
    # Episodic storage
    # --------------------------------------------------

    def add(self, kind: str, content: str, tags: list | None = None):
        entry = {
            "time": datetime.utcnow().isoformat(),
            "kind": kind,
            "content": content,
            "tags": tags or [],
        }
        self.entries.append(entry)

    # --------------------------------------------------
    # Confidence learning
    # --------------------------------------------------

    def add_candidate(self, key: str, weight: float, example: str = ""):
        """
        Increase confidence for a candidate belief.
        """
        now = datetime.utcnow().isoformat()

        if key in self.facts:
            # already promoted; keep a light tally
            self.facts[key]["score"] += weight * 0.25
            self.facts[key]["count"] += 1
            return

        if key not in self.candidates:
            self.candidates[key] = {
                "score": 0.0,
                "count": 0,
                "last_time": now,
                "example": example[:240]
            }

        self.candidates[key]["score"] += weight
        self.candidates[key]["count"] += 1
        self.candidates[key]["last_time"] = now
        if example:
            self.candidates[key]["example"] = example[:240]

    def promote_candidates(self, threshold_score: float = 3.0, threshold_count: int = 3):
        """
        Promote candidates into stable facts if thresholds are met.
        """
        now = datetime.utcnow().isoformat()
        to_promote = []

        for key, v in self.candidates.items():
            if v["score"] >= threshold_score and v["count"] >= threshold_count:
                to_promote.append(key)

        for key in to_promote:
            v = self.candidates.pop(key)
            self.facts[key] = {
                "score": v["score"],
                "count": v["count"],
                "promoted_time": now,
                "example": v.get("example", "")
            }

    # --------------------------------------------------
    # Queries & summaries
    # --------------------------------------------------

    def recent(self, n: int = 10):
        return self.entries[-n:]

    def by_tag(self, tag: str):
        return [e for e in self.entries if tag in e["tags"]]

    def summary(self):
        tag_counts = defaultdict(int)
        kind_counts = defaultdict(int)

        for e in self.entries:
            kind_counts[e["kind"]] += 1
            for t in e["tags"]:
                tag_counts[t] += 1

        top_tags = dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10])

        return {
            "total_entries": len(self.entries),
            "by_kind": dict(kind_counts),
            "top_tags": top_tags,
            "candidate_count": len(self.candidates),
            "fact_count": len(self.facts),
        }