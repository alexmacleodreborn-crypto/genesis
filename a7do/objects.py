import uuid
import time
from dataclasses import dataclass
from typing import Dict, Optional, List


@dataclass
class ObjectEntity:
    object_id: str
    label: str
    colour: Optional[str] = None
    owner_entity_id: Optional[str] = None
    attached_to: Optional[str] = None   # pet or person
    location: Optional[str] = None
    state: str = "present"              # present | gone | unknown
    created_at: float = time.time()
    last_seen: Optional[float] = None


class ObjectManager:
    def __init__(self):
        self.objects: Dict[str, ObjectEntity] = {}

    # ---------- Creation ----------
    def create(
        self,
        label: str,
        colour: Optional[str] = None,
        owner_entity_id: Optional[str] = None,
    ) -> ObjectEntity:
        obj = ObjectEntity(
            object_id=str(uuid.uuid4()),
            label=label,
            colour=colour,
            owner_entity_id=owner_entity_id,
            last_seen=time.time(),
        )
        self.objects[obj.object_id] = obj
        return obj

    # ---------- Lookup ----------
    def candidates(self, label: str) -> List[ObjectEntity]:
        return [
            o for o in self.objects.values()
            if o.label == label and o.state != "gone"
        ]

    def find_by_colour(self, label: str, colour: str) -> Optional[ObjectEntity]:
        for o in self.objects.values():
            if o.label == label and o.colour == colour and o.state != "gone":
                return o
        return None

    # ---------- State ----------
    def mark_gone(self, obj: ObjectEntity):
        obj.state = "gone"
        obj.location = None
        obj.last_seen = time.time()

    # ---------- Attach ----------
    def attach(self, obj: ObjectEntity, entity_id: str):
        obj.attached_to = entity_id
        obj.last_seen = time.time()