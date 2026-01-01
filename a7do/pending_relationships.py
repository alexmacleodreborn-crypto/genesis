import time
import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional

# -----------------------------
# Decay configuration
# -----------------------------
DECAY_RATE = 0.02          # confidence lost per minute
MIN_CONFIDENCE = 0.15     # below this → dormant
REINFORCE_BOOST = 0.10    # added when new evidence appears


@dataclass
class PendingRelationship:
    pending_id: str
    subject_id: str
    object_id: str
    rel_type: str
    confidence: float
    evidence: dict
    created_at: float
    last_updated: float
    status: str = "pending"   # pending | confirmed | rejected | dormant
    note: Optional[str] = None


class PendingRelationshipStore:
    """
    Stores inferred (hypothesised) relationships that decay over time
    unless reinforced by new evidence.
    """

    def __init__(self):
        self.pending: Dict[str, PendingRelationship] = {}

    # -------------------------------------------------
    # Create or reinforce
    # -------------------------------------------------
    def add(
        self,
        subject_id: str,
        object_id: str,
        rel_type: str,
        confidence: float,
        evidence: dict,
        note: Optional[str] = None,
    ) -> PendingRelationship:

        now = time.time()

        # Reinforce existing hypothesis
        for p in self.pending.values():
            if (
                p.status == "pending"
                and p.subject_id == subject_id
                and p.object_id == object_id
                and p.rel_type == rel_type
            ):
                p.confidence = min(1.0, p.confidence + REINFORCE_BOOST)
                p.last_updated = now
                p.evidence.update(evidence or {})
                return p

        pid = str(uuid.uuid4())
        pr = PendingRelationship(
            pending_id=pid,
            subject_id=subject_id,
            object_id=object_id,
            rel_type=rel_type,
            confidence=float(confidence),
            evidence=evidence or {},
            created_at=now,
            last_updated=now,
            note=note,
        )
        self.pending[pid] = pr
        return pr

    # -------------------------------------------------
    # Decay logic
    # -------------------------------------------------
    def _apply_decay(self, p: PendingRelationship):
        if p.status != "pending":
            return

        now = time.time()
        minutes = (now - p.last_updated) / 60.0
        if minutes <= 0:
            return

        p.confidence -= minutes * DECAY_RATE
        p.last_updated = now

        if p.confidence < MIN_CONFIDENCE:
            p.status = "dormant"

    # -------------------------------------------------
    # Accessors
    # -------------------------------------------------
    def list_pending(self) -> List[PendingRelationship]:
        out = []
        for p in self.pending.values():
            self._apply_decay(p)
            if p.status == "pending":
                out.append(p)
        return out

    def list_dormant(self) -> List[PendingRelationship]:
        out = []
        for p in self.pending.values():
            self._apply_decay(p)
            if p.status == "dormant":
                out.append(p)
        return out

    # -------------------------------------------------
    # Resolution
    # -------------------------------------------------
    def reject(self, pending_id: str):
        p = self.pending.get(pending_id)
        if p:
            p.status = "rejected"

    def confirm(self, pending_id: str):
        p = self.pending.get(pending_id)
        if p:
            p.status = "confirmed"