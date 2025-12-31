import time
import inspect
from typing import Dict, Any, List

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
    - No assumptions about Identity helper methods
    - No assumptions about Memory.add signature
    - Coherence scorer is optional / adaptive
    - Entity promotion is gated and explicit
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

        # Inspect memory.add once so we can call it safely
        self._memory_add_sig = inspect.signature(self.memory.add)

    # -----------------------------
    # Internal helpers
    # -----------------------------
    def emit(self, kind: str, message: str):
        self._last_signal = {
            "kind": kind,
            "message": message,
            "time": time.time(),
        }

    def _memory_add_safe(self, **kwargs):
        """
        Call memory.add with only supported parameters.
        Falls back to positional add(kind, content).
        Never crashes cognition for storage.
        """
        supported = {}
        for name in self._memory_add_sig.parameters:
            if name in kwargs:
                supported[name] = kwargs[name]

        try:
            self.memory.add(**supported)
        except TypeError:
            try:
                self.memory.add(kwargs.get("kind"), kwargs.get("content"))
            except Exception:
                pass

    def _identity_handles_question(self, text: str) -> bool:
        """
        If Identity implements is_identity_question(), use it.
        Otherwise, we do a tiny heuristic fallback.
        """
        if hasattr(self.identity, "is_identity_question") and callable(self.identity.is_identity_question):
            try:
                return bool(self.identity.is_identity_question(text))
            except Exception:
                return False

        # Heuristic fallback (very light)
        t = text.lower().strip()
        return any(
            phrase in t
            for phrase in (
                "who are you",
                "what are you",
                "your name",
                "who is a7do",
                "what is a7do",
            )
        )

    def _identity_respond_safe(self):
        """
        If Identity implements respond(profile), use it; otherwise fall back.
        """
        if hasattr(self.identity, "respond") and callable(self.identity.respond):
            try:
                return self.identity.respond(None)
            except Exception:
                pass
        return None

    def _identity_default_safe(self):
        """
        If Identity implements default_response(profile), use it.
        Otherwise return a neutral sentence.
        """
        if hasattr(self.identity, "default_response") and callable(self.identity.default_response):
            try:
                return self.identity.default_response(None)
            except Exception:
                pass
        return "I’m awake and learning."

    def _evaluate_coherence_safe(self, text: str, tags: List[str]) -> Dict[str, Any]:
        """
        Safely evaluate coherence if the scorer supports it.
        Tries several method names, otherwise returns a neutral coherence object.
        """
        scorer = self.coherence

        # Case 1: expected evaluate(text=, tags=)
        if hasattr(scorer, "evaluate") and callable(getattr(scorer, "evaluate")):
            try:
                out = scorer.evaluate(text=text, tags=tags)
                return out if isinstance(out, dict) else {"score": out}
            except Exception:
                pass

        # Case 2: alternate method names
        for name in ("score", "assess", "compute"):
            if hasattr(scorer, name) and callable(getattr(scorer, name)):
                try:
                    out = getattr(scorer, name)(text, tags)
                    return out if isinstance(out, dict) else {"score": out}
                except Exception:
                    pass

        # Fallback: neutral coherence
        return {
            "score": 0.5,
            "label": "neutral",
            "note": "coherence module inactive or method not found",
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
        if not isinstance(tags, list):
            tags = list(tags)

        # 2) Speaker / owner name (default)
        owner_name = getattr(self.identity, "creator", None) or "Alex Macleod"

        # 3) Entity Promotion Bridge (linguistic → entity binding)
        bridge_tags, bridge_events, bridge_questions = self.bridge.observe(text, owner_name=owner_name)
        for t in bridge_tags:
            if t not in tags:
                tags.append(t)

        # 4) Store memory (safe)
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

        # Entity query support
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

        # Identity questions
        if answer is None and self._identity_handles_question(text):
            answer = self._identity_respond_safe()

        # Default response
        if answer is None:
            answer = self._identity_default_safe()

        # 6) Coherence (safe)
        coherence = self._evaluate_coherence_safe(text=text, tags=tags)

        # 7) Sleep trigger (every 8 inputs)
        sleep_report = None
        if self._events_since_sleep >= 8:
            try:
                recent = self.memory.recent(n=20)
            except Exception:
                recent = []

            # Your SleepEngine may expose run_global() or run(); adapt safely
            if hasattr(self.sleep_engine, "run_global") and callable(getattr(self.sleep_engine, "run_global")):
                try:
                    sleep_report = self.sleep_engine.run_global(recent)
                except Exception:
                    sleep_report = None
            elif hasattr(self.sleep_engine, "run") and callable(getattr(self.sleep_engine, "run")):
                try:
                    sleep_report = self.sleep_engine.run(recent)
                except Exception:
                    sleep_report = None

            # decay reflection versions if available
            try:
                self.reflections.decay()
            except Exception:
                pass

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