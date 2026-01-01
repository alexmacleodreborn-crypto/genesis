import re
from dataclasses import dataclass
from typing import List


@dataclass
class SensoryExtraction:
    smells: List[str]          # normalised labels like "smoke_smell"
    sounds: List[str]          # normalised labels like "birds_sound"
    raw: List[str]             # raw phrases like "smell smoke"


def _norm(label: str, suffix: str) -> str:
    label = (label or "").strip().lower()
    label = re.sub(r"[^a-z0-9\s\-]", "", label)
    label = re.sub(r"\s+", "_", label).strip("_")
    if not label:
        return ""
    return f"{label}_{suffix}"


class SensoryParser:
    """
    Refined sensory grounding.
    Smell and sound now behave symmetrically.

    Stores:
      - RAW phrases
      - NORMALISED tokens with suffix _smell / _sound
    """

    # Smell patterns
    RE_SMELL_LIKE = re.compile(r"\b(smell(?:ed|s)?\s+like)\s+([a-zA-Z0-9\s\-]+)", re.I)
    RE_SMELL_SIMPLE = re.compile(r"\b(smell|smells|smelled|can\s+smell|i\s+smell)\s+([a-zA-Z0-9\s\-]+)", re.I)

    # Sound patterns
    RE_SOUND_HEAR = re.compile(r"\b(hear|heard|could\s+hear)\s+([a-zA-Z0-9\s\-]+)", re.I)
    RE_SOUND_OF = re.compile(r"\b(sound|noise)\s+of\s+([a-zA-Z0-9\s\-]+)", re.I)

    def extract(self, text: str) -> SensoryExtraction:
        text = text or ""
        smells_n, sounds_n, raw = [], [], []

        # --- Smells (like)
        for m in self.RE_SMELL_LIKE.finditer(text):
            phrase, thing = m.group(1), (m.group(2) or "").strip()
            if thing:
                raw.append(f"{phrase} {thing}".strip())
                n = _norm(thing, "smell")
                if n:
                    smells_n.append(n)

        # --- Smells (simple)
        for m in self.RE_SMELL_SIMPLE.finditer(text):
            phrase, thing = m.group(1), (m.group(2) or "").strip()
            if thing:
                raw.append(f"{phrase} {thing}".strip())
                n = _norm(thing, "smell")
                if n:
                    smells_n.append(n)

        # --- Sounds (hear/heard)
        for m in self.RE_SOUND_HEAR.finditer(text):
            phrase, thing = m.group(1), (m.group(2) or "").strip()
            if thing:
                raw.append(f"{phrase} {thing}".strip())
                n = _norm(thing, "sound")
                if n:
                    sounds_n.append(n)

        # --- Sounds (sound/noise of X)
        for m in self.RE_SOUND_OF.finditer(text):
            phrase, thing = m.group(1), (m.group(2) or "").strip()
            if thing:
                raw.append(f"{phrase} of {thing}".strip())
                n = _norm(thing, "sound")
                if n:
                    sounds_n.append(n)

        # Deduplicate while preserving order
        def uniq(seq):
            seen = set()
            out = []
            for x in seq:
                if x not in seen:
                    out.append(x)
                    seen.add(x)
            return out

        return SensoryExtraction(
            smells=uniq(smells_n),
            sounds=uniq(sounds_n),
            raw=uniq(raw),
        )