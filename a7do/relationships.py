from dataclasses import dataclass
from typing import List


@dataclass
class Relationship:
    subject_id: str
    object_id: str
    rel_type: str
    note: str


class RelationshipStore:
    def __init__(self):
        self.relations: List[Relationship] = []

    def add(self, subject_id, object_id, rel_type, note=""):
        self.relations.append(
            Relationship(subject_id, object_id, rel_type, note)
        )