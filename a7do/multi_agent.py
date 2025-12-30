import random


class MultiAgent:
    """
    Explorer–Critic–Integrator reasoning system.
    """

    def __init__(self):
        pass

    # --------------------------------------------------
    # Public interface
    # --------------------------------------------------

    def run(self, text: str, mode: str = "deliberation") -> dict:
        """
        mode:
          - recognition: fast, minimal reasoning
          - deliberation: full cognitive dynamics
        """

        if mode == "recognition":
            return self._recognition(text)

        return self._deliberation(text)

    # --------------------------------------------------
    # Recognition (low cognitive load)
    # --------------------------------------------------

    def _recognition(self, text: str) -> dict:
        z = [1.0 for _ in range(30)]
        sigma = [0.2 for _ in range(30)]

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

        explorer = [
            "Exploring possible meanings",
            "Generating hypotheses",
            "Expanding interpretation"
        ]

        critic = [
            "Checking consistency",
            "Reducing ambiguity"
        ]

        integrator = "Synthesised response to: " + text

        return {
            "final": integrator,
            "signals": {
                "z": z,
                "sigma": sigma,
                "mode": "deliberation"
            }
        }