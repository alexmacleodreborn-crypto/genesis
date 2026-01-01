from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ScheduledEvent:
    builder: str                 # relationship | object | sensory | language | shapes | routine | user_input
    payload: Dict[str, Any]
    hour_cost: int = 1
    note: str = ""


@dataclass
class DaySchedule:
    day_index: int
    events: List[ScheduledEvent] = field(default_factory=list)
    started: bool = False
    awake_hours_used: int = 0
    asleep: bool = False
    completed: bool = False
    cursor: int = 0  # next event index to run

    def awake_hours_remaining(self) -> int:
        return max(0, 6 - self.awake_hours_used)

    def can_add_event(self) -> bool:
        return (not self.started) and (not self.completed)

    def add_event(self, ev: ScheduledEvent) -> None:
        if not self.can_add_event():
            raise RuntimeError("Cannot add events after schedule has started/completed.")
        self.events.append(ev)

    def has_minimum_to_start(self) -> bool:
        # per your rule: at least 1 event must exist before Start Schedule
        return len(self.events) >= 1

    def start(self) -> None:
        if not self.has_minimum_to_start():
            raise RuntimeError("Need at least 1 scheduled event before starting.")
        self.started = True
        self.asleep = False
        self.completed = False
        self.awake_hours_used = 0
        self.cursor = 0

    def mark_sleep(self) -> None:
        self.asleep = True

    def mark_complete(self) -> None:
        self.completed = True
        self.asleep = False

    def next_event(self) -> Optional[ScheduledEvent]:
        if not self.started or self.completed:
            return None
        if self.asleep:
            return None
        if self.cursor >= len(self.events):
            return None
        return self.events[self.cursor]

    def consume_next(self) -> Optional[ScheduledEvent]:
        ev = self.next_event()
        if ev is None:
            return None
        # consume hour cost
        if self.awake_hours_used + ev.hour_cost > 6:
            # force sleep boundary
            return None
        self.awake_hours_used += ev.hour_cost
        self.cursor += 1
        return ev

    def should_force_sleep(self) -> bool:
        # sleep when awake hours filled OR events exhausted
        if self.awake_hours_used >= 6:
            return True
        if self.cursor >= len(self.events):
            return True
        return False


class ScheduleEngine:
    """
    Controls Day→Wake→(≤6 awake events)→Sleep(6 hrs)→Advance Day.
    Time is external and authoritative.
    """
    def __init__(self):
        self.day = DaySchedule(day_index=0)

    def reset(self) -> None:
        self.day = DaySchedule(day_index=0)

    def new_day(self) -> None:
        self.day = DaySchedule(day_index=self.day.day_index + 1)

    def status(self) -> Dict[str, Any]:
        return {
            "day": self.day.day_index,
            "started": self.day.started,
            "awake_used": self.day.awake_hours_used,
            "awake_remaining": self.day.awake_hours_remaining(),
            "asleep": self.day.asleep,
            "completed": self.day.completed,
            "cursor": self.day.cursor,
            "events_count": len(self.day.events),
        }