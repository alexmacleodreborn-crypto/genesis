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

    FINAL FOUNDATION VERSION
    ------------------------
    - Memory is the event stream
    - `events` is a backward-compatible alias
    - Entity promotion is gated and explicit
    - Coherence is optional and non-blocking
    - Sleep & reflection are safe and deferred
    """

    def __init__(self):
        # Core cognition
        self.identity = Identity()
        self.memory = Memory()
        self.tagger = Tagger()
        self.coherence = CoherenceScorer()
        self.background = BackgroundDensity()

        # Reflection + sleep
        self.reflections = ReflectionStore()
        self.sleep_engine = SleepEngine(self.reflections)
        self._events_since_sleep = 0

        # Entity grounding
        self.bridge = EntityPromotionBridge()

        # System signal
        self._last_signal = None

        # Inspect memory.add once for safe calls
        self._memory_add_sig = inspect.signature(self.memory.add)

    # -------------------------------------------------
    # Backward compatibility (IMPORTANT)
    # -------------------------------------------------
    @property
    def events(self):
        """
        Backward-compatibility alias.

        Older inspectors expect `mind.events`.
        Conceptually correct: events ARE memory.
        """
        return self.memory

    # -------------------------------------------------
    # Internal helpers
    # -------------------------------------------------
    def emit(self, kind: str, message: str):
        self._last_signal = {
            "kind": kind,
            "message": message,
            "time": time.time(),
        }

    def _memory_add_safe(self, **kwargs):
        """
        Call memory.add with only supported parameters.
        Never crash cognition for storage mismatches.
        """
        supported = {}
        for name in self._memory_add_sig.parameters:
            if name in kwargs:
                supported[name] = kwargs[name]

        try:
            self.memory.add(**supported)
        except TypeError:
            try:
                # Fallback: positional (kind, content)
                self.memory.add(kwargs.get("kind"), kwargs.get("content"))
            except Exception:
                pass

    def _identity_handles_question(self, text: str) -> bool:
        """
        Use Identity helper if present, otherwise light heuristic.
        """
        if hasattr(self.identity, "is_identity_question") and callable(self.identity.is_identity_question):
            try:
                return bool(self.identity.is_identity_question(text))
            except Exception:
                return False

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
        if hasattr(self.identity, "respond") and callable(self.identity.respond):
            try:
                return self.identity.respond(None)
            except Exception:
                pass
        return None

    def _identity_default_safe(self):
        if hasattr(self.identity, "default_response") and callable(self.identity.default_response):
            try:
                return self.identity.default_response(None)
            except Exception:
                pass
        return "I’m awake and learning."

    def _evaluate_coherence_safe(self, text: str, tags: List[str]) -> Dict[str, Any]:
        """
        Coherence is optional meta-cognition.
        Never blocks reasoning.
        """
        scorer = self.coherence

        if hasattr(scorer, "evaluate") and callable(getattr(scorer, "evaluate")):
            try:
                out = scorer.evaluate(text=text, tags=tags)
                return out if isinstance(out, dict) else {"score": out}
            except Exception:
                pass

        for name in ("score", "assess", "compute"):
            if hasattr(scorer, name) and callable(getattr(scorer, name)):
                try:
                    out = getattr(scorer, name)(text, tags)
                    return out if isinstance(out, dict) else {"score": out}
                except Exception:
                    pass

        return {
            "score": 0.5,
            "label": "neutral",
            "note": "coherence module inactive or undefined",
        }

    # -------------------------------------------------
    # Main cognitive loop
    # -------------------------------------------------
    def process(self, text: str) -> Dict[str, Any]:
        now = time.time()

        # 1) Tag input
        tags = self.tagger.tag(text) or []
        if isinstance(tags, dict):
            tags = tags.get("tags", [])
        if not isinstance(tags, list):
            tags = list(tags)

        # 2) Default speaker / owner
        owner_name = getattr(self.identity, "creator", None) or "Alex Macleod"

        # 3) Entity Promotion Bridge
        bridge_tags, bridge_events, bridge_questions = self.bridge.observe(
            text, owner_name=owner_name
        )
        for t in bridge_tags:
            if t not in tags:
                tags.append(t)

        # 4) Store memory (event)
        self._memory_add_safe(
            kind="utterance",
            content=text,
            tags=tags,
            timestamp=now,
        )

        self._events_since_sleep += 1

        # 5) Answer resolution
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

        if answer is None and self._identity_handles_question(text):
            answer = self._identity_respond_safe()

        if answer is None:
            answer = self._identity_default_safe()

        # 6) Coherence (safe)
        coherence = self._evaluate_coherence_safe(text=text, tags=tags)

        # 7) Sleep trigger (every 8 events)
        sleep_report = None
        if self._events_since_sleep >= 8:
            try:
                recent = self.memory.recent(n=20)
            except Exception:
                recent = []

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