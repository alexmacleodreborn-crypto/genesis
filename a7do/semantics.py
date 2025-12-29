from typing import List, Dict


# ------------------------------------------------------------
# 1. Homophones and easily-confused word families
# ------------------------------------------------------------
HOMOPHONE_GROUPS = [
    {"break", "brake"},
    {"arm"},  # body part vs weapon context
    {"fall"},  # season vs action
]

HOMOPHONE_MAP: Dict[str, set] = {}
for group in HOMOPHONE_GROUPS:
    for w in group:
        HOMOPHONE_MAP[w] = group


# ------------------------------------------------------------
# 2. Semantic clusters (conceptual categories)
# ------------------------------------------------------------
SEMANTIC_CLUSTERS: Dict[str, List[str]] = {
    "injury": ["break", "broke", "hurt", "fracture", "arm", "pain", "injury"],
    "mechanical": ["brake", "gear", "engine", "wheel", "mechanical"],
    "emotion": ["sad", "happy", "fear", "love", "hurt", "lonely"],
    "identity": ["name", "alex", "a7do", "father", "self"],
    "narrative": ["story", "stories", "time", "meaning", "events"],
    "math": ["number", "numbers", "count", "math", "pattern"],
    "science": ["gravity", "atom", "energy", "planet", "biology"],
    "body": ["arm", "leg", "hand", "head", "body", "hurt"],
}


# ------------------------------------------------------------
# 3. Sense disambiguation rules
# ------------------------------------------------------------
def disambiguate(word: str, context: List[str]) -> str:
    """
    Returns a sense-tagged version of the word.
    Example: "break" -> "break_injury" or "break_mechanical"
    """
    w = word.lower()

    if w not in HOMOPHONE_MAP:
        return w

    # Injury context
    if any(c in context for c in ["hurt", "pain", "arm", "injury", "broke"]):
        return f"{w}_injury"

    # Mechanical context
    if any(c in context for c in ["car", "engine", "wheel", "gear", "mechanical"]):
        return f"{w}_mechanical"

    return w


# ------------------------------------------------------------
# 4. Semantic expansion
# ------------------------------------------------------------
def semantic_expand(word: str) -> List[str]:
    """
    Returns semantic tags for a word:
    - cluster names
    - sense-specific tags
    """
    tags = [word]

    # Strip sense suffix (e.g. break_injury -> break) for cluster lookup
    base = word.split("_")[0]

    for cluster_name, cluster_words in SEMANTIC_CLUSTERS.items():
        if base in cluster_words or word in cluster_words:
            tags.append(cluster_name)

    return tags


# ------------------------------------------------------------
# 5. Main semantic tagging function
# ------------------------------------------------------------
def semantic_tags(words: List[str]) -> List[str]:
    """
    Given a list of raw words, return:
    - disambiguated words
    - semantic cluster tags
    """
    context = set(words)
    final_tags: List[str] = []

    for w in words:
        sense = disambiguate(w, list(context))
        expanded = semantic_expand(sense)
        final_tags.extend(expanded)

    return list(sorted(set(final_tags)))
