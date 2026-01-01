class Lexicon:
    def __init__(self):
        self.words = {}

    def learn(self, phrase):
        for w in phrase.split():
            self.words[w] = self.words.get(w, 0) + 1

    def snapshot(self):
        return dict(self.words)