from typing import Dict, Any
from a7do.experience import ExperienceStore
from a7do.lexicon import Lexicon
from a7do.sleep import SleepEngine
from a7do.coherence import CoherenceEngine

class A7DOMind:
    """
    Non-aware infant cognition:
    - experiences scheduled events
    - updates lexicon exposure counts
    - updates spatial state via schedule
    - sleeps + replay stats
    Observer can see full trace; A7DO cannot.
    """

    def __init__(self, schedule, world):
        self.schedule = schedule
        self.world = world

        self.experiences = ExperienceStore()
        self.lexicon = Lexicon()
        self.sleep_engine = SleepEngine()
        self.coherence = CoherenceEngine()

        self.last = None
        self.last_coherence = None
        self.last_sleep_report = None

        # observer trace buffer
        self.trace = []

    def wake(self):
        self.last = "wake"
        self.trace.append({"phase": "wake", "room": self.schedule.current_room})

    def ingest_event(self, ev) -> Dict[str, Any]:
        # coherence validation
        coh = self.coherence.evaluate(self.world, self.schedule.homeplot, ev)
        self.last_coherence = coh

        # if coherence fails hard, we do not ingest (prevents decoherence crash)
        if coh["score"] <= 0.25:
            self.last = "blocked"
            self.trace.append({"phase": "blocked", "event": ev.as_prompt(), "coherence": coh})
            return {"ok": False, "blocked": True, "coherence": coh}

        # apply movement: if event has to_room, update schedule spatial room
        if ev.to_room:
            # movement inferred from place transition in stream
            from_room = self.schedule.current_room
            self.schedule.current_room = ev.to_room
            self.schedule.spatial.room = ev.to_room
            self.trace.append({"phase": "movement", "from": from_room, "to": ev.to_room})

        # update local position if provided
        if ev.pos_xy:
            self.schedule.spatial.pos_xy = ev.pos_xy

        # locomotion exposure (crawl/walk)
        if ev.motor and ev.motor.get("type") in ("crawl", "walk"):
            self.schedule.spatial.locomotion = ev.motor.get("type")

        # store experience + learn lexicon
        self.experiences.add(ev)
        self.lexicon.learn_from_event(ev)

        # observer trace
        self.trace.append({
            "phase": "experience",
            "room": ev.room,
            "prompt": ev.as_prompt(),
            "event": {
                "room": ev.room,
                "to_room": ev.to_room,
                "agent": ev.agent,
                "action": ev.action,
                "object": ev.obj,
                "emphasis": ev.emphasis,
                "sound": ev.sound,
                "smell": ev.smell,
                "motor": ev.motor,
                "pos_xy": ev.pos_xy,
            },
            "coherence": coh
        })

        self.last = f"experienced in {ev.room}"
        return {"ok": True, "coherence": coh}

    def sleep(self):
        self.last = "sleep"
        rep = self.sleep_engine.replay(self.experiences)
        self.last_sleep_report = rep
        self.trace.append({"phase": "sleep", "report": rep})
        return rep