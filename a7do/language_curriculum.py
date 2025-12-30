import time


class LanguageCurriculum:
    """
    Drip-feed foundational English learning in small bursts.

    - Runs on a timer (default 10s).
    - Produces structured "lesson packets" (alphabet, phonics, words, sentences, tense).
    - Designed to be low-risk: it becomes foundational memory + background density, not immediate beliefs.
    """

    def __init__(self, drip_seconds: int = 10):
        self.drip_seconds = drip_seconds
        self._last_drip_ts = 0.0
        self._i = 0

        # A small but expandable curriculum.
        self._lessons = self._build_lessons()

    def _build_lessons(self):
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        vowels = "AEIOU"
        consonants = "".join([c for c in alphabet if c not in vowels])

        lessons = [
            {
                "title": "Alphabet introduction",
                "tags": ["foundational", "language", "alphabet"],
                "content": {
                    "alphabet": list(alphabet),
                    "vowels": list(vowels),
                    "consonants": list(consonants),
                },
            },
            {
                "title": "Letters are symbols",
                "tags": ["foundational", "language", "symbols"],
                "content": {
                    "idea": "Letters are symbols used to build words.",
                    "examples": ["A", "B", "C", "a", "b", "c"],
                    "note": "Uppercase and lowercase represent the same letter."
                },
            },
            {
                "title": "Phonics burst: basic blends",
                "tags": ["foundational", "language", "phonics"],
                "content": {
                    "blends": ["ba", "be", "bi", "bo", "bu", "da", "de", "di", "do", "du"],
                    "idea": "Sounds can combine to form syllables."
                },
            },
            {
                "title": "Word types: nouns (things)",
                "tags": ["foundational", "language", "words", "nouns"],
                "content": {
                    "definition": "A noun is a person, place, thing, or idea.",
                    "examples": ["bike", "room", "Alex", "chair", "dog"]
                },
            },
            {
                "title": "Word types: verbs (actions)",
                "tags": ["foundational", "language", "words", "verbs"],
                "content": {
                    "definition": "A verb is an action or state.",
                    "examples": ["ride", "walk", "build", "learn", "is", "are"]
                },
            },
            {
                "title": "Word types: adjectives (descriptions)",
                "tags": ["foundational", "language", "words", "adjectives"],
                "content": {
                    "definition": "An adjective describes a noun.",
                    "examples": ["blue", "small", "fast", "new", "old"]
                },
            },
            {
                "title": "Sentence pattern: Subject → Verb → Object",
                "tags": ["foundational", "language", "sentences", "grammar"],
                "content": {
                    "pattern": ["Subject", "Verb", "Object"],
                    "examples": [
                        "I ride a bike.",
                        "Alex builds systems.",
                        "We learn words."
                    ],
                },
            },
            {
                "title": "Tense: ride / rode / riding",
                "tags": ["foundational", "language", "tense", "morphology"],
                "content": {
                    "base": "ride",
                    "past": "rode",
                    "continuous": "riding",
                    "examples": [
                        "I ride my bike.",
                        "I rode my bike yesterday.",
                        "I am riding my bike now."
                    ],
                },
            },
            {
                "title": "Meaning links: synonyms (small set)",
                "tags": ["foundational", "language", "semantics"],
                "content": {
                    "pairs": [
                        ["happy", "glad"],
                        ["sad", "unhappy"],
                        ["fast", "quick"],
                        ["big", "large"],
                    ],
                    "idea": "Some different words can share a similar meaning."
                },
            },
        ]

        return lessons

    def ready(self) -> bool:
        now = time.time()
        return (now - self._last_drip_ts) >= self.drip_seconds

    def next_packet(self) -> dict:
        """
        Returns the next lesson packet and advances the pointer.
        Loops the curriculum for now.
        """
        pkt = self._lessons[self._i % len(self._lessons)]
        self._i += 1
        self._last_drip_ts = time.time()
        return pkt

    def peek_progress(self) -> dict:
        return {
            "drip_seconds": self.drip_seconds,
            "last_drip_age_s": (time.time() - self._last_drip_ts) if self._last_drip_ts else None,
            "lesson_index": self._i,
            "lesson_total": len(self._lessons),
        }