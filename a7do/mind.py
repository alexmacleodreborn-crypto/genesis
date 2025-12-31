import time
import re
import inspect
from typing import Dict, Any, Set, Optional

from a7do.identity import Identity
from a7do.memory import Memory
from a7do.tagger import Tagger
from a7do.coherence import CoherenceScorer
from a7do.background_density import BackgroundDensity
from a7do.reflection import ReflectionStore
from a7do.sleep import SleepEngine

from a7do.entity_promotion import EntityPromotionBridge
from a7do.language import LanguageModule


PLACE_WORDS = {"park", "home", "garden", "vet", "beach", "gate", "street"}


class A7DOMind:
    """
    A7DO Mind (stable + speaker grounding + robust ownership parsing)

    Guarantees:
    - Speaker defaults to "Alex Macleod" unless user self-identifies otherwise
    - "Xena is my dog" always binds ownership to SPEAKER
    - Entities Alex + Xena exist and connect through relations
    """

    # Robust patterns
    RE_MY_DOG = re.compile(r"^\s*(?P<name>.+?)\s+is\s+my\s+dog\s*[.!?]*\s*$", re.I)
    RE_IS_A_DOG = re.compile(r"^\s*(?P<name>.+?)\s+is\s+a\s+dog\s*[.!?]*\s*$", re.I)
    RE_MY_DOG_CALLED = re.compile(r"^\s*my\s+dog\s+is\s+(called|named)\s+(?P<name>.+?)\s*[.!?]*\s*$", re.I)

    def __init__(self):
        self.identity = Identity()
        self.memory = Memory()
        self.tagger = Tagger()
        self.coherence = CoherenceScorer()
        self.background = BackgroundDensity()

        self.reflections = ReflectionStore()
        self.sleep_engine = SleepEngine(self.reflections)

        self.bridge = EntityPromotionBridge()
        self.language = LanguageModule()

        self._memory_add_sig = inspect.signature(self.memory.add)

    @property
    def events(self):
        return self.memory

    def _memory_add_safe(self, **kwargs):
        supported = {k: v for k, v in kwargs.items() if k in self._memory_add_sig.parameters}
        try:
            self.memory.add(**supported)
        except Exception:
            pass

    def _speaker_name(self) -> str:
        """
        Speaker is ALWAYS known:
        - use language speaker if set
        - else fall back to identity.creator if present
        - else default to Alex Macleod
        """
        s = self.language.speaker()
        if s:
            return s
        c = getattr(self.identity, "creator", None)
        if isinstance(c, str) and c.strip():
            return c.strip()
        return "Alex Macleod"

    def _ensure_person_entity(self, name: str):
        # Creates the person entity if it doesn't exist yet
        try:
            self.bridge.confirm_entity(name=name, kind="person", owner_name=None)
        except Exception:
            pass

    def _extract_place(self, text: str) -> Optional[str]:
        tl = (text or "").lower()
        for p in PLACE_WORDS:
            if p in tl:
                return p
        return None

    def process(self, text: str) -> Dict[str, Any]:
        now = time.time()
        text = text or ""
        tags = self.tagger.tag(text) or []

        # Always log the raw utterance
        self._memory_add_safe(kind="utterance", content=text, tags=tags, timestamp=now)

        # -------------------------
        # 1) Language first (self-binding)
        # -------------------------
        lang = self.language.interpret(text)
        if lang.get("self_assertion") and lang.get("speaker_name"):
            name = lang["speaker_name"]
            self.language.lock_speaker(name)
            try:
                setattr(self.identity, "creator", name)
            except Exception:
                pass

            # Crucial: create person entity for speaker
            self._ensure_person_entity(name)

            return {"answer": f"Locked. You are **{name}**.", "tags": tags}

        speaker = self._speaker_name()
        self._ensure_person_entity(speaker)

        # -------------------------
        # 2) Identity query: who am I?
        # -------------------------
        if text.strip().lower().startswith("who am i"):
            return {"answer": f"You are **{speaker}**.", "tags": tags}

        # -------------------------
        # 3) Entity statements (robust)
        # -------------------------

        # "My dog is called Xena"
        m = self.RE_MY_DOG_CALLED.match(text)
        if m:
            name = m.group("name").strip().strip(" .!?")
            name = name[:1].upper() + name[1:] if name else name

            ent = self.bridge.confirm_entity(
                name=name,
                kind="pet",
                owner_name=speaker,
                relation="my dog",
            )
            return {"answer": f"Noted. **{ent.name}** is your dog.", "tags": tags}

        # "Xena is my dog"
        m = self.RE_MY_DOG.match(text)
        if m:
            name = m.group("name").strip().strip(" .!?")
            name = name[:1].upper() + name[1:] if name else name

            ent = self.bridge.confirm_entity(
                name=name,
                kind="pet",
                owner_name=speaker,
                relation="my dog",
            )
            return {"answer": f"Noted. **{ent.name}** is your dog.", "tags": tags}

        # "Xena is a dog"
        m = self.RE_IS_A_DOG.match(text)
        if m:
            name = m.group("name").strip().strip(" .!?")
            name = name[:1].upper() + name[1:] if name else name

            ent = self.bridge.confirm_entity(
                name=name,
                kind="pet",
                owner_name=None,
                relation=None,
            )
            return {"answer": f"Noted. **{ent.name}** is a dog.", "tags": tags}

        # -------------------------
        # 4) Who is X? (owner-aware)
        # -------------------------
        if text.strip().lower().startswith("who is "):
            name = text.strip()[7:].strip(" ?!.")
            desc = self.bridge.describe(name, owner_name=speaker)
            if desc:
                return {"answer": desc, "tags": tags}

            # ambiguity
            cands = self.bridge.candidates(name)
            if cands and len(cands) > 1:
                # human labels
                labels = []
                for e in cands[:2]:
                    if e.owner_name and e.owner_name.lower() == speaker.lower():
                        labels.append(f"your {e.name}")
                    else:
                        labels.append(f"the other {e.name}")
                return {"answer": f"Do you mean **1) {labels[0]}** or **2) {labels[1]}**?", "tags": tags}

            return {"answer": f"I don’t know who **{name}** is yet.", "tags": tags}

        # -------------------------
        # 5) Experience binding (basic, safe)
        # -------------------------
        # (You already want full mind-pathing; we’ll add event graph next once this works)
        # For now just capture place and mentioned entities into memory tags later.
        place = self._extract_place(text)
        if place:
            # add a second structured memory entry (optional)
            self._memory_add_safe(kind="context", content=f"place:{place}", tags=["place"], timestamp=now)

        # Observe unknown Titlecase names as pending
        self.bridge.observe(text, owner_name=speaker)

        # -------------------------
        # Default
        # -------------------------
        return {"answer": "Noted.", "tags": tags}