import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# -------------------------------------------------
# Starter lexicons (expand over time)
# -------------------------------------------------
DEFAULT_OBJECT_NOUNS = {
    "ball", "toy", "stick", "cube", "block", "box",
    "chair", "table", "door", "bottle"
}

DEFAULT_COLORS = {
    "red", "blue", "green", "yellow", "orange", "purple",
    "pink", "black", "white", "brown", "grey", "gray"
}

DEFAULT_SHAPES = {
    "round", "square", "triangle", "circular",
    "rectangular", "oval", "flat", "long"
}


# -------------------------------------------------
# Data models
# -------------------------------------------------
@dataclass
class ObjectRecord:
    object_id: str
    entity_id: str
    label: str                         # canonical noun: "ball"
    attributes: Dict[str, str] = field(default_factory=dict)
    created_at: float = field(default_factory=lambda: time.time())
    last_seen: float = field(default_factory=lambda: time.time())
    confidence: float = 0.85           # objects are concrete by default


@dataclass
class PendingObject:
    pending_id: str
    label: str
    owner_entity_id: Optional[str]
    candidate_entity_id: Optional[str]
    stage: str                         # "confirm_same" | "ask_which"
    prompt: str
    hint: Dict[str, str] = field(default_factory=dict)
    created_at: float = field(default_factory=lambda: time.time())


# -------------------------------------------------
# Attribute lexicons
# -------------------------------------------------
class ColorLexicon:
    def __init__(self):
        self.known = set(DEFAULT_COLORS)

    def is_color(self, token: str) -> bool:
        return token.lower() in self.known

    def learn(self, token: str):
        self.known.add(token.lower())


class ShapeLexicon:
    def __init__(self):
        self.known = set(DEFAULT_SHAPES)

    def is_shape(self, token: str) -> bool:
        return token.lower() in self.known

    def learn(self, token: str):
        self.known.add(token.lower())


# -------------------------------------------------
# Object Manager (Option B)
# -------------------------------------------------
class ObjectManager:
    """
    OPTION B (locked):

    - First mention of "ball" => create canonical Ball₁
    - Later mentions reuse Ball₁
    - Attribute conflicts trigger clarification
    - New objects created only after user confirms difference
    """

    def __init__(self):
        self.objects: Dict[str, ObjectRecord] = {}          # object_id → record
        self.by_label: Dict[str, List[str]] = {}            # label → [object_id]
        self.pending: Dict[str, PendingObject] = {}

        self.object_nouns = set(DEFAULT_OBJECT_NOUNS)
        self.colors = ColorLexicon()
        self.shapes = ShapeLexicon()

    # -------------------------------------------------
    # Utilities
    # -------------------------------------------------
    def _new_id(self) -> str:
        return str(uuid.uuid4())

    def _add_record(
        self,
        label: str,
        entity_id: str,
        attrs: Optional[Dict[str, str]] = None
    ) -> ObjectRecord:
        oid = self._new_id()
        rec = ObjectRecord(
            object_id=oid,
            entity_id=entity_id,
            label=label.lower().strip(),
        )
        if attrs:
            for k, v in attrs.items():
                if v:
                    rec.attributes[k] = v
        self.objects[oid] = rec
        self.by_label.setdefault(rec.label, []).append(oid)
        return rec

    def _records_for(self, label: str) -> List[ObjectRecord]:
        return [
            self.objects[oid]
            for oid in self.by_label.get(label.lower().strip(), [])
            if oid in self.objects
        ]

    def _describe(self, rec: ObjectRecord) -> str:
        parts = []
        if "colour" in rec.attributes:
            parts.append(rec.attributes["colour"])
        if "shape" in rec.attributes:
            parts.append(rec.attributes["shape"])
        parts.append(rec.label)
        return " ".join(parts)

    def _make_pending(
        self,
        label: str,
        owner_entity_id: Optional[str],
        candidate: Optional[ObjectRecord],
        stage: str,
        hint: Dict[str, str]
    ) -> PendingObject:
        pid = self._new_id()
        if stage == "confirm_same" and candidate:
            prompt = f"Is that the **{self._describe(candidate)}**? (yes/no)"
        else:
            prompt = f"Which **{label}** is it? (e.g. 'the orange one')"

        p = PendingObject(
            pending_id=pid,
            label=label,
            owner_entity_id=owner_entity_id,
            candidate_entity_id=candidate.entity_id if candidate else None,
            stage=stage,
            prompt=prompt,
            hint=hint,
        )
        self.pending[pid] = p
        return p

    # -------------------------------------------------
    # Public API
    # -------------------------------------------------
    def is_object_noun(self, token: str) -> bool:
        return token.lower() in self.object_nouns

    def learn_object_noun(self, token: str):
        self.object_nouns.add(token.lower())

    def mention(
        self,
        label: str,
        *,
        entity_id_factory,
        owner_entity_id: Optional[str] = None,
        colour: Optional[str] = None,
        shape: Optional[str] = None,
    ) -> Tuple[Optional[str], Optional[PendingObject]]:
        """
        Returns:
          - (entity_id, None) if resolved
          - (None, PendingObject) if clarification needed
        """

        label = label.lower().strip()
        records = self._records_for(label)

        # Learn new attribute tokens
        if colour:
            self.colors.learn(colour)
        if shape:
            self.shapes.learn(shape)

        # -------------------------
        # First mention → canonical
        # -------------------------
        if not records:
            ent_id = entity_id_factory(label, "object")
            attrs = {}
            if colour and self.colors.is_color(colour):
                attrs["colour"] = colour.lower()
            if shape and self.shapes.is_shape(shape):
                attrs["shape"] = shape.lower()
            rec = self._add_record(label, ent_id, attrs)
            return rec.entity_id, None

        # -------------------------
        # Single known object
        # -------------------------
        if len(records) == 1:
            rec = records[0]

            # Colour refinement
            if colour and self.colors.is_color(colour):
                existing = rec.attributes.get("colour")
                if not existing:
                    rec.attributes["colour"] = colour.lower()
                    rec.last_seen = time.time()
                    return rec.entity_id, None
                if existing != colour.lower():
                    return None, self._make_pending(
                        label, owner_entity_id, rec,
                        stage="confirm_same",
                        hint={"colour": colour.lower()},
                    )

            # Shape refinement
            if shape and self.shapes.is_shape(shape):
                existing = rec.attributes.get("shape")
                if not existing:
                    rec.attributes["shape"] = shape.lower()
                    rec.last_seen = time.time()
                    return rec.entity_id, None
                if existing != shape.lower():
                    return None, self._make_pending(
                        label, owner_entity_id, rec,
                        stage="confirm_same",
                        hint={"shape": shape.lower()},
                    )

            rec.last_seen = time.time()
            return rec.entity_id, None

        # -------------------------
        # Multiple known objects
        # -------------------------
        if colour and self.colors.is_color(colour):
            matches = [
                r for r in records
                if r.attributes.get("colour") == colour.lower()
            ]
            if len(matches) == 1:
                matches[0].last_seen = time.time()
                return matches[0].entity_id, None

        # Ambiguous → ask about most recent
        best = sorted(records, key=lambda r: r.last_seen, reverse=True)[0]
        return None, self._make_pending(
            label, owner_entity_id, best,
            stage="confirm_same",
            hint={"colour": colour.lower() if colour else ""},
        )

    # -------------------------------------------------
    # Resolution
    # -------------------------------------------------
    def resolve_pending_yes(self, pending_id: str) -> Optional[str]:
        p = self.pending.pop(pending_id, None)
        return p.candidate_entity_id if p else None

    def resolve_pending_no(self, pending_id: str) -> Optional[PendingObject]:
        p = self.pending.get(pending_id)
        if not p:
            return None
        p.stage = "ask_which"
        p.prompt = f"Which **{p.label}** is it? (e.g. 'the orange one')"
        return p

    def resolve_pending_description(
        self,
        pending_id: str,
        description: str,
        *,
        entity_id_factory,
    ) -> Optional[str]:
        p = self.pending.pop(pending_id, None)
        if not p:
            return None

        tokens = [
            t.strip(",.!?;:")
            for t in description.lower().split()
        ]

        colour = next((t for t in tokens if self.colors.is_color(t)), None)
        shape = next((t for t in tokens if self.shapes.is_shape(t)), None)

        # Try match existing
        records = self._records_for(p.label)
        if colour:
            matches = [r for r in records if r.attributes.get("colour") == colour]
            if len(matches) == 1:
                matches[0].last_seen = time.time()
                return matches[0].entity_id

        # Create new object
        ent_id = entity_id_factory(p.label, "object")
        attrs = {}
        if colour:
            attrs["colour"] = colour
        if shape:
            attrs["shape"] = shape
        rec = self._add_record(p.label, ent_id, attrs)
        return rec.entity_id