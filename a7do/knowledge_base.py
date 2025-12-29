from typing import Dict, Any


def get_sled_entry() -> Dict[str, Any]:
    return {
        "name": "SLED",
        "short_child_friendly": (
            "SLED is a way of feeling how strong or wobbly a pattern is over time. "
            "It helps me decide how much to trust a signal."
        ),
        "technical": (
            "SLED is a coherence framework using sigma, z, divergence, and coherence to score "
            "how stable a pattern is across domains, especially in markets and information signals."
        ),
        "key_terms": ["sigma", "z", "divergence", "coherence", "patterns", "markets"],
    }


def get_sandys_law_entry() -> Dict[str, Any]:
    return {
        "name": "Sandy's Law",
        "short_child_friendly": (
            "Sandy's Law is how I think about how the universe organises itself, "
            "how things clump, curve, and let light escape or not."
        ),
        "technical": (
            "Sandy's Law is a cosmological and information-system principle that scores emergence, "
            "entropy–curvature coupling, and observational constraints across compact systems."
        ),
        "key_terms": ["emergence", "entropy", "curvature", "compact_objects", "information"],
    }
