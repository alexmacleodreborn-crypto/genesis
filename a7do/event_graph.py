import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional, Set, List


@dataclass
class Event:
    event_id: str
    participants: Set[str]
    place: Optional[str]
    description: str
    timestamp: float

    # Sensory grounding (C rule)
    smells: List[str] = field(default_factory=list)       # normalised
    sounds: List[str] = field(default_factory=list)       # normalised
    raw_sensory: List[str] = field(default_factory=list)  # raw phrases


class EventGraph:
    def __init__(self):
        self.events: Dict[str, Event] = {}

    def create_event(
        self,
        participants: Set[str],
        place: Optional[str],
        description: str,
        timestamp: Optional[float] = None,
        smells: Optional[List[str]] = None,
        sounds: Optional[List[str]] = None,
        raw_sensory: Optional[List[str]] = None,
    ) -> Event:
        eid = str(uuid.uuid4())
        ts = timestamp if timestamp is not None else time.time()

        ev = Event(
            event_id=eid,
            participants=set(participants or set()),
            place=place,
            description=description or "",
            timestamp=ts,
            smells=list(smells or []),
            sounds=list(sounds or []),
            raw_sensory=list(raw_sensory or []),
        )
        self.events[eid] = ev
        return ev