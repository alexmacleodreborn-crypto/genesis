import time
import math
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class ReflectionVersion:
    version_id: str
    reflection_key: Tuple[str, str]  # (entity_id, pattern)
    score: float
    band: str
    created_at: float
    last_seen: float
    support_events: List[str]
    active: bool = True


class ReflectionStore:
    def __init__(self):
        self.versions: Dict[Tuple[str, str], List[ReflectionVersion]] = {}
        self._counter = 0

    def _new_version_id(self):
        self._counter += 1
        return f"RV_{self._counter:05d}"

    def confidence_band(self, score: float) -> str:
        if score < 0.3:
            return "very_low"
        if score < 0.6:
            return "low"
        if score < 1.0:
            return "medium"
        return "high"

    def score(self, freq, consistency, breadth, recency):
        return freq * consistency * breadth * recency

    def create_version(
        self,
        entity_id: str,
        pattern: str,
        freq: int,
        consistency: float,
        breadth: float,
        last_seen_ts: float,
        support_events: List[str],
        tau: float = 3600.0
    ):
        F = math.log(1 + freq)
        C = consistency
        B = breadth
        R = math.exp(-(time.time() - last_seen_ts) / tau)

        score = self.score(F, C, B, R)
        band = self.confidence_band(score)

        key = (entity_id, pattern)
        version = ReflectionVersion(
            version_id=self._new_version_id(),
            reflection_key=key,
            score=score,
            band=band,
            created_at=time.time(),
            last_seen=last_seen_ts,
            support_events=support_events,
            active=True
        )

        self.versions.setdefault(key, []).append(version)
        return version

    def active_versions(self, entity_id: str):
        out = []
        for (eid, _), versions in self.versions.items():
            if eid == entity_id:
                out.extend(v for v in versions if v.active)
        return out

    def decay(self, tau: float = 7200.0):
        now = time.time()
        for versions in self.versions.values():
            for v in versions:
                if now - v.last_seen > tau:
                    v.active = False