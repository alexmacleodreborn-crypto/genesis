import time
import inspect
from typing import Dict, Any, Set

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
    A7DO Cognitive Core — BOOT-SAFE FOUNDATION
    """

    def __init__(self):
        self.identity = Identity()
        self.memory = Memory()
        self.tagger = Tagger()
        self.coherence = CoherenceScorer()
        self.background = BackgroundDensity()

        self.reflections = ReflectionStore()
        self.sleep_engine = SleepEngine(self.reflections)

        self.bridge = EntityPromotionBridge()
        self._last_signal = None

        self._pending_confirmation = None

        self._memory_add_sig = inspect.signature(self.memory.add)

    # -----------------------------
    # Inspector compatibility
    # -----------------------------
    @property
    def events(self):
        return self.memory

    # -----------------------------
    # Safe helpers
    # -----------------------------
    def _memory_add_safe(self, **kwargs):
        supported = {k: v for k, v in kwargs.items() if k in self._memory_add_sig.parameters}
        try:
            self.memory.add(**supported)
        except Exception:
            pass

    def _identity_question_safe(self, text: str) -> bool:
        if hasattr(self.identity, "is_identity_question"):
            try:
                return bool(self.identity.is_identity_question(text))
            except Exception:
                return False
        t = text.lower()
        return any(p in t for p in ("who are you", "what are you", "your name"))

    def _identity_respond_safe(self) -> str:
        if hasattr(self.identity, "respond"):
            try:
                return self.identity.respond(None)
            except Exception:
                pass
        return "I’m A7DO, and I’m learning."

    def _evaluate_coherence_safe(self, text, tags):
        try:
            return self.coherence.evaluate(text=text, tags=tags)
        except Exception:
            return {"score": 0.5, "label": "neutral"}

    # -----------------------------
    # Confirmation intent
    # -----------------------------
    def _detect_confirmation_intent(self, text: str):
        t = text.lower().strip()

        if t.startswith("my name is "):
            return {"name": text[11:].strip(), "kind": "person", "is_self": True, "is_creator": True}

        if t.endswith(" is my dog") or t.endswith(" is a dog"):
            return {"name": text.split(" is ")[0].strip(), "kind": "pet"}

        if " is a nickname for " in t:
            a, b = text.split(" is a nickname for ")
            return {"alias": a.strip(), "name": b.strip()}

        return None

    # -----------------------------
    # Main loop
    # -----------------------------
    def process(self, text: str) -> Dict[str, Any]:
        now = time.time()
        lowered = text.lower().strip()

        tags = self.tagger.tag(text) or []

        self._memory_add_safe(
            kind="utterance",
            content=text,
            tags=tags,
            timestamp=now,
        )

        # ---- Confirmation reply
        if self._pending_confirmation:
            p = self._pending_confirmation

            if lowered in CONFIRM_WORDS:
                ent = self.bridge.confirm_entity(
                    name=p["name"],
                    kind=p["kind"],
                    owner_name=getattr(self.identity, "creator", None),
                )
                self._pending_confirmation = None
                return {"answer": f"Confirmed. I now know who **{ent.name}** is.", "tags": tags}

            if lowered in CANCEL_WORDS:
                self._pending_confirmation = None
                return {"answer": "Okay — I won’t record that.", "tags": tags}

            # Narrative input cancels confirmation mode
            self._pending_confirmation = None

        # ---- Who is X?
        if lowered.startswith("who is "):
            name = text[7:].strip(" ?!.")
            desc = self.bridge.describe(name)
            if desc:
                return {"answer": desc, "tags": tags}
            return {"answer": f"I don’t know who **{name}** is yet.", "tags": tags}

        # ---- Observe names
        self.bridge.observe(text, owner_name=getattr(self.identity, "creator", None))

        # ---- Confirmation intent
        intent = self._detect_confirmation_intent(text)
        if intent:
            if "alias" in intent:
                ok = self.bridge.add_alias(intent["name"], intent["alias"])
                if ok:
                    return {"answer": f"Noted. **{intent['alias']}** is now an alias for **{intent['name']}**.", "tags": tags}
                return {"answer": "I couldn’t attach that alias yet.", "tags": tags}

            self._pending_confirmation = intent
            return {
                "answer": f"Just to confirm — should I record **{intent['name']}** as a **{intent['kind']}**?",
                "tags": tags,
            }

        # ---- Identity
        if self._identity_question_safe(text):
            return {"answer": self._identity_respond_safe(), "tags": tags}

        # ---- Normal narrative
        coherence = self._evaluate_coherence_safe(text, tags)
        return {"answer": "Noted.", "tags": tags, "coherence": coherence}