class Memory:
    def __init__(self):
        self.entries = []

    def add(self, kind: str, content: str):
        self.entries.append({
            "kind": kind,
            "content": content
        })

    def recent(self, n=5):
        return self.entries[-n:]

    def summary(self):
        return {"count": len(self.entries)}