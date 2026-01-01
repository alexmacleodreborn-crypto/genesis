import uuid
import time
from dataclasses import dataclass
from typing import Dict, Optional, List


@dataclass
class ObjectEntity:
    object_id: str
    label: str                     # ball, swing, toy...
    colour: Optional[str] = None
    owner_entity_id: Optional[str] = None
    attached_to: Optional[str] = None      # entity_id
    state: str = "present"                 # present | gone | unknown
    location: Optional[str] = None         # last known place
    created_at: float = 0.0
    last_seen: float = 0.0


class ObjectManager:
    def __init__(self):
        self.objects: Dict[str, ObjectEntity] = {}

    def create(self, label: str, colour: Optional[str] = None, owner_entity_id: Optional[str] = None) -> ObjectEntity:
        now = time.time()
        obj = ObjectEntity(
            object_id=str(uuid.uuid4()),
            label=label,
            colour=colour,
            owner_entity_id=owner_entity_id,
            attached_to=None,
            state="present",
            location=None,
            created_at=now,
            last_seen=now,
        )
        self.objects[obj.object_id] = obj
        return obj

    def candidates(self, label: str, include_gone: bool = False) -> List[ObjectEntity]:
        out = []
        for o in self.objects.values():
            if o.label != label:
                continue
            if (not include_gone) and o.state == "gone":
                continue
            out.append(o)
        return out

    def find(self, label: str, colour: Optional[str] = None, include_gone: bool = False) -> Optional[ObjectEntity]:
        for o in self.objects.values():
            if o.label != label:
                continue
            if (not include_gone) and o.state == "gone":
                continue
            if colour is None or o.colour == colour:
                return o
        return None

    def list_owned(self, owner_entity_id: str, label: Optional[str] = None, include_gone: bool = False) -> List[ObjectEntity]:
        out = []
        for o in self.objects.values():
            if o.owner_entity_id != owner_entity_id:
                continue
            if label and o.label != label:
                continue
            if (not include_gone) and o.state == "gone":
                continue
            out.append(o)
        return out

    def list_attached_to(self, entity_id: str, include_gone: bool = False) -> List[ObjectEntity]:
        out = []
        for o in self.objects.values():
            if o.attached_to != entity_id:
                continue
            if (not include_gone) and o.state == "gone":
                continue
            out.append(o)
        return out

    def attach(self, obj: ObjectEntity, entity_id: str):
        obj.attached_to = entity_id
        obj.last_seen = time.time()

    def set_location(self, obj: ObjectEntity, place: Optional[str]):
        if place:
            obj.location = place
        obj.last_seen = time.time()

    def mark_gone(self, obj: ObjectEntity):
        obj.state = "gone"
        obj.last_seen = time.time()