import random

class MultiAgent:
    def __init__(self):
        self.last_signals = {}

    def run(self, text: str) -> dict:
        z = [random.uniform(0.6, 1.2) for _ in range(100)]
        sigma = [random.uniform(0.2, 1.0) for _ in range(100)]

        self.last_signals = {"z": z, "sigma": sigma}

        return {
            "final": f"Synthesised response to: {text}",
            "signals": self.last_signals
        }