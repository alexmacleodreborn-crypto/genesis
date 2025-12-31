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


PLACE_WORDS = {
    "park", "home", "house", "garden", "vet", "beach", "work", "school", "gate", "street"
}
ACTIVITY_WORDS = {
    "walk", "walking", "ran", "run", "playing", "play", "sleep", "slept", "ride", "riding", "driving"
}
RELATION_WORDS = {
    "my dog", "my friend", "my mum", "my dad", "my sister", "my brother"
}


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

        # confirmation and disambiguation state
        self._pending_confirmation = None
        self._pending_disambiguation = None

    @property
    def events(self):
        return self.memory

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
    # Context extraction
    # -----------------------------
    def _extract_context(self, text: str, owner_name: str) -> Dict[str, Set[str]]:
        t = text.lower()
        places = {w for w in PLACE_WORDS if w in t}
        activities = {w for w in ACTIVITY_WORDS if w in t}

        relations = set()
        for r in RELATION_WORDS:
            if r in t:
                relations.add(r)

        # lightweight extra: "at the X" / "in the X"
        for token in ("at the ", "in the ", "to the "):
            if token in t:
                frag = t.split(token, 1)[1].split(" ", 1)[0]
                if frag and frag.isalpha():
                    places.add(frag)

        return {"places": places, "relations": relations, "activities": activities, "owner": {owner_name}}

    # -----------------------------
    # Chat confirmation intent
    # -----------------------------
    def _detect_confirmation_intent(self, text: str):
        t = text.lower().strip()

        if t.startswith("my name is "):
            return {"name": text[11:].strip(), "kind": "person", "is_self": True, "is_creator": True}

        if t.endswith(" is my dog"):
            return {"name": text[:-10].strip(), "kind": "pet"}

        if " is a nickname for " in t:
            a, b = text.split(" is a nickname for ")
            return {"alias": a.strip(), "name": b.strip()}

        # also accept: "Xena is a dog"
        if t.endswith(" is a dog"):
            return {"name": text[:-9].strip(), "kind": "pet"}

        return None

    # -----------------------------
    # Main loop
    # -----------------------------
    def process(self, text: str) -> Dict[str, Any]:
        now = time.time()
        lowered = text.lower().strip()

        tags = self.tagger.tag(text) or []
        owner_name = getattr(self.identity, "creator", None) or "Alex Macleod"
        context = self._extract_context(text, owner_name)

        # Always store memory
        self._memory_add_safe(kind="utterance", content=text, tags=tags, timestamp=now)

        # ---- Handle disambiguation reply (B-mode)
        if self._pending_disambiguation:
            d = self._pending_disambiguation
            # choices are simple: "1" or "2"
            if lowered in ("1", "first"):
                chosen = d["choices"][0]
            elif lowered in ("2", "second"):
                chosen = d["choices"][1]
            else:
                # if they give a name, try resolve again
                chosen, _, _ = self.bridge.resolve(d["name"], context)
                self._pending_disambiguation = None
                return {"answer": "Okay — carry on, and I’ll adapt as more context appears.", "tags": tags}

            # strengthen anchors on chosen
            chosen.places |= context.get("places", set())
            chosen.relations |= context.get("relations", set())
            chosen.activities |= context.get("activities", set())

            self._pending_disambiguation = None
            return {"answer": f"Got it — I’ll treat **{chosen.name}** as {d['labels'][chosen.entity_id]}.", "tags": tags}

        # ---- Handle confirmation replies
        if self._pending_confirmation:
            p = self._pending_confirmation
            if lowered in CONFIRM_WORDS:
                ent = self.bridge.confirm_entity(
                    name=p["name"],
                    kind=p["kind"],
                    owner_name=owner_name,
                    is_self=p.get("is_self", False),
                    is_creator=p.get("is_creator", False),
                    context=context,
                )
                self._pending_confirmation = None
                return {"answer": f"Confirmed. I now know who **{ent.name}** is.", "tags": tags}

            if lowered in CANCEL_WORDS:
                self._pending_confirmation = None
                return {"answer": "Okay — I won’t record that.", "tags": tags}

            # narrative input cancels confirmation mode
            self._pending_confirmation = None

        # ---- “Who is X?” (with B-mode ambiguity)
        if lowered.startswith("who is "):
            name = text[7:].strip(" ?!.")
            best, gap, ranked = self.bridge.resolve(name, context)

            if not best:
                return {"answer": f"I don’t know who **{name}** is yet.", "tags": tags}

            # If ambiguous and low gap -> ask (B mode)
            if len(ranked) > 1 and gap < 0.8:
                e1, e2 = ranked[0][0], ranked[1][0]
                labels = {
                    e1.entity_id: self.bridge.entity_label(e1, owner_name),
                    e2.entity_id: self.bridge.entity_label(e2, owner_name),
                }
                self._pending_disambiguation = {
                    "name": name,
                    "choices": [e1, e2],
                    "labels": labels,
                }
                return {
                    "answer": (
                        f"Do you mean **1) {labels[e1.entity_id]}** "
                        f"or **2) {labels[e2.entity_id]}**?"
                    ),
                    "tags": tags,
                }

            desc = self.bridge.describe(name, context=context)
            return {"answer": desc or "Noted.", "tags": tags}

        # ---- Observe unknowns (creates pending only for truly unknown names)
        self.bridge.observe(text, owner_name=owner_name)

        # ---- Confirmation intent
        intent = self._detect_confirmation_intent(text)
        if intent:
            if "alias" in intent:
                ok = self.bridge.add_alias(intent["name"], intent["alias"], context=context)
                if ok:
                    return {"answer": f"Noted. **{intent['alias']}** is now an alias for **{intent['name']}**.", "tags": tags}
                return {"answer": "I couldn’t attach that alias yet — tell me who it refers to.", "tags": tags}

            self._pending_confirmation = intent
            return {"answer": f"Just to confirm — should I record **{intent['name']}** as a **{intent['kind']}**?", "tags": tags}

        # ---- Identity questions
        if self._identity_question_safe(text):
            return {"answer": self._identity_respond_safe(), "tags": tags}

        # ---- Normal narrative
        coherence = self._evaluate_coherence_safe(text, tags)
        return {"answer": "Noted.", "tags": tags, "coherence": coherence}