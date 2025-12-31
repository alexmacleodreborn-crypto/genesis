import time
import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class PendingRelationship:
    pending_id: str
    subject_id: str
    object_id: str
    rel_type: str            # "pet" (for now)
    confidence: float
    evidence: dict
    created_at: float
    status: str = "pending"  # pending | confirmed | rejected
    note: Optional[str] = None


class PendingRelationshipStore:
    """
    Stores hypotheses that require user confirmation.
    """

    def __init__(self):
        self.pending: Dict[str, PendingRelationship] = {}

    def add(
        self,
        subject_id: str,
        object_id: str,
        rel_type: str,
        confidence: float,
        evidence: dict,
        note: Optional[str] = None,
    ) -> PendingRelationship:
        # de-dup same subject/object/type if already pending
        for p in self.pending.values():
            if (
                p.status == "pending"
                and p.subject_id == subject_id
                and p.object_id == object_id
                and p.rel_type == rel_type
            ):
                return p

        pid = str(uuid.uuid4())
        pr = PendingRelationship(
            pending_id=pid,
            subject_id=subject_id,
            object_id=object_id,
            rel_type=rel_type,
            confidence=float(confidence),
            evidence=evidence or {},
            created_at=time.time(),
            note=note,
        )
        self.pending[pid] = pr
        return pr

    def get(self, pending_id: str) -> Optional[PendingRelationship]:
        return self.pending.get(pending_id)

    def list_pending(self) -> List[PendingRelationship]:
        return [p for p in self.pending.values() if p.status == "pending"]

    def reject(self, pending_id: str):
        p = self.pending.get(pending_id)
        if p:
            p.status = "rejected"

    def confirm(self, pending_id: str):
        p = self.pending.get(pending_id)
        if p:
            p.status = "confirmed"