import random


class MultiAgent:
    """
    Explorer–Critic–Integrator reasoning engine.
    Stateless by design.
    """

    def run(self, text: str, mode: str = "deliberation") -> dict:
        if mode == "recognition":
            return self._recognition(text)

        return self._deliberation(text)

    # --------------------------------------------------
    # Recognition (low-load cognition)
    # --------------------------------------------------

    def _recognition(self, text: str) -> dict:
        z = [1.0 for _ in range(30)]
        sigma = [0.25 for _ in range(30)]

        return {
            "final": "",
            "signals": {
                "z": z,
                "sigma": sigma,
                "mode": "recognition"
            }
        }

    # --------------------------------------------------
    # Deliberation (full reasoning)
    # --------------------------------------------------

    def _deliberation(self, text: str) -> dict:
        steps = 100

        z = [random.uniform(0.5, 1.2) for _ in range(steps)]
        sigma = [random.uniform(0.2, 1.0) for _ in range(steps)]

        integrator = f"Synthesised response to: {text}"

        return {
            "final": integrator,
            "signals": {
                "z": z,
                "sigma": sigma,
                "mode": "deliberation"
            }
        }