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
    relations: Set[str] = field(default_factory=set)  # e.g. {"my dog"}
    places: Set[str] = field(default_factory=set)
    activities: Set[str] = field(default_factory=set)


class EntityPromotionBridge:
    """
    Entity layer:
    - Pending name detection
    - Confirm/persist entities
    - Multiple entities can share the same display name (e.g. two 'Xena')
    - Owner-aware describe and lookup
    """

    def __init__(self):
        self.pending: Dict[str, PendingEntity] = {}
        self.entities: Dict[str, Entity] = {}

    def _norm(self, s: str) -> str:
        return (s or "").strip().lower()

    # --------- Pending detection (conservative) ----------
    def observe(self, text: str, owner_name: Optional[str] = None):
        words = [w.strip(".,!?") for w in (text or "").split()]
        for w in words:
            if not w or not w.istitle():
                continue
            # If already exists as an entity/alias, do not create pending
            if self.find_entity(w, owner_name=owner_name) is not None:
                continue

            key = self._norm(w)
            if key in self.pending:
                p = self.pending[key]
                p.count += 1
                p.confidence = min(1.0, p.confidence + 0.1)
            else:
                self.pending[key] = PendingEntity(name=w)

    # --------- Entity lookup ----------
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
            ok = [e for e in cands if self._norm(e.owner_name) == self._norm(owner_name)]
            if len(ok) == 1:
                return ok[0]
        # If only one candidate, return it
        if len(cands) == 1:
            return cands[0]
        # ambiguous
        return None

    # --------- Confirm / create (idempotent per owner+kind) ----------
    def confirm_entity(
        self,
        name: str,
        kind: str,
        owner_name: Optional[str] = None,
        relation: Optional[str] = None,
        places: Optional[Set[str]] = None,
        activities: Optional[Set[str]] = None,
    ) -> Entity:
        name = (name or "").strip().strip(" .!?")
        kind = (kind or "").strip().lower() or "entity"

        # If a matching entity already exists for this owner+kind, reuse it
        for e in self.candidates(name):
            if self._norm(e.kind) == self._norm(kind) and self._norm(e.owner_name) == self._norm(owner_name):
                e.aliases.add(name)
                if relation:
                    e.relations.add(relation)
                if places:
                    e.places |= set(places)
                if activities:
                    e.activities |= set(activities)
                return e

        # Create a new entity (allows multiple same-name entities)
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
        if places:
            e.places |= set(places)
        if activities:
            e.activities |= set(activities)

        self.entities[entity_id] = e

        # Remove pending if it exists
        key = self._norm(name)
        if key in self.pending:
            del self.pending[key]

        return e

    # --------- Alias ----------
    def add_alias(self, name: str, alias: str, owner_name: Optional[str] = None) -> bool:
        e = self.find_entity(name, owner_name=owner_name)
        if not e:
            # if ambiguous, try first candidate
            cands = self.candidates(name)
            if not cands:
                return False
            e = cands[0]
        e.aliases.add((alias or "").strip())
        return True

    # --------- Describe (owner-aware) ----------
    def describe(self, name: str, owner_name: Optional[str] = None) -> Optional[str]:
        cands = self.candidates(name)
        if not cands:
            return None

        # Prefer owned entity if unique
        if owner_name:
            owned = [e for e in cands if self._norm(e.owner_name) == self._norm(owner_name)]
            if len(owned) == 1:
                e = owned[0]
                if "my dog" in {r.lower() for r in e.relations}:
                    return f"{e.name} is your dog."
                return f"{e.name} is a {e.kind}."

        # If only one candidate
        if len(cands) == 1:
            e = cands[0]
            return f"{e.name} is a {e.kind}."

        # ambiguous
        return None