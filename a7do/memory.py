class Memory:
    def __init__(self):
        self.entries = []

    def add(self, **kwargs):
        self.entries.append(kwargs)

    def recent(self, n: int = 20):
        return self.entries[-n:]