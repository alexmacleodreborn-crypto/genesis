import time
from typing import Dict, Any

from a7do.identity import Identity
from a7do.memory import Memory
from a7do.tagger import Tagger
from a7do.coherence import CoherenceScorer
from a7do.background_density import BackgroundDensity

from a7do.reflection import ReflectionStore
from a7do.sleep import SleepEngine
from a7do.entity_promotion import EntityPromotionBridge


class A7DOMind:
    """
    Central cognitive orchestrator for A7DO.

    Design notes:
    - Memory IS the event stream
    - Profile system is optional / future
    - Entity promotion is gated + explicit
    - Sleep & reflection are safe and per-entity
    """

    def __init__(self):
        self.identity = Identity()
        self.memory = Memory()
        self.tagger = Tagger()
        self.coherence = CoherenceScorer()
        self.background = BackgroundDensity()

        # Reflection + sleep
        self.reflections = ReflectionStore()
        self.sleep_engine = SleepEngine(self.reflections)
        self._events_since_sleep = 0

        # Entity promotion bridge
        self.bridge = EntityPromotionBridge()

        self._last_signal = None

    # -----------------------------
    # Internal signal helper
    # -----------------------------
    def emit(self, kind: str, message: str):
        self._last_signal = {
            "kind": kind,
            "message": message,
            "time": time.time()
        }

    # -----------------------------
    # Main cognitive loop
    # -----------------------------
    def process(self, text: str) -> Dict[str, Any]:
        now = time.time()

        # 1) Tag input
        tags = self.tagger.tag(text) or []
        if isinstance(tags, dict):
            tags = tags.get("tags", [])

        # 2) Determine speaker / owner name
        # Default until a real profile system exists
        owner_name = getattr(self.identity, "creator", None) or "Alex Macleod"

        # 3) Entity Promotion Bridge
        bridge_tags, bridge_events, bridge_questions = self.bridge.observe(
            text, owner_name=owner_name
        )
        for t in bridge_tags:
            if t not in tags:
                tags.append(t)

        # 4) Store memory (this is the event)
        self.memory.add(
            kind="utterance",
            content=text,
            tags=tags,
            timestamp=now
        )

        self._events_since_sleep += 1

        # 5) Answer resolution
        answer = None
        lowered = text.lower().strip()

        # Entity queries
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

        # Identity queries
        if answer is None and self.identity.is_identity_question(text):
            answer = self.identity.respond(None)

        # Default response
        if answer is None:
            answer = self.identity.default_response(None)

        # 6) Coherence scoring
        coherence = self.coherence.evaluate(
            text=text,
            tags=tags
        )

        # 7) Sleep trigger (every 8 memories)
        sleep_report = None
        if self._events_since_sleep >= 8:
            recent = self.memory.recent(n=20)
            sleep_report = self.sleep_engine.run_global(recent)
            self.reflections.decay()
            self._events_since_sleep = 0
            self.emit("SLEEP", "Memory consolidation complete")

        # 8) Inspector payload
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