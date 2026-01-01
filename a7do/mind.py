import time
from typing import Any, Dict, Optional, Set

from a7do.identity import Identity
from a7do.language import LanguageModule
from a7do.entity_promotion import EntityPromotionBridge
from a7do.relationships import RelationshipStore
from a7do.objects import ObjectManager
from a7do.event_graph import EventGraph
from a7do.sensory import SensoryParser
from a7do.memory import Memory
from a7do.experience import ExperienceStore
from a7do.sleep import SleepEngine


class A7DOMind:
    def __init__(self):
        self.identity = Identity()
        self.language = LanguageModule()
        self.bridge = EntityPromotionBridge()
        self.relationships = RelationshipStore()
        self.objects = ObjectManager()
        self.events = EventGraph()
        self.events_graph = self.events  # compat alias
        self.sensory = SensoryParser()
        self.memory = Memory()
        self.experiences = ExperienceStore()

        self.agent = self.bridge.confirm_entity("A7DO", "agent", confidence=1.0, origin="system")

        # schedule/sleep logs
        self.day_external_events = []  # authoritative replay source
        self.sleep_engine = SleepEngine()
        self.last_sleep_report: Dict[str, Any] = {}

    # -------------------------
    # Identity / speaker
    # -------------------------
    def lock_speaker(self, name: str):
        name = (name or "").strip()
        if not name:
            return
        self.language.lock_speaker(name)
        self.identity.creator = name
        self.bridge.confirm_entity(name, "person", confidence=1.0, origin="declared")

    def speaker_name(self) -> str:
        return self.language.speaker() or self.identity.creator

    def speaker_entity(self):
        return self.bridge.confirm_entity(self.speaker_name(), "person", confidence=1.0, origin="user")

    # -------------------------
    # External truth log for reflection
    # -------------------------
    def record_external_event(
        self,
        builder: str,
        payload: Dict[str, Any],
        entities: Optional[Set[str]] = None,
        objects: Optional[Set[str]] = None,
        place: Optional[str] = None,
        smells=None,
        sounds=None,
        emotion: Optional[str] = None,
    ):
        self.day_external_events.append({
            "t": time.time(),
            "builder": builder,
            "payload": payload,
            "entities": list(entities or set()),
            "objects": list(objects or set()),
            "place": place,
            "smells": list(smells or []),
            "sounds": list(sounds or []),
            "emotion": emotion,
        })

    # -------------------------
    # Ingest scheduled builder events
    # -------------------------
    def ingest_scheduled_event(self, builder: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Authoritative scheduled learning / truth injection.
        No hallucination: only stores what payload declares.
        """
        builder = (builder or "").strip().lower()
        now = time.time()
        speaker = self.speaker_entity()

        # Always store schedule event in memory
        self.memory.add(kind="scheduled_event", builder=builder, payload=payload, timestamp=now)

        # 1) user_input builder can lock identity (your day anchor)
        if builder == "user_input":
            # expected payload: {"text": "..."} optionally {"name": "..."}
            text = (payload.get("text") or "").strip()
            name = (payload.get("name") or "").strip()
            if name:
                self.lock_speaker(name)
                speaker = self.speaker_entity()

            # store as external event with speaker
            self.record_external_event(builder, payload, entities={speaker.entity_id})
            return {"answer": f"User input anchored for {self.speaker_name()}.", "mode": "schedule"}

        # 2) relationship builder
        if builder == "relationship":
            # payload: subject, relation, object, object_kind(optional), note(optional)
            subj_name = (payload.get("subject") or "").strip()
            obj_name = (payload.get("object") or "").strip()
            rel = (payload.get("relation") or "").strip().lower()
            note = (payload.get("note") or "").strip()
            obj_kind = (payload.get("object_kind") or "person").strip().lower()

            # default subject "speaker" if omitted
            if not subj_name:
                subj_name = self.speaker_name()

            subj = self.bridge.confirm_entity(subj_name, "person", confidence=1.0, origin="declared")
            obj = self.bridge.confirm_entity(obj_name, obj_kind, confidence=1.0, origin="declared")

            self.relationships.add(subj.entity_id, obj.entity_id, rel, note or "scheduled")

            self.record_external_event(builder, payload, entities={subj.entity_id, obj.entity_id})
            return {"answer": f"Relationship stored: {subj.name} → {rel} → {obj.name}.", "mode": "schedule"}

        # 3) object builder
        if builder == "object":
            # payload: label, colour(optional), owner(optional), attached_to(optional), state(optional), place(optional)
            label = (payload.get("label") or "").strip().lower()
            colour = (payload.get("colour") or "").strip().lower() or None
            owner_name = (payload.get("owner") or "").strip()
            attached_name = (payload.get("attached_to") or "").strip()
            state = (payload.get("state") or "present").strip().lower()
            place = (payload.get("place") or "").strip().lower() or None

            if not label:
                return {"answer": "Object event missing label.", "mode": "schedule"}

            if not owner_name:
                owner_name = self.speaker_name()

            owner = self.bridge.confirm_entity(owner_name, "person", confidence=1.0, origin="declared")
            obj = self.objects.find(label, colour=colour, include_gone=True) or self.objects.create(label, colour=colour, owner_entity_id=owner.entity_id)

            # state
            if state == "gone":
                self.objects.mark_gone(obj)
            else:
                obj.state = "present"

            # attach to entity (pet/person)
            attached_ids = set()
            if attached_name:
                attached = self.bridge.find_entity(attached_name) or self.bridge.confirm_entity(attached_name, "person", confidence=0.8, origin="declared")
                self.objects.attach(obj, attached.entity_id)
                attached_ids.add(attached.entity_id)

            if place:
                self.objects.set_location(obj, place)

            self.record_external_event(builder, payload, entities={owner.entity_id, *attached_ids}, objects={obj.object_id}, place=place)
            return {"answer": f"Object stored: {(colour+' ') if colour else ''}{label} (state={obj.state}).", "mode": "schedule"}

        # 4) sensory builder
        if builder == "sensory":
            # payload: place, smells(list), sounds(list), emotion(optional), note(optional)
            place = (payload.get("place") or "").strip().lower() or None
            smells = payload.get("smells") or []
            sounds = payload.get("sounds") or []
            emotion = (payload.get("emotion") or "").strip().lower() or None

            # record as external sensory truth; also add event frame
            self.events.create_event(
                participants={speaker.entity_id},
                place=place,
                description=payload.get("note") or "sensory",
                timestamp=now,
                smells=smells,
                sounds=sounds,
            )

            self.record_external_event(builder, payload, entities={speaker.entity_id}, place=place, smells=smells, sounds=sounds, emotion=emotion)
            return {"answer": f"Sensory stored for {place or '—'}.", "mode": "schedule"}

        # 5) language builder (pronouns/word meaning)
        if builder == "language":
            # payload: concept, token, meaning, examples(optional)
            concept = (payload.get("concept") or "").strip().lower()
            token = (payload.get("token") or "").strip()
            meaning = (payload.get("meaning") or "").strip()
            # store as external truth in memory only (no hallucination)
            self.record_external_event(builder, payload, entities={speaker.entity_id})
            return {"answer": f"Language learned: {concept} / {token} → {meaning}", "mode": "schedule"}

        # 6) shapes builder
        if builder == "shapes":
            # payload: shape, properties(optional), example(optional)
            self.record_external_event(builder, payload, entities={speaker.entity_id})
            return {"answer": f"Shape learned: {payload.get('shape','—')}", "mode": "schedule"}

        # 7) routine builder
        if builder == "routine":
            # payload: slot, activity, participants(list), place(optional)
            part = payload.get("participants") or []
            ids = set()
            for n in part:
                n = (n or "").strip()
                if not n:
                    continue
                ids.add(self.bridge.confirm_entity(n, "person", confidence=0.9, origin="declared").entity_id)
            place = (payload.get("place") or "").strip().lower() or None
            self.record_external_event(builder, payload, entities=ids or {speaker.entity_id}, place=place)
            return {"answer": f"Routine stored: {payload.get('activity','—')}", "mode": "schedule"}

        # fallback
        self.record_external_event(builder, payload, entities={speaker.entity_id})
        return {"answer": f"Stored scheduled event ({builder}).", "mode": "schedule"}

    # -------------------------
    # Sleep hook
    # -------------------------
    def sleep(self) -> Dict[str, Any]:
        """
        Run sleep: consolidation + reflection Pattern1 + confidence decay.
        """
        report = self.sleep_engine.run_sleep(self)
        self.last_sleep_report = report
        return report

    def new_day_reset(self):
        """
        Start next day. We do not erase world model; we reset only day external replay buffer.
        """
        self.day_external_events = []