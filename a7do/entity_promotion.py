import uuid
import time
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class Entity:
    entity_id: str
    name: str
    kind: str                  # person | pet | object | agent
    owner_name: Optional[str] = None
    confidence: float = 1.0
    origin: str = "declarative"
    created_at: float = field(default_factory=lambda: time.time())


class EntityPromotionBridge:
    def __init__(self):
        self.entities: Dict[str, Entity] = {}

    def find_entity(self, name: str, owner_name: Optional[str] = None) -> Optional[Entity]:
        name = name.strip().lower()
        for ent in self.entities.values():
            if ent.name.lower() == name:
                return ent
        return None

    def confirm_entity(
        self,
        name: str,
        kind: str,
        owner_name: Optional[str] = None,
        relation: Optional[str] = None,
        confidence: float = 1.0,
        origin: str = "declarative",
    ) -> Entity:

        name = name.strip()

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
            owner_name=owner_name,
            confidence=confidence,
            origin=origin,
        )

        self.entities[ent.entity_id] = ent
        return ent