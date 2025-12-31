import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class PendingEntity:
    name: str
    count: int = 1
    confidence: float = 0.3


@dataclass
class Entity:
    entity_id: str
    name: str
    kind: str
    owner_name: Optional[str] = None
    aliases: Set[str] = field(default_factory=set)
    relations: Set[str] = field(default_factory=set)


class EntityPromotionBridge:
    def __init__(self):
        self.pending: Dict[str, PendingEntity] = {}
        self.entities: Dict[str, Entity] = {}

    def _norm(self, s: str) -> str:
        return (s or "").strip().lower()

    def candidates(self, name_or_alias: str) -> List[Entity]:
        key = self._norm(name_or_alias)
        out: List[Entity] = []
        for e in self.entities.values():
            if self._norm(e.name) == key:
                out.append(e)
                continue
            if any(self._norm(a) == key for a in e.aliases):
                out.append(e)
        return out

    def find_entity(self, name_or_alias: str, owner_name: Optional[str] = None) -> Optional[Entity]:
        cands = self.candidates(name_or_alias)
        if not cands:
            return None
        if owner_name:
            owned = [e for e in cands if self._norm(e.owner_name) == self._norm(owner_name)]
            if len(owned) == 1:
                return owned[0]
        if len(cands) == 1:
            return cands[0]
        return None  # ambiguous

    def observe(self, text: str, owner_name: Optional[str] = None):
        words = [w.strip(".,!?") for w in (text or "").split()]
        for w in words:
            if not w or not w.istitle():
                continue
            # if already exists, skip
            if self.candidates(w):
                continue
            key = self._norm(w)
            if key in self.pending:
                p = self.pending[key]
                p.count += 1
                p.confidence = min(1.0, p.confidence + 0.1)
            else:
                self.pending[key] = PendingEntity(name=w)

    def confirm_entity(
        self,
        name: str,
        kind: str,
        owner_name: Optional[str] = None,
        relation: Optional[str] = None,
    ) -> Entity:
        name = (name or "").strip().strip(" .!?")
        kind = (kind or "").strip().lower() or "entity"

        # Reuse entity if same name+kind+owner matches
        for e in self.candidates(name):
            if self._norm(e.kind) == self._norm(kind) and self._norm(e.owner_name) == self._norm(owner_name):
                e.aliases.add(name)
                if relation:
                    e.relations.add(relation)
                return e

        # Create new entity (allows two Xenas)
        entity_id = str(uuid.uuid4())
        e = Entity(
            entity_id=entity_id,
            name=name,
            kind=kind,
            owner_name=owner_name,
            aliases={name},
        )
        if relation:
            e.relations.add(relation)
        self.entities[entity_id] = e

        # clear pending
        key = self._norm(name)
        if key in self.pending:
            del self.pending[key]

        return e

    def add_alias(self, name: str, alias: str, owner_name: Optional[str] = None) -> bool:
        e = self.find_entity(name, owner_name=owner_name)
        if not e:
            cands = self.candidates(name)
            if not cands:
                return False
            e = cands[0]
        e.aliases.add((alias or "").strip())
        return True

    def describe(self, name: str, owner_name: Optional[str] = None) -> Optional[str]:
        cands = self.candidates(name)
        if not cands:
            return None

        # prefer owned if unique
        if owner_name:
            owned = [e for e in cands if self._norm(e.owner_name) == self._norm(owner_name)]
            if len(owned) == 1:
                e = owned[0]
                if "my dog" in {r.lower() for r in e.relations}:
                    return f"{e.name} is your dog."
                return f"{e.name} is a {e.kind}."

        if len(cands) == 1:
            e = cands[0]
            return f"{e.name} is a {e.kind}."

        return None  # ambiguous