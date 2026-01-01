class Lexicon:
    """
    Tracks word exposure by context.
    """

    def __init__(self):
        self.words = {}

    def learn_from_event(self, event):
        tokens = [
            event.place,
            event.agent,
            event.action
        ]

        if event.object:
            tokens.append(event.object)

        tokens += event.emphasis

        for t in tokens:
            t = t.lower()
            self.words[t] = self.words.get(t, 0) + 1

    def snapshot(self):
        return dict(self.words)