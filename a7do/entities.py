from collections import defaultdict
from datetime import datetime
import uuid


class Entity:
    """
    A stable cognitive entity: person, animal, object, place, concept.
    """

    def __init__(self, entity_type: str):
        self.id = f"{entity_type}_{uuid.uuid4().hex[:8]}"
        self.type = entity_type

        self.created_at = datetime.utcnow().isoformat()

        self.names = set()
        self.aliases = set()

        self.attributes = defaultdict(float)   # attribute -> confidence
        self.roles = set()

        self.relationships = defaultdict(set)  # relation -> entity_ids

    def add_name(self, name: str):
        self.names.add(name)

    def add_alias(self, alias: str):
        self.aliases.add(alias)

    def add_attribute(self, key: str, weight: float = 0.5):
        self.attributes[key] += weight

    def add_role(self, role: str):
        self.roles.add(role)

    def link(self, relation: str, other_entity_id: str):
        self.relationships[relation].add(other_entity_id)

    def snapshot(self):
        return {
            "id": self.id,
            "type": self.type,
            "names": list(self.names),
            "aliases": list(self.aliases),
            "roles": list(self.roles),
            "attributes": dict(self.attributes),
            "relationships": {k: list(v) for k, v in self.relationships.items()},
        }


class EntityGraph:
    """
    Stores and resolves entities.
    """

    def __init__(self):
        self.entities = {}

    # --------------------------------------------------

    def create(self, entity_type: str) -> Entity:
        e = Entity(entity_type)
        self.entities[e.id] = e
        return e

    def get(self, entity_id: str):
        return self.entities.get(entity_id)

    # --------------------------------------------------
    # Resolution helpers
    # --------------------------------------------------

    def find_by_name(self, name: str):
        name = name.lower()
        for e in self.entities.values():
            if name in (n.lower() for n in e.names):
                return e
        return None

    # --------------------------------------------------

    def summary(self):
        return {eid: e.snapshot() for eid, e in self.entities.items()}