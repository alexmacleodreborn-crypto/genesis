class ExperienceStore:
    def __init__(self):
        self.items = []

    def add(self, text):
        self.items.append(text)

    def recent(self, n=5):
        return self.items[-n:]