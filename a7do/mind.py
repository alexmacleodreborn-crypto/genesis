import time
import inspect
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

    Fully defensive:
    - No assumptions about Identity helpers
    - No assumptions about Memory API
    - Entity promotion gated and explicit
    """

    def __init__(self):
        self.identity = Identity()
        self.memory = Memory()
        self.tagger = Tagger()
        self.coherence = CoherenceScorer()
        self.background = BackgroundDensity()

        self.reflections = ReflectionStore()
        self.sleep_engine = SleepEngine(self.reflections)
        self._events_since_sleep = 0

        self.bridge = EntityPromotionBridge()

        self._last_signal = None

        # Inspect memory.add once
        self._memory_add_sig = inspect.signature(self.memory.add)

    # -----------------------------
    # Internal helpers
    # -----------------------------
    def emit(self, kind: str, message: str):
        self._last_signal = {
            "kind": kind,
            "message": message,
            "time": time.time()
        }

    def _memory_add_safe(self, **kwargs):
        supported = {}
        for name in self._memory_add_sig.parameters:
            if name in kwargs:
                supported[name] = kwargs[name]

        try:
            self.memory.add(**supported)
        except TypeError:
            try:
                self.memory.add(
                    kwargs.get("kind"),
                    kwargs.get("content")
                )
            except Exception:
                pass  # never crash cognition for storage

    def _identity_handles_question(self, text: str) -> bool:
        if hasattr(self.identity, "is_identity_question") and callable(
            self.identity.is_identity_question
        ):
            try:
                return self.identity.is_identity_question(text)
            except Exception:
                return False
        return False

    def _identity_respond(self, text: str):
        if hasattr(self.identity, "respond") and callable(self.identity.respond):
            try:
                return self.identity.respond(None)
            except Exception:
                return None
        return None

    def _identity_default(self):
        if hasattr(self.identity, "default_response") and callable(
            self.identity.default_response
        ):
            try:
                return self.identity.default_response(None)
            except Exception:
                return None
        return "I’m here and learning."

    # -----------------------------
    # Main cognitive loop
    # -----------------------------
    def process(self, text: str) -> Dict[str, Any]:
        now = time.time()

        # 1) Tag input
        tags = self.tagger.tag(text) or []
        if isinstance(tags, dict):
            tags = tags.get("tags", [])

        # 2) Speaker / owner (default)
        owner_name = getattr(self.identity, "creator", None) or "Alex Macleod"

        # 3) Entity Promotion Bridge
        bridge_tags, bridge_events, bridge_questions = self.bridge.observe(
            text, owner_name=owner_name
        )
        for t in bridge_tags:
            if t not in tags:
                tags.append(t)

        # 4) Memory
        self._memory_add_safe(
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

        # Identity queries (safe)
        if answer is None and self._identity_handles_question(text):
            answer = self._identity_respond(text)

        # Default response
        if answer is None:
            answer = self._identity_default()

        # 6) Coherence
        coherence = self.coherence.evaluate(text=text, tags=tags)

        # 7) Sleep
        sleep_report = None
        if self._events_since_sleep >= 8:
            try:
                recent = self.memory.recent(n=20)
            except Exception:
                recent = []
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