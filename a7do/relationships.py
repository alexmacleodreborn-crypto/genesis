import time
import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Relationship:
    rel_id: str
    subject_id: str
    object_id: str
    rel_type: str           # e.g. "pet", "friend", "family", "doctor", "dentist", "coworker"
    created_at: float
    note: Optional[str] = None


class RelationshipStore:
    """
    First-class relationship graph (entity_id -> entity_id).
    Supports multiple relationships and querying by subject/object/type.
    """

    def __init__(self):
        self.rels: Dict[str, Relationship] = {}

    def add(self, subject_id: str, object_id: str, rel_type: str, note: Optional[str] = None) -> Relationship:
        # de-dup: same (subject, object, type) should not multiply
        for r in self.rels.values():
            if r.subject_id == subject_id and r.object_id == object_id and r.rel_type == rel_type:
                return r

        rid = str(uuid.uuid4())
        rel = Relationship(
            rel_id=rid,
            subject_id=subject_id,
            object_id=object_id,
            rel_type=rel_type,
            created_at=time.time(),
            note=note,
        )
        self.rels[rid] = rel
        return rel

    def all(self) -> List[Relationship]:
        return list(self.rels.values())

    def by_subject(self, subject_id: str) -> List[Relationship]:
        return [r for r in self.rels.values() if r.subject_id == subject_id]

    def by_object(self, object_id: str) -> List[Relationship]:
        return [r for r in self.rels.values() if r.object_id == object_id]

    def find(self, subject_id: str, rel_type: str) -> List[Relationship]:
        return [r for r in self.rels.values() if r.subject_id == subject_id and r.rel_type == rel_type]