import random

class MultiAgent:
    def __init__(self):
        self._last = {}

    def run(self, prompt: str):
        explorer = f"Exploring interpretations of: {prompt}"
        critic = f"Challenging assumptions in: {prompt}"
        integrator = f"Synthesised response to: {prompt}"

        # Generate fake but structured signals (replace with real math later)
        z = [random.uniform(0.5, 1.2) for _ in range(100)]
        sigma = [random.uniform(0.2, 1.1) for _ in range(100)]

        self._last = {"z": z, "sigma": sigma}

        return {
            "explorer": explorer,
            "critic": critic,
            "final": integrator
        }

    def last_signals(self):
        return self._last