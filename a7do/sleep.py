class SleepEngine:
    def replay(self, experiences):
        return {
            "replayed": experiences.recent(),
            "note": "replay only, no abstraction"
        }