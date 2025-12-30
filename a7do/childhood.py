import time
import re
from collections import defaultdict

class Childhood:
    """
    Childhood learning module.
    Handles short, passive learning bursts without reasoning or output.
    """

    BURST_DURATION = 10.0  # seconds

    def __init__(self):
        self.active = False
        self.start_time = None

        # Primitive learning stores
        self.letters = defaultdict(int)
        self.symbols = defaultdict(int)
        self.words = defaultdict(int)
        self.relations = defaultdict(int)

        self.last_burst_summary = {}

    # -------------------------------------------------
    # Lifecycle
    # -------------------------------------------------

    def start_burst(self):
        self.active = True
        self.start_time = time.time()
        self.last_burst_summary = {}

    def is_active(self) -> bool:
        if not self.active:
            return False
        if time.time() - self.start_time > self.BURST_DURATION:
            self.end_burst()
            return False
        return True

    def end_burst(self):
        self.active = False
        self.start_time = None

        self.last_burst_summary = {
            "letters": dict(self.letters),
            "symbols": dict(self.symbols),
            "words": dict(self.words),
            "relations": dict(self.relations),
        }

    # -------------------------------------------------
    # Learning
    # -------------------------------------------------

    def absorb(self, text: str):
        """
        Passive learning only.
        No inference, no reasoning.
        """
        if not self.is_active():
            return

        # Letters
        for c in text:
            if c.isalpha():
                self.letters[c.lower()] += 1
            elif not c.isspace():
                self.symbols[c] += 1

        # Words
        for w in re.findall(r"\b[a-zA-Z]{2,}\b", text):
            self.words[w.lower()] += 1

        # Simple relations (very primitive)
        relation_patterns = [
            r"\b(is)\b",
            r"\b(are)\b",
            r"\b(means)\b",
            r"\b(=)\b",
        ]

        for pattern in relation_patterns:
            if re.search(pattern, text.lower()):
                self.relations[pattern] += 1

    # -------------------------------------------------
    # Introspection
    # -------------------------------------------------

    def summary(self):
        return {
            "active": self.active,
            "seconds_remaining": max(
                0,
                round(self.BURST_DURATION - (time.time() - self.start_time), 2)
            ) if self.active else 0,
            "letters": dict(self.letters),
            "symbols": dict(self.symbols),
            "words": dict(self.words),
            "relations": dict(self.relations),
        }