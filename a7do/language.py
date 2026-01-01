class LanguageModule:
    def __init__(self):
        self._speaker = None  # locked user name

    def lock_speaker(self, name: str):
        self._speaker = (name or "").strip()

    def speaker(self):
        return self._speaker