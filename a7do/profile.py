import re
from collections import defaultdict
from datetime import datetime


class PersonProfile:
    """
    Language-derived profile of a person.
    Built gradually from how they speak.
    """

    def __init__(self, name: str | None = None):
        self.name = name
        self.created_at = datetime.utcnow().isoformat()

        self.utterances = 0
        self.self_references = 0

        self.preferences = defaultdict(int)
        self.objects = defaultdict(int)
        self.actions = defaultdict(int)
        self.emotions = defaultdict(int)

    # -----------------------------
    # Language learning
    # -----------------------------

    def learn(self, text: str):
        self.utterances += 1
        t = text.lower()

        # Self references
        if re.search(r"\b(i|me|my|we|our)\b", t):
            self.self_references += 1

        # Preferences
        for verb in ["like", "love", "enjoy"]:
            m = re.search(rf"\bi {verb} ([a-z\s]+)", t)
            if m:
                self.preferences[m.group(1).strip()] += 1

        for verb in ["hate", "dislike"]:
            m = re.search(rf"\bi {verb} ([a-z\s]+)", t)
            if m:
                self.preferences[f"not:{m.group(1).strip()}"] += 1

        # Objects
        for word in ["bike", "dog", "cat", "project", "code", "system", "ai"]:
            if word in t:
                self.objects[word] += 1

        # Actions
        for verb in ["build", "create", "make", "ride", "learn", "think"]:
            if verb in t:
                self.actions[verb] += 1

        # Emotion words
        for emo in ["happy", "excited", "frustrated", "tired", "confused"]:
            if emo in t:
                self.emotions[emo] += 1

    # -----------------------------
    # Inspection
    # -----------------------------

    def summary(self) -> dict:
        return {
            "name": self.name,
            "utterances": self.utterances,
            "self_references": self.self_references,
            "preferences": dict(self.preferences),
            "objects": dict(self.objects),
            "actions": dict(self.actions),
            "emotions": dict(self.emotions),
        }


class ProfileManager:
    """
    Manages language profiles for users.
    """

    def __init__(self):
        self.profiles = {}

    def get_or_create(self, name: str | None):
        key = name or "unknown"
        if key not in self.profiles:
            self.profiles[key] = PersonProfile(name)
        return self.profiles[key]

    def summary(self):
        return {k: v.summary() for k, v in self.profiles.items()}