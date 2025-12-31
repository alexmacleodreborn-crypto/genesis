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


CONFIRM_WORDS = {"yes", "confirm", "correct"}
CANCEL_WORDS = {"no", "cancel", "stop"}


class A7DOMind:
    """
    A7DO Cognitive Core — FINAL STABLE FOUNDATION

    Guarantees:
    - No crashes from missing bridge APIs
    - Explicit entity confirmation only
    - Narrative input always allowed
    - Identity handled defensively
    - Memory = event stream
    """

    def __init__(self):
        # Core systems
        self.identity = Identity()
        self.memory = Memory()
        self.tagger = Tagger()
        self.coherence = CoherenceScorer()
        self.background = BackgroundDensity()

        # Reflection & sleep
        self.reflections = ReflectionStore()
        self.sleep_engine = SleepEngine(self.reflections)
        self._events_since_sleep = 0

        # Entity grounding
        self.bridge = EntityPromotionBridge()

        # Signals
        self._last_signal = None

        # Safe memory.add inspection
        self._memory_add_sig = inspect.signature(self.memory.add)

        # Confirmation state
        self._pending_confirmation = None

    # -------------------------------------------------
    # Backward compatibility
    # -------------------------------------------------
    @property
    def events(self):
        """Inspector compatibility: events == memory"""
        return self.memory

    # -------------------------------------------------
    # Utilities
    # -------------------------------------------------
    def emit(self, kind: str, message: str):
        self._last_signal = {
            "kind": kind,
            "message": message,
            "time": time.time(),
        }

    def _memory_add_safe(self, **kwargs):
        supported = {
            k: v for k, v in kwargs.items()
            if k in self._memory_add_sig.parameters
        }
        try:
            self.memory.add(**supported)
        except Exception:
            pass

    # -------------------------------------------------
    # SAFE identity handling
    # -------------------------------------------------
    def _identity_question_safe(self, text: str) -> bool:
        if hasattr(self.identity, "is_identity_question"):
            try:
                return bool(self.identity.is_identity_question(text))
            except Exception:
                return False

        t = text.lower()
        return any(p in t for p in ("who are you", "what are you", "your name"))

    def _identity_respond_safe(self):
        if hasattr(self.identity, "respond"):
            try:
                return self.identity.respond(None)
            except Exception:
                pass
        return "I’m A7DO, and I’m learning."

    def _identity_default_safe(self):
        if hasattr(self.identity, "default_response"):
            try:
                return self.identity.default_response(None)
            except Exception:
                pass
        return "I’m learning from what you tell me."

    # -------------------------------------------------
    # SAFE entity confirmation adapter
    # -------------------------------------------------
    def _confirm_entity_safe(self, **kwargs) -> bool:
        """
        Attempt to confirm/promote an entity without assuming
        the bridge API exists.
        """
        bridge = self.bridge

        if hasattr(bridge, "confirm_entity") and callable(bridge.confirm_entity):
            try:
                bridge.confirm_entity(**kwargs)
                return True
            except Exception:
                return False

        for name in ("promote", "promote_entity", "confirm"):
            if hasattr(bridge, name) and callable(getattr(bridge, name)):
                try:
                    getattr(bridge, name)(**kwargs)
                    return True
                except Exception:
                    return False

        return False

    # -------------------------------------------------
    # Confirmation intent detection (STRICT)
    # -------------------------------------------------
    def _detect_confirmation_intent(self, text: str):
        t = text.lower().strip()

        if t.startswith("my name is "):
            return {
                "name": text[11:].strip(),
                "kind": "person",
                "is_self": True,
                "is_creator": True,
            }

        if t.endswith(" is my dog"):
            return {
                "name": text[:-10].strip(),
                "kind": "pet",
            }

        if " is a nickname for " in t:
            a, b = text.split(" is a nickname for ")
            return {
                "alias": a.strip(),
                "name": b.strip(),
            }

        return None

    # -------------------------------------------------
    # SAFE coherence
    # -------------------------------------------------
    def _evaluate_coherence_safe(self, text, tags):
        try:
            return self.coherence.evaluate(text=text, tags=tags)
        except Exception:
            return {"score": 0.5, "label": "neutral"}

    # -------------------------------------------------
    # MAIN cognitive loop
    # -------------------------------------------------
    def process(self, text: str) -> Dict[str, Any]:
        now = time.time()
        lowered = text.lower().strip()

        tags = self.tagger.tag(text) or []

        # Always record memory
        self._memory_add_safe(
            kind="utterance",
            content=text,
            tags=tags,
            timestamp=now,
        )

        # ---------------------------------------------
        # Handle confirmation replies (ONLY if matched)
        # ---------------------------------------------
        if self._pending_confirmation:
            p = self._pending_confirmation

            if lowered in CONFIRM_WORDS:
                ok = self._confirm_entity_safe(
                    name=p["name"],
                    kind=p["kind"],
                    is_self=p.get("is_self", False),
                    is_creator=p.get("is_creator", False),
                )
                self._pending_confirmation = None

                if ok:
                    return {
                        "answer": f"Confirmed. I now know who **{p['name']}** is.",
                        "tags": tags,
                    }

                return {
                    "answer": (
                        f"I’ve noted the confirmation for **{p['name']}**, "
                        f"but my entity system isn’t ready to lock it in yet."
                    ),
                    "tags": tags,
                }

            if lowered in CANCEL_WORDS:
                self._pending_confirmation = None
                return {
                    "answer": "Okay — I won’t record that.",
                    "tags": tags,
                }

            # Narrative input → exit confirmation mode
            self._pending_confirmation = None

        # ---------------------------------------------
        # Detect new confirmation intent
        # ---------------------------------------------
        intent = self._detect_confirmation_intent(text)
        if intent:
            if "alias" in intent:
                if hasattr(self.bridge, "add_alias"):
                    try:
                        self.bridge.add_alias(intent["name"], intent["alias"])
                        return {
                            "answer": (
                                f"Noted. **{intent['alias']}** is now an alias "
                                f"for **{intent['name']}**."
                            ),
                            "tags": tags,
                        }
                    except Exception:
                        pass

            self._pending_confirmation = intent
            return {
                "answer": (
                    f"Just to confirm — should I record **{intent['name']}** "
                    f"as a **{intent['kind']}**?"
                ),
                "tags": tags,
            }

        # ---------------------------------------------
        # Identity questions
        # ---------------------------------------------
        if self._identity_question_safe(text):
            return {
                "answer": self._identity_respond_safe(),
                "tags": tags,
            }

        # ---------------------------------------------
        # Normal narrative input (ALWAYS allowed)
        # ---------------------------------------------
        coherence = self._evaluate_coherence_safe(text, tags)

        return {
            "answer": "Noted.",
            "tags": tags,
            "coherence": coherence,
            "signal": self._last_signal,
            "pending_entities": [
                {
                    "name": p.name,
                    "confidence": p.confidence,
                    "count": p.count,
                }
                for p in getattr(self.bridge, "pending", {}).values()
            ],
            "entity_graph": [
                {
                    "name": e.name,
                    "kind": e.kind,
                    "aliases": e.aliases,
                }
                for e in getattr(self.bridge, "entities", {}).values()
            ],
        }