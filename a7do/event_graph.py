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
        participants: Set[str],
        place: Optional[str],
        description: str,
        timestamp: Optional[float] = None,
        smells: Optional[List[str]] = None,
        sounds: Optional[List[str]] = None,
    ):
        self.events.append(
            Event(
                participants=participants or set(),
                place=place,
                description=description,
                timestamp=timestamp if timestamp is not None else time.time(),
                smells=smells or [],
                sounds=sounds or [],
            )
        )