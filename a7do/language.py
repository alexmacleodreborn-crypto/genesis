import re
from typing import Dict, Any, List

from a7do.linguistic_roles import decide_entity_candidates, CandidateDecision


RE_SELF = re.compile(
    r"^\s*(my\s+name\s+is|i\s+am|i'm)\s+(?P<name>[A-Za-z][A-Za-z\- ]+)\s*[.!?]*\s*$",
    re.I
)

class LanguageModule:
    """
    Stage-1: Language module with Linguistic Role Filter (LRF).
    It provides:
      - speaker locking ("my name is Alex")
      - entity candidate extraction (capitalised tokens, role-filtered)
      - guard decisions for UI/debugging
    """

    def __init__(self):
        self._speaker_name = None
        self.last_guard: Dict[str, Any] = {
            "accepted": [],
            "rejected": [],
        }

    def speaker(self):
        return self._speaker_name

    def lock_speaker(self, name: str):
        if name and isinstance(name, str):
            self._speaker_name = name.strip()

    def interpret(self, text: str) -> Dict[str, Any]:
        """
        Detect self-assertion: "my name is Alex", "I am Alex", "I'm Alex"
        """
        m = RE_SELF.match(text or "")
        if not m:
            return {"self_assertion": False}

        name = (m.group("name") or "").strip()
        # normalize multiple spaces
        name = " ".join(name.split())
        return {"self_assertion": True, "speaker_name": name}

    def entity_candidates(self, text: str) -> List[str]:
        """
        Stage-1 entity candidate extraction with role filtering.
        Updates last_guard for UI.
        """
        accepted, decisions = decide_entity_candidates(text or "")
        self.last_guard = {
            "accepted": [d.token for d in decisions if d.accepted],
            "rejected": [{"token": d.token, "reason": d.reason} for d in decisions if not d.accepted],
        }
        return accepted