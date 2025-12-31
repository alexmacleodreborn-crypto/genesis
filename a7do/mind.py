import time
from typing import Dict, Any

from a7do.identity import Identity
from a7do.memory import Memory
from a7do.events import EventManager
from a7do.tagger import Tagger
from a7do.profile import ProfileManager
from a7do.coherence import CoherenceScorer
from a7do.background_density import BackgroundDensity

from a7do.reflection import ReflectionStore
from a7do.sleep import SleepEngine

# NEW
from a7do.entity_promotion import EntityPromotionBridge


class A7DOMind:
    """
    Central orchestrator + flow.
    Now includes:
      - Entity Promotion Bridge (linguistic recognition → entity binding)
      - Sleep + Reflection (safe awareness)
    """

    def __init__(self):
        self.identity = Identity()
        self.memory = Memory()
        self.events = EventManager()
        self.tagger = Tagger()
        self.profiles = ProfileManager()
        self.coherence = CoherenceScorer()
        self.background = BackgroundDensity()

        # reflection + sleep
        self.reflections = ReflectionStore()
        self.sleep_engine = SleepEngine(self.reflections)
        self._events_since_sleep = 0

        # NEW: bridge
        self.bridge = EntityPromotionBridge()

        self._last_signal = None

    def emit(self, kind: str, message: str):
        self._last_signal = {"kind": kind, "message": message, "time": time.time()}

    def process(self, text: str) -> Dict[str, Any]:
        now = time.time()

        # 1) Tag input
        tags = self.tagger.tag(text) or []
        if isinstance(tags, dict):
            # if your tagger returns dict, normalise to list
            tags = tags.get("tags", [])

        # 2) Profile / speaker
        profile = self.profiles.current()
        profile.learn(text, tags)

        # Determine "owner_name" for bridge (default to Alex Macleod if known)
        owner_name = getattr(profile, "name", "") or "Alex Macleod"

        # 3) BRIDGE: observe candidates and maybe promote
        bridge_tags, bridge_events, bridge_questions = self.bridge.observe(text, owner_name=owner_name)
        for bt in bridge_tags:
            if bt not in tags:
                tags.append(bt)

        # 4) Event ingest
        event = self.events.ingest(
            utterance=text,
            tags=tags,
            timestamp=now
        )

        # 5) Memory log
        self.memory.add(
            kind="utterance",
            content=text,
            tags=tags,
            timestamp=now
        )

        # 6) Quick entity Q&A (works once promoted)
        # If user asks "who is X", and X exists, answer from entity graph.
        answer = None
        lowered = text.strip().lower()

        # Helper: detect "who is ___"
        if lowered.startswith("who is "):
            name = text.strip()[7:].strip(" ?!.")
            desc = self.bridge.describe(name)
            if desc:
                answer = desc
            else:
                # If it’s pending, ask for confirmation rather than hallucinating
                p = self.bridge.pending.get(name.lower())
                if p:
                    answer = (
                        f"I’m still learning who **{p.name}** is. "
                        f"So far I’ve seen it {p.count} time(s) (confidence ~{p.confidence:.2f}). "
                        f"Is {p.name} a person, a pet, or something else?"
                    )

        # 7) Identity questions
        if answer is None and self.identity.is_identity_question(text):
            answer = self.identity.respond(profile)

        # 8) Default response (keep your current behaviour)
        if answer is None:
            answer = self.identity.default_response(profile)

        # 9) Coherence
        coherence = self.coherence.evaluate(text=text, tags=tags, event=event)

        # 10) Sleep trigger (every 8 events)
        self._events_since_sleep += 1
        sleep_report = None
        if self._events_since_sleep >= 8:
            sleep_report = {}
            for entity_id in self.events.silos.keys():
                frames = self.events.silo_events(entity_id, n=10)
                created = self.sleep_engine.run_for_entity(entity_id, frames)
                if created:
                    sleep_report[entity_id] = len(created)

            self.reflections.decay()
            self._events_since_sleep = 0
            self.emit("SLEEP", "Per-silo consolidation complete")

        # 11) Build debug/inspector payload
        pending_entities = [
            {
                "name": p.name,
                "kind_guess": p.kind_guess,
                "relation_hint": p.relation_hint,
                "owner_name": p.owner_name,
                "count": p.count,
                "confidence": round(p.confidence, 3),
                "contexts": p.contexts,
            }
            for p in self.bridge.pending.values()
            if not self.bridge.find_entity_id(p.name)
        ]

        entity_graph = [
            {
                "entity_id": e.entity_id,
                "name": e.name,
                "kind": e.kind,
                "owner_name": e.owner_name,
                "aliases": e.aliases,
            }
            for e in self.bridge.entities.values()
        ]

        result = {
            "answer": answer,
            "event_id": getattr(event, "event_id", None),
            "tags": tags,
            "coherence": coherence,
            "signal": self._last_signal,
            "sleep": sleep_report,

            # NEW: bridge visibility
            "bridge_events": bridge_events,
            "bridge_questions": bridge_questions,
            "pending_entities": pending_entities,
            "entity_graph": entity_graph,

            # reflections
            "reflections": {
                eid: [
                    {
                        "pattern": v.reflection_key[1],
                        "score": round(v.score, 3),
                        "band": v.band,
                        "active": v.active
                    }
                    for v in self.reflections.active_versions(eid)
                ]
                for eid in self.events.silos.keys()
            }
        }

        return result