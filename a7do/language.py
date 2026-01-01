class LanguageModule:
    def __init__(self):
        self._speaker = None

    def lock_speaker(self, name):
        self._speaker = name

    def speaker(self):
        return self._speaker