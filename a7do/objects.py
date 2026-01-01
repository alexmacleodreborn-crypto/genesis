import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# Very small starter lexicons (expand anytime)
DEFAULT_OBJECT_NOUNS = {
    "ball", "toy", "stick", "cube", "block", "square", "circle", "triangle",
    "box", "door", "chair", "table", "bottle"
}

DEFAULT_COLORS = {
    "red", "blue", "green", "yellow", "orange", "purple", "pink",
    "black", "white", "brown", "grey", "gray"
}

DEFAULT_SHAPES = {"round", "square", "triangle", "circular", "rectangular", "oval", "flat", "long"}


@dataclass
class ObjectRecord:
    object_id: str
    entity_id: str
    label: str                         # canonical noun e.g. "ball"
    attributes: Dict[str, str] = field(default_factory=dict)  # colour, shape, etc
    created_at: float = field(default_factory=lambda: time.time())
    last_seen: float = field(default_factory=lambda: time.time())
    confidence: float = 0.85           # stable by default (objects are concrete)


@dataclass
class PendingObject:
    pending_id: str
    label: str
    owner_entity_id: Optional[str]
    candidate_entity_id: Optional[str]   # the best existing candidate (if any)
    stage: str                           # "confirm_same" | "ask_which"
    prompt: str
    created_at: float = field(default_factory=lambda: time.time())
    hint: Dict[str, str] = field(default_factory=dict)  # e.g. {"colour":"red"}


class ColorLexicon:
    """
    C approach later wants raw + normalised for smells/sounds.
    For objects, we keep a growing known color set.
    """
    def __init__(self):
        self.known = set(DEFAULT_COLORS)

    def is_color(self, tok: str) -> bool:
        return (tok or "").lower() in self.known

    def learn(self, tok: str):
        if tok:
            self.known.add(tok.lower().strip())


class ShapeLexicon:
    def __init__(self):
        self.known = set(DEFAULT_SHAPES)

    def is_shape(self, tok: str) -> bool:
        return (tok or "").lower() in self.known

    def learn(self, tok: str):
        if tok:
            self.known.add(tok.lower().strip())


class ObjectManager:
    """
    Option B:
    - First time "ball" appears => create Ball₁ and treat as canonical referent.
    - Subsequent "ball" => reuse Ball₁ unless attributes indicate a mismatch.
    - If mismatch/ambiguity => ask: "Is that the red ball?" Yes/No
      - If No => ask "Which one is it?" and create/resolve from answer ("orange one")
    """
    def __init__(self):
        self.objects: Dict[str, ObjectRecord] = {}     # object_id -> record
        self.by_label: Dict[str, List[str]] = {}       # label -> [object_id,...]
        self.pending: Dict[str, PendingObject] = {}

        self.object_nouns = set(DEFAULT_OBJECT_NOUNS)
        self.colors = ColorLexicon()
        self.shapes = ShapeLexicon()

    # -----------------------------
    # Helpers
    # -----------------------------
    def _new_id(self) -> str:
        return str(uuid.uuid4())

    def _add_record(self, label: str, entity_id: str, attrs: Optional[Dict[str, str]] = None) -> ObjectRecord:
        oid = self._new_id()
        rec = ObjectRecord(object_id=oid, entity_id=entity_id, label=label.lower().strip())
        if attrs:
            rec.attributes.update({k: v for k, v in attrs.items() if v})
        self.objects[oid] = rec
        self.by_label.setdefault(rec.label, []).append(oid)
        return rec

    def find_records(self, label: str) -> List[ObjectRecord]:
        ids = self.by_label.get(label.lower().strip(), [])
        return [self.objects[i] for i in ids if i in self.objects]

    def set_attr(self, rec: ObjectRecord, key: str, value: str):
        rec.attributes[key] = value
        rec.last_seen = time.time()

    def describe(self, rec: ObjectRecord) -> str:
        c = rec.attributes.get("colour")
        s = rec.attributes.get("shape")
        parts = []
        if c:
            parts.append(c)
        if s:
            parts.append(s)
        parts.append(rec.label)
        return " ".join(parts)

    def _make_pending(self, label: str, owner_entity_id: Optional[str], candidate: Optional[ObjectRecord], stage: str, hint: Dict[str, str]) -> PendingObject:
        pid = self._new_id()

        if stage == "confirm_same" and candidate:
            # Ask about the best-known candidate (e.g. "red ball")
            prompt = f"Is that the **{self.describe(candidate)}**? (yes/no)"
        else:
            prompt = f"Which **{label}** is it? (e.g. 'the orange one', 'the red one')"

        p = PendingObject(
            pending_id=pid,
            label=label,
            owner_entity_id=owner_entity_id,
            candidate_entity_id=candidate.entity_id if candidate else None,
            stage=stage,
            prompt=prompt,
            hint=hint or {}
        )
        self.pending[pid] = p
        return p

    # -----------------------------
    # Public API
    # -----------------------------
    def is_object_noun(self, tok: str) -> bool:
        return (tok or "").lower() in self.object_nouns

    def learn_object_noun(self, tok: str):
        if tok:
            self.object_nouns.add(tok.lower().strip())

    def mention(
        self,
        label: str,
        *,
        entity_id_factory,              # callback to create an entity in bridge: (name, kind)-> entity_id
        owner_entity_id: Optional[str] = None,
        colour: Optional[str] = None,
        shape: Optional[str] = None,
    ) -> Tuple[Optional[str], Optional[PendingObject]]:
        """
        Returns:
          - (entity_id, None) if resolved
          - (None, PendingObject) if needs clarification
        """
        label = (label or "").lower().strip()
        if not label:
            return None, None

        # ensure colour/shape lexicons grow
        if colour:
            self.colors.learn(colour)
        if shape:
            self.shapes.learn(shape)

        records = self.find_records(label)

        # Option B: first mention => create canonical
        if not records:
            # create entity via bridge
            # We name the entity with a human-readable label: "ball"
            ent = entity_id_factory(label, "object")
            attrs = {}
            if colour and self.colors.is_color(colour):
                attrs["colour"] = colour.lower()
            if shape and self.shapes.is_shape(shape):
                attrs["shape"] = shape.lower()
            rec = self._add_record(label=label, entity_id=ent, attrs=attrs)
            return rec.entity_id, None

        # If there is exactly one known object of that label, treat as canonical
        if len(records) == 1:
            rec = records[0]

            # If colour mentioned and rec doesn't have it yet: learn/refine
            if colour and self.colors.is_color(colour):
                c = colour.lower()
                existing = rec.attributes.get("colour")
                if not existing:
                    self.set_attr(rec, "colour", c)
                    return rec.entity_id, None
                # conflict: mentions a different colour than known -> ambiguity
                if existing != c:
                    # Ask: is that the known one? (red ball)
                    p = self._make_pending(label, owner_entity_id, rec, stage="confirm_same", hint={"colour": c})
                    return None, p

            # shape refinement
            if shape and self.shapes.is_shape(shape):
                s = shape.lower()
                existing = rec.attributes.get("shape")
                if not existing:
                    self.set_attr(rec, "shape", s)
                elif existing != s:
                    p = self._make_pending(label, owner_entity_id, rec, stage="confirm_same", hint={"shape": s})
                    return None, p

            rec.last_seen = time.time()
            return rec.entity_id, None

        # Multiple known objects: try to resolve by attributes
        # If colour provided, match by colour
        if colour and self.colors.is_color(colour):
            c = colour.lower()
            matches = [r for r in records if r.attributes.get("colour") == c]
            if len(matches) == 1:
                matches[0].last_seen = time.time()
                return matches[0].entity_id, None

        # Ambiguous -> ask about the "best" candidate (most recent)
        best = sorted(records, key=lambda r: r.last_seen, reverse=True)[0]
        p = self._make_pending(label, owner_entity_id, best, stage="confirm_same", hint={"colour": colour.lower() if colour else ""})
        return None, p

    def resolve_pending_yes(
        self,
        pending_id: str,
    ) -> Optional[str]:
        p = self.pending.get(pending_id)
        if not p:
            return None
        # "Yes" => use the candidate
        self.pending.pop(pending_id, None)
        return p.candidate_entity_id

    def resolve_pending_no(self, pending_id: str) -> Optional[PendingObject]:
        p = self.pending.get(pending_id)
        if not p:
            return None
        # "No" => move to ask_which stage
        # Keep same pending id by overwriting stage/prompt
        p.stage = "ask_which"
        p.prompt = f"Okay. Which **{p.label}** is it? (e.g. 'the orange one')"
        return p

    def resolve_pending_description(
        self,
        pending_id: str,
        description: str,
        *,
        entity_id_factory,
    ) -> Optional[str]:
        """
        Description like: "the orange one" or "orange ball"
        We parse for colour/shape, create new object if needed, or match existing.
        """
        p = self.pending.get(pending_id)
        if not p:
            return None

        text = (description or "").lower()
        toks = [t.strip(",.!?;:()[]{}\"") for t in text.split() if t.strip(",.!?;:()[]{}\"")]

        colour = None
        shape = None
        for t in toks:
            if self.colors.is_color(t):
                colour = t
            if self.shapes.is_shape(t):
                shape = t

        # If we have existing objects of that label, try match by colour/shape
        records = self.find_records(p.label)
        if colour:
            matches = [r for r in records if r.attributes.get("colour") == colour]
            if len(matches) == 1:
                self.pending.pop(pending_id, None)
                matches[0].last_seen = time.time()
                return matches[0].entity_id

        # Otherwise create a new one (Ball₂)
        ent = entity_id_factory(p.label, "object")
        rec = self._add_record(
            label=p.label,
            entity_id=ent,
            attrs={"colour": colour or "", "shape": shape or ""},
        )
        self.pending.pop(pending_id, None)
        return rec.entity_id