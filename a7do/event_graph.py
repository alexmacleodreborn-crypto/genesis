from dataclasses import dataclass
from typing import List, Set, Optional
import time


@dataclass
class Event:
    participants: Set[str]
    place: Optional[str]
    description: str
    timestamp: float
    smells: List[str]
    sounds: List[str]


class EventGraph:
    def __init__(self):
        self.events: List[Event] = []

    def create_event(
        self,
        participants,
        place,
        description,
        timestamp=None,
        smells=None,
        sounds=None,
    ):
        self.events.append(
            Event(
                participants=participants or set(),
                place=place,
                description=description,
                timestamp=timestamp or time.time(),
                smells=smells or [],
                sounds=sounds or [],
            )
        )