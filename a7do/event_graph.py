import uuid
from dataclasses import dataclass, field
from typing import List, Set, Dict


@dataclass
class Event:
    event_id: str
    participants: Set[str]        # entity_ids
    place: str | None = None
    description: str | None = None
    timestamp: float | None = None


class EventGraph:
    """
    Connects entities through shared events.
    This is the neural binding layer.
    """

    def __init__(self):
        self.events: Dict[str, Event] = {}
        self.by_entity: Dict[str, Set[str]] = {}

    def create_event(
        self,
        participants: Set[str],
        place: str | None,
        description: str,
        timestamp: float,
    ) -> Event:
        eid = str(uuid.uuid4())
        ev = Event(
            event_id=eid,
            participants=set(participants),
            place=place,
            description=description,
            timestamp=timestamp,
        )
        self.events[eid] = ev

        for pid in participants:
            self.by_entity.setdefault(pid, set()).add(eid)

        return ev

    def events_for_entity(self, entity_id: str) -> List[Event]:
        eids = self.by_entity.get(entity_id, set())
        return [self.events[eid] for eid in eids]