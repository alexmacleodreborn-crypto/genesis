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
from a7do.language import LanguageModule


CONFIRM_WORDS = {"yes", "confirm", "correct"}
CANCEL_WORDS = {"no", "cancel", "stop"}


PLACE_WORDS = {"park", "home", "house", "garden", "vet", "beach", "work", "school", "gate", "street"}
ACTIVITY_WORDS = {"walk", "walking", "run", "ran", "play", "playing", "sleep", "slept", "ride", "riding", "drive", "driving"}


class A7DOMind:
    def __init__(self):
        self.identity = Identity()
        self.memory = Memory()
        self.tagger = Tagger()
        self.coherence = CoherenceScorer()
        self.background = BackgroundDensity()

        self.reflections = ReflectionStore()
        self.sleep_engine = SleepEngine(self.reflections)

        self.bridge = EntityPromotionBridge()
        self.language = LanguageModule()

        self._last_signal = None
        self._pending_confirmation = None

        self._memory_add_sig = inspect.signature(self.memory.add)

    @property
    def events(self):
        return self.memory

    def _memory_add_safe(self, **kwargs):
        supported = {k: v for k, v in kwargs.items() if k in self._memory_add_sig.parameters}
        try:
            self.memory.add(**supported)
        except Exception:
            pass

    def _evaluate_coherence_safe(self, text, tags):
        try:
            return self.coherence.evaluate(text=text, tags=tags)
        except Exception:
            return {"score": 0.5, "label": "neutral"}

    def _extract_places_activities(self, text: str) -> (Set[str], Set[str]):
        tl = (text or "").lower()
        places = {w for w in PLACE_WORDS if w in tl}
        acts = {w for w in ACTIVITY_WORDS if w in tl}
        return places, acts

    # -----------------------------
    # Main loop
    # -----------------------------
    def process(self, text: str) -> Dict[str, Any]:
        now = time.time()
        lowered = (text or "").lower().strip()
        tags = self.tagger.tag(text) or []

        # Always log memory (raw)
        self._memory_add_safe(kind="utterance", content=text, tags=tags, timestamp=now)

        # 1) LANGUAGE FIRST (speaker / pronouns / ownership)
        lang = self.language.interpret(text)
        if lang.get("self_assertion") and lang.get("speaker_name"):
            # Strong lock (A)
            self.language.lock_speaker(lang["speaker_name"])

            # Optional: reflect in identity module fields if they exist
            try:
                setattr(self.identity, "creator", lang["speaker_name"])
            except Exception:
                pass
            try:
                setattr(self.identity, "name", "A7DO")
            except Exception:
                pass

            return {
                "answer": f"Locked. You are **{lang['speaker_name']}**.",
                "tags": tags,
            }

        speaker = self.language.speaker()  # may be None

        # 2) Handle pending confirmation replies (for optional entity confirmation flows)
        if self._pending_confirmation:
            p = self._pending_confirmation
            if lowered in CONFIRM_WORDS:
                places, acts = self._extract_places_activities(text)
                ent = self.bridge.confirm_entity(
                    name=p["name"],
                    kind=p["kind"],
                    owner_name=speaker if p.get("owner_is_speaker") else None,
                    relation=p.get("relation"),
                    places=places,
                    activities=acts,
                )
                self._pending_confirmation = None
                return {"answer": f"Confirmed. I now know who **{ent.name}** is.", "tags": tags}

            if lowered in CANCEL_WORDS:
                self._pending_confirmation = None
                return {"answer": "Okay — I won’t record that.", "tags": tags}

            # narrative input cancels confirmation mode
            self._pending_confirmation = None

        # 3) “who am I?” — pronoun grounding
        if lowered in {"who am i", "who am i?", "who am i !", "who am i."} or lowered.startswith("who am i"):
            if speaker:
                return {"answer": f"You are **{speaker}**.", "tags": tags}
            return {
                "answer": "I don’t know your name yet. Tell me: **“my name is …”**",
                "tags": tags,
            }

        # 4) “who is X?” — entity lookup (owner-aware)
        if lowered.startswith("who is "):
            name = text[7:].strip(" ?!.")
            desc = self.bridge.describe(name, owner_name=speaker)
            if desc:
                return {"answer": desc, "tags": tags}

            # ambiguous case: multiple entities share same name
            cands = self.bridge.candidates(name)
            if cands and len(cands) > 1:
                # human labels: "your Xena" vs "the other Xena"
                labels = []
                for e in cands[:2]:
                    if speaker and e.owner_name and e.owner_name.lower() == speaker.lower():
                        labels.append(f"your {e.name}")
                    else:
                        labels.append(f"the other {e.name}")
                return {
                    "answer": f"Do you mean **1) {labels[0]}** or **2) {labels[1]}**?",
                    "tags": tags,
                }

            return {"answer": f"I don’t know who **{name}** is yet.", "tags": tags}

        # 5) Strong ownership pattern: “my dog is called Xena”
        # This should create the entity immediately (no confirmation needed)
        if speaker and ("my dog is called " in lowered or "my dog is named " in lowered):
            if "my dog is called " in lowered:
                name = text.lower().split("my dog is called ", 1)[1].strip().strip(" .!?")
            else:
                name = text.lower().split("my dog is named ", 1)[1].strip().strip(" .!?")
            # restore capitalization simply
            name = name[:1].upper() + name[1:] if name else name
            places, acts = self._extract_places_activities(text)
            ent = self.bridge.confirm_entity(
                name=name,
                kind="pet",
                owner_name=speaker,
                relation="my dog",
                places=places,
                activities=acts,
            )
            return {"answer": f"Noted. **{ent.name}** is your dog.", "tags": tags}

        # 6) Optional confirmation pattern: “Xena is my dog” / “Xena is a dog”
        if " is my dog" in lowered or lowered.endswith(" is a dog"):
            name = text.split(" is ")[0].strip().strip(" .!?")
            # ask for confirmation (keeps behaviour consistent)
            self._pending_confirmation = {
                "name": name,
                "kind": "pet",
                "relation": "my dog" if "is my dog" in lowered else None,
                "owner_is_speaker": True if "is my dog" in lowered else False,
            }
            return {
                "answer": f"Just to confirm — should I record **{name}** as **your dog**?",
                "tags": tags,
            }

        # 7) Observe unknown names (pending entities)
        self.bridge.observe(text, owner_name=speaker)

        # 8) Identity module (A7DO’s identity)
        if hasattr(self.identity, "is_identity_question"):
            try:
                if self.identity.is_identity_question(text):
                    if hasattr(self.identity, "respond"):
                        return {"answer": self.identity.respond(text), "tags": tags}
            except Exception:
                pass

        # 9) Normal narrative
        coherence = self._evaluate_coherence_safe(text, tags)
        return {
            "answer": "Noted.",
            "tags": tags,
            "coherence": coherence,
        }