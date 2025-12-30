import random


class MultiAgent:
    """
    Explorer–Critic–Integrator reasoning engine.
    Coherence-aware and self-stabilising.
    Stateless by design.
    """

    def run(self, text: str, mode: str = "deliberation", coherence_hint: float | None = None) -> dict:
        if mode == "recognition":
            return self._recognition(text)

        return self._deliberation(text, coherence_hint)

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
    # Deliberation (coherence-aware)
    # --------------------------------------------------

    def _deliberation(self, text: str, coherence_hint: float | None) -> dict:
        # Default behaviour (no history yet)
        if coherence_hint is None:
            steps = 100
            sigma_scale = 1.0
            z_scale = 1.0
        else:
            # High coherence → more exploration
            if coherence_hint >= 0.75:
                steps = 120
                sigma_scale = 1.2
                z_scale = 0.9

            # Medium coherence → balanced
            elif coherence_hint >= 0.55:
                steps = 100
                sigma_scale = 1.0
                z_scale = 1.0

            # Low coherence → stabilise
            else:
                steps = 60
                sigma_scale = 0.6
                z_scale = 1.3

        z = [random.uniform(0.5, 1.2) * z_scale for _ in range(steps)]
        sigma = [random.uniform(0.2, 1.0) * sigma_scale for _ in range(steps)]

        integrator = f"Synthesised response to: {text}"

        return {
            "final": integrator,
            "signals": {
                "z": z,
                "sigma": sigma,
                "mode": "deliberation"
            }
        }