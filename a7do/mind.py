import time
from typing import Dict, Any

from a7do.identity import Identity
from a7do.memory import Memory
from a7do.events import EventManager
from a7do.tagger import Tagger
from a7do.profile import ProfileManager
from a7do.coherence import CoherenceScorer
from a7do.background_density import BackgroundDensity

from a7do.reflection import ReflectionStore
from a7do.sleep import SleepEngine


class A7DOMind:
    """
    Central cognitive orchestrator.

    Responsibilities:
    - Event flow
    - Identity resolution
    - Memory logging
    - Reflection + sleep
    - Safe output composition
    """

    def __init__(self):
        self.identity = Identity()
        self.memory = Memory()
        self.events = EventManager()
        self.tagger = Tagger()
        self.profiles = ProfileManager()
        self.coherence = CoherenceScorer()
        self.background = BackgroundDensity()

        # NEW
        self.reflections = ReflectionStore()
        self.sleep_engine = SleepEngine(self.reflections)

        self._events_since_sleep = 0
        self._last_signal = None

    # -----------------------------
    # Internal helper
    # -----------------------------

    def emit(self, kind: str, message: str):
        self._last_signal = {
            "kind": kind,
            "message": message,
            "time": time.time()
        }

    # -----------------------------
    # Main processing loop
    # -----------------------------

    def process(self, text: str) -> Dict[str, Any]:
        now = time.time()

        # 1. Tag input (language grounding only)
        tags = self.tagger.tag(text)

        # 2. Resolve / update speaker profile
        profile = self.profiles.current()
        profile.learn(text, tags)

        # 3. Create / extend event frame
        event = self.events.ingest(
            utterance=text,
            tags=tags,
            timestamp=now
        )

        # 4. Memory log (raw experience)
        self.memory.add(
            kind="utterance",
            content=text,
            tags=tags,
            timestamp=now
        )

        # 5. Identity handling (only if explicitly asked)
        answer = None
        if self.identity.is_identity_question(text):
            answer = self.identity.respond(profile)

        # 6. Update coherence score
        coherence = self.coherence.evaluate(
            text=text,
            tags=tags,
            event=event
        )

        # 7. Track for sleep
        self._events_since_sleep += 1

        # 8. Trigger per-silo sleep safely
        sleep_report = None
        if self._events_since_sleep >= 8:
            sleep_report = {}
            for entity_id in self.events.silos.keys():
                frames = self.events.silo_events(entity_id, n=10)
                created = self.sleep_engine.run_for_entity(entity_id, frames)
                if created:
                    sleep_report[entity_id] = len(created)

            self.reflections.decay()
            self._events_since_sleep = 0
            self.emit("SLEEP", "Per-silo consolidation complete")

        # 9. Compose response
        if answer is None:
            answer = self.identity.default_response(profile)

        result = {
            "answer": answer,
            "event_id": event.event_id,
            "tags": tags,
            "coherence": coherence,
            "signal": self._last_signal,
            "sleep": sleep_report,
            "reflections": {
                eid: [
                    {
                        "pattern": v.reflection_key[1],
                        "score": round(v.score, 3),
                        "band": v.band,
                        "active": v.active
                    }
                    for v in self.reflections.active_versions(eid)
                ]
                for eid in self.events.silos.keys()
            }
        }

        return result