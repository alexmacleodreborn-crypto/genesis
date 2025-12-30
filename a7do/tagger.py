import re
from collections import defaultdict


class Tagger:
    """
    Multi-domain tagger for incoming language.
    One input can belong to many domains.
    """

    BASE_DOMAINS = {
        # Social + self
        "relationship": [r"\bi\b", r"\bmy\b", r"\bme\b", r"\bwe\b", r"\bour\b", r"\byou\b"],
        "people": [r"\b(dad|mum|friend|alex|conner)\b"],

        # Affect + cognition language
        "emotion": ["happy", "sad", "like", "love", "hate", "frustrated", "excited", "anxious", "angry"],
        "cognition": ["remember", "forget", "attention", "focus", "mind", "thought", "coherence", "decoherence"],

        # Time
        "timeline": ["yesterday", "today", "tomorrow", "before", "after", "later", "now", "then"],

        # Language/symbols
        "language_symbols": ["word", "sentence", "meaning", "symbol", "letter", "grammar", "semantics"],

        # Technical domains
        "maths": ["equation", "number", "math", "calculate", "integral", "derivative", "proof"],
        "computing": ["code", "program", "python", "software", "system", "streamlit", "api", "repo", "github"],
        "ai_neural": ["ai", "neural", "model", "network", "agent", "llm", "training", "inference"],
        "algorithms": ["algorithm", "optimise", "search", "heuristic", "complexity"],

        # Sciences
        "science": ["physics", "biology", "chemistry", "science"],
        "quantum": ["quantum", "wavefunction", "superposition", "measurement", "entanglement", "decoherence"],
        "neuroscience": ["brain", "alzheim", "dementia", "neuron", "synapse", "hippocampus"],

        # Your projects
        "sled": ["sled", "a7do", "doorman", "concierge", "manager", "ymarket"],
        "sandys_law": ["sandy", "sandys law", "omnifield", "omnium", "z–σ", "z-sigma", "photon escape"],
        "tesla": ["tesla", "nikola tesla", "alternator", "wireless power", "resonance", "coil", "oscillator"],
    }

    def tag(self, text: str) -> dict:
        t = text.lower()
        tags = defaultdict(int)

        for domain, patterns in self.BASE_DOMAINS.items():
            for p in patterns:
                if p.startswith(r"\b") or any(ch in p for ch in "[]()\\"):
                    # regex-ish pattern
                    if re.search(p, t):
                        tags[domain] += 1
                else:
                    # plain keyword
                    if p in t:
                        tags[domain] += 1

        return dict(tags)