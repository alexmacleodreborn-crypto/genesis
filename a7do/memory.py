class Memory:
    def __init__(self):
        self.entries = []

    def add(self, kind: str, content: str, emotion: str):
        self.entries.append({
            "kind": kind,
            "content": content,
            "emotion": emotion
        })

    def recent(self, n=5):
        return self.entries[-n:]

    def summary(self):
        return {
            "count": len(self.entries),
            "last": self.entries[-1] if self.entries else None
        }