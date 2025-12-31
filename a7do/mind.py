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

        self._memory_add_sig = inspect.signature(self.memory.add)

        # Chat confirmation state
        self._pending_confirmation = None

    # ----------------------------------
    # Backward compatibility
    # ----------------------------------
    @property
    def events(self):
        return self.memory

    # ----------------------------------
    # Utilities
    # ----------------------------------
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

    # ----------------------------------
    # Chat confirmation detection
    # ----------------------------------
    def _detect_confirmation_intent(self, text: str):
        t = text.lower().strip()

        # Explicit patterns only
        if t.startswith("my name is "):
            name = text[11:].strip()
            return {
                "name": name,
                "kind": "person",
                "is_self": True,
                "is_creator": True,
            }

        if " is my dog" in t:
            name = text.split(" is my dog")[0].strip()
            return {
                "name": name,
                "kind": "pet",
                "is_self": False,
                "is_creator": False,
            }

        if " is a nickname for " in t:
            a, b = text.split(" is a nickname for ")
            return {
                "alias": a.strip(),
                "name": b.strip(),
            }

        return None

    # ----------------------------------
    # Coherence (safe)
    # ----------------------------------
    def _evaluate_coherence_safe(self, text, tags):
        try:
            return self.coherence.evaluate(text=text, tags=tags)
        except Exception:
            return {"score": 0.5, "label": "neutral"}

    # ----------------------------------
    # Main cognitive loop
    # ----------------------------------
    def process(self, text: str) -> Dict[str, Any]:
        now = time.time()
        tags = self.tagger.tag(text) or []

        self._memory_add_safe(
            kind="utterance",
            content=text,
            tags=tags,
            timestamp=now,
        )

        # --- Handle pending confirmation reply
        if self._pending_confirmation:
            if text.lower() in ("yes", "confirm", "correct"):
                p = self._pending_confirmation
                self.bridge.confirm_entity(
                    name=p["name"],
                    kind=p["kind"],
                    is_self=p.get("is_self", False),
                    is_creator=p.get("is_creator", False),
                )
                self._pending_confirmation = None
                return {
                    "answer": f"Confirmed. I now know who **{p['name']}** is.",
                    "tags": tags,
                }
            else:
                self._pending_confirmation = None

        # --- Detect confirmation intent
        confirm = self._detect_confirmation_intent(text)
        if confirm:
            if "alias" in confirm:
                self.bridge.add_alias(confirm["name"], confirm["alias"])
                return {
                    "answer": f"Noted. **{confirm['alias']}** is now an alias for **{confirm['name']}**.",
                    "tags": tags,
                }

            self._pending_confirmation = confirm
            return {
                "answer": (
                    f"Just to confirm — should I record **{confirm['name']}** "
                    f"as a **{confirm['kind']}**?"
                ),
                "tags": tags,
            }

        # --- Identity questions
        if self.identity.is_identity_question(text):
            return {
                "answer": self.identity.respond(text),
                "tags": tags,
            }

        # --- Default response
        coherence = self._evaluate_coherence_safe(text, tags)

        return {
            "answer": "I’m learning and recording what you tell me.",
            "tags": tags,
            "coherence": coherence,
            "signal": self._last_signal,
            "pending_entities": [
                {
                    "name": p.name,
                    "confidence": p.confidence,
                    "count": p.count,
                }
                for p in self.bridge.pending.values()
            ],
            "entity_graph": [
                {
                    "name": e.name,
                    "kind": e.kind,
                    "aliases": e.aliases,
                }
                for e in self.bridge.entities.values()
            ],
        }