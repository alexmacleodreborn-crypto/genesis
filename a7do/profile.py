from collections import defaultdict
from datetime import datetime


class PersonProfile:
    """
    Language-derived profile of a person.
    Built from tagged experience, not prompts.
    """

    def __init__(self, name=None):
        self.name = name
        self.created_at = datetime.utcnow().isoformat()

        self.utterances = 0

        # Domain familiarity (maths, AI, Sandy's Law, etc.)
        self.domains = defaultdict(int)

        # Social / affective indicators
        self.references = defaultdict(int)
        self.emotions = defaultdict(int)

    # --------------------------------------------------
    # Learning from tagged input
    # --------------------------------------------------

    def learn(self, text: str, tags_map: dict):
        """
        Learn from a single utterance using multi-domain tags.
        """
        self.utterances += 1

        # Accumulate domain exposure
        for domain, count in tags_map.items():
            self.domains[domain] += count

        # Simple social inference
        if "relationship" in tags_map:
            self.references["self"] += 1

        if "emotion" in tags_map:
            self.emotions["expressed"] += 1

    # --------------------------------------------------
    # Inspection
    # --------------------------------------------------

    def summary(self) -> dict:
        return {
            "name": self.name,
            "utterances": self.utterances,
            "domains": dict(self.domains),
            "references": dict(self.references),
            "emotions": dict(self.emotions),
        }


class ProfileManager:
    """
    Manages multiple person profiles.
    """

    def __init__(self):
        self.profiles = {}

    def get_or_create(self, name):
        key = name or "unknown"
        if key not in self.profiles:
            self.profiles[key] = PersonProfile(name)
        return self.profiles[key]

    def summary(self):
        return {k: v.summary() for k, v in self.profiles.items()}