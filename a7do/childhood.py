import time


class Childhood:
    """
    Childhood experiential learning (ages ~0–5).

    - Activates only on simple, concrete language
    - Runs in short bursts
    - Produces low-confidence imprints (not facts)
    """

    def __init__(self, burst_seconds: int = 10):
        self.burst_seconds = burst_seconds
        self._active_until = None
        self.imprints = []

    # --------------------------------------------------

    def is_simple_input(self, text: str) -> bool:
        """
        VERY conservative filter for child-like input.
        """
        t = text.lower()

        simple_words = [
            "see", "is", "my", "this", "that",
            "dog", "cat", "ball", "bike", "room",
            "mum", "dad", "blue", "red", "big", "small"
        ]

        # short, simple sentences only
        if len(t.split()) > 8:
            return False

        return any(w in t for w in simple_words)

    # --------------------------------------------------

    def start_burst(self):
        self._active_until = time.time() + self.burst_seconds

    def is_active(self) -> bool:
        return self._active_until is not None and time.time() < self._active_until

    # --------------------------------------------------

    def absorb(self, text: str):
        if not self.is_active():
            return

        self.imprints.append({
            "text": text,
            "time": time.time()
        })

    # --------------------------------------------------

    def summary(self):
        return {
            "active": self.is_active(),
            "imprint_count": len(self.imprints),
            "recent": self.imprints[-5:]
        }