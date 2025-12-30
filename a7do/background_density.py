from collections import deque
from dataclasses import dataclass
import time


@dataclass
class DensityPacket:
    text: str
    tags: list
    timestamp: float
    weight: float  # a simple “entropy pressure” proxy


class BackgroundDensity:
    """
    Buffers incoming information so cognition doesn’t decohere under load.
    Think: working-memory protection + deferred integration queue.
    """

    def __init__(self, max_queue: int = 250):
        self.queue = deque(maxlen=max_queue)
        self.working_set = deque(maxlen=50)  # what “makes it into thought”
        self.last_ingest_time = 0.0

    def ingest(self, text: str, tags: list):
        # Simple weight heuristic: length + number of tags
        weight = min(1.0, (len(text) / 280.0) + (0.05 * len(tags)))
        self.queue.append(DensityPacket(text=text, tags=tags, timestamp=time.time(), weight=weight))

    def should_promote(self, coherence_score: float | None) -> bool:
        if coherence_score is None:
            return True
        # Promote aggressively when coherent, cautiously when not
        return coherence_score >= 0.55

    def promote(self, coherence_score: float | None):
        """
        Move a small number of packets from background queue into working set.
        Coherence controls how many packets get promoted per cycle.
        """
        if not self.queue:
            return

        if coherence_score is None:
            budget = 3
        elif coherence_score >= 0.75:
            budget = 6
        elif coherence_score >= 0.55:
            budget = 3
        else:
            budget = 1

        for _ in range(min(budget, len(self.queue))):
            self.working_set.append(self.queue.popleft())

    def get_working_context(self, max_items: int = 8) -> str:
        """
        Produce a small context string for the reasoning engine.
        """
        items = list(self.working_set)[-max_items:]
        if not items:
            return ""
        lines = []
        for p in items:
            lines.append(f"- ({', '.join(p.tags)}) {p.text}")
        return "\n".join(lines)

    def stats(self) -> dict:
        return {
            "queue_len": len(self.queue),
            "working_len": len(self.working_set),
            "last_queue_item_tags": (self.queue[-1].tags if self.queue else []),
        }