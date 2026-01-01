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

from a7do.objects import ObjectManager
from a7do.sensory import SensoryParser
from a7do.recall import RecallEngine


PLACE_WORDS = {"park", "home", "garden", "vet", "beach", "gate", "street"}
STOPWORDS = {"I", "We", "The", "A", "An", "It", "This", "That", "There", "Here"}


class A7DOMind:
    RE_SELF = re.compile(r"(my name is|i am|i'm)\s+(?P<name>[A-Za-z ]+)", re.I)
    RE_MY_DOG = re.compile(r"(?P<name>[A-Za-z]+)\s+is\s+my\s+dog", re.I)
    RE_IS_DOG = re.compile(r"(?P<name>[A-Za-z]+)\s+is\s+a\s+dog", re.I)

    RE_OBJECT = re.compile(r"\b(ball|toy|stick|box)\b", re.I)
    RE_COLOUR = re.compile(r"\b(red|blue|orange|green|yellow)\b", re.I)

    def __init__(self):
        self.identity = Identity()
        self.memory = Memory()
        self.tagger = Tagger()

        self.bridge = EntityPromotionBridge()
        self.language = LanguageModule()
        self.events = EventGraph()
        self.relationships = RelationshipStore()

        self.objects = ObjectManager()
        self.sensory = SensoryParser()
        self.recall = RecallEngine(self.events, self.bridge.entities)

        self.agent = self.bridge.confirm_entity("A7DO", "agent", confidence=1.0)

        self.awaiting: Optional[Dict[str, Any]] = None
        self._mem_sig = inspect.signature(self.memory.add)

    # -------------------------------------------------
    def _speaker(self):
        name = self.language.speaker() or getattr(self.identity, "creator", "Alex Macleod")
        return self.bridge.confirm_entity(name, "person", confidence=1.0)

    # -------------------------------------------------
    def process(self, text: str) -> Dict[str, Any]:
        now = time.time()
        text = text.strip()
        tags = self.tagger.tag(text) or []

        self.memory.add(kind="utterance", content=text, timestamp=now, tags=tags)

        # ---------- Awaiting disambiguation ----------
        if self.awaiting:
            if self.awaiting["type"] == "object_disambiguation":
                if text.lower() in ("yes", "y"):
                    obj = self.awaiting["object"]
                    self.awaiting = None
                    return {"answer": f"Okay — the {obj.colour or ''} {obj.label}.", "tags": tags}
                if text.lower() in ("no", "n"):
                    self.awaiting = {
                        "type": "object_colour",
                        "label": self.awaiting["object"].label
                    }
                    return {"answer": "Which one is it?", "tags": tags}

            if self.awaiting["type"] == "object_colour":
                colour = text.lower()
                speaker = self._speaker()
                obj = self.objects.create(
                    label=self.awaiting["label"],
                    colour=colour,
                    owner_entity_id=speaker.entity_id
                )
                self.awaiting = None
                return {"answer": f"Okay — a {colour} {obj.label}.", "tags": tags}

        # ---------- Identity ----------
        m = self.RE_SELF.search(text)
        if m:
            name = m.group("name").strip()
            self.language.lock_speaker(name)
            self.identity.creator = name
            self.bridge.confirm_entity(name, "person", confidence=1.0)
            return {"answer": f"Noted. You are {name}.", "tags": tags}

        speaker = self._speaker()

        # ---------- Pets ----------
        m = self.RE_MY_DOG.search(text)
        if m:
            dog = self.bridge.confirm_entity(m.group("name"), "pet", confidence=1.0)
            self.relationships.add(speaker.entity_id, dog.entity_id, "pet", "explicit")
            return {"answer": f"Noted. {dog.name} is your dog.", "tags": tags}

        m = self.RE_IS_DOG.search(text)
        if m:
            self.bridge.confirm_entity(m.group("name"), "pet", confidence=1.0)
            return {"answer": f"Noted. {m.group('name')} is a dog.", "tags": tags}

        # ---------- Objects ----------
        obj_match = self.RE_OBJECT.search(text)
        if obj_match:
            label = obj_match.group(1).lower()
            colour_match = self.RE_COLOUR.search(text)
            colour = colour_match.group(1).lower() if colour_match else None

            if colour:
                existing = self.objects.find_by_colour(label, colour)
                if existing:
                    return {"answer": f"Noted. The {colour} {label}.", "tags": tags}
                obj = self.objects.create(label, colour, speaker.entity_id)
                return {"answer": f"Noted. A {colour} {label}.", "tags": tags}

            candidates = self.objects.candidates(label)
            if len(candidates) == 1:
                self.awaiting = {
                    "type": "object_disambiguation",
                    "object": candidates[0]
                }
                return {
                    "answer": f"Do you mean the {candidates[0].colour or ''} {label}? (yes / no)",
                    "tags": tags
                }
            if len(candidates) > 1:
                return {"answer": "Which one?", "tags": tags}

            obj = self.objects.create(label, owner_entity_id=speaker.entity_id)
            return {"answer": f"Noted. A {label}.", "tags": tags}

        # ---------- Attach objects to pets ----------
        for ent in self.bridge.entities.values():
            if ent.kind == "pet" and ent.name.lower() in text.lower():
                for obj in self.objects.candidates("ball"):
                    self.objects.attach(obj, ent.entity_id)

        # ---------- GONE ----------
        if "gone" in text.lower():
            for obj in self.objects.objects.values():
                if obj.label in text.lower():
                    self.objects.mark_gone(obj)
                    return {"answer": f"Okay — the {obj.label} is gone.", "tags": tags}

        # ---------- HARD STOP BEFORE EVENTS ----------
        if any(t.startswith("object") for t in tags):
            return {"answer": "Noted.", "tags": tags}

        # ---------- EVENT ----------
        place = next((p for p in PLACE_WORDS if p in text.lower()), None)
        sx = self.sensory.extract(text)

        if place or sx.smells or sx.sounds:
            self.events.create_event(
                participants={speaker.entity_id},
                place=place,
                description=text,
                timestamp=now,
                smells=sx.smells,
                sounds=sx.sounds,
            )
            return {"answer": "Noted — remembered.", "tags": tags}

        return {"answer": "Noted.", "tags": tags}