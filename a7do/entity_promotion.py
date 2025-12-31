import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# -------------------------------------------------
# Data models
# -------------------------------------------------

@dataclass
class PendingEntity:
    name: str
    owner_name: Optional[str] = None
    kind_guess: str = "unknown"
    count: int = 1
    confidence: float = 0.3
    contexts: List[str] = field(default_factory=list)
    relation_hint: Optional[str] = None


@dataclass
class Entity:
    entity_id: str
    name: str
    kind: str
    owner_name: Optional[str] = None
    aliases: List[str] = field(default_factory=list)


# -------------------------------------------------
# Promotion bridge
# -------------------------------------------------

class EntityPromotionBridge:
    """
    Responsible for:
    - tracking pending entities
    - promoting confirmed entities
    - managing aliases
    """

    def __init__(self):
        self.pending: Dict[str, PendingEntity] = {}
        self.entities: Dict[str, Entity] = {}

    # ---------------------------------------------
    # Observation (called from mind)
    # ---------------------------------------------
    def observe(self, text: str, owner_name: Optional[str] = None):
        """
        Detect candidate entities from text.
        VERY conservative by design.
        """
        words = [w.strip(".,!?") for w in text.split()]
        tags = []
        events = []
        questions = []

        for w in words:
            if w.istitle():
                key = w.lower()
                if key not in self.pending and not self.find_entity_id(w):
                    self.pending[key] = PendingEntity(
                        name=w,
                        owner_name=owner_name,
                        count=1,
                        confidence=0.3,
                    )
                elif key in self.pending:
                    p = self.pending[key]
                    p.count += 1
                    p.confidence = min(1.0, p.confidence + 0.1)

        return tags, events, questions

    # ---------------------------------------------
    # Promotion
    # ---------------------------------------------
    def confirm_entity(
        self,
        name: str,
        kind: str,
        is_self: bool = False,
        is_creator: bool = False,
        merge_with: Optional[str] = None,
    ):
        key = name.lower()

        # Merge first if requested
        aliases = [name]
        if merge_with:
            merge_key = merge_with.lower()
            if merge_key in self.pending:
                aliases.append(self.pending[merge_key].name)
                del self.pending[merge_key]

        # Pull from pending if exists
        if key in self.pending:
            pending = self.pending[key]
            aliases.extend(pending.contexts)
            del self.pending[key]

        # Create entity
        entity_id = str(uuid.uuid4())
        entity = Entity(
            entity_id=entity_id,
            name=name,
            kind=kind,
            owner_name=name if is_self else None,
            aliases=list(set(aliases)),
        )

        self.entities[entity_id] = entity
        return entity

    # ---------------------------------------------
    # Alias management
    # ---------------------------------------------
    def add_alias(self, name: str, alias: str):
        eid = self.find_entity_id(name)
        if eid:
            e = self.entities[eid]
            if alias not in e.aliases:
                e.aliases.append(alias)

    # ---------------------------------------------
    # Lookup
    # ---------------------------------------------
    def find_entity_id(self, name: str) -> Optional[str]:
        lname = name.lower()
        for eid, e in self.entities.items():
            if e.name.lower() == lname or lname in (a.lower() for a in e.aliases):
                return eid
        return None

    def describe(self, name: str) -> Optional[str]:
        eid = self.find_entity_id(name)
        if not eid:
            return None
        e = self.entities[eid]
        return f"{e.name} is a {e.kind}."