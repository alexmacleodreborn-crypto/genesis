import time
import inspect
from typing import Dict, Any, Set

from a7do.identity import Identity
from a7do.memory import Memory
from a7do.tagger import Tagger
from a7do.coherence import CoherenceScorer
from a7do.background_density import BackgroundDensity
from a7do.reflection import ReflectionStore
from a7do.sleep import SleepEngine

from a7do.entity_promotion import EntityPromotionBridge
from a7do.language import LanguageModule
from a7do.event_graph import EventGraph


PLACE_WORDS = {"park", "home", "garden", "vet", "beach", "gate"}


class A7DOMind:
    def __init__(self):
        self.identity = Identity()
        self.memory = Memory()
        self.tagger = Tagger()
        self.coherence = CoherenceScorer()
        self.background = BackgroundDensity()

        self.bridge = EntityPromotionBridge()
        self.language = LanguageModule()
        self.events_graph = EventGraph()

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

    def _extract_place(self, text: str) -> str | None:
        tl = text.lower()
        for p in PLACE_WORDS:
            if p in tl:
                return p
        return None

    # -----------------------------
    # Main cognition loop
    # -----------------------------
    def process(self, text: str) -> Dict[str, Any]:
        now = time.time()
        tags = self.tagger.tag(text) or []

        # Always log raw memory
        self._memory_add_safe(kind="utterance", content=text, tags=tags, timestamp=now)

        # ---- Language grounding
        lang = self.language.interpret(text)
        if lang.get("self_assertion") and lang.get("speaker_name"):
            name = lang["speaker_name"]
            self.language.lock_speaker(name)

            # Ensure self entity exists
            self.bridge.confirm_entity(
                name=name,
                kind="person",
                owner_name=None,
            )

            return {"answer": f"Locked. You are **{name}**.", "tags": tags}

        speaker = self.language.speaker()

        # ---- Entity statements
        if " is a dog" in text.lower():
            name = text.split(" is ")[0].strip()
            self.bridge.confirm_entity(name=name, kind="pet")
            return {"answer": f"Noted. **{name}** is a dog.", "tags": tags}

        if speaker and " is my dog" in text.lower():
            name = text.split(" is ")[0].strip()
            self.bridge.confirm_entity(
                name=name,
                kind="pet",
                owner_name=speaker,
                relation="my dog",
            )
            return {"answer": f"Noted. **{name}** is your dog.", "tags": tags}

        # ---- Shared experience → neural binding
        if speaker and "with" in text.lower():
            place = self._extract_place(text)
            participants: Set[str] = set()

            # speaker entity
            sp_ent = self.bridge.find_entity(speaker, owner_name=None)
            if sp_ent:
                participants.add(sp_ent.entity_id)

            # find mentioned entities
            for e in self.bridge.entities.values():
                if e.name.lower() in text.lower():
                    participants.add(e.entity_id)

            if len(participants) >= 2:
                ev = self.events_graph.create_event(
                    participants=participants,
                    place=place,
                    description=text,
                    timestamp=now,
                )
                return {
                    "answer": "Noted — that experience has been remembered.",
                    "tags": tags,
                }

        # ---- Recall
        if text.lower().startswith("what do you remember about "):
            name = text.split("about", 1)[1].strip()
            ent = self.bridge.find_entity(name, owner_name=speaker)
            if not ent:
                return {"answer": f"I don’t have memories linked to **{name}** yet.", "tags": tags}

            evs = self.events_graph.events_for_entity(ent.entity_id)
            if not evs:
                return {"answer": f"I don’t remember any shared experiences with **{name}** yet.", "tags": tags}

            # Build human answer
            lines = []
            for ev in evs:
                others = [
                    self.bridge.entities[pid].name
                    for pid in ev.participants
                    if pid != ent.entity_id
                ]
                if ev.place and others:
                    lines.append(f"{' and '.join(others)} were at the {ev.place} with {ent.name}.")
                elif ev.place:
                    lines.append(f"{ent.name} was at the {ev.place}.")
                else:
                    lines.append(ev.description)

            return {"answer": " ".join(lines), "tags": tags}

        # ---- Default
        return {"answer": "Noted.", "tags": tags}