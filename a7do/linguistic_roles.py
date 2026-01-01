import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

# -----------------------------
# Stage-1: Role vocabulary
# -----------------------------
FUNCTION_WORDS = {
    # pronouns / determiners
    "i", "me", "my", "mine", "myself",
    "you", "your", "yours", "yourself",
    "he", "him", "his", "she", "her", "hers",
    "they", "them", "their", "theirs",
    "we", "us", "our", "ours",

    # wh-words / question words
    "what", "who", "whom", "whose", "which", "when", "where", "why", "how",

    # conjunctions / operators
    "and", "or", "but", "so", "because", "if", "then",

    # copulas / helpers (we don’t want these promoted)
    "is", "am", "are", "was", "were", "be", "been", "being",

    # common meta words that cause the “Name / First” issue
    "name", "first", "last", "middle", "surname", "called", "named",

    # misc frequent glue words
    "a", "an", "the", "of", "to", "in", "on", "at", "for", "from", "with", "as",
}

# Words that might be capitalised but are not entities in this system.
NON_ENTITY_CAPS = {
    "Hi", "Hello", "Yes", "No", "Okay", "Ok", "Thanks", "Thank",
}

APOSTROPHE_POSSESSIVE = re.compile(r"^(?P<base>[A-Za-z][A-Za-z\-]+)'s$")


@dataclass
class CandidateDecision:
    token: str
    accepted: bool
    reason: str


def normalize_token(tok: str) -> str:
    tok = tok.strip()
    tok = tok.strip(",.!?;:()[]{}\"")
    return tok


def is_function_word(tok: str) -> bool:
    return tok.lower() in FUNCTION_WORDS


def strip_possessive(tok: str) -> Tuple[str, bool]:
    m = APOSTROPHE_POSSESSIVE.match(tok)
    if m:
        return m.group("base"), True
    return tok, False


def decide_entity_candidates(text: str) -> Tuple[List[str], List[CandidateDecision]]:
    """
    Stage-1 rule:
    - only consider *capitalised* tokens (simple heuristic)
    - reject function words (What, You, Or, Name, First, etc.)
    - reject short / junk tokens
    - allow possessives ("Craig's" -> "Craig")
    """
    raw = text.split()
    accepted: List[str] = []
    decisions: List[CandidateDecision] = []

    for tok in raw:
        tok = normalize_token(tok)
        if not tok:
            continue

        # Handle possessive: Craig's -> Craig
        base, had_possessive = strip_possessive(tok)

        # Reject non-entity common caps
        if base in NON_ENTITY_CAPS:
            decisions.append(CandidateDecision(tok, False, "non-entity common cap"))
            continue

        # Only consider likely proper nouns: TitleCase or ALLCAPS (avoid “park” etc.)
        looks_named = (base[:1].isupper() and base[1:].islower()) or base.isupper()
        if not looks_named:
            decisions.append(CandidateDecision(tok, False, "not a named token"))
            continue

        # Reject function words (what/you/name/first/or/etc.)
        if is_function_word(base):
            decisions.append(CandidateDecision(tok, False, "function word"))
            continue

        # Reject too short
        if len(base) < 2:
            decisions.append(CandidateDecision(tok, False, "too short"))
            continue

        accepted.append(base)
        reason = "accepted"
        if had_possessive:
            reason = "accepted (possessive->base)"
        decisions.append(CandidateDecision(tok, True, reason))

    # Deduplicate while preserving order
    seen = set()
    uniq = []
    for a in accepted:
        key = a.lower()
        if key not in seen:
            uniq.append(a)
            seen.add(key)

    return uniq, decisions