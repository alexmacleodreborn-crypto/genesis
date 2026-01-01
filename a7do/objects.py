import uuid
import time
from dataclasses import dataclass
from typing import Dict, Optional, List


@dataclass
class ObjectEntity:
    object_id: str
    label: str
    colour: Optional[str]
    owner_entity_id: Optional[str]
    attached_to: Optional[str]
    state: str                # present | gone | unknown
    created_at: float
    last_seen: float


class ObjectManager:
    def __init__(self):
        self.objects: Dict[str, ObjectEntity] = {}

    def create(self, label, colour=None, owner_entity_id=None):
        obj = ObjectEntity(
            object_id=str(uuid.uuid4()),
            label=label,
            colour=colour,
            owner_entity_id=owner_entity_id,
            attached_to=None,
            state="present",
            created_at=time.time(),
            last_seen=time.time(),
        )
        self.objects[obj.object_id] = obj
        return obj

    def candidates(self, label) -> List[ObjectEntity]:
        return [o for o in self.objects.values()
                if o.label == label and o.state != "gone"]

    def find(self, label, colour=None):
        for o in self.objects.values():
            if o.label == label and o.state != "gone":
                if colour is None or o.colour == colour:
                    return o
        return None

    def mark_gone(self, obj: ObjectEntity):
        obj.state = "gone"
        obj.last_seen = time.time()

    def attach(self, obj: ObjectEntity, entity_id: str):
        obj.attached_to = entity_id
        obj.last_seen = time.time()