class Lexicon:
    """
    Exposure counts only (infant stage).
    No semantic claims.
    """

    def __init__(self):
        self.words = {}

    def _inc(self, token: str):
        t = (token or "").strip().lower()
        if not t:
            return
        self.words[t] = self.words.get(t, 0) + 1

    def learn_from_event(self, ev):
        # place anchors
        self._inc(ev.room)
        if ev.to_room:
            self._inc(ev.to_room)

        # core language exposure
        self._inc(ev.agent)
        self._inc(ev.action)
        if ev.obj:
            self._inc(ev.obj)

        # emphasis (catch the BALL)
        for w in (ev.emphasis or []):
            self._inc(w)

        # sensory tokens (as labels; still just exposure)
        if ev.sound:
            self._inc("sound")
            self._inc(ev.sound.get("pattern", ""))
        if ev.smell:
            self._inc("smell")
            self._inc(ev.smell.get("pattern", ""))
        if ev.motor:
            self._inc("motor")
            self._inc(ev.motor.get("type", ""))

    def snapshot(self):
        return dict(self.words)