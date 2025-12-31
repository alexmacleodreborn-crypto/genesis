import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


# -----------------------------
# Models
# -----------------------------

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
    aliases: Set[str] = field(default_factory=set)

    # Context anchors (lightweight)
    places: Set[str] = field(default_factory=set)
    relations: Set[str] = field(default_factory=set)
    activities: Set[str] = field(default_factory=set)


# -----------------------------
# Bridge
# -----------------------------

class EntityPromotionBridge:
    """
    Handles:
    - pending entity detection
    - confirmed entity creation
    - aliasing
    - contextual disambiguation (B-mode: ask only when low confidence)
    """

    def __init__(self):
        self.pending: Dict[str, PendingEntity] = {}
        self.entities: Dict[str, Entity] = {}

    # -----------------------------
    # Helpers
    # -----------------------------

    def _norm(self, s: str) -> str:
        return (s or "").strip().lower()

    def candidates(self, name_or_alias: str) -> List[Entity]:
        """Return all entities that match by name or alias."""
        key = self._norm(name_or_alias)
        out: List[Entity] = []
        for e in self.entities.values():
            if self._norm(e.name) == key:
                out.append(e)
                continue
            if any(self._norm(a) == key for a in e.aliases):
                out.append(e)
        return out

    def entity_label(self, e: Entity, current_owner: Optional[str]) -> str:
        """
        Human label for disambiguation:
        - 'your Xena' when owner matches the speaker/creator context
        - otherwise 'the other Xena' (or 'Xena (vet)' if anchors exist)
        """
        if current_owner and e.owner_name and self._norm(e.owner_name) == self._norm(current_owner):
            return f"your {e.name}"

        # If it has a dominant place anchor, use it
        if e.places:
            place = sorted(list(e.places))[0]
            return f"{e.name} ({place})"

        return f"the other {e.name}"

    def score_entity(self, e: Entity, context: Dict[str, Set[str]]) -> float:
        """
        Simple, explainable scoring:
        + matches to places/relations/activities anchors.
        """
        score = 0.0
        places = context.get("places", set())
        rels = context.get("relations", set())
        acts = context.get("activities", set())

        score += 1.2 * len(e.places.intersection(places))
        score += 1.0 * len(e.relations.intersection(rels))
        score += 0.8 * len(e.activities.intersection(acts))

        # slight preference if entity owner matches current owner context
        owner = context.get("owner", set())
        if owner and e.owner_name and self._norm(e.owner_name) in {self._norm(x) for x in owner}:
            score += 0.7

        return score

    def resolve(self, name: str, context: Dict[str, Set[str]]) -> Tuple[Optional[Entity], float, List[Tuple[Entity, float]]]:
        """
        Return (best_entity, confidence_gap, ranked_candidates).
        confidence_gap = best_score - second_best_score (0 if <2 candidates)
        """
        cands = self.candidates(name)
        if not cands:
            return None, 0.0, []

        ranked = [(e, self.score_entity(e, context)) for e in cands]
        ranked.sort(key=lambda x: x[1], reverse=True)

        best, best_s = ranked[0]
        second_s = ranked[1][1] if len(ranked) > 1 else 0.0
        gap = best_s - second_s
        return best, gap, ranked

    # -----------------------------
    # Observation
    # -----------------------------

    def observe(self, text: str, owner_name: Optional[str] = None):
        """
        Conservative pending detection:
        - only creates pending for Titlecase tokens that do NOT match any existing entity/alias
        """
        words = [w.strip(".,!?") for w in text.split()]
        tags = []
        events = []
        questions = []

        for w in words:
            if not w or not w.istitle():
                continue

            # If already known (by name or alias), don't create pending
            if self.candidates(w):
                continue

            key = self._norm(w)
            if key in self.pending:
                p = self.pending[key]
                p.count += 1
                p.confidence = min(1.0, p.confidence + 0.1)
            else:
                self.pending[key] = PendingEntity(
                    name=w,
                    owner_name=owner_name,
                    count=1,
                    confidence=0.3,
                )

        return tags, events, questions

    # -----------------------------
    # Promotion / confirmation
    # -----------------------------

    def confirm_entity(
        self,
        name: str,
        kind: str,
        owner_name: Optional[str] = None,
        is_self: bool = False,
        is_creator: bool = False,
        merge_with: Optional[str] = None,
        context: Optional[Dict[str, Set[str]]] = None,
    ) -> Entity:
        """
        Confirm entity:
        - If an existing candidate strongly matches context, reuse it (no duplication).
        - Otherwise create a new entity with anchors seeded from context.
        """
        context = context or {"places": set(), "relations": set(), "activities": set(), "owner": set()}
        if owner_name:
            context.setdefault("owner", set()).add(owner_name)

        # Try resolve to existing entity
        best, gap, ranked = self.resolve(name, context)

        # If we have a strong winner, reuse it (idempotent)
        # gap threshold can be tuned; 0.8 works well for early anchors
        if best is not None and gap >= 0.8:
            # update kind if unknown or empty
            if not best.kind:
                best.kind = kind
            # attach anchors
            best.places |= context.get("places", set())
            best.relations |= context.get("relations", set())
            best.activities |= context.get("activities", set())
            best.aliases.add(name)
            return best

        # Otherwise: create new entity
        key = self._norm(name)

        # Merge pending if requested
        aliases: Set[str] = {name}
        if merge_with:
            mk = self._norm(merge_with)
            if mk in self.pending:
                aliases.add(self.pending[mk].name)
                del self.pending[mk]

        # Pull from pending if exists
        if key in self.pending:
            del self.pending[key]

        entity_id = str(uuid.uuid4())
        ent_owner = owner_name if (kind == "pet" or is_self) else None

        e = Entity(
            entity_id=entity_id,
            name=name,
            kind=kind,
            owner_name=ent_owner,
            aliases=aliases,
        )
        e.places |= context.get("places", set())
        e.relations |= context.get("relations", set())
        e.activities |= context.get("activities", set())

        self.entities[entity_id] = e
        return e

    # -----------------------------
    # Alias management
    # -----------------------------

    def add_alias(self, name: str, alias: str, context: Optional[Dict[str, Set[str]]] = None):
        """
        Attach alias to the best-resolved entity for `name`.
        """
        context = context or {"places": set(), "relations": set(), "activities": set(), "owner": set()}
        best, _, _ = self.resolve(name, context)
        if not best:
            return False
        best.aliases.add(alias)
        return True

    # -----------------------------
    # Describe
    # -----------------------------

    def describe(self, name: str, context: Optional[Dict[str, Set[str]]] = None) -> Optional[str]:
        context = context or {"places": set(), "relations": set(), "activities": set(), "owner": set()}
        best, gap, ranked = self.resolve(name, context)
        if not best:
            return None

        # If ambiguous (low gap), let the mind ask the question (B-mode)
        if len(ranked) > 1 and gap < 0.8:
            return None

        kind = best.kind or "entity"
        return f"{best.name} is a {kind}."