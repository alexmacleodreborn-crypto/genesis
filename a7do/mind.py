import time
import re
import inspect
from typing import Dict, Any, Optional, Set, Tuple

from a7do.identity import Identity
from a7do.memory import Memory
from a7do.tagger import Tagger

from a7do.entity_promotion import EntityPromotionBridge
from a7do.language import LanguageModule
from a7do.event_graph import EventGraph
from a7do.relationships import RelationshipStore
from a7do.pending_relationships import PendingRelationshipStore

from a7do.objects import ObjectManager


PLACE_WORDS = {"park", "home", "garden", "vet", "beach", "gate", "street"}

BASIC_COLORS = {
    "red", "blue", "green", "yellow", "orange", "purple", "pink",
    "black", "white", "brown", "grey", "gray"
}


class A7DOMind:
    RE_MY_DOG = re.compile(r"^\s*(?P<name>.+?)\s+is\s+my\s+dog\s*[.!?]*\s*$", re.I)
    RE_IS_A_DOG = re.compile(r"^\s*(?P<name>.+?)\s+is\s+a\s+dog\s*[.!?]*\s*$", re.I)
    RE_MY_DOG_CALLED = re.compile(r"^\s*my\s+dog\s+is\s+(called|named)\s+(?P<name>.+?)\s*[.!?]*\s*$", re.I)

    RE_SELF = re.compile(r"^\s*(my\s+name\s+is|i\s+am|i'm)\s+(?P<name>[A-Za-z][A-Za-z\- ]+)\s*[.!?]*\s*$", re.I)
    RE_WHOAMI = re.compile(r"^\s*who\s+am\s+i\s*\??\s*$", re.I)

    RE_X_IS_MY_REL = re.compile(
        r"^\s*(?P<name>.+?)\s+is\s+my\s+(?P<rel>friend|family|mum|mom|dad|father|mother|brother|sister|partner|wife|husband|coworker|co-worker|colleague|doctor|dentist)\s*[.!?]*\s*$",
        re.I,
    )

    # Object patterns
    RE_MY_OBJECT = re.compile(r"^\s*my\s+(?P<label>ball|toy|stick|cube|block|box|chair|table|door|bottle)\s*[.!?]*\s*$", re.I)
    RE_A_OBJECT = re.compile(r"^\s*(a|an|the)\s+(?P<label>ball|toy|stick|cube|block|box|chair|table|door|bottle)\s*[.!?]*\s*$", re.I)
    RE_COLORED_OBJECT = re.compile(r"^\s*(?P<color>[A-Za-z]+)\s+(?P<label>ball|toy|stick|cube|block|box|chair|table|door|bottle)\s*[.!?]*\s*$", re.I)
    RE_POSSESSIVE_OBJECT = re.compile(
        r"^\s*(?P<owner>[A-Za-z][A-Za-z\- ]+?)'s\s+(?P<label>ball|toy|stick|cube|block|box|chair|table|door|bottle)\s*[.!?]*\s*$",
        re.I
    )

    YES_WORDS = {"yes", "y", "yeah", "yep", "correct", "right", "true"}
    NO_WORDS = {"no", "n", "nope", "nah", "incorrect", "wrong", "false"}

    def __init__(self):
        self.identity = Identity()
        self.memory = Memory()
        self.tagger = Tagger()

        self.bridge = EntityPromotionBridge()
        self.language = LanguageModule()
        self.events_graph = EventGraph()

        self.relationships = RelationshipStore()
        self.pending_relationships = PendingRelationshipStore()

        # Objects
        self.objects = ObjectManager()

        # Confirmation state (generic)
        # {"type": "rel"|"obj", "id": <pending_id>, "stage": "..."}
        self.awaiting: Optional[Dict[str, str]] = None

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

    def _ensure_person(self, name: str):
        self.bridge.confirm_entity(name=name, kind="person", owner_name=None)

    def _entity_id_factory(self, name: str, kind: str) -> str:
        ent = self.bridge.confirm_entity(name=name, kind=kind, owner_name=None)
        return ent.entity_id

    def _speaker_entity_id(self) -> Optional[str]:
        sp = self.bridge.find_entity(self._speaker_name(), owner_name=None)
        return sp.entity_id if sp else None

    def _extract_place(self, text: str) -> Optional[str]:
        tl = (text or "").lower()
        for p in PLACE_WORDS:
            if p in tl:
                return p
        return None

    def _has_confirmed_owner(self, pet_entity_id: str) -> bool:
        for r in self.relationships.all():
            if r.rel_type == "pet" and r.object_id == pet_entity_id:
                return True
        return False

    def _maybe_infer_pet_owner_from_event(self, participants: Set[str]) -> Optional[str]:
        persons = []
        pets = []
        for pid in participants:
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

                self.awaiting = {"type": "rel", "id": pending.pending_id, "stage": "yesno"}
                return f"It looks like **{pet.name}** might be **{person.name}**’s dog. Is that correct? (yes/no)"
        return None

    def _handle_confirmation(self, text: str) -> Optional[Dict[str, Any]]:
        if not self.awaiting:
            return None

        t = (text or "").strip().lower()

        # Relationship pending yes/no
        if self.awaiting["type"] == "rel":
            pid = self.awaiting["id"]
            if t in self.YES_WORDS:
                target = None
                for item in self.pending_relationships.list_pending():
                    if item.pending_id == pid:
                        target = item
                        break
                if target:
                    self.relationships.add(subject_id=target.subject_id, object_id=target.object_id, rel_type=target.rel_type, note="Confirmed pending inference")
                    self.pending_relationships.confirm(pid)

                    subj = self.bridge.entities.get(target.subject_id)
                    obj = self.bridge.entities.get(target.object_id)
                    self.awaiting = None
                    if subj and obj:
                        return {"answer": f"Confirmed. **{obj.name}** is **{subj.name}**’s dog."}
                self.awaiting = None
                return {"answer": "Confirmed."}

            if t in self.NO_WORDS:
                self.pending_relationships.reject(pid)
                self.awaiting = None
                return {"answer": "Got it — I won’t assume that relationship."}

            return {"answer": "Please answer **yes** or **no**."}

        # Object disambiguation flow
        if self.awaiting["type"] == "obj":
            pid = self.awaiting["id"]
            stage = self.awaiting.get("stage", "yesno")

            if stage == "yesno":
                if t in self.YES_WORDS:
                    ent_id = self.objects.resolve_pending_yes(pid)
                    self.awaiting = None
                    if ent_id:
                        return {"answer": "Noted — same object.", "resolved_object": ent_id}
                    return {"answer": "Noted."}

                if t in self.NO_WORDS:
                    p = self.objects.resolve_pending_no(pid)
                    self.awaiting["stage"] = "which"
                    return {"answer": p.prompt if p else "Which one is it?"}

                return {"answer": "Please answer **yes** or **no**."}

            # stage == "which"
            ent_id = self.objects.resolve_pending_description(pid, text, entity_id_factory=self._entity_id_factory)
            self.awaiting = None
            if ent_id:
                return {"answer": "Noted — created/selected that object.", "resolved_object": ent_id}
            return {"answer": "Noted."}

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

        # Confirmation has priority
        conf = self._handle_confirmation(text)
        if conf:
            return {**conf, "tags": tags}

        # Self-binding
        m = self.RE_SELF.match(text)
        if m:
            name = " ".join((m.group("name") or "").strip().split())
            self.language.lock_speaker(name)
            try:
                setattr(self.identity, "creator", name)
            except Exception:
                pass
            self._ensure_person(name)
            return {"answer": f"Locked. You are **{name}**.", "tags": tags}

        speaker = self._speaker_name()
        self._ensure_person(speaker)

        # Who am I
        if self.RE_WHOAMI.match(text):
            return {"answer": f"You are **{speaker}**.", "tags": tags}

        # -----------------------------
        # Explicit pet learning
        # -----------------------------
        m = self.RE_MY_DOG_CALLED.match(text)
        if m:
            pet_name = m.group("name").strip().strip(" .!?")
            pet_name = pet_name[:1].upper() + pet_name[1:] if pet_name else pet_name
            ent = self.bridge.confirm_entity(name=pet_name, kind="pet", owner_name=speaker, relation="my dog")

            spid = self._speaker_entity_id()
            if spid:
                self.relationships.add(subject_id=spid, object_id=ent.entity_id, rel_type="pet", note="my dog")
            return {"answer": f"Noted. **{ent.name}** is your dog.", "tags": tags}

        m = self.RE_MY_DOG.match(text)
        if m:
            pet_name = m.group("name").strip().strip(" .!?")
            pet_name = pet_name[:1].upper() + pet_name[1:] if pet_name else pet_name
            ent = self.bridge.confirm_entity(name=pet_name, kind="pet", owner_name=speaker, relation="my dog")

            spid = self._speaker_entity_id()
            if spid:
                self.relationships.add(subject_id=spid, object_id=ent.entity_id, rel_type="pet", note="my dog")
            return {"answer": f"Noted. **{ent.name}** is your dog.", "tags": tags}

        m = self.RE_IS_A_DOG.match(text)
        if m:
            pet_name = m.group("name").strip().strip(" .!?")
            pet_name = pet_name[:1].upper() + pet_name[1:] if pet_name else pet_name
            ent = self.bridge.confirm_entity(name=pet_name, kind="pet", owner_name=None)
            return {"answer": f"Noted. **{ent.name}** is a dog.", "tags": tags}

        # -----------------------------
        # Relationships (simple)
        # -----------------------------
        m = self.RE_X_IS_MY_REL.match(text)
        if m:
            other = m.group("name").strip().strip(" .!?")
            rel = (m.group("rel") or "").lower().strip()
            self._ensure_person(other)

            sp = self.bridge.find_entity(speaker, owner_name=None)
            ob = self.bridge.find_entity(other, owner_name=None)
            if sp and ob:
                self.relationships.add(subject_id=sp.entity_id, object_id=ob.entity_id, rel_type=rel, note=f"{other} is my {rel}")
                return {"answer": f"Noted. **{other}** is your **{rel}**.", "tags": tags}

        # -----------------------------
        # OBJECTS (Option B)
        # -----------------------------
        # 1) Possessive: "Xena's ball"
        mo = self.RE_POSSESSIVE_OBJECT.match(text)
        if mo:
            owner = mo.group("owner").strip()
            label = mo.group("label").lower().strip()

            # owner could be person or pet — ensure entity exists (Stage safe: if known pet name exists, it will already be pet)
            owner_ent = self.bridge.find_entity(owner, owner_name=None)
            if not owner_ent:
                # default to person if not known; user can later correct via "Xena is a dog"
                self._ensure_person(owner)
                owner_ent = self.bridge.find_entity(owner, owner_name=None)

            ent_id, pending = self.objects.mention(
                label,
                entity_id_factory=self._entity_id_factory,
                owner_entity_id=owner_ent.entity_id if owner_ent else None,
            )
            if pending:
                self.awaiting = {"type": "obj", "id": pending.pending_id, "stage": "yesno"}
                return {"answer": pending.prompt, "tags": tags}

            if ent_id and owner_ent:
                self.relationships.add(subject_id=owner_ent.entity_id, object_id=ent_id, rel_type="owns", note="possessive object")
            return {"answer": f"Noted. **{owner}** has a **{label}**.", "tags": tags}

        # 2) "my ball"
        mo = self.RE_MY_OBJECT.match(text)
        if mo:
            label = mo.group("label").lower().strip()
            spid = self._speaker_entity_id()

            ent_id, pending = self.objects.mention(
                label,
                entity_id_factory=self._entity_id_factory,
                owner_entity_id=spid,
            )
            if pending:
                self.awaiting = {"type": "obj", "id": pending.pending_id, "stage": "yesno"}
                return {"answer": pending.prompt, "tags": tags}

            if ent_id and spid:
                self.relationships.add(subject_id=spid, object_id=ent_id, rel_type="owns", note="my object")
            return {"answer": f"Noted. You have a **{label}**.", "tags": tags}

        # 3) "red ball" (learn/attach color; if conflict, disambiguate)
        mo = self.RE_COLORED_OBJECT.match(text)
        if mo:
            color = mo.group("color").lower().strip()
            label = mo.group("label").lower().strip()

            # learn color on demand (as you requested: colour learning)
            if color:
                self.objects.colors.learn(color)

            ent_id, pending = self.objects.mention(
                label,
                entity_id_factory=self._entity_id_factory,
                owner_entity_id=self._speaker_entity_id(),
                colour=color if color else None,
            )

            if pending:
                self.awaiting = {"type": "obj", "id": pending.pending_id, "stage": "yesno"}
                return {"answer": pending.prompt, "tags": tags}

            return {"answer": f"Noted. **{color} {label}**.", "tags": tags}

        # 4) "a ball" / "the ball"
        mo = self.RE_A_OBJECT.match(text)
        if mo:
            label = mo.group("label").lower().strip()
            ent_id, pending = self.objects.mention(
                label,
                entity_id_factory=self._entity_id_factory,
                owner_entity_id=self._speaker_entity_id(),
            )
            if pending:
                self.awaiting = {"type": "obj", "id": pending.pending_id, "stage": "yesno"}
                return {"answer": pending.prompt, "tags": tags}
            return {"answer": f"Noted. **{label}**.", "tags": tags}

        # -----------------------------
        # EVENTS (include objects)
        # -----------------------------
        if "with" in lowered or any(p in lowered for p in PLACE_WORDS):
            place = self._extract_place(text)
            participants: Set[str] = set()

            # speaker participates
            sp_ent = self.bridge.find_entity(speaker, owner_name=None)
            if sp_ent:
                participants.add(sp_ent.entity_id)

            # known entities mentioned (people/pets/objects)
            for e in self.bridge.entities.values():
                if e.name.lower() in lowered:
                    participants.add(e.entity_id)

            if place or len(participants) >= 2:
                self.events_graph.create_event(
                    participants=participants,
                    place=place,
                    description=text,
                    timestamp=now,
                )

                # infer pet ownership from event cooccurrence
                inf_q = self._maybe_infer_pet_owner_from_event(participants)
                if inf_q:
                    return {"answer": inf_q, "tags": tags}

                return {"answer": "Noted — that experience has been remembered.", "tags": tags}

        # Stage-1 LRF guarded promotion (names only)
        candidates = self.language.entity_candidates(text)
        for name in candidates:
            self.bridge.confirm_entity(name=name, kind="person", owner_name=None)

        return {"answer": "Noted.", "tags": tags}