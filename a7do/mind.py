import time
from typing import Dict, Any

from a7do.identity import Identity
from a7do.memory import Memory
from a7do.tagger import Tagger
from a7do.profile import ProfileManager
from a7do.coherence import CoherenceScorer
from a7do.background_density import BackgroundDensity

from a7do.reflection import ReflectionStore
from a7do.sleep import SleepEngine

from a7do.entity_promotion import EntityPromotionBridge


class A7DOMind:
    """
    Central cognitive orchestrator for A7DO.

    Uses:
    - Memory as the event stream
    - Entity Promotion Bridge for grounded identity
    - Sleep + Reflection for consolidation
    """

    def __init__(self):
        self.identity = Identity()
        self.memory = Memory()
        self.tagger = Tagger()
        self.profiles = ProfileManager()
        self.coherence = CoherenceScorer()
        self.background = BackgroundDensity()

        self.reflections = ReflectionStore()
        self.sleep_engine = SleepEngine(self.reflections)

        self.bridge = EntityPromotionBridge()

        self._events_since_sleep = 0
        self._last_signal = None

    def emit(self, kind: str, message: str):
        self._last_signal = {
            "kind": kind,
            "message": message,
            "time": time.time()
        }

    def process(self, text: str) -> Dict[str, Any]:
        now = time.time()

        # 1) Tag input
        tags = self.tagger.tag(text) or []
        if isinstance(tags, dict):
            tags = tags.get("tags", [])

        # 2) Profile learning
        profile = self.profiles.current()
        profile.learn(text, tags)

        owner_name = getattr(profile, "name", "") or "Alex Macleod"

        # 3) Entity Promotion Bridge
        bridge_tags, bridge_events, bridge_questions = self.bridge.observe(
            text, owner_name=owner_name
        )
        for t in bridge_tags:
            if t not in tags:
                tags.append(t)

        # 4) Store as memory (this IS the event)
        self.memory.add(
            kind="utterance",
            content=text,
            tags=tags,
            timestamp=now
        )

        self._events_since_sleep += 1

        # 5) Entity question handling
        answer = None
        lowered = text.lower().strip()

        if lowered.startswith("who is "):
            name = text[7:].strip(" ?!.")
            desc = self.bridge.describe(name)
            if desc:
                answer = desc
            else:
                p = self.bridge.pending.get(name.lower())
                if p:
                    answer = (
                        f"I’m still learning who **{p.name}** is. "
                        f"I’ve seen this name {p.count} time(s) "
                        f"(confidence {p.confidence:.2f}). "
                        f"Is {p.name} a person, a pet, or something else?"
                    )

        # 6) Identity questions
        if answer is None and self.identity.is_identity_question(text):
            answer = self.identity.respond(profile)

        # 7) Default response
        if answer is None:
            answer = self.identity.default_response(profile)

        # 8) Coherence scoring
        coherence = self.coherence.evaluate(
            text=text,
            tags=tags
        )

        # 9) Sleep trigger (every 8 memories)
        sleep_report = None
        if self._events_since_sleep >= 8:
            recent = self.memory.recent(n=20)
            created = self.sleep_engine.run_global(recent)
            self.reflections.decay()
            self._events_since_sleep = 0
            self.emit("SLEEP", "Memory consolidation complete")
            sleep_report = created

        # 10) Inspector payload
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

        return {
            "answer": answer,
            "tags": tags,
            "coherence": coherence,
            "signal": self._last_signal,
            "sleep": sleep_report,
            "bridge_events": bridge_events,
            "bridge_questions": bridge_questions,
            "pending_entities": pending_entities,
            "entity_graph": entity_graph,
        }