import re
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class LanguageState:
    speaker_name: Optional[str] = None
    last_self_assertion: Optional[str] = None
    rules: Dict[str, Any] = field(default_factory=dict)


class LanguageModule:
    """
    Language grounding layer (v1):
    - Pronouns (I/me/my) bind to SPEAKER
    - Ostensive self-binding: "I am Alex", "my name is Alex" locks speaker identity
    - Ownership cues: "my dog" => relation with SPEAKER
    """

    SELF_PATTERNS = [
        re.compile(r"^\s*my name is\s+(?P<name>.+?)\s*$", re.I),
        re.compile(r"^\s*i am\s+(?P<name>.+?)\s*$", re.I),
        re.compile(r"^\s*i'm\s+(?P<name>.+?)\s*$", re.I),
        re.compile(r"^\s*call me\s+(?P<name>.+?)\s*$", re.I),
    ]

    def __init__(self):
        self.state = LanguageState()
        # fixed pronoun rules (can expand later)
        self.state.rules["pronouns"] = {
            "i": "SPEAKER",
            "me": "SPEAKER",
            "my": "SPEAKER_POSSESSIVE",
            "mine": "SPEAKER_POSSESSIVE",
            "you": "SYSTEM",
            "your": "SYSTEM_POSSESSIVE",
        }

    def interpret(self, text: str) -> Dict[str, Any]:
        """
        Returns a dict with:
        - speaker_name (if inferred/locked)
        - pronoun_hits
        - ownership_hits
        - self_assertion (bool)
        """
        t = (text or "").strip()
        tl = t.lower()

        out: Dict[str, Any] = {
            "speaker_name": None,
            "self_assertion": False,
            "pronoun_hits": set(),
            "ownership_hits": set(),  # e.g. {"dog"}
        }

        # Pronoun hits
        for w in re.findall(r"[a-zA-Z']+", tl):
            if w in self.state.rules["pronouns"]:
                out["pronoun_hits"].add(w)

        # Ownership hits (very simple v1)
        # "my dog", "my cat", "my friend" etc. For now focus on dog.
        if "my dog" in tl:
            out["ownership_hits"].add("dog")

        # Ostensive self-binding (strong lock)
        for pat in self.SELF_PATTERNS:
            m = pat.match(t)
            if m:
                name = (m.group("name") or "").strip()
                # strip trailing punctuation
                name = name.strip(" .!?")
                if name:
                    out["speaker_name"] = name
                    out["self_assertion"] = True
                break

        return out

    def lock_speaker(self, name: str):
        name = (name or "").strip().strip(" .!?")
        if not name:
            return
        self.state.speaker_name = name
        self.state.last_self_assertion = name

    def speaker(self) -> Optional[str]:
        return self.state.speaker_name