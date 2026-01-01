from dataclasses import dataclass
from typing import List, Optional, Tuple

@dataclass
class SpatialState:
    """
    Body-in-world location.
    """
    room: str = "hall"
    pos_xy: Tuple[float, float] = (0.5, 0.5)   # normalized 0..1
    locomotion: str = "crawl"                  # crawl -> walk later

class Schedule:
    """
    Always-present schedule + spatial state.
    """
    def __init__(self):
        self.day = 0
        self.state = "waiting"  # waiting | awake | asleep | complete
        self.current_room = "hall"
        self.events: List[object] = []
        self.homeplot = None
        self.spatial = SpatialState()

    def load_day(self, day: int, homeplot, start_room: str, events: List[object]):
        self.day = day
        self.homeplot = homeplot
        self.current_room = start_room
        self.spatial.room = start_room
        self.events = list(events)
        self.state = "waiting"

    def wake(self):
        self.state = "awake"

    def next_event(self):
        if self.events:
            return self.events.pop(0)
        return None

    def sleep(self):
        self.state = "asleep"

    def complete(self):
        self.state = "complete"

    def status(self):
        return {
            "day": self.day,
            "state": self.state,
            "room": self.current_room,
            "events_remaining": len(self.events),
            "locomotion": self.spatial.locomotion,
            "pos_xy": self.spatial.pos_xy,
            "home_rooms": list(self.homeplot.rooms.keys()) if self.homeplot else [],
        }