import time
import re
import inspect
from typing import Dict, Any, Optional, Set

from a7do.identity import Identity
from a7do.memory import Memory
from a7do.tagger import Tagger

from a7do.entity_promotion import EntityPromotionBridge
from a7do.language import LanguageModule
from a7do.event_graph import EventGraph
from a7do.relationships import RelationshipStore
from a7do.pending_relationships import PendingRelationshipStore

from a7do.objects import ObjectManager
from a7do.sensory import SensoryParser
from a7do.recall import RecallEngine


PLACE_WORDS = {"park", "home", "garden", "vet", "beach", "gate", "street"}


class A7DOMind:
    RE_SELF = re.compile(r"^\s*(my\s+name\s+is|i\s+am|i'm)\s+(?P<name>[A-Za-z][A-Za-z\- ]+)\s*[.!?]*\s*$", re.I)
    RE_WHOAMI = re.compile(r"^\s*who\s+am\s+i\s*\??\s*$", re.I)

    RE_RECALL_ABOUT = re.compile(r"^\s*what\s+do\s+you\s+remember\s+about\s+(?P<target>.+?)\s*\??\s*$", re.I)
    RE_RECALL_PLACE = re.compile(r"^\s*what\s+happened\s+at\s+(?P<place>.+?)\s*\??\s*$", re.I)

    def __init__(self):
        self.identity = Identity()
        self.memory = Memory()
        self.tagger = Tagger()

        self.bridge = EntityPromotionBridge()
        self.language = LanguageModule()
        self.events_graph = EventGraph()

        self.relationships = RelationshipStore()
        self.pending_relationships = PendingRelationshipStore()

        self.objects = ObjectManager()
        self.sensory = SensoryParser()

        self.recall_engine = RecallEngine(
            self.events_graph,
            self.bridge.entities
        )

        self.awaiting: Optional[Dict[str, str]] = None
        self._memory_add_sig = inspect.signature(self.memory.add)

    # -------------------------------------------------
    # Utilities
    # -------------------------------------------------
    def _memory_add_safe(self, **kwargs):
        supported = {k: v for k, v in kwargs.items() if k in self._memory_add_sig.parameters}
        try:
            self.memory.add(**supported)
        except Exception:
            pass

    def _speaker_name(self) -> str:
        s = self.language.speaker()
        if s:
            return s
        c = getattr(self.identity, "creator", None)
        return c if isinstance(c, str) else "Alex Macleod"

    def _ensure_person(self, name: str):
        self.bridge.confirm_entity(name=name, kind="person", owner_name=None)

    def _speaker_entity_id(self) -> Optional[str]:
        ent = self.bridge.find_entity(self._speaker_name(), owner_name=None)
        return ent.entity_id if ent else None

    def _extract_place(self, text: str) -> Optional[str]:
        tl = text.lower()
        for p in PLACE_WORDS:
            if p in tl:
                return p
        return None

    # -------------------------------------------------
    # Main processing
    # -------------------------------------------------
    def process(self, text: str) -> Dict[str, Any]:
        now = time.time()
        text = text or ""
        lowered = text.lower().strip()
        tags = self.tagger.tag(text) or []

        self._memory_add_safe(kind="utterance", content=text, tags=tags, timestamp=now)

        # -------------------------
        # Recall v1
        # -------------------------
        m = self.RE_RECALL_ABOUT.match(text)
        if m:
            target = m.group("target").strip()
            events = self.recall_engine.recall(entity_name=target)
            return {"answer": self.recall_engine.format(events), "tags": tags}

        m = self.RE_RECALL_PLACE.match(text)
        if m:
            place = m.group("place").strip()
            events = self.recall_engine.recall(place=place)
            return {"answer": self.recall_engine.format(events), "tags": tags}

        # -------------------------
        # Identity binding
        # -------------------------
        m = self.RE_SELF.match(text)
        if m:
            name = m.group("name").strip()
            self.language.lock_speaker(name)
            try:
                setattr(self.identity, "creator", name)
            except Exception:
                pass
            self._ensure_person(name)
            return {"answer": f"Locked. You are **{name}**.", "tags": tags}

        if self.RE_WHOAMI.match(text):
            return {"answer": f"You are **{self._speaker_name()}**.", "tags": tags}

        speaker = self._speaker_name()
        self._ensure_person(speaker)

        # -------------------------
        # Event capture (+ sensory)
        # -------------------------
        sx = self.sensory.extract(text)
        place = self._extract_place(text)

        participants: Set[str] = set()
        sp_ent = self.bridge.find_entity(speaker, owner_name=None)
        if sp_ent:
            participants.add(sp_ent.entity_id)

        for e in self.bridge.entities.values():
            if e.name.lower() in lowered:
                participants.add(e.entity_id)

        if place or participants or sx.smells or sx.sounds:
            self.events_graph.create_event(
                participants=participants,
                place=place,
                description=text,
                timestamp=now,
                smells=sx.smells,
                sounds=sx.sounds,
                raw_sensory=sx.raw,
            )
            return {"answer": "Noted — that experience has been remembered.", "tags": tags}

        return {"answer": "Noted.", "tags": tags}