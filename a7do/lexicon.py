class Lexicon:
    """
    Infant word store.
    """

    def __init__(self):
        self.words = {}
        # word -> count

    def learn_from_tokens(self, tokens):
        for t in tokens:
            if t not in self.words:
                self.words[t] = 0
            self.words[t] += 1

    def known_words(self):
        return dict(self.words)