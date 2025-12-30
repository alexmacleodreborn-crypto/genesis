import re
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class TokenRole:
    text: str
    role: str  # PRONOUN, DETERMINER, PROPER_NOUN, COMMON_NOUN, UNKNOWN


class LinguisticRoleGuard:
    """
    Minimal grammar guard (v1).
    Prevents pronouns/determiners from contaminating identity binding.
    """

    PRONOUNS = {"i", "me", "you", "he", "she", "we", "they", "him", "her", "them", "us"}
    DETERMINERS = {"my", "your", "his", "her", "our", "their", "a", "an", "the", "this", "that", "these", "those"}

    # Tokens we never allow to bind as identity anchors (even if capitalized)
    NEVER_NAME = {"i", "my", "a", "an", "the", "this", "that"}

    # Lightweight naming triggers
    NAMING_TRIGGERS = {
        "called", "named", "name", "nickname", "nicknamed", "known as"
    }

    def tokenize(self, text: str) -> List[str]:
        return re.findall(r"[A-Za-z']+", text)

    def classify(self, text: str) -> List[TokenRole]:
        tokens = self.tokenize(text)
        out: List[TokenRole] = []

        for tok in tokens:
            low = tok.lower()

            if low in self.PRONOUNS:
                out.append(TokenRole(tok, "PRONOUN"))
                continue

            if low in self.DETERMINERS:
                out.append(TokenRole(tok, "DETERMINER"))
                continue

            # Proper noun heuristic: title-case token not in NEVER_NAME
            if tok.istitle() and low not in self.NEVER_NAME:
                out.append(TokenRole(tok, "PROPER_NOUN"))
                continue

            # Everything else: unknown/common
            out.append(TokenRole(tok, "UNKNOWN"))

        return out

    def is_naming_context(self, text: str) -> bool:
        t = text.lower()
        if " is called " in t or " named " in t:
            return True
        if any(trig in t for trig in self.NAMING_TRIGGERS):
            return True
        if t.strip().startswith("this is "):
            return True
        return False

    def speaker_intent(self, roles: List[TokenRole]) -> Dict[str, bool]:
        """
        Determines whether the utterance is about the speaker.
        """
        lows = [r.text.lower() for r in roles]
        return {
            "mentions_i": any(x in {"i", "me"} for x in lows),
            "mentions_my": "my" in lows
        }