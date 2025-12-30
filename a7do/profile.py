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

        # Core profile fields
        self.preferences = defaultdict(int)     # like / dislike
        self.objects = defaultdict(int)         # bike, dog, project
        self.actions = defaultdict(int)         # build, ride, think
        self.topics = defaultdict(int)          # inferred themes
        self.emotions = defaultdict(int)        # happy, frustrated

        self.self_references = 0
        self.utterances = 0
        
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

    # --------------------------------------------------
    # Language learning
    # --------------------------------------------------

    def learn(self, text: str):
        self.utterances += 1
        t = text.lower()

        # -------------------------
        # Self reference
        # -------------------------
        if re.search(r"\b(i|my|me|we|our)\b", t):
            self.self_references += 1

        # -------------------------
        # Preferences
        # -------------------------
        likes = re.findall(r"\bi (like|love|enjoy)\b ([a-z\s]+)", t)
        dislikes = re.findall(r"\bi (hate|dislike)\b ([a-z\s]+)", t)

        for _, thing in likes:
            self.preferences[thing.strip()] += 1

        for _, thing in dislikes:
            self.preferences[f"not:{thing.strip()}"] += 1

        # -------------------------
        # Objects (very simple noun capture)
        # -------------------------
        for word in ["bike", "dog", "cat", "project", "code", "system", "ai"]:
            if word in t:
                self.objects[word] += 1

        # -------------------------
        # Actions
        # -------------------------
        for verb in ["build", "make", "create", "ride", "learn", "think"]:
            if verb in t:
                self.actions[verb] += 1

        # -------------------------
        # Emotion words
        # -------------------------
        for emo in ["happy", "excited", "frustrated", "tired", "confused"]:
            if emo in t:
                self.emotions[emo] += 1

    # --------------------------------------------------
    # Inspection
    # --------------------------------------------------

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