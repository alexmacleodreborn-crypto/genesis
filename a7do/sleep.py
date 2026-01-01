class SleepEngine:
    """
    Sleep = replay only.
    No summary. No abstraction.
    """

    def replay(self, experiences):
        # visual reoccurrence placeholder
        return {
            "replayed_phrases": experiences.recent(5),
            "note": "A7DO replayed recent experiences."
        }