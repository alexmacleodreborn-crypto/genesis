import time
import re
import inspect
from typing import Dict, Any, Optional, Set, Tuple

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
from a7do.relationships import RelationshipStore
from a7do.pending_relationships import PendingRelationshipStore


PLACE_WORDS = {"park", "home", "garden", "vet", "beach", "gate", "street"}


class A7DOMind:
    RE_MY_DOG = re.compile(r"^\s*(?P<name>.+?)\s+is\s+my\s+dog\s*[.!?]*\s*$", re.I)
    RE_IS_A_DOG = re.compile(r"^\s*(?P<name>.+?)\s+is\s+a\s+dog\s*[.!?]*\s*$", re.I)
    RE_MY_DOG_CALLED = re.compile(r"^\s*my\s+dog\s+is\s+(called|named)\s+(?P<name>.+?)\s*[.!?]*\s*$", re.I)

    RE_X_IS_MY_REL = re.compile(
        r"^\s*(?P<name>.+?)\s+is\s+my\s+(?P<rel>friend|family|mum|mom|dad|father|mother|brother|sister|partner|wife|husband|coworker|co-worker|colleague|doctor|dentist)\s*[.!?]*\s*$",
        re.I,
    )
    RE_MY_REL_IS_X = re.compile(
        r"^\s*my\s+(?P<rel>friend|family|doctor|dentist|coworker|co-worker|colleague)\s+is\s+(?P<name>.+?)\s*[.!?]*\s*$",
        re.I,
    )
    RE_I_WORK_WITH = re.compile(r"^\s*i\s+work\s+with\s+(?P<name>.+?)\s*[.!?]*\s*$", re.I)

    RE_NO_OVERRIDE = re.compile(r"^\s*no[:,]?\s*(?P<rest>.+)\s*$", re.I)
    YES_WORDS = {"yes", "y", "yeah", "yep", "correct", "right", "true"}
    NO_WORDS = {"no", "n", "nope", "nah", "incorrect", "wrong", "false"}

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
        self.events_graph = EventGraph()

        self.relationships = RelationshipStore()
        self.pending_relationships = PendingRelationshipStore()

        self.awaiting_confirmation: Optional[Tuple[str, str]] = None

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
        s = self.language.speaker()
        if s:
            return s
        c = getattr(self.identity, "creator", None)
        if isinstance(c, str) and c.strip():
            return c.strip()
        return "Alex Macleod"

    def _ensure_person_entity(self, name: str):
        self.bridge.confirm_entity(name=name, kind="person", owner_name=None)

    def _speaker_entity_id(self, speaker: str) -> Optional[str]:
        sp = self.bridge.find_entity(speaker, owner_name=None)
        return sp.entity_id if sp else None

    def _extract_place(self, text: str) -> Optional[str]:
        tl = (text or "").lower()
        for p in PLACE_WORDS:
            if p in tl:
                return p
        return None

    def _canon_rel(self, rel: str) -> str:
        r = (rel or "").strip().lower()
        if r in {"coworker", "co-worker", "colleague"}:
            return "coworker"
        if r in {"mum", "mom", "mother", "dad", "father", "brother", "sister"}:
            return "family"
        return r

    def _ensure_person_named(self, name: str):
        name = name.strip().strip(" .!?")
        if name:
            self.bridge.confirm_entity(name=name, kind="person", owner_name=None)

    def _has_confirmed_owner(self, pet_entity_id: str) -> bool:
        for r in self.relationships.all():
            if r.rel_type == "pet" and r.object_id == pet_entity_id:
                return True
        return False

    def _maybe_create_pending_pet_owner_from_event(self, event_participants: Set[str]) -> Optional[Dict[str, Any]]:
        persons = []
        pets = []
        for pid in event_participants:
            ent = self.bridge.entities.get(pid)
            if not ent:
                continue
            if ent.kind == "person":
                persons.append(ent)
            elif ent.kind == "pet":
                pets.append(ent)

        if not persons or not pets:
            return None

        for pet in pets:
            if self._has_confirmed_owner(pet.entity_id):
                continue

            speaker = self._speaker_name().strip().lower()

            for person in persons:
                if person.name.strip().lower() == speaker:
                    continue

                pending = self.pending_relationships.add(
                    subject_id=person.entity_id,
                    object_id=pet.entity_id,
                    rel_type="pet",
                    confidence=0.55,
                    evidence={"rule": "event_cooccurrence"},
                    note="Inferred from shared event co-occurrence",
                )

                q = f"It looks like **{pet.name}** might be **{person.name}**’s dog. Is that correct?"
                self.awaiting_confirmation = (pending.pending_id, q)
                return {"answer": q, "pending": pending.pending_id}

        return None

    def _handle_confirmation(self, text: str) -> Optional[Dict[str, Any]]:
        if not self.awaiting_confirmation:
            return None

        pending_id, _ = self.awaiting_confirmation
        t = (text or "").strip().lower()

        m_over = self.RE_NO_OVERRIDE.match(text or "")
        if m_over:
            self.pending_relationships.reject(pending_id)
            self.awaiting_confirmation = None
            return {"answer": "Okay — understood. State the correct relationship (e.g., “Millie is my dog”)."}

        if t in self.YES_WORDS:
            p = None
            # Pending store has no direct get() in our decay version; keep it simple:
            for item in self.pending_relationships.list_pending():
                if item.pending_id == pending_id:
                    p = item
                    break
            if not p:
                self.awaiting_confirmation = None
                return {"answer": "Okay."}

            self.relationships.add(subject_id=p.subject_id, object_id=p.object_id, rel_type=p.rel_type, note="Confirmed pending inference")
            self.pending_relationships.confirm(pending_id)
            self.awaiting_confirmation = None

            subj = self.bridge.entities.get(p.subject_id)
            obj = self.bridge.entities.get(p.object_id)
            if subj and obj:
                return {"answer": f"Confirmed. **{obj.name}** is **{subj.name}**’s dog."}
            return {"answer": "Confirmed."}

        if t in self.NO_WORDS:
            self.pending_relationships.reject(pending_id)
            self.awaiting_confirmation = None
            return {"answer": "Got it — I won’t assume that relationship."}

        return None

    # -----------------------------
    # Main loop
    # -----------------------------
    def process(self, text: str) -> Dict[str, Any]:
        now = time.time()
        text = text or ""
        lowered = text.lower().strip()
        tags = self.tagger.tag(text) or []

        self._memory_add_safe(kind="utterance", content=text, tags=tags, timestamp=now)

        # 0) Confirmation
        conf = self._handle_confirmation(text)
        if conf:
            return {**conf, "tags": tags}

        # 1) Self-binding
        lang = self.language.interpret(text)
        if lang.get("self_assertion") and lang.get("speaker_name"):
            name = lang["speaker_name"]
            self.language.lock_speaker(name)
            try:
                setattr(self.identity, "creator", name)
            except Exception:
                pass
            self._ensure_person_entity(name)
            return {"answer": f"Locked. You are **{name}**.", "tags": tags}

        speaker = self._speaker_name()
        self._ensure_person_entity(speaker)

        # 2) Identity query
        if lowered.startswith("who am i"):
            return {"answer": f"You are **{speaker}**.", "tags": tags}

        # 3) Pets (explicit)
        m = self.RE_MY_DOG_CALLED.match(text)
        if m:
            pet_name = m.group("name").strip().strip(" .!?")
            pet_name = pet_name[:1].upper() + pet_name[1:] if pet_name else pet_name
            ent = self.bridge.confirm_entity(name=pet_name, kind="pet", owner_name=speaker, relation="my dog")
            spid = self._speaker_entity_id(speaker)
            if spid:
                self.relationships.add(subject_id=spid, object_id=ent.entity_id, rel_type="pet", note="my dog")
            return {"answer": f"Noted. **{ent.name}** is your dog.", "tags": tags}

        m = self.RE_MY_DOG.match(text)
        if m:
            pet_name = m.group("name").strip().strip(" .!?")
            pet_name = pet_name[:1].upper() + pet_name[1:] if pet_name else pet_name
            ent = self.bridge.confirm_entity(name=pet_name, kind="pet", owner_name=speaker, relation="my dog")
            spid = self._speaker_entity_id(speaker)
            if spid:
                self.relationships.add(subject_id=spid, object_id=ent.entity_id, rel_type="pet", note="my dog")
            return {"answer": f"Noted. **{ent.name}** is your dog.", "tags": tags}

        m = self.RE_IS_A_DOG.match(text)
        if m:
            pet_name = m.group("name").strip().strip(" .!?")
            pet_name = pet_name[:1].upper() + pet_name[1:] if pet_name else pet_name
            ent = self.bridge.confirm_entity(name=pet_name, kind="pet", owner_name=None)
            return {"answer": f"Noted. **{ent.name}** is a dog.", "tags": tags}

        # 4) Relationships
        m = self.RE_X_IS_MY_REL.match(text)
        if m:
            other = m.group("name").strip().strip(" .!?")
            rel = self._canon_rel(m.group("rel"))
            self._ensure_person_named(other)

            sp = self.bridge.find_entity(speaker, owner_name=None)
            ob = self.bridge.find_entity(other, owner_name=None)
            if sp and ob:
                self.relationships.add(subject_id=sp.entity_id, object_id=ob.entity_id, rel_type=rel, note=f"{other} is my {rel}")
                return {"answer": f"Noted. **{other}** is your **{rel}**.", "tags": tags}

        m = self.RE_MY_REL_IS_X.match(text)
        if m:
            rel = self._canon_rel(m.group("rel"))
            other = m.group("name").strip().strip(" .!?")
            self._ensure_person_named(other)

            sp = self.bridge.find_entity(speaker, owner_name=None)
            ob = self.bridge.find_entity(other, owner_name=None)
            if sp and ob:
                self.relationships.add(subject_id=sp.entity_id, object_id=ob.entity_id, rel_type=rel, note=f"my {rel} is {other}")
                return {"answer": f"Noted. **{other}** is your **{rel}**.", "tags": tags}

        m = self.RE_I_WORK_WITH.match(text)
        if m:
            other = m.group("name").strip().strip(" .!?")
            self._ensure_person_named(other)

            sp = self.bridge.find_entity(speaker, owner_name=None)
            ob = self.bridge.find_entity(other, owner_name=None)
            if sp and ob:
                self.relationships.add(subject_id=sp.entity_id, object_id=ob.entity_id, rel_type="coworker", note="I work with")
                return {"answer": f"Noted. You work with **{other}**.", "tags": tags}

        # 5) Events
        if "with" in lowered:
            place = self._extract_place(text)
            participants: Set[str] = set()

            sp_ent = self.bridge.find_entity(speaker, owner_name=None)
            if sp_ent:
                participants.add(sp_ent.entity_id)

            for e in self.bridge.entities.values():
                if e.name.lower() in lowered:
                    participants.add(e.entity_id)

            if len(participants) >= 2:
                self.events_graph.create_event(
                    participants=participants,
                    place=place,
                    description=text,
                    timestamp=now,
                )

                inf = self._maybe_create_pending_pet_owner_from_event(participants)
                if inf:
                    return {"answer": inf["answer"], "tags": tags, "pending": inf["pending"]}

                return {"answer": "Noted — that experience has been remembered.", "tags": tags}

        # 6) Stage-1 LRF guarded promotion (THIS IS THE STAGE-1 FIX)
        candidates = self.language.entity_candidates(text)
        for name in candidates:
            # Default kind: person (Stage-1)
            # This stops "What/You/Name/Or/First" being promoted
            self.bridge.confirm_entity(name=name, kind="person", owner_name=None)

        return {"answer": "Noted.", "tags": tags}