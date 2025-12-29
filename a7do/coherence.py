from dataclasses import dataclass
from typing import List


@dataclass
class CoherenceState:
    sigma: float
    z: float
    divergence: float
    coherence: float
    domains: List[str]


def compute_coherence(domains: List[str], recall_strength: float, emotional_valence: float) -> CoherenceState:
    """
    Simple placeholder for SLED-style coherence:
    - more domains → higher entropy (sigma)
    - stronger recall → higher z (confidence)
    - emotional valence modulates z slightly
    """
    num_domains = max(1, len(domains))
    domain_entropy = 0.3 + 0.1 * (num_domains - 1)

    sigma = 0.2 + 0.2 * domain_entropy
    z = 0.4 + 0.4 * recall_strength
    z += 0.1 * emotional_valence
    z = max(0.0, min(1.0, z))

    divergence = sigma * (1 - z)
    coherence = max(0.0, 1.0 - divergence)

    return CoherenceState(
        sigma=sigma,
        z=z,
        divergence=divergence,
        coherence=coherence,
        domains=domains,
    )


def describe_coherence(state: CoherenceState) -> str:
    """
    Human-readable description in SLED-ish language.
    """
    level = "low"
    if state.coherence > 0.75:
        level = "high"
    elif state.coherence > 0.45:
        level = "medium"

    return (
        f"Using my SLED-style intuition, this feels like {level} coherence "
        f"(coherence={state.coherence:.2f}, sigma={state.sigma:.2f}, z={state.z:.2f}, "
        f"domains={state.domains})."
    )
