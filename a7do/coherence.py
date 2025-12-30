# a7do/coherence.py

class CoherenceScorer:
    """
    Coherence scoring for A7DO.
    Returns a score in [0,1] plus a label.
    """

    def score(self, *, mode: str, emotion_value: float, signals: dict | None) -> dict:
        # Base score by mode (recognition is naturally more stable)
        base = 0.85 if mode == "recognition" else 0.65

        # Emotional penalty (large absolute emotion drifts reduce coherence)
        # Keep mild effect; this is a toy stability term.
        emo_penalty = min(abs(emotion_value) / 5.0, 0.25)  # caps at 0.25

        # Signal-based coherence from Z–Σ if available
        sig_bonus = 0.0
        if signals and signals.get("z") and signals.get("sigma"):
            z = signals["z"]
            sigma = signals["sigma"]
            # coherence trace: sigma/(z+eps)
            eps = 1e-3
            coh = [s / (zz + eps) for s, zz in zip(sigma, z)]
            # reward if median coherence stays under threshold (stable)
            median = sorted(coh)[len(coh) // 2]
            # Lower median coherence implies more constraint; clamp
            stability = max(0.0, min(1.0, 1.0 - median))  # invert-ish
            sig_bonus = 0.20 * stability  # small bonus

        score = base - emo_penalty + sig_bonus
        score = max(0.0, min(1.0, score))

        if score >= 0.75:
            label = "GREEN"
        elif score >= 0.55:
            label = "AMBER"
        else:
            label = "RED"

        return {"score": round(score, 3), "label": label}