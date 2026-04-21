from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass
class SpatialState:
    room: Optional[str] = None
    pos_xy: tuple[float, float] = (0.5, 0.5)
    locomotion: str = "still"


class Schedule:
    """Always-present day schedule with lightweight spatial tracking."""

    def __init__(self):
        self.day = 0
        self.place = None
        self.homeplot = None
        self.current_room: Optional[str] = None
        self.events: List[Any] = []
        self.state = "waiting"  # waiting | awake | asleep | complete
        self.spatial = SpatialState()

    def load_day(self, day, place=None, events=None, homeplot=None, start_room="hall"):
        self.day = day
        self.place = place
        self.homeplot = homeplot or place
        self.events = list(events or [])
        self.state = "waiting"
        self.current_room = start_room
        self.spatial.room = start_room
        self.spatial.pos_xy = (0.5, 0.5)
        self.spatial.locomotion = "still"

    def wake(self):
        self.state = "awake"

    def sleep(self):
        self.state = "asleep"

    def complete(self):
        self.state = "complete"

    def next_event(self):
        if self.events:
            return self.events.pop(0)
        return None

    def status(self):
        return {
            "day": self.day,
            "state": self.state,
            "room": self.current_room or "—",
            "events_remaining": len(self.events),
            "locomotion": self.spatial.locomotion,
            "pos_xy": self.spatial.pos_xy,
        }
