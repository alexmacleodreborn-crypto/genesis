import uuid
import time
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class Entity:
    entity_id: str
    name: str
    kind: str          # person | pet | object | agent
    confidence: float = 1.0
    origin: str = "declarative"
    created_at: float = field(default_factory=lambda: time.time())


class EntityPromotionBridge:
    def __init__(self):
        self.entities: Dict[str, Entity] = {}

    def find_entity(self, name: str) -> Optional[Entity]:
        for e in self.entities.values():
            if e.name.lower() == name.lower():
                return e
        return None

    def confirm_entity(
        self,
        name: str,
        kind: str,
        confidence: float = 1.0,
        origin: str = "declarative",
    ) -> Entity:
        existing = self.find_entity(name)
        if existing:
            if confidence > existing.confidence:
                existing.confidence = confidence
                existing.origin = origin
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