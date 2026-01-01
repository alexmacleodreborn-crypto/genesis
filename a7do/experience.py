class ExperienceStore:
    """
    Stores simple experiences.
    No interpretation.
    """

    def __init__(self):
        self.raw_phrases = []

    def add_raw_phrase(self, phrase: str):
        self.raw_phrases.append(phrase)

    def recent(self, n=10):
        return self.raw_phrases[-n:]