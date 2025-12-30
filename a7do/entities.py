from collections import defaultdict
from datetime import datetime
import uuid


class Entity:
    def __init__(self, entity_type: str):
        self.id = f"{entity_type}_{uuid.uuid4().hex[:8]}"
        self.type = entity_type
        self.created_at = datetime.utcnow().isoformat()

        self.names = set()
        self.aliases = set()
        self.roles = set()

        self.attributes = defaultdict(float)
        self.relationships = defaultdict(set)

    def add_name(self, name: str):
        self.names.add(name)

    def add_alias(self, alias: str):
        self.aliases.add(alias)

    def add_role(self, role: str):
        self.roles.add(role)

    def add_attribute(self, key: str, weight: float = 0.5):
        self.attributes[key] += weight

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
    def __init__(self):
        self.entities = {}

    def create(self, entity_type: str) -> Entity:
        e = Entity(entity_type)
        self.entities[e.id] = e
        return e

    def find_by_name_or_alias(self, label: str):
        l = label.lower()
        for e in self.entities.values():
            if l in (n.lower() for n in e.names) or l in (a.lower() for a in e.aliases):
                return e
        return None

    def summary(self):
        return {eid: e.snapshot() for eid, e in self.entities.items()}