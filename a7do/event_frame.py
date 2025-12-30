import time
from dataclasses import dataclass, field
from typing import Dict, List, Any


@dataclass
class EventFrame:
    """
    One temporally-bound 'moment' of lived experience.
    Can accumulate multiple user inputs within a time window.
    """
    event_id: str
    t0: float
    t1: float
    utterances: List[str] = field(default_factory=list)

    entities: List[str] = field(default_factory=list)      # entity_ids
    labels: List[str] = field(default_factory=list)        # surface labels mentioned (e.g., "Xena", "park")
    domains: List[str] = field(default_factory=list)       # tagger domains

    modalities: Dict[str, float] = field(default_factory=dict)  # visual/sound/touch etc (lightweight)
    emotions: Dict[str, float] = field(default_factory=dict)    # excited/sad etc
    environments: Dict[str, float] = field(default_factory=dict) # park/home/gate etc
    actions: Dict[str, float] = field(default_factory=dict)      # tied/trained/ride etc

    meta: Dict[str, Any] = field(default_factory=dict)

    def add_utterance(self, text: str):
        self.utterances.append(text)
        self.t1 = time.time()

    def merge_signals(self, other: "EventFrame"):
        """Merge another frame into this one."""
        self.t1 = max(self.t1, other.t1)
        self.utterances.extend(other.utterances)

        self.entities = list(dict.fromkeys(self.entities + other.entities))
        self.labels = list(dict.fromkeys(self.labels + other.labels))
        self.domains = list(dict.fromkeys(self.domains + other.domains))

        for k, v in other.modalities.items():
            self.modalities[k] = self.modalities.get(k, 0.0) + v
        for k, v in other.emotions.items():
            self.emotions[k] = self.emotions.get(k, 0.0) + v
        for k, v in other.environments.items():
            self.environments[k] = self.environments.get(k, 0.0) + v
        for k, v in other.actions.items():
            self.actions[k] = self.actions.get(k, 0.0) + v

    def snapshot(self):
        return {
            "event_id": self.event_id,
            "t0": self.t0,
            "t1": self.t1,
            "duration_s": round(self.t1 - self.t0, 2),
            "utterances": self.utterances[-10:],
            "entities": self.entities,
            "labels": self.labels,
            "domains": self.domains,
            "modalities": self.modalities,
            "emotions": self.emotions,
            "environments": self.environments,
            "actions": self.actions,
            "meta": self.meta,
        }


class EventMemory:
    """
    Stores event frames and supports temporal binding.
    Also maintains 'silos' (life-streams) per entity_id.
    """

    def __init__(self, bind_window_s: int = 20):
        self.bind_window_s = bind_window_s
        self.frames: List[EventFrame] = []
        self.silos: Dict[str, List[str]] = {}  # entity_id -> [event_id]
        self._last_event: EventFrame | None = None
        self._counter = 0

    def _new_id(self):
        self._counter += 1
        return f"EVT_{self._counter:06d}"

    def start_or_bind(self) -> EventFrame:
        now = time.time()
        if self._last_event and (now - self._last_event.t1) <= self.bind_window_s:
            return self._last_event
        evt = EventFrame(event_id=self._new_id(), t0=now, t1=now)
        self.frames.append(evt)
        self._last_event = evt
        return evt

    def attach_entity(self, evt: EventFrame, entity_id: str):
        if entity_id not in evt.entities:
            evt.entities.append(entity_id)
        self.silos.setdefault(entity_id, [])
        if evt.event_id not in self.silos[entity_id]:
            self.silos[entity_id].append(evt.event_id)

    def recent(self, n=10):
        return [f.snapshot() for f in self.frames[-n:]]

    def get_event(self, event_id: str):
        for f in self.frames:
            if f.event_id == event_id:
                return f
        return None

    def silo_events(self, entity_id: str, n=15):
        ids = self.silos.get(entity_id, [])[-n:]
        out = []
        for eid in ids:
            f = self.get_event(eid)
            if f:
                out.append(f)
        return out

    def stats(self):
        return {
            "bind_window_s": self.bind_window_s,
            "event_count": len(self.frames),
            "silo_count": len(self.silos),
            "last_event_id": self._last_event.event_id if self._last_event else None
        }