import uuid
import time
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class Entity:
    entity_id: str
    name: str
    kind: str                 # person | pet | agent
    confidence: float = 1.0
    origin: str = "declarative"
    created_at: float = field(default_factory=lambda: time.time())


class EntityPromotionBridge:
    def __init__(self):
        self.entities: Dict[str, Entity] = {}

    def find_entity(self, name: str) -> Optional[Entity]:
        name = (name or "").strip().lower()
        if not name:
            return None
        for e in self.entities.values():
            if e.name.lower() == name:
                return e
        return None

    def confirm_entity(self, name: str, kind: str, confidence: float = 1.0, origin: str = "declarative") -> Entity:
        name = (name or "").strip()
        existing = self.find_entity(name)
        if existing:
            if confidence > existing.confidence:
                existing.confidence = confidence
                existing.origin = origin
            # allow kind upgrade (e.g. event-person -> person)
            if existing.kind != kind and confidence >= 0.8:
                existing.kind = kind
            return existing

        ent = Entity(
            entity_id=str(uuid.uuid4()),
            name=name,
            kind=kind,
            confidence=confidence,
            origin=origin,
        )
        self.entities[ent.entity_id] = ent
        return ent